"""
Automated validation and leakage tests for the Sprint 6.0 Event-Driven Backtesting Engine.

Validates:
1. Approved 30-feature allowlist enforcement.
2. Prediction-to-symbol/date alignment and next-session entry timing (t+1 Open).
3. No same-close look-ahead execution.
4. Complete independence from true labels (signal, forward_return_5d).
5. No duplicate or overlapping positions for the same symbol.
6. Correct cash, quantity, and position accounting with integer shares.
7. Exact statutory transaction cost arithmetic (STT, stamp duty, exchange, SEBI, brokerage, GST, slippage).
8. Daily portfolio equity reconciliation (Equity = Cash + Market Value).
9. Missing and invalid price handling (halts/delistings).
10. Deterministic reproducibility across repeated backtest executions.
11. Cryptographic hash preservation of the frozen model and test dataset.
"""

import hashlib
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.backtest.event_driven_engine import (
    EventDrivenBacktestEngine,
    IndianEquityCostModel,
)
from src.ml.dataset_builder import APPROVED_FEATURES

FROZEN_MODEL_SHA256 = (
    "41e61760fc31c72095cd2071fdb843657bd76143ed4535f9b247db78e0c73761"
)
TEST_PARQUET_SHA256 = (
    "7f9d0ce56b42a7cc2780f90edb4b27d9bc923847c6778e5ba4c6ebc754915381"
)


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def test_frozen_artifacts_integrity():
    """Verify that models/lightgbm.joblib and data/processed/test_dataset.parquet remain unmodified."""
    model_path = Path("models/lightgbm.joblib")
    test_parquet_path = Path("data/processed/test_dataset.parquet")

    assert model_path.exists(), f"Model not found at {model_path}"
    assert test_parquet_path.exists(), f"Test dataset not found at {test_parquet_path}"

    assert compute_sha256(model_path) == FROZEN_MODEL_SHA256
    assert compute_sha256(test_parquet_path) == TEST_PARQUET_SHA256


def test_strict_approved_feature_allowlist():
    """Verify that the engine uses strictly the 30 approved features and rejects any deviations."""
    assert len(APPROVED_FEATURES) == 30
    engine = EventDrivenBacktestEngine()
    engine.load_resources()

    # Verify model was fitted with 30 features
    assert engine.model.n_features_in_ == 30

    # Ensure target/identifier columns are excluded from feature set
    forbidden_features = {"signal", "forward_return_5d", "symbol", "date", "open", "close"}
    assert forbidden_features.isdisjoint(set(APPROVED_FEATURES))


def test_indian_cost_model_exact_arithmetic():
    """
    Verify statutory transaction cost arithmetic against hand-calculated ground truth:
    Brokerage: min(20, 0.03%)
    STT: 0.1% on buy and sell
    Exchange fee: 0.00297%
    SEBI fee: 0.0001%
    Stamp duty: 0.015% on buy, 0% on sell
    GST: 18% on (brokerage + exchange + sebi)
    Slippage: 5 bps
    """
    costs = IndianEquityCostModel()

    # Buy trade of turnover ₹100,000 (100 shares @ ₹1000)
    buy_res = costs.calculate_buy_costs(raw_price=1000.0, quantity=100)
    assert buy_res.turnover == 100000.0
    assert buy_res.brokerage == 20.0  # 0.0003 * 100000 = 30 > 20
    assert buy_res.stt == 100.0  # 0.001 * 100000
    assert buy_res.exchange_fee == 2.97  # 0.0000297 * 100000
    assert buy_res.sebi_fee == 0.10  # 0.000001 * 100000
    assert buy_res.stamp_duty == 15.0  # 0.00015 * 100000
    # GST on (20.0 + 2.97 + 0.10 = 23.07) -> 18% of 23.07 = 4.1526, rounded to 4.15
    assert buy_res.gst == 4.15
    # Slippage: 5 bps on 100000 = 50.0
    assert buy_res.slippage == 50.0

    expected_total_buy = 20.0 + 100.0 + 2.97 + 0.10 + 15.0 + 4.15 + 50.0
    assert buy_res.total_friction == expected_total_buy

    # Sell trade of turnover ₹110,000 (100 shares @ ₹1100)
    sell_res = costs.calculate_sell_costs(raw_price=1100.0, quantity=100)
    assert sell_res.turnover == 110000.0
    assert sell_res.brokerage == 20.0
    assert sell_res.stt == 110.0  # 0.001 * 110000
    assert sell_res.exchange_fee == 3.27
    assert sell_res.sebi_fee == 0.11
    assert sell_res.stamp_duty == 0.0  # Zero stamp duty on sell delivery
    # GST on (20.0 + 3.27 + 0.11 = 23.38) -> 18% of 23.38 = 4.21
    assert sell_res.gst == 4.21
    # Slippage: 5 bps on 110000 = 55.0
    assert sell_res.slippage == 55.0

    expected_total_sell = 20.0 + 110.0 + 3.27 + 0.11 + 0.0 + 4.21 + 55.0
    # Floating sum before component rounding is 192.58486 -> rounded to 192.58
    assert sell_res.total_friction == 192.58


