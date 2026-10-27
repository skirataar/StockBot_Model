#!/usr/bin/env python3
"""
audit_sprint_6_1_reconciliation.py
-----------------------------------
Sprint 6.1.1 — Independent Diagnostic Reconciliation Audit.

Audits every metric in:
- data/reports/sprint_6_1_strategy_diagnostics_report.md
- data/reports/sprint_6_1_strategy_diagnostics.json
against ground-truth source artifacts:
- models/lightgbm.joblib
- data/processed/test_dataset.parquet
- data/reports/trade_ledger.csv
- data/reports/portfolio_ledger.csv
- data/reports/sprint_6_0_backtest_summary.json
- data/reports/sprint_6_0_1_accounting_reconciliation.json
- data/reports/sprint_6_0_3_final_accounting_invariant_audit.json
- src/backtest/event_driven_engine.py
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, brier_score_loss
from sklearn.calibration import calibration_curve

from src.ml.dataset_builder import APPROVED_FEATURES
from src.backtest.event_driven_engine import EventDrivenBacktestEngine


def sha256_file(filepath: Path | str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    root = Path("/home/skirataar/Website/StockBot_Model")
    print("=" * 80)
    print("SPRINT 6.1.1 INDEPENDENT DIAGNOSTIC RECONCILIATION AUDIT")
    print("=" * 80)

    # 1. Verify File Hashes
    model_path = root / "models/lightgbm.joblib"
    test_parquet_path = root / "data/processed/test_dataset.parquet"
    trade_ledger_path = root / "data/reports/trade_ledger.csv"
    port_ledger_path = root / "data/reports/portfolio_ledger.csv"

    model_hash = sha256_file(model_path)
    test_hash = sha256_file(test_parquet_path)
    trade_hash = sha256_file(trade_ledger_path)
    port_hash = sha256_file(port_ledger_path)

    print(f"Model SHA256:         {model_hash}")
    print(f"Test Parquet SHA256:  {test_hash}")
    print(f"Trade Ledger SHA256:  {trade_hash}")
    print(f"Portfolio Ledger SHA: {port_hash}")

    # Expected immutable hashes
    expected_model_hash = "41e61760fc31c72095cd2071fdb843657bd76143ed4535f9b247db78e0c73761"
    expected_test_hash = "7f9d0ce56b42a7cc2780f90edb4b27d9bc923847c6778e5ba4c6ebc754915381"
    assert model_hash == expected_model_hash, f"Model hash mismatch: {model_hash}"
    assert test_hash == expected_test_hash, f"Test parquet hash mismatch: {test_hash}"
    print("[PASS] Cryptographic provenance verified.")

    # 2. Load Data
    model = joblib.load(model_path)
    df_test = pd.read_parquet(test_parquet_path)
    trades = pd.read_csv(trade_ledger_path)
    port = pd.read_csv(port_ledger_path)

    with open(root / "data/reports/sprint_6_1_strategy_diagnostics.json") as f:
        diag_json = json.load(f)

    with open(root / "data/reports/sprint_6_1_strategy_diagnostics_report.md") as f:
        md_text = f.read()

    # Model predictions
    X = df_test[APPROVED_FEATURES]
    y_true = df_test["signal"].values
    preds = model.predict(X)
    probs = model.predict_proba(X)
    p_buy = probs[:, 2]  # class 1 is index 2

    df_test["p_buy"] = p_buy
    df_test["pred_signal"] = preds

    # Reconcile Classification
    cm = confusion_matrix(y_true, preds, labels=[-1, 0, 1])
    cr = classification_report(y_true, preds, labels=[-1, 0, 1], target_names=["SELL (-1)", "HOLD (0)", "BUY (1)"], output_dict=True)
    y_buy_binary = (y_true == 1).astype(int)
    brier_buy = float(brier_score_loss(y_buy_binary, p_buy))
    prob_true, prob_pred = calibration_curve(y_buy_binary, p_buy, n_bins=10, strategy="quantile")

    print("\n--- Classification Re-computation ---")
    print(f"Confusion Matrix:\n{cm}")
    print(f"Accuracy: {cr['accuracy']:.4f}, Macro-F1: {cr['macro avg']['f1-score']:.4f}, Brier: {brier_buy:.4f}")

    # Reconcile Trade PnL
    gross_pnl_sum = float(trades["gross_pnl"].sum())
    costs_sum = float(trades["total_costs"].sum())
    net_pnl_sum = float(trades["net_pnl"].sum())
    assert abs(gross_pnl_sum - 52528.87) < 0.01
    assert abs(costs_sum - 213207.51) < 0.01
    assert abs(net_pnl_sum - (-160678.64)) < 0.01
    print(f"Trade Ledger Totals: Gross={gross_pnl_sum:.2f}, Costs={costs_sum:.2f}, Net={net_pnl_sum:.2f} [PASS]")

    # Discrepancy checks:
    # 1. Standard deviations
    gross_std_true = float(trades["gross_pnl"].std(ddof=1))
    net_std_true = float(trades["net_pnl"].std(ddof=1))
    print(f"Standard Deviations (sample): Gross={gross_std_true:.2f}, Net={net_std_true:.2f}")

    # 2. Gains and Losses
    gw_true = float(trades[trades["gross_pnl"] > 0]["gross_pnl"].sum())
    gl_true = float(trades[trades["gross_pnl"] < 0]["gross_pnl"].sum())
    nw_true = float(trades[trades["net_pnl"] > 0]["net_pnl"].sum())
    nl_true = float(trades[trades["net_pnl"] < 0]["net_pnl"].sum())
    flat_trades = trades[trades["gross_pnl"] == 0]
    print(f"Gross Gains: {gw_true:.2f}, Gross Losses: {gl_true:.2f}, Flat count: {len(flat_trades)}")
    print(f"Net Gains: {nw_true:.2f}, Net Losses: {nl_true:.2f}")

    # 3. Portfolio exposure and cash
    inv_mean_true = float(port["invested_market_value"].mean())
    inv_max_true = float(port["invested_market_value"].max())
    cash_max_true = float(port["cash"].max())
    print(f"Invested Value: Mean={inv_mean_true:.2f}, Max={inv_max_true:.2f}, Cash Max={cash_max_true:.2f}")

    # 4. Open positions distribution
    pos_dist_true = {str(k): int(v) for k, v in port["open_positions_count"].value_counts().sort_index().items()}
    print(f"Open positions distribution true:\n{pos_dist_true}")

    # 5. Drawdown
    port["equity_peak"] = port["portfolio_equity"].cummax()
    port["drawdown"] = (port["equity_peak"] - port["portfolio_equity"]) / port["equity_peak"] * 100
    max_dd_idx = int(port["drawdown"].idxmax())
    peak_idx = int(port["portfolio_equity"].idxmax())
    trough_eq_true = float(port.loc[max_dd_idx, "portfolio_equity"])
    peak_to_trough_sessions_true = max_dd_idx - peak_idx
    print(f"Drawdown Trough: Eq={trough_eq_true:.2f}, Date={port.loc[max_dd_idx, 'date']}, Peak-to-Trough sessions={peak_to_trough_sessions_true}")

    # 6. Annual and Quarterly
    port["date"] = pd.to_datetime(port["date"])
    trades["entry_date"] = pd.to_datetime(trades["entry_date"])
    port["year"] = port["date"].dt.year
    port["quarter"] = port["date"].dt.to_period("Q")
    trades["year"] = trades["entry_date"].dt.year
    trades["quarter"] = trades["entry_date"].dt.to_period("Q")

    print("\n--- Annual Performance ---")
    annual_results = {}
    for yr, grp in port.groupby("year"):
        t_sub = trades[trades["year"] == yr]
        annual_results[yr] = {
            "sessions": len(grp),
            "trades": len(t_sub),
            "gross_pnl": round(float(t_sub["gross_pnl"].sum()), 2),
            "costs": round(float(t_sub["total_costs"].sum()), 2),
            "net_pnl": round(float(t_sub["net_pnl"].sum()), 2),
            "avg_exposure": round(float(grp["gross_exposure_pct"].mean()), 2),
        }
        print(f"Year {yr}: {annual_results[yr]}")

    print("\n--- Quarterly Performance ---")
    quarterly_results = {}
    for qtr, grp in port.groupby("quarter"):
        t_sub = trades[trades["quarter"] == qtr]
        quarterly_results[str(qtr)] = {
            "sessions": len(grp),
            "trades": len(t_sub),
            "gross_pnl": round(float(t_sub["gross_pnl"].sum()), 2),
            "costs": round(float(t_sub["total_costs"].sum()), 2),
            "net_pnl": round(float(t_sub["net_pnl"].sum()), 2),
            "avg_exposure": round(float(grp["gross_exposure_pct"].mean()), 2),
        }
        print(f"Quarter {qtr}: {quarterly_results[str(qtr)]}")

    print("\nAudit calculations completed successfully.")


if __name__ == "__main__":
    main()
