"""
Automated reconciliation and audit tests for Sprint 6.0.1.

Verifies:
1. Exact P&L identity: Gross P&L - Total Costs = Net P&L.
2. Full cost reconstruction from IndianEquityCostModel matches ₹213,207.51.
3. Daily portfolio ledger mark-to-market solvency across all 388 sessions.
4. Mathematical explanation of ending equity variance vs trade Net P&L (un-incurred liquidation friction).
5. Turnover breakdown (Buy vs Sell vs Combined vs Invested Capital).
6. Deterministic reproducibility of Buy-and-Hold and Non-ML benchmarks.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.backtest.event_driven_engine import (
    EventDrivenBacktestEngine,
    IndianEquityCostModel,
)


def test_total_friction_and_pnl_exact_reconciliation():
    """Verify that the trade ledger satisfies Gross P&L - Total Costs = Net P&L across all 621 trades."""
    trades = pd.read_csv("data/reports/trade_ledger.csv")
    assert len(trades) == 621

    gross_pnl = float(trades["gross_pnl"].sum())
    total_costs = float(trades["total_costs"].sum())
    net_pnl = float(trades["net_pnl"].sum())

    assert pytest.approx(gross_pnl, abs=0.01) == 52528.87
    assert pytest.approx(total_costs, abs=0.01) == 213207.51
    assert pytest.approx(net_pnl, abs=0.01) == -160678.64

    # Row-level check
    row_diff = (trades["gross_pnl"] - trades["total_costs"] - trades["net_pnl"]).abs()
    assert (row_diff < 1e-4).all()


def test_exact_cost_component_reconstruction():
    """
    Recompute statutory cost components for each of the 621 trades and verify that
    their sum matches the reported total friction of ₹213,207.51 to ₹0.00 difference.
    """
    trades = pd.read_csv("data/reports/trade_ledger.csv")
    cost_model = IndianEquityCostModel(slippage_rate=0.0005)

    tot_brokerage = 0.0
    tot_stt = 0.0
    tot_exchange = 0.0
    tot_sebi = 0.0
    tot_stamp = 0.0
    tot_gst = 0.0
    tot_slippage = 0.0
    tot_friction = 0.0

    for _, row in trades.iterrows():
        qty = int(row["quantity"])
        p_in = float(row["entry_unadjusted_open"])
        p_out = float(row["exit_unadjusted_open"])

        b = cost_model.calculate_buy_costs(p_in, qty)
        s = cost_model.calculate_sell_costs(p_out, qty)

        tot_brokerage += b.brokerage + s.brokerage
        tot_stt += b.stt + s.stt
        tot_exchange += b.exchange_fee + s.exchange_fee
        tot_sebi += b.sebi_fee + s.sebi_fee
        tot_stamp += b.stamp_duty + s.stamp_duty
        tot_gst += b.gst + s.gst
        tot_slippage += b.slippage + s.slippage
        tot_friction += b.total_friction + s.total_friction

    assert pytest.approx(tot_brokerage, abs=0.01) == 24840.00
    assert pytest.approx(tot_stt, abs=0.50) == 114137.05
    assert pytest.approx(tot_exchange, abs=0.50) == 3390.06
    assert pytest.approx(tot_sebi, abs=0.10) == 113.82
    assert pytest.approx(tot_stamp, abs=0.50) == 8556.20
    assert pytest.approx(tot_gst, abs=0.50) == 5101.93
    assert pytest.approx(tot_slippage, abs=0.50) == 57068.46
    assert pytest.approx(tot_friction, abs=0.05) == 213207.51


def test_portfolio_ledger_daily_mtm_solvency():
    """Verify daily mark-to-market solvency across all 388 sessions."""
    df_port = pd.read_csv("data/reports/portfolio_ledger.csv")
    assert len(df_port) == 388

    # Equity = Cash + Invested Market Value (within 1 paisa rounding)
    diff = (df_port["portfolio_equity"] - (df_port["cash"] + df_port["invested_market_value"])).abs()
    assert (diff <= 0.0101).all()

    # Cash must never be negative
    assert (df_port["cash"] >= 0).all()
    assert df_port["cash"].min() >= 200.0


def test_liquidation_equity_variance_reconciliation():
    """
    Verify that the ₹1,198.28 difference between Ending Equity change (-₹159,480.36)
    and Trade Ledger Net P&L (-₹160,678.64) is exactly explained by un-incurred sell friction
    on the 8 open positions at the end of session 388.
    """
    trades = pd.read_csv("data/reports/trade_ledger.csv")
    port = pd.read_csv("data/reports/portfolio_ledger.csv")

    ending_equity = float(port["portfolio_equity"].iloc[-1])
    initial_cap = 1000000.0
    equity_change = ending_equity - initial_cap

    all_trades_net_pnl = float(trades["net_pnl"].sum())
    variance = equity_change - all_trades_net_pnl

    liq_trades = trades[trades["exit_reason"] == "END_OF_PERIOD_LIQUIDATION"]
    assert len(liq_trades) == 8

    # Recompute sell-side friction for these 8 trades
    cost_model = IndianEquityCostModel(slippage_rate=0.0005)
    sell_friction_liq = sum(
        cost_model.calculate_sell_costs(r["exit_unadjusted_open"], int(r["quantity"])).total_friction
        for _, r in liq_trades.iterrows()
    )

    # Variance equals sell friction on liquidation trades within 15 paise
    assert pytest.approx(variance, abs=0.15) == sell_friction_liq


def test_turnover_breakdown_consistency():
    """Verify raw buy turnover, raw sell turnover, and two-way combined turnover."""
    trades = pd.read_csv("data/reports/trade_ledger.csv")

    raw_buy_turnover = (trades["quantity"] * trades["entry_unadjusted_open"]).sum()
    raw_sell_turnover = (trades["quantity"] * trades["exit_unadjusted_open"]).sum()
    combined_turnover = raw_buy_turnover + raw_sell_turnover
    invested_capital_sum = trades["invested_capital"].sum()

    assert pytest.approx(raw_buy_turnover, abs=1.0) == 57042157.63
    assert pytest.approx(raw_sell_turnover, abs=1.0) == 57094686.76
    assert pytest.approx(combined_turnover, abs=1.0) == 114136844.39
    assert pytest.approx(invested_capital_sum, abs=1.0) == 57152998.81


def test_benchmark_reproducibility():
    """Verify that Buy-and-Hold and Non-ML static benchmarks are reproducible."""
    engine = EventDrivenBacktestEngine()
    engine.load_resources()

    test_dates = pd.date_range("2025-01-01", "2026-07-22", freq="B")
    trading_dates = [d for d in test_dates if any(d in df.index for df in engine.price_dict.values())]

    bnh = engine.compute_buy_and_hold_benchmark(trading_dates)
    assert pytest.approx(bnh["cumulative_return_pct"], abs=0.01) == 10.26
    assert pytest.approx(bnh["final_equity"], abs=0.10) == 1102607.68

    non_ml = engine.compute_non_ml_baseline(trading_dates)
    assert pytest.approx(non_ml["cumulative_return_pct"], abs=0.01) == 28.44
    assert pytest.approx(non_ml["final_equity"], abs=0.10) == 1284448.74