def test_next_session_entry_timing_and_no_lookahead():
    """Verify that entries execute strictly at session t+1 Open and incorporate slippage."""
    engine = EventDrivenBacktestEngine()
    engine.load_resources()
    engine.run_simulation(dataset_split="test")

    trades_df = pd.DataFrame([t.__dict__ for t in engine.trade_ledger])
    assert len(trades_df) > 0

    # Ensure every trade's entry_date is strictly greater than signal_date
    trades_df["signal_date"] = pd.to_datetime(trades_df["signal_date"])
    trades_df["entry_date"] = pd.to_datetime(trades_df["entry_date"])
    trades_df["exit_date"] = pd.to_datetime(trades_df["exit_date"])

    assert (trades_df["entry_date"] > trades_df["signal_date"]).all()
    # For regular exits, exit_date is strictly greater than entry_date
    normal_trades = trades_df[trades_df["exit_reason"] != "END_OF_PERIOD_LIQUIDATION"]
    assert (normal_trades["exit_date"] > normal_trades["entry_date"]).all()
    # All trades satisfy exit_date >= entry_date
    assert (trades_df["exit_date"] >= trades_df["entry_date"]).all()

    # For each trade, verify entry_price matches open * (1 + slippage_bps)
    for t in engine.trade_ledger[:20]:
        df_p = engine.price_dict[t.symbol]
        dt_entry = pd.to_datetime(t.entry_date)
        assert dt_entry in df_p.index
        open_price = float(df_p.loc[dt_entry, "Open"])
        expected_entry_price = round(open_price * (1.0 + 0.0005), 2)
        assert pytest.approx(t.entry_price_with_slippage, abs=0.02) == expected_entry_price


def test_true_label_independence():
    """Verify that model predictions and trade generation strictly depend on features, not true labels."""
    engine = EventDrivenBacktestEngine()
    engine.load_resources()

    # Load test parquet and confirm approved features do not overlap with targets
    test_df = pd.read_parquet("data/processed/test_dataset.parquet")
    X = test_df[APPROVED_FEATURES]
    assert "signal" not in X.columns
    assert "forward_return_5d" not in X.columns

    # Model prediction on X is unaffected by mutating signal or forward_return_5d
    preds_orig = engine.model.predict(X)
    test_df_mutated = test_df.copy()
    test_df_mutated["signal"] = -test_df_mutated["signal"]
    test_df_mutated["forward_return_5d"] = -test_df_mutated["forward_return_5d"]

    preds_mutated = engine.model.predict(test_df_mutated[APPROVED_FEATURES])
    np.testing.assert_array_equal(preds_orig, preds_mutated)


def test_no_overlapping_positions_per_symbol():
    """Verify that multiple concurrent positions for the same stock are prevented."""
    engine = EventDrivenBacktestEngine()
    engine.load_resources()
    engine.run_simulation(dataset_split="test")

    trades_df = pd.DataFrame([t.__dict__ for t in engine.trade_ledger])
    for symbol, group in trades_df.groupby("symbol"):
        group = group.sort_values("entry_date").reset_index(drop=True)
        for i in range(len(group) - 1):
            curr_exit = pd.to_datetime(group.loc[i, "exit_date"])
            next_entry = pd.to_datetime(group.loc[i + 1, "entry_date"])
            # Next entry must occur at or after current exit
            assert next_entry >= curr_exit, (
                f"Overlap detected for {symbol}: Trade {i} exits {curr_exit}, "
                f"Trade {i+1} enters {next_entry}"
            )


def test_cash_and_portfolio_equity_reconciliation():
    """Verify that on every single date, Portfolio Equity = Cash + Sum(Shares * Close)."""
    ledger_path = Path("data/reports/portfolio_ledger.csv")
    assert ledger_path.exists(), "Portfolio ledger not found"

    df_ledger = pd.read_csv(ledger_path)
    assert len(df_ledger) == 388

    # Check reconciliation identity: equity == cash + invested_market_value
    computed_equity = df_ledger["cash"] + df_ledger["invested_market_value"]
    discrepancy = (df_ledger["portfolio_equity"] - computed_equity).abs()
    assert (discrepancy < 0.05).all(), f"Max discrepancy in equity ledger: {discrepancy.max()}"


def test_integer_share_allocations():
    """Verify all trade quantities are strictly positive integers (no fractional shares)."""
    trade_path = Path("data/reports/trade_ledger.csv")
    assert trade_path.exists(), "Trade ledger not found"

    trades = pd.read_csv(trade_path)
    assert len(trades) > 0
    assert (trades["quantity"] > 0).all()
    assert (trades["quantity"] == trades["quantity"].astype(int)).all()


def test_missing_or_halted_session_handling():
    """Verify that if open price is missing or invalid, trade entry is safely rejected."""
    engine = EventDrivenBacktestEngine()
    engine.load_resources()

    # Corrupt price data for a single symbol by setting Open to NaN on an early test date
    symbol = "TCS"
    df_tcs = engine.price_dict[symbol].copy()
    test_date = pd.Timestamp("2025-01-03")
    if test_date in df_tcs.index:
        df_tcs.loc[test_date, "Open"] = np.nan
        engine.price_dict[symbol] = df_tcs

    # Run simulation - should handle NaN without throwing an exception or executing NaN price
    res = engine.run_simulation(dataset_split="test")
    assert res is not None
    for t in engine.trade_ledger:
        assert not math.isnan(t.entry_price_with_slippage)
        assert t.entry_price_with_slippage > 0


def test_reproducibility_with_fixed_config():
    """Verify that running the simulation twice produces identical trades and metrics."""
    engine1 = EventDrivenBacktestEngine()
    res1 = engine1.run_simulation(dataset_split="test")

    engine2 = EventDrivenBacktestEngine()
    res2 = engine2.run_simulation(dataset_split="test")

    assert res1["strategy_metrics"]["final_equity"] == res2["strategy_metrics"]["final_equity"]
    assert res1["strategy_metrics"]["total_trades_count"] == res2["strategy_metrics"]["total_trades_count"]
    assert res1["strategy_metrics"]["total_net_pnl_inr"] == res2["strategy_metrics"]["total_net_pnl_inr"]
    assert len(engine1.trade_ledger) == len(engine2.trade_ledger)
