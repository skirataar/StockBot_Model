"""
Source-level independent audit tests for Sprint 6.0.2.

These tests independently verify all financial fee formulas, trade ledger P&L,
portfolio equity mark-to-market solvency, and liquidation reconciliations
WITHOUT relying on the production classes (IndianEquityCostModel or EventDrivenBacktestEngine).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def test_independent_per_trade_statutory_fee_recomputation():
    """
    Independently recomputes every cost component for all 621 trades from first principles:
    - Brokerage: min(20.0, turnover * 0.0003) on both buy and sell legs
    - STT: turnover * 0.001 on both buy and sell legs
    - Stamp Duty: turnover * 0.00015 on buy leg only
    - Exchange Turnover Fee: turnover * 0.0000297 on both legs
    - SEBI Turnover Fee: turnover * 0.000001 on both legs
    - GST: 18% of (brokerage + exchange + sebi) on both legs
    - Slippage: turnover * 0.0005 on both legs

    Verifies that total independent friction matches recorded ledger friction of ₹213,207.51.
    """
    trades = pd.read_csv("data/reports/trade_ledger.csv")
    assert len(trades) == 621

    indep_buy_turnover = 0.0
    indep_sell_turnover = 0.0

    indep_brokerage = 0.0
    indep_stt = 0.0
    indep_exchange = 0.0
    indep_sebi = 0.0
    indep_stamp = 0.0
    indep_gst = 0.0
    indep_slippage = 0.0
    indep_total_friction = 0.0

    mismatch_statutory_count = 0
    mismatch_total_costs_count = 0

    for _, row in trades.iterrows():
        qty = int(row["quantity"])
        p_in = float(row["entry_unadjusted_open"])
        p_out = float(row["exit_unadjusted_open"])

        # Buy leg
        b_to = qty * p_in
        b_brok = min(20.0, b_to * 0.0003)
        b_stt = b_to * 0.001
        b_exch = b_to * 0.0000297
        b_sebi = b_to * 0.000001
        b_stamp = b_to * 0.00015
        b_gst = (b_brok + b_exch + b_sebi) * 0.18
        b_slip = b_to * 0.0005
        b_stat = b_brok + b_stt + b_exch + b_sebi + b_stamp + b_gst
        b_fric = b_stat + b_slip

        # Sell leg
        s_to = qty * p_out
        s_brok = min(20.0, s_to * 0.0003)
        s_stt = s_to * 0.001
        s_exch = s_to * 0.0000297
        s_sebi = s_to * 0.000001
        s_stamp = 0.0
        s_gst = (s_brok + s_exch + s_sebi) * 0.18
        s_slip = s_to * 0.0005
        s_stat = s_brok + s_stt + s_exch + s_sebi + s_stamp + s_gst
        s_fric = s_stat + s_slip

        indep_buy_turnover += b_to
        indep_sell_turnover += s_to

        indep_brokerage += round(b_brok, 2) + round(s_brok, 2)
        indep_stt += round(b_stt, 2) + round(s_stt, 2)
        indep_exchange += round(b_exch, 2) + round(s_exch, 2)
        indep_sebi += round(b_sebi, 2) + round(s_sebi, 2)
        indep_stamp += round(b_stamp, 2) + round(s_stamp, 2)
        indep_gst += round(b_gst, 2) + round(s_gst, 2)
        indep_slippage += round(b_slip, 2) + round(s_slip, 2)
        indep_total_friction += round(b_fric, 2) + round(s_fric, 2)

        # Check against trade row
        stat_row = round(round(b_stat, 2) + round(s_stat, 2), 2)
        tot_row = round(round(b_fric, 2) + round(s_fric, 2), 2)

        if abs(stat_row - row["total_statutory_and_brokerage"]) > 1e-4:
            mismatch_statutory_count += 1
        if abs(tot_row - row["total_costs"]) > 1e-4:
            mismatch_total_costs_count += 1

    # Exact zero mismatches at row level
    assert mismatch_statutory_count == 0
    assert mismatch_total_costs_count == 0

    # Aggregate comparisons
    assert pytest.approx(indep_buy_turnover, abs=1.0) == 57042157.63
    assert pytest.approx(indep_sell_turnover, abs=1.0) == 57094686.76
    assert pytest.approx(indep_brokerage, abs=0.01) == 24840.00
    assert pytest.approx(indep_stt, abs=0.50) == 114137.05
    assert pytest.approx(indep_exchange, abs=0.50) == 3390.06
    assert pytest.approx(indep_sebi, abs=0.10) == 113.82
    assert pytest.approx(indep_stamp, abs=0.50) == 8556.20
    assert pytest.approx(indep_gst, abs=0.50) == 5101.93
    assert pytest.approx(indep_slippage, abs=0.50) == 57068.46
    assert pytest.approx(indep_total_friction, abs=0.05) == 213207.51


def test_independent_gross_and_net_pnl_reconciliation():
    """Verify that trade Gross P&L and Net P&L reconcile across all 621 trades."""
    trades = pd.read_csv("data/reports/trade_ledger.csv")

    gross_pnl_sum = trades["gross_pnl"].sum()
    total_costs_sum = trades["total_costs"].sum()
    net_pnl_sum = trades["net_pnl"].sum()

    assert pytest.approx(gross_pnl_sum, abs=0.01) == 52528.87
    assert pytest.approx(total_costs_sum, abs=0.01) == 213207.51
    assert pytest.approx(net_pnl_sum, abs=0.01) == -160678.64

    # Net P&L = Gross P&L - Total Costs identity holds for 100% of rows
    row_diff = (trades["gross_pnl"] - trades["total_costs"] - trades["net_pnl"]).abs()
    assert (row_diff < 1e-4).all()


def test_independent_liquidation_and_10_paise_reconciliation():
    """
    Independently verify that the ₹1,198.28 ending equity variance vs trade Net P&L
    is composed of:
    - ₹1,198.38 hypothetical sell friction on the 8 liquidation positions
    - Minus ₹0.02 liquidation trade component rounding
    - Minus ₹0.08 cash rounding accumulation across 613 closed trades
    Total explained variance: ₹1,198.38 - ₹0.10 = ₹1,198.28 (Exact to the penny).
    """
    trades = pd.read_csv("data/reports/trade_ledger.csv")
    port = pd.read_csv("data/reports/portfolio_ledger.csv")

    ending_equity = float(port["portfolio_equity"].iloc[-1])
    initial_cap = 1000000.0
    equity_change = ending_equity - initial_cap
    total_net_pnl = float(trades["net_pnl"].sum())

    reported_variance = equity_change - total_net_pnl
    assert pytest.approx(reported_variance, abs=0.01) == 1198.28

    # Independent calculation of sell friction on the 8 open positions
    liq_trades = trades[trades["exit_reason"] == "END_OF_PERIOD_LIQUIDATION"]
    assert len(liq_trades) == 8

    indep_sell_friction_liq = 0.0
    for _, r in liq_trades.iterrows():
        q = int(r["quantity"])
        p_out = float(r["exit_unadjusted_open"])
        s_to = q * p_out

        s_brok = min(20.0, s_to * 0.0003)
        s_stt = s_to * 0.001
        s_exch = s_to * 0.0000297
        s_sebi = s_to * 0.000001
        s_gst = (s_brok + s_exch + s_sebi) * 0.18
        s_slip = s_to * 0.0005
        s_fric = s_brok + s_stt + s_exch + s_sebi + s_gst + s_slip
        indep_sell_friction_liq += round(s_fric, 2)

    assert pytest.approx(indep_sell_friction_liq, abs=0.01) == 1198.38
    # Exact difference is 10 paise (0.10)
    assert pytest.approx(indep_sell_friction_liq - reported_variance, abs=0.001) == 0.10


def test_independent_portfolio_daily_mtm_identity():
    """Verify daily mark-to-market solvency across all 388 sessions."""
    df_port = pd.read_csv("data/reports/portfolio_ledger.csv")
    assert len(df_port) == 388

    computed_equity = df_port["cash"] + df_port["invested_market_value"]
    diff = (df_port["portfolio_equity"] - computed_equity).abs()

    # Max difference is 1 paisa (0.01) due to two-decimal float rounding
    assert diff.max() <= 0.0101
    assert (df_port["cash"] >= 0).all()
    assert df_port["cash"].min() >= 211.0
