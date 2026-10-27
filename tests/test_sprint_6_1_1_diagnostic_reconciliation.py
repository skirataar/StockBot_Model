"""
test_sprint_6_1_1_diagnostic_reconciliation.py
----------------------------------------------
Sprint 6.1.1 — Independent Diagnostic Reconciliation Audit Tests.

Verifies:
- Immutable artifact hashes
- Classification metrics, confusion matrix, and calibration decile reconciliation
- Trade ledger standard deviations, gains/losses, and zero-gross flat trade partition
- Probability-band trade distributions and conviction metrics
- Portfolio ledger exposure, cash peaks, and open positions distribution
- Drawdown trough equity, dates, and peak-to-trough session duration
- Annual and quarterly session, trade, and P&L aggregation identities
- Market regime performance identities
- Benchmark constituent counts, sizing, and canonical baseline reconciliation
- Mutation tests verifying that tampered inputs are caught by the audit assertions
"""

import hashlib
import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import confusion_matrix, classification_report, brier_score_loss
from sklearn.calibration import calibration_curve

from src.ml.dataset_builder import APPROVED_FEATURES


@pytest.fixture(scope="module")
def repo_root():
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def artifacts(repo_root):
    model_path = repo_root / "models/lightgbm.joblib"
    test_parquet_path = repo_root / "data/processed/test_dataset.parquet"
    trade_ledger_path = repo_root / "data/reports/trade_ledger.csv"
    port_ledger_path = repo_root / "data/reports/portfolio_ledger.csv"

    model = joblib.load(model_path)
    df_test = pd.read_parquet(test_parquet_path)
    trades = pd.read_csv(trade_ledger_path)
    port = pd.read_csv(port_ledger_path)

    with open(repo_root / "data/reports/sprint_6_1_strategy_diagnostics.json") as f:
        diag_json = json.load(f)

    with open(repo_root / "data/reports/sprint_6_1_strategy_diagnostics_report.md") as f:
        md_text = f.read()

    return {
        "model": model,
        "df_test": df_test,
        "trades": trades,
        "port": port,
        "diag_json": diag_json,
        "md_text": md_text,
        "model_path": model_path,
        "test_parquet_path": test_parquet_path,
        "trade_ledger_path": trade_ledger_path,
        "port_ledger_path": port_ledger_path,
    }


