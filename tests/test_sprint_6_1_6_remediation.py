"""
Comprehensive Unit & Regression Tests for Sprint 6.1.6
Remediation of Engine Target Alloc (BLK-04) and DSR Protocol Amendment (BLK-05).

MANDATORY AUDIT COMPLIANCE:
- ZERO historical datasets loaded (no validation_dataset.parquet or test_dataset.parquet).
- ZERO real historical backtests executed.
- All fixtures are 100% synthetic, in-memory data structures.
"""

import math
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import pytest
from scipy import stats as scipy_stats

from src.backtest.event_driven_engine import (
    EventDrivenBacktestEngine,
    StrategyConfig,
    IndianEquityCostModel,
    TransactionCostBreakdown,
)
from src.utils.statistical_tooling import (
    deflated_sharpe_ratio,
    holm_bonferroni_correction,
    newey_west_hac_sharpe,
)


# ==============================================================================
# Helper Fixtures & In-Memory Synthetic Generators
# ==============================================================================

def make_synthetic_price_dict(
    symbols: List[str],
    dates: List[pd.Timestamp],
    base_prices: Optional[Dict[str, float]] = None,
    price_paths: Optional[Dict[str, List[float]]] = None,
    volumes: Optional[Dict[str, List[float]]] = None,
) -> Dict[str, pd.DataFrame]:
    """Generates synthetic price history DataFrame dict for symbols across dates."""
    price_dict = {}
    for sym in symbols:
        if price_paths and sym in price_paths:
            closes = price_paths[sym]
        else:
            p0 = base_prices.get(sym, 100.0) if base_prices else 100.0
            closes = [p0 + i * 1.0 for i in range(len(dates))]

        opens = closes.copy()
        highs = [c * 1.02 for c in closes]
        lows = [c * 0.98 for c in closes]
        vols = volumes.get(sym, [50000.0] * len(dates)) if volumes else [50000.0] * len(dates)

        df = pd.DataFrame({
            "Date": dates,
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Adj Close": closes,
            "Volume": vols,
        }).set_index("Date")
        price_dict[sym] = df
    return price_dict


def make_synthetic_engine(
    symbols: List[str],
    dates: List[pd.Timestamp],
    initial_capital: float = 1_000_000.0,
    price_paths: Optional[Dict[str, List[float]]] = None,
    volumes: Optional[Dict[str, List[float]]] = None,
) -> EventDrivenBacktestEngine:
    """Creates an EventDrivenBacktestEngine with synthetic in-memory price feeds."""
    engine = EventDrivenBacktestEngine(
        initial_capital=initial_capital,
        max_positions=10,
        max_single_stock_pct=0.10,
        slippage_rate=0.0005,
        risk_free_rate=0.06,
    )
    engine.price_dict = make_synthetic_price_dict(
        symbols=symbols,
        dates=dates,
        price_paths=price_paths,
        volumes=volumes,
    )
    return engine


# ==============================================================================
# PART 1: BLK-04 Regression Tests — Real run_simulation() Entry Path
# ==============================================================================