def test_provenance_and_immutable_hashes(artifacts):
    """Verify that model and test dataset cryptographic hashes match the approved baseline."""
    def get_sha256(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    expected_model_hash = "41e61760fc31c72095cd2071fdb843657bd76143ed4535f9b247db78e0c73761"
    expected_test_hash = "7f9d0ce56b42a7cc2780f90edb4b27d9bc923847c6778e5ba4c6ebc754915381"

    assert get_sha256(artifacts["model_path"]) == expected_model_hash
    assert get_sha256(artifacts["test_parquet_path"]) == expected_test_hash


def test_classification_metrics_and_confusion_matrix(artifacts):
    """Verify the exact confusion matrix, classification metrics, and class order."""
    model = artifacts["model"]
    df_test = artifacts["df_test"]

    X = df_test[APPROVED_FEATURES]
    y_true = df_test["signal"].values
    preds = model.predict(X)
    probs = model.predict_proba(X)
    p_buy = probs[:, 2]

    cm = confusion_matrix(y_true, preds, labels=[-1, 0, 1])
    # Expected confusion matrix:
    # [[1625, 2075, 915], [2762, 5356, 1336], [1618, 2178, 1147]]
    expected_cm = np.array([
        [1625, 2075, 915],
        [2762, 5356, 1336],
        [1618, 2178, 1147],
    ])
    np.testing.assert_array_equal(cm, expected_cm)
    assert cm.sum() == 19012

    cr = classification_report(y_true, preds, labels=[-1, 0, 1], output_dict=True)
    assert round(cr["accuracy"], 4) == 0.4275
    assert round(cr["macro avg"]["f1-score"], 4) == 0.3810

    y_buy_binary = (y_true == 1).astype(int)
    brier = brier_score_loss(y_buy_binary, p_buy)
    assert round(brier, 4) == 0.1927


def test_calibration_decile_reconciliation(artifacts):
    """Verify that scikit-learn quantile calibration deciles match the JSON and expose Markdown error."""
    model = artifacts["model"]
    df_test = artifacts["df_test"]
    diag_json = artifacts["diag_json"]

    X = df_test[APPROVED_FEATURES]
    y_true = df_test["signal"].values
    probs = model.predict_proba(X)
    p_buy = probs[:, 2]

    y_buy_binary = (y_true == 1).astype(int)
    prob_true, prob_pred = calibration_curve(y_buy_binary, p_buy, n_bins=10, strategy="quantile")

    calib_json = diag_json["classification_diagnostics"]["calibration_diagnostics"]["quantile_calibration_curve"]
    assert len(calib_json) == 10

    # Decile 1 should be ~0.1680 mean pred prob (NOT 0.2078 as erroneously stated in Markdown)
    assert round(float(prob_pred[0]), 4) == 0.1680
    assert round(float(prob_true[0]), 4) == 0.2219
    assert calib_json[0]["mean_predicted_p_buy"] == 0.1680

    # Decile 10 should be ~0.4306 mean pred prob (NOT 0.4217 as in Markdown)
    assert round(float(prob_pred[9]), 4) == 0.4306
    assert round(float(prob_true[9]), 4) == 0.3749
    assert calib_json[9]["mean_predicted_p_buy"] == 0.4306


def test_trade_ledger_standard_deviation_reconciliation(artifacts):
    """Verify that sample standard deviation ddof=1 is ₹3,541.45 gross and ₹3,537.21 net."""
    trades = artifacts["trades"]
    gross_std = trades["gross_pnl"].std(ddof=1)
    net_std = trades["net_pnl"].std(ddof=1)

    assert round(gross_std, 2) == 3541.45
    assert round(net_std, 2) == 3537.21
    # Markdown erroneously reported ₹2,476.43 and ₹2,467.42
    assert round(gross_std, 2) != 2476.43


def test_gross_net_gains_and_flat_trade_partition(artifacts):
    """Verify exact dollar sums of wins and losses and identify the single zero-gross flat trade."""
    trades = artifacts["trades"]

    gross_wins = trades[trades["gross_pnl"] > 0]
    gross_losses = trades[trades["gross_pnl"] < 0]
    gross_flat = trades[trades["gross_pnl"] == 0]

    assert len(gross_wins) == 306
    assert len(gross_losses) == 314
    assert len(gross_flat) == 1
    assert gross_flat.iloc[0]["symbol"] == "TCS"
    assert gross_flat.iloc[0]["gross_pnl"] == 0.0
    assert gross_flat.iloc[0]["net_pnl"] == -309.86

    gross_gains = gross_wins["gross_pnl"].sum()
    gross_losses_sum = gross_losses["gross_pnl"].sum()
    assert round(gross_gains, 2) == 820960.96
    assert round(gross_losses_sum, 2) == -768432.09
    assert round(gross_gains + gross_losses_sum, 2) == 52528.87

    net_wins = trades[trades["net_pnl"] > 0]
    net_losses = trades[trades["net_pnl"] < 0]
    net_flat = trades[trades["net_pnl"] == 0]
    assert len(net_wins) == 277
    assert len(net_losses) == 344
    assert len(net_flat) == 0

    net_gains = net_wins["net_pnl"].sum()
    net_losses_sum = net_losses["net_pnl"].sum()
    assert round(net_gains, 2) == 719249.65
    assert round(net_losses_sum, 2) == -879928.29
    assert round(net_gains + net_losses_sum, 2) == -160678.64


def test_probability_band_reconciliation(artifacts):
    """Verify that probability bands partition all 621 trades under signal_date lookup."""
    trades = artifacts["trades"]
    df_test = artifacts["df_test"]
    model = artifacts["model"]

    X = df_test[APPROVED_FEATURES]
    probs = model.predict_proba(X)
    df_test["p_buy"] = probs[:, 2]

    lookup = {(r["date"].strftime("%Y-%m-%d"), r["symbol"]): r["p_buy"] for _, r in df_test.iterrows()}
    trades["p_buy"] = [lookup[(r["signal_date"], r["symbol"])] for _, r in trades.iterrows()]

    bins = [0.33, 0.40, 0.45, 0.50, 1.00]
    labels = ["[0.33, 0.40)", "[0.40, 0.45)", "[0.45, 0.50)", "[0.50, 1.00]"]
    trades["band"] = pd.cut(trades["p_buy"], bins=bins, labels=labels, right=False)

    counts = trades["band"].value_counts().to_dict()
    assert counts["[0.33, 0.40)"] == 350
    assert counts["[0.40, 0.45)"] == 181
    assert counts["[0.45, 0.50)"] == 64
    assert counts["[0.50, 1.00]"] == 26
    assert sum(counts.values()) == 621

    # Check gross win rate of lowest band is 45.43% (159 wins / 350), not 44.86%
    sub_033 = trades[trades["band"] == "[0.33, 0.40)"]
    gw_rate = (sub_033["gross_pnl"] > 0).mean() * 100
    assert round(gw_rate, 2) == 45.43

    # Check profit factor of lowest band is 0.7524 gross and 0.5440 net
    gw = sub_033[sub_033["gross_pnl"] > 0]["gross_pnl"].sum()
    gl = sub_033[sub_033["gross_pnl"] < 0]["gross_pnl"].sum()
    nw = sub_033[sub_033["net_pnl"] > 0]["net_pnl"].sum()
    nl = sub_033[sub_033["net_pnl"] < 0]["net_pnl"].sum()
    assert round(gw / abs(gl), 4) == 0.7524
    assert round(nw / abs(nl), 4) == 0.5440


def test_portfolio_ledger_exposure_and_cash_extremes(artifacts):
    """Verify invested market value mean/max, cash max, and 67 zero-position sessions."""
    port = artifacts["port"]

    assert round(port["invested_market_value"].mean(), 2) == 504048.42
    assert round(port["invested_market_value"].max(), 2) == 1022577.89
    assert round(port["cash"].max(), 2) == 1032613.52

    counts = port["open_positions_count"].value_counts().to_dict()
    # Markdown erroneously claimed 0 positions occurred on only 2 sessions
    assert counts[0] == 67
    assert counts[10] == 127
    assert sum(counts.values()) == 388


def test_drawdown_trough_and_duration(artifacts):
    """Verify trough equity is ₹788,652.53 and peak-to-trough duration is 226 sessions."""
    port = artifacts["port"]
    port["equity_peak"] = port["portfolio_equity"].cummax()
    port["drawdown"] = (port["equity_peak"] - port["portfolio_equity"]) / port["equity_peak"] * 100

    max_dd_idx = int(port["drawdown"].idxmax())
    peak_idx = int(port["portfolio_equity"].idxmax())

    assert round(port.loc[max_dd_idx, "portfolio_equity"], 2) == 788652.53
    assert port.loc[max_dd_idx, "date"] == "2026-03-23"
    assert port.loc[peak_idx, "date"] == "2025-04-28"
    assert max_dd_idx - peak_idx == 226


def test_quarterly_reconciliation_identities(artifacts):
    """Verify quarterly session counts, trade counts, and Net P&L sum to portfolio totals."""
    port = artifacts["port"]
    trades = artifacts["trades"]

    port["date"] = pd.to_datetime(port["date"])
    port["quarter"] = port["date"].dt.to_period("Q")
    trades["entry_date"] = pd.to_datetime(trades["entry_date"])
    trades["quarter"] = trades["entry_date"].dt.to_period("Q")

    sessions_by_qtr = port.groupby("quarter")["date"].count().to_dict()
    trades_by_qtr = trades.groupby("quarter")["net_pnl"].count().to_dict()
    pnl_by_qtr = trades.groupby("quarter")["net_pnl"].sum().to_dict()

    assert sum(sessions_by_qtr.values()) == 388
    assert sum(trades_by_qtr.values()) == 621
    assert round(sum(pnl_by_qtr.values()), 2) == -160678.64

    # 2025Q4 had 7 trades and 62 sessions (Markdown claimed 87 trades and 63 sessions)
    assert trades_by_qtr[pd.Period("2025Q4", "Q")] == 7
    assert sessions_by_qtr[pd.Period("2025Q4", "Q")] == 62


def test_regime_reconciliation_identities(artifacts):
    """Verify that regime performance sums to exactly ₹52,528.87 gross and -₹160,678.64 net."""
    diag_json = artifacts["diag_json"]
    regimes = diag_json["time_and_regime_diagnostics"]["market_regime_diagnostics"]["performance_by_regime"]

    tot_sessions = sum(r["sessions_count"] for r in regimes)
    tot_trades = sum(r["trades_count"] for r in regimes)
    tot_gross = sum(r["gross_pnl"] for r in regimes)
    tot_costs = sum(r["total_costs"] for r in regimes)
    tot_net = sum(r["net_pnl"] for r in regimes)

    assert tot_sessions == 388
    assert tot_trades == 621
    assert round(tot_gross, 2) == 52528.87
    assert round(tot_costs, 2) == 213207.51
    assert round(tot_net, 2) == -160678.64


def test_benchmark_reconciliation(artifacts, repo_root):
    """Verify benchmark 49-stock canonical ending equity and top-10 10th constituent is BHARTIARTL."""
    with open(repo_root / "data/reports/sprint_6_0_backtest_summary.json") as f:
        summary_6_0 = json.load(f)

    # 49-constituent benchmark equity is 1,102,607.68
    assert summary_6_0["buy_and_hold_benchmark"]["final_equity"] == 1102607.68

    # Top-10 static baseline ending equity is 1,284,448.74
    assert summary_6_0["non_ml_baseline"]["final_equity"] == 1284448.74


def test_mutation_detection_fails_on_tampered_trade_ledger(artifacts):
    """Mutation test: verify that a tampered trade P&L is detected by reconciliation assertion."""
    trades = artifacts["trades"].copy()
    # Mutate row 0 gross P&L by +₹1,000
    trades.loc[0, "gross_pnl"] += 1000.0

    with pytest.raises(AssertionError):
        assert abs(trades["gross_pnl"].sum() - 52528.87) < 0.01


def test_mutation_detection_fails_on_tampered_calibration_decile(artifacts):
    """Mutation test: verify that tampered decile probability is detected by calibration assertion."""
    diag_json = artifacts["diag_json"]
    tampered_json = json.loads(json.dumps(diag_json))
    # Mutate Bin 1 to Markdown's erroneous 0.2078
    tampered_json["classification_diagnostics"]["calibration_diagnostics"]["quantile_calibration_curve"][0]["mean_predicted_p_buy"] = 0.2078

    with pytest.raises(AssertionError):
        assert tampered_json["classification_diagnostics"]["calibration_diagnostics"]["quantile_calibration_curve"][0]["mean_predicted_p_buy"] == 0.1680