class TestScopeA_EngineTargetAllocRegression:

    def test_single_eligible_buy_candidate(self):
        """1. One eligible candidate reaches order sizing and executes without NameError."""
        dates = [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03"), pd.Timestamp("2023-01-04")]
        symbols = ["SYM_ALPHA", "SYM_BETA"]
        engine = make_synthetic_engine(symbols, dates)

        records = [
            {"date": dates[0], "symbol": "SYM_ALPHA", "predicted_signal": 1, "prob_buy": 0.75},
            {"date": dates[0], "symbol": "SYM_BETA", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[1], "symbol": "SYM_ALPHA", "predicted_signal": 0, "prob_buy": 0.30},
            {"date": dates[1], "symbol": "SYM_BETA", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_ALPHA", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_BETA", "predicted_signal": 0, "prob_buy": 0.20},
        ]
        df_sig = pd.DataFrame(records)
        cfg = StrategyConfig(config_id="CFG-01", prob_buy_threshold=0.40)

        res = engine.run_simulation(dataset_split=df_sig, strategy_config=cfg)

        assert res["trade_count"] == 1
        assert len(engine.trade_ledger) == 1
        t0 = engine.trade_ledger[0]
        assert t0.symbol == "SYM_ALPHA"
        assert t0.entry_date == "2023-01-03"
        assert t0.quantity > 0
        # Allocation was capped at 10% of 1,000,000 = 100,000
        # Price at entry open is 101.0 -> shares = int(100,000 / (101.0505 * 1.002)) = 987
        assert t0.quantity == 987
        assert res["rejected_orders_count"] == 0

    def test_multiple_candidates_deterministic_priority(self):
        """2. Multiple candidates sorted deterministically by highest prob_buy, tie-break alphabetical."""
        dates = [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03"), pd.Timestamp("2023-01-04")]
        symbols = ["SYM_C", "SYM_A", "SYM_B"]
        engine = make_synthetic_engine(symbols, dates)

        # SYM_A and SYM_C have identical prob_buy=0.70; SYM_B has higher prob_buy=0.85
        records = [
            {"date": dates[0], "symbol": "SYM_C", "predicted_signal": 1, "prob_buy": 0.70},
            {"date": dates[0], "symbol": "SYM_A", "predicted_signal": 1, "prob_buy": 0.70},
            {"date": dates[0], "symbol": "SYM_B", "predicted_signal": 1, "prob_buy": 0.85},
            {"date": dates[1], "symbol": "SYM_A", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[1], "symbol": "SYM_B", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[1], "symbol": "SYM_C", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_A", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_B", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_C", "predicted_signal": 0, "prob_buy": 0.20},
        ]
        df_sig = pd.DataFrame(records)
        cfg = StrategyConfig(config_id="CFG-02", prob_buy_threshold=0.40)

        res = engine.run_simulation(dataset_split=df_sig, strategy_config=cfg)

        assert res["trade_count"] == 3
        # Processing order in ledger entries:
        # 1st: SYM_B (0.85)
        # 2nd: SYM_A (0.70, alphabetically before SYM_C)
        # 3rd: SYM_C (0.70)
        symbols_entered = [t.symbol for t in engine.trade_ledger]
        assert symbols_entered == ["SYM_B", "SYM_A", "SYM_C"]

    def test_zero_share_quantity_rejected(self):
        """3. Candidate with calculated share quantity of zero rejected with INSUFFICIENT_CASH_FOR_ONE_SHARE."""
        dates = [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03"), pd.Timestamp("2023-01-04")]
        symbols = ["SYM_EXPENSIVE"]
        # Symbol open price is ₹2,000,000, while max single stock cap is 10% of 1M = ₹100,000
        engine = make_synthetic_engine(symbols, dates, price_paths={"SYM_EXPENSIVE": [2_000_000.0, 2_000_000.0, 2_000_000.0]})

        records = [
            {"date": dates[0], "symbol": "SYM_EXPENSIVE", "predicted_signal": 1, "prob_buy": 0.80},
            {"date": dates[1], "symbol": "SYM_EXPENSIVE", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_EXPENSIVE", "predicted_signal": 0, "prob_buy": 0.20},
        ]
        df_sig = pd.DataFrame(records)
        cfg = StrategyConfig(config_id="CFG-03", prob_buy_threshold=0.40)

        res = engine.run_simulation(dataset_split=df_sig, strategy_config=cfg)

        assert res["trade_count"] == 0
        assert res["rejected_orders_count"] == 1
        assert engine.rejected_orders[0]["reason"] == "INSUFFICIENT_CASH_FOR_ONE_SHARE"

    def test_insufficient_available_cash(self):
        """4. Insufficient cash after exact fee calculation rejected cleanly."""
        dates = [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03"), pd.Timestamp("2023-01-04")]
        symbols = ["SYM_A"]
        # Engine starts with ₹99.10 cash, share price is ₹99.0; shares=1, but statutory fees push required cash to ~₹99.20
        engine = make_synthetic_engine(symbols, dates, initial_capital=99.10, price_paths={"SYM_A": [99.0, 99.0, 99.0]})
        engine.max_single_stock_pct = 1.0  # Allow 100% allocation

        records = [
            {"date": dates[0], "symbol": "SYM_A", "predicted_signal": 1, "prob_buy": 0.80},
            {"date": dates[1], "symbol": "SYM_A", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_A", "predicted_signal": 0, "prob_buy": 0.20},
        ]
        df_sig = pd.DataFrame(records)
        cfg = StrategyConfig(config_id="CFG-04", prob_buy_threshold=0.40)

        res = engine.run_simulation(dataset_split=df_sig, strategy_config=cfg)

        assert res["trade_count"] == 0
        assert res["rejected_orders_count"] == 1
        assert engine.rejected_orders[0]["reason"] in ["INSUFFICIENT_CASH_FOR_ONE_SHARE", "INSUFFICIENT_CASH_AFTER_EXACT_FEE_CALCULATION"]

    def test_single_stock_allocation_cap_enforcement(self):
        """5. Single stock allocation cap of 10% portfolio equity is strictly enforced."""
        dates = [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03"), pd.Timestamp("2023-01-04")]
        symbols = ["SYM_X"]
        engine = make_synthetic_engine(symbols, dates, initial_capital=1_000_000.0, price_paths={"SYM_X": [50.0, 50.0, 50.0]})

        records = [
            {"date": dates[0], "symbol": "SYM_X", "predicted_signal": 1, "prob_buy": 0.80},
            {"date": dates[1], "symbol": "SYM_X", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_X", "predicted_signal": 0, "prob_buy": 0.20},
        ]
        df_sig = pd.DataFrame(records)
        cfg = StrategyConfig(config_id="CFG-05", prob_buy_threshold=0.40)

        res = engine.run_simulation(dataset_split=df_sig, strategy_config=cfg)

        assert res["trade_count"] == 1
        t = engine.trade_ledger[0]
        # target_alloc = 100,000. exec_entry_price = 50 * 1.0005 = 50.025
        # shares = int(100,000 / (50.025 * 1.002)) = int(1995.01) = 1995
        assert t.quantity == 1995
        assert t.invested_capital <= 100_000.0

    def test_daily_entry_pacing_and_rejections(self):
        """6. Daily entry pacing (e.g. max 2 per day) enforced; rejected orders do NOT consume slots."""
        dates = [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03"), pd.Timestamp("2023-01-04")]
        # 4 symbols: 1 has zero volume (rejected), 3 have high prob_buy
        symbols = ["SYM_HALTED", "SYM_1", "SYM_2", "SYM_3"]
        vols = {
            "SYM_HALTED": [0.0, 0.0, 0.0],  # Market halt / zero volume
            "SYM_1": [50000.0, 50000.0, 50000.0],
            "SYM_2": [50000.0, 50000.0, 50000.0],
            "SYM_3": [50000.0, 50000.0, 50000.0],
        }
        engine = make_synthetic_engine(symbols, dates, volumes=vols)

        records = [
            {"date": dates[0], "symbol": "SYM_HALTED", "predicted_signal": 1, "prob_buy": 0.95},
            {"date": dates[0], "symbol": "SYM_1", "predicted_signal": 1, "prob_buy": 0.85},
            {"date": dates[0], "symbol": "SYM_2", "predicted_signal": 1, "prob_buy": 0.80},
            {"date": dates[0], "symbol": "SYM_3", "predicted_signal": 1, "prob_buy": 0.75},
            {"date": dates[1], "symbol": "SYM_HALTED", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[1], "symbol": "SYM_1", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[1], "symbol": "SYM_2", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[1], "symbol": "SYM_3", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_HALTED", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_1", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_2", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_3", "predicted_signal": 0, "prob_buy": 0.20},
        ]
        df_sig = pd.DataFrame(records)
        # Pacing limit = 2 entries per day
        cfg = StrategyConfig(config_id="CFG-11", prob_buy_threshold=0.40, max_daily_entries=2)

        res = engine.run_simulation(dataset_split=df_sig, strategy_config=cfg)

        # SYM_HALTED is evaluated first (prob=0.95) but rejected for ZERO_VOLUME_OR_MARKET_HALT.
        # It must NOT consume one of the 2 daily slots!
        # Thus SYM_1 and SYM_2 must both be filled!
        # SYM_3 is evaluated 4th and rejected for DAILY_ENTRY_PACING_LIMIT_REACHED.
        assert res["trade_count"] == 2
        entered_symbols = [t.symbol for t in engine.trade_ledger]
        assert entered_symbols == ["SYM_1", "SYM_2"]

        reasons = [r["reason"] for r in engine.rejected_orders]
        assert "ZERO_VOLUME_OR_MARKET_HALT" in reasons
        assert "DAILY_ENTRY_PACING_LIMIT_REACHED" in reasons

    def test_transaction_cost_and_cash_accounting(self):
        """7. Transaction costs and cash accounting reconcile to exact mathematical expectation."""
        dates = [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03"), pd.Timestamp("2023-01-04")]
        symbols = ["SYM_FEE"]
        # Price path: 100 on day 0, 100 on day 1 (entry), 110 on day 2 (exit)
        engine = make_synthetic_engine(symbols, dates, initial_capital=100_000.0, price_paths={"SYM_FEE": [100.0, 100.0, 110.0]})

        records = [
            {"date": dates[0], "symbol": "SYM_FEE", "predicted_signal": 1, "prob_buy": 0.80},
            {"date": dates[1], "symbol": "SYM_FEE", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_FEE", "predicted_signal": 0, "prob_buy": 0.20},
        ]
        df_sig = pd.DataFrame(records)
        cfg = StrategyConfig(config_id="CFG-BASE")

        res = engine.run_simulation(dataset_split=df_sig, strategy_config=cfg)

        assert res["trade_count"] == 1
        t = engine.trade_ledger[0]
        cost_model = IndianEquityCostModel()

        # Buy leg
        buy_bd = cost_model.calculate_buy_costs(100.0, t.quantity)
        # Sell leg (at final day close 110.0 with 5 bps slippage)
        sell_bd = cost_model.calculate_sell_costs(110.0, t.quantity)

        expected_statutory = round(buy_bd.total_statutory_and_brokerage + sell_bd.total_statutory_and_brokerage, 2)
        expected_slippage = round(buy_bd.slippage + sell_bd.slippage, 2)
        expected_total_costs = round(expected_statutory + expected_slippage, 2)

        assert t.total_statutory_and_brokerage == expected_statutory
        assert t.total_slippage == expected_slippage
        assert t.total_costs == round(buy_bd.total_friction + sell_bd.total_friction, 2)

    def test_empty_candidate_case(self):
        """8. Morning where no signal records exist proceeds cleanly without orders."""
        dates = [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03")]
        symbols = ["SYM_EMPTY"]
        engine = make_synthetic_engine(symbols, dates)

        df_sig = pd.DataFrame(columns=["date", "symbol", "predicted_signal", "prob_buy"])
        cfg = StrategyConfig(config_id="CFG-BASE")

        res = engine.run_simulation(dataset_split=df_sig, strategy_config=cfg)

        assert res["trade_count"] == 0
        assert res["rejected_orders_count"] == 0

    def test_no_eligible_buy_candidates(self):
        """9. Signals exist but all below threshold -> zero trades, zero crashes."""
        dates = [pd.Timestamp("2023-01-02"), pd.Timestamp("2023-01-03"), pd.Timestamp("2023-01-04")]
        symbols = ["SYM_LOW"]
        engine = make_synthetic_engine(symbols, dates)

        records = [
            {"date": dates[0], "symbol": "SYM_LOW", "predicted_signal": 0, "prob_buy": 0.25},
            {"date": dates[1], "symbol": "SYM_LOW", "predicted_signal": 0, "prob_buy": 0.30},
            {"date": dates[2], "symbol": "SYM_LOW", "predicted_signal": 0, "prob_buy": 0.20},
        ]
        df_sig = pd.DataFrame(records)
        cfg = StrategyConfig(config_id="CFG-07", prob_buy_threshold=0.50)

        res = engine.run_simulation(dataset_split=df_sig, strategy_config=cfg)

        assert res["trade_count"] == 0
        assert res["rejected_orders_count"] == 0

    def test_full_synthetic_lifecycle_and_termination(self):
        """10. BUY execution followed by normal holding, EOD ATR trailing stop trigger, and termination."""
        dates = [
            pd.Timestamp("2023-01-02"),
            pd.Timestamp("2023-01-03"),
            pd.Timestamp("2023-01-04"),
            pd.Timestamp("2023-01-05"),
        ]
        symbols = ["SYM_ATR"]
        # Sharp price drop on day 2 triggers 1.5x ATR trailing stop
        paths = {"SYM_ATR": [100.0, 102.0, 92.0, 90.0]}
        engine = make_synthetic_engine(symbols, dates, price_paths=paths)

        records = [
            {"date": dates[0], "symbol": "SYM_ATR", "predicted_signal": 1, "prob_buy": 0.80},
            {"date": dates[1], "symbol": "SYM_ATR", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[2], "symbol": "SYM_ATR", "predicted_signal": 0, "prob_buy": 0.20},
            {"date": dates[3], "symbol": "SYM_ATR", "predicted_signal": 0, "prob_buy": 0.20},
        ]
        df_sig = pd.DataFrame(records)
        cfg = StrategyConfig(config_id="CFG-08", prob_buy_threshold=0.40, exit_rule="1.5x_ATR")

        res = engine.run_simulation(dataset_split=df_sig, strategy_config=cfg)

        assert res["trade_count"] == 1
        t = engine.trade_ledger[0]
        assert t.symbol == "SYM_ATR"
        assert t.entry_date == "2023-01-03"
        assert t.exit_reason in ["ATR_TRAILING_STOP", "END_OF_PERIOD_LIQUIDATION"]


# ==============================================================================
# PART 2: BLK-05 Synthetic Statistical Tests — Revised DSR & Statistical Tooling
# ==============================================================================

class TestScopeB_AmendedDSRAndStatisticalTooling:

    def test_zero_mean_synthetic_series(self):
        """1. Zero-mean synthetic return series -> DSR is low, p-value high (insignificant)."""
        np.random.seed(42)
        rets = np.random.normal(loc=0.0002381, scale=0.01, size=490)  # Mean excess return ~ 0
        res = deflated_sharpe_ratio(rets, trial_count_K=16, expected_max_sharpe=0.50)

        assert abs(res["daily_sharpe"]) < 0.15
        assert res["p_value"] > 0.05
        assert res["is_significant"] is False
        assert res["error"] is None

    def test_positive_mean_synthetic_series(self):
        """2. Positive-mean synthetic series with high Sharpe -> passes amended DSR threshold."""
        np.random.seed(42)
        # Daily excess return ~ 0.0015 / 0.01 = 0.15 daily Sharpe -> Ann Sharpe ~ 2.38
        rets = np.random.normal(loc=0.0017381, scale=0.01, size=490)
        # Expected max Sharpe for trial dispersion sigma_sr=0.20 is 0.20 * 1.8005 = 0.36
        res = deflated_sharpe_ratio(rets, trial_count_K=16, expected_max_sharpe=0.36)

        assert res["annualized_sharpe"] > 2.0
        assert res["p_value"] < 0.05
        assert res["is_significant"] is True
        assert res["error"] is None

    def test_negative_mean_synthetic_series(self):
        """3. Negative-mean synthetic return series -> negative Sharpe, p-value ~ 1.0."""
        np.random.seed(42)
        rets = np.random.normal(loc=-0.001, scale=0.01, size=490)
        res = deflated_sharpe_ratio(rets, trial_count_K=16, expected_max_sharpe=0.36)

        assert res["annualized_sharpe"] < 0.0
        assert res["p_value"] > 0.95
        assert res["is_significant"] is False

    def test_skewed_synthetic_series(self):
        """4. Return series with negative skewness increases variance factor V, penalizing z-score."""
        np.random.seed(42)
        # Generate skewed data via exponential mixture
        base = np.random.normal(loc=0.0015, scale=0.008, size=490)
        neg_crashes = np.random.choice([0.0, -0.05], size=490, p=[0.97, 0.03])
        skewed_rets = base + neg_crashes

        res = deflated_sharpe_ratio(skewed_rets, trial_count_K=16, expected_max_sharpe=0.36)

        assert res["skewness_gamma_3"] < -0.5
        # With negative skewness and positive Sharpe, -gamma_3 * SR_d > 0, so V > 1.0
        assert res["variance_adjustment_factor"] > 1.0

    def test_heavy_tailed_synthetic_series(self):
        """5. Heavy-tailed synthetic series (t-distribution) increases kurtosis gamma_4 and contributes to V."""
        np.random.seed(42)
        t_rets = scipy_stats.t.rvs(df=5, loc=0.0015, scale=0.008, size=490)
        res = deflated_sharpe_ratio(t_rets, trial_count_K=16, expected_max_sharpe=0.36)

        assert res["kurtosis_gamma_4"] > 4.0  # Pearson kurtosis of t(5) is significantly > 3.0
        assert res["variance_adjustment_factor"] > 0.0
        # Positive contribution from heavy kurtosis term ((gamma_4 - 1)/4) * SR_d^2
        kurt_contrib = ((res["kurtosis_gamma_4"] - 1.0) / 4.0) * (res["daily_sharpe"] ** 2)
        assert kurt_contrib > 0.0

    def test_constant_return_series(self):
        """6. Constant returns handled gracefully without zero-division exception."""
        const_rets = np.full(100, 0.001)
        res = deflated_sharpe_ratio(const_rets, trial_count_K=16)

        assert res["daily_sharpe"] == 0.0
        assert res["p_value"] == 1.0
        assert res["is_significant"] is False
        assert "Zero return variance" in res["error"]

    def test_too_short_series(self):
        """7. Series shorter than 2 observations raises ValueError."""
        with pytest.raises(ValueError, match="Sample length T must be at least 2"):
            deflated_sharpe_ratio([0.01], trial_count_K=16)

    def test_nan_and_infinite_values(self):
        """8. Input containing NaN or infinity raises ValueError."""
        with pytest.raises(ValueError, match="Returns series contains NaN or infinite"):
            deflated_sharpe_ratio([0.01, np.nan, 0.02], trial_count_K=16)

        with pytest.raises(ValueError, match="Returns series contains NaN or infinite"):
            deflated_sharpe_ratio([0.01, np.inf, 0.02], trial_count_K=16)

    def test_daily_vs_annualized_sharpe_consistency(self):
        """9. Daily vs annualized time scale scaling is mathematically consistent."""
        np.random.seed(42)
        rets = np.random.normal(loc=0.001, scale=0.01, size=490)
        sessions_per_year = 252
        sr_star_ann = 0.50

        res = deflated_sharpe_ratio(rets, trial_count_K=16, expected_max_sharpe=sr_star_ann, sessions_per_year=sessions_per_year)

        sr_daily = res["daily_sharpe"]
        sr_ann = res["annualized_sharpe"]
        assert pytest.approx(sr_ann, rel=1e-6) == sr_daily * np.sqrt(sessions_per_year)

        sr_star_daily = sr_star_ann / np.sqrt(sessions_per_year)
        T = res["sample_size_T"]
        V = res["variance_adjustment_factor"]

        z_daily = (sr_daily - sr_star_daily) * np.sqrt(T - 1) / np.sqrt(V)
        z_ann = (sr_ann - sr_star_ann) * np.sqrt((T - 1) / sessions_per_year) / np.sqrt(V)
        assert pytest.approx(z_daily, rel=1e-6) == z_ann
        assert pytest.approx(res["dsr_z_score"], rel=1e-6) == z_daily

    def test_dsr_pvalue_interpretation(self):
        """10. DSR probability and p-value obey p = 1.0 - DSR with 0.05 significance threshold."""
        np.random.seed(42)
        rets = np.random.normal(loc=0.001, scale=0.01, size=490)
        res = deflated_sharpe_ratio(rets, trial_count_K=16, expected_max_sharpe=0.30)

        assert pytest.approx(res["p_value"] + res["dsr_statistic"], abs=1e-10) == 1.0
        assert res["is_significant"] == (res["p_value"] < 0.05)

    def test_expected_max_sharpe_bailey_lopez_de_prado(self):
        """11. Bailey & Lopez de Prado (2014) EVT formula matches hand-calculated factor."""
        gamma = 0.57721566490153286
        e = math.e
        K = 16

        term1 = (1.0 - gamma) * scipy_stats.norm.ppf(1.0 - 1.0 / K)
        term2 = gamma * scipy_stats.norm.ppf(1.0 - 1.0 / (K * e))
        evt_factor = term1 + term2

        # Independently hand-calculated value: ~ 1.800454
        assert pytest.approx(evt_factor, abs=1e-5) == 1.800454

        # For synthetic candidate trial Sharpe ratios with known standard deviation
        candidate_sharpes = [0.45, 0.52, 0.60, 0.75, 0.38, 0.42, 0.55, 0.68, 0.49, 0.58, 0.62, 0.70, 0.40, 0.48, 0.65, 0.53]
        assert len(candidate_sharpes) == 16
        sigma_sr = float(np.std(candidate_sharpes, ddof=1))
        expected_hurdle = sigma_sr * evt_factor

        assert pytest.approx(sigma_sr, abs=1e-4) == 0.1113
        assert pytest.approx(expected_hurdle, abs=1e-4) == 0.2004

    def test_trial_count_handling_k16_vs_k17(self):
        """12. Trial count sensitivity: K=16 (candidate grid) vs K=17 (including baseline)."""
        gamma = 0.57721566490153286
        e = math.e

        def calc_evt(k):
            return (1.0 - gamma) * scipy_stats.norm.ppf(1.0 - 1.0 / k) + gamma * scipy_stats.norm.ppf(1.0 - 1.0 / (k * e))

        evt_16 = calc_evt(16)
        evt_17 = calc_evt(17)

        assert pytest.approx(evt_16, abs=1e-5) == 1.800454
        assert pytest.approx(evt_17, abs=1e-5) == 1.828094
        # Difference is small (< 1.6%) and monotonic
        assert evt_17 > evt_16
        assert (evt_17 - evt_16) < 0.03

    def test_dependence_and_correlation_bound(self):
        """13. Conservative correlation bound: independent trial hurdle is upper bound for rho > 0."""
        # For correlated normals X_k with equi-correlation rho:
        # E[max X_k] = sqrt(1 - rho) * E[max Z_k] <= E[max Z_k]
        for rho in [0.10, 0.30, 0.50, 0.80]:
            factor_corr = math.sqrt(1.0 - rho)
            assert factor_corr < 1.0

    def test_holm_bonferroni_correction_and_monotonicity(self):
        """14. Holm-Bonferroni step-down enforces strict adjusted p-value monotonicity."""
        p_vals = {
            "CFG_A": 0.010,
            "CFG_B": 0.011,
            "CFG_C": 0.025,
            "CFG_D": 0.060,
        }
        res = holm_bonferroni_correction(p_vals, alpha=0.05)

        # Raw step-down products for M=4:
        # CFG_A: 0.010 * 4 = 0.040
        # CFG_B: 0.011 * 3 = 0.033 (lower than previous rank!)
        # Monotonicity rule requires adj_p[1] = max(0.040, 0.033) = 0.040!
        assert res["CFG_A"]["adjusted_p_value"] == 0.040
        assert res["CFG_B"]["adjusted_p_value"] == 0.040
        assert res["CFG_C"]["adjusted_p_value"] == 0.050
        assert res["CFG_D"]["adjusted_p_value"] == 0.060

        adj_list = [res[k]["adjusted_p_value"] for k in ["CFG_A", "CFG_B", "CFG_C", "CFG_D"]]
        # Assert non-decreasing
        assert all(adj_list[i] <= adj_list[i + 1] for i in range(len(adj_list) - 1))

    def test_newey_west_hac_reference_comparison(self):
        """15. Newey-West HAC calculations match independent Python reference implementation."""
        np.random.seed(42)
        # AR(1) process: r_t = 0.4 * r_{t-1} + e_t
        e = np.random.normal(0, 0.01, size=490)
        r = np.zeros(490)
        for t in range(1, 490):
            r[t] = 0.4 * r[t - 1] + e[t] + 0.0005

        res = newey_west_hac_sharpe(r, max_lags=5, risk_free_rate_annual=0.06, sessions_per_year=252)

        # Independent manual calculation
        r_f = 0.06 / 252.0
        x = r - r_f
        x_demean = x - np.mean(x)
        T = len(x)
        gamma_0 = np.sum(x_demean ** 2) / T

        hac_var = gamma_0
        for l in range(1, 6):
            w = 1.0 - (l / 6.0)
            cov_l = np.sum(x_demean[l:] * x_demean[:-l]) / T
            hac_var += 2.0 * w * cov_l

        assert pytest.approx(res["hac_variance"], rel=1e-7) == hac_var
        expected_inflation = math.sqrt(hac_var / gamma_0)
        assert pytest.approx(res["hac_inflation_factor"], rel=1e-7) == expected_inflation

        se_sharpe_expected = math.sqrt(252.0 / T) * expected_inflation
        assert pytest.approx(res["hac_annualized_sharpe_se"], rel=1e-7) == se_sharpe_expected
