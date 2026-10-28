"""
Sprint 6.1.2 - Holdout Integrity & Research Governance Audit Automated Tests.

This test module programmatically validates quantitative governance invariants:
1. Cryptographic immutability of frozen models, datasets, and ledgers.
2. Chronological separation and boundary purging between dataset splits.
3. Repository data ceiling (proving historical data ends at 2026-07-22).
4. Validation dataset backtest isolation (zero trades in validation period).
5. Mathematical verification of sub-band P&L (exposing [0.40, 0.45) net loss).
6. High-conviction sample size fragility and signal starvation risk.
7. Exit mechanism performance asymmetry.
8. Governance artifact presence, structural validity, and verdict compliance.
9. Mutation detection to prevent silent tampering.
"""

import hashlib
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest

from src.ml.dataset_builder import APPROVED_FEATURES

REPO_ROOT = Path(__file__).resolve().parent.parent

CANONICAL_HASHES = {
    "models/lightgbm.joblib": "41e61760fc31c72095cd2071fdb843657bd76143ed4535f9b247db78e0c73761",
    "data/processed/test_dataset.parquet": "7f9d0ce56b42a7cc2780f90edb4b27d9bc923847c6778e5ba4c6ebc754915381",
    "data/processed/validation_dataset.parquet": "a937fde4c039f4e55025a3bb338dd5894879f928efc55fd0a18fbdf43df23cf8",
    "data/processed/training_dataset.parquet": "1d39b686f111e8caecb00cf268de7de00b8fe0dfa5d2073a9173bea0e4b2cf56",
    "data/reports/trade_ledger.csv": "f5340b8402c198730d53e4126a8b40463c7cdd832fc0919c1b6bafacf501eeff",
    "data/reports/portfolio_ledger.csv": "f565b8c09b958023a243394bfb6e96887dd3588d44d38623c2b24faa43117f78",
}


@pytest.fixture(scope="module")
def audit_resources():
    """Load canonical audit artifacts for governance testing."""
    resources = {}
    for rel_path, expected_hash in CANONICAL_HASHES.items():
        p = REPO_ROOT / rel_path
        assert p.exists(), f"Missing required file: {rel_path}"
        with open(p, "rb") as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}: {actual_hash}"
        resources[rel_path] = p

    resources["model"] = joblib.load(resources["models/lightgbm.joblib"])
    resources["trades"] = pd.read_csv(resources["data/reports/trade_ledger.csv"])
    resources["test_df"] = pd.read_parquet(resources["data/processed/test_dataset.parquet"])
    resources["val_df"] = pd.read_parquet(resources["data/processed/validation_dataset.parquet"])
    resources["train_df"] = pd.read_parquet(resources["data/processed/training_dataset.parquet"])
    return resources


def test_immutable_artifact_hashes(audit_resources):
    """Enforce that all canonical repository files remain cryptographically untouched."""
    for rel_path, expected_hash in CANONICAL_HASHES.items():
        with open(REPO_ROOT / rel_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        assert h == expected_hash, f"File {rel_path} was modified! Expected {expected_hash}, got {h}"


def test_dataset_chronological_bounds_and_purging_invariants(audit_resources):
    """Verify strict chronological non-overlap and boundary purging gaps across dataset splits."""
    train_df = audit_resources["train_df"]
    val_df = audit_resources["val_df"]
    test_df = audit_resources["test_df"]

    train_min, train_max = train_df["date"].min(), train_df["date"].max()
    val_min, val_max = val_df["date"].min(), val_df["date"].max()
    test_min, test_max = test_df["date"].min(), test_df["date"].max()

    # Exact expected chronological dates
    assert str(train_min)[:10] == "2010-01-04"
    assert str(train_max)[:10] == "2022-12-23"
    assert len(train_df) == 146878

    assert str(val_min)[:10] == "2023-01-02"
    assert str(val_max)[:10] == "2024-12-23"
    assert len(val_df) == 23658

    assert str(test_min)[:10] == "2025-01-01"
    assert str(test_max)[:10] == "2026-07-22"
    assert len(test_df) == 19012

    # Invariant: Strict non-overlap
    assert train_max < val_min, "Train and Validation dates overlap!"
    assert val_max < test_min, "Validation and Test dates overlap!"

    # Invariant: 5-day horizon purging gap
    train_val_gap_days = (val_min - train_max).days
    val_test_gap_days = (test_min - val_max).days
    assert train_val_gap_days >= 7, f"Insufficient calendar gap for train->val purging: {train_val_gap_days}d"
    assert val_test_gap_days >= 7, f"Insufficient calendar gap for val->test purging: {val_test_gap_days}d"


def test_repository_data_ceiling_and_holdout_exhaustion():
    """Verify that labeled raw data terminates on 2026-07-22, proving holdout exhaustion."""
    labeled_dir = REPO_ROOT / "data/labeled"
    csv_files = list(labeled_dir.glob("*_labeled.csv"))
    assert len(csv_files) >= 49, f"Expected 49 constituent CSVs, found {len(csv_files)}"

    max_dates = []
    for f in csv_files:
        df = pd.read_csv(f, usecols=["Date"])
        max_dates.append(df["Date"].max())

    overall_max = max(max_dates)
    assert overall_max == "2026-07-22", (
        f"Data ceiling mismatch: expected '2026-07-22', found '{overall_max}'. "
        "Untouched chronological data cannot exist beyond this date in repository."
    )


def test_validation_set_backtest_isolation(audit_resources):
    """Verify that trade_ledger.csv contains zero trades executed in the validation date range."""
    trades = audit_resources["trades"]
    val_df = audit_resources["val_df"]

    val_start = val_df["date"].min().strftime("%Y-%m-%d")
    val_end = val_df["date"].max().strftime("%Y-%m-%d")

    val_trades = trades[(trades["entry_date"] >= val_start) & (trades["entry_date"] <= val_end)]
    assert len(val_trades) == 0, (
        f"Validation isolation violation! Found {len(val_trades)} trades in trade_ledger.csv "
        f"falling within validation period [{val_start}, {val_end}]."
    )

    # Invariant: All 621 trades strictly fall into the test set period
    test_trades = trades[(trades["entry_date"] >= "2025-01-01") & (trades["entry_date"] <= "2026-07-22")]
    assert len(test_trades) == 621, f"Expected 621 test trades, found {len(test_trades)}"


def test_probability_band_sub_band_negative_pnl_invariant(audit_resources):
    """
    Mathematically prove that claiming P(BUY) >= 0.40 is a monolithic trading edge is invalid.
    The largest sub-band [0.40, 0.45) (N=181) is net unprofitable after statutory friction.
    """
    trades = audit_resources["trades"].copy()
    test_df = audit_resources["test_df"]
    model = audit_resources["model"]

    X_test = test_df[APPROVED_FEATURES]
    probs = model.predict_proba(X_test)
    test_df_copy = test_df.copy()
    test_df_copy["p_buy"] = probs[:, 2]

    lookup = {(r["date"].strftime("%Y-%m-%d"), r["symbol"]): r["p_buy"] for _, r in test_df_copy.iterrows()}
    trades["p_buy"] = [lookup[(r["signal_date"], r["symbol"])] for _, r in trades.iterrows()]

    bins = [0.33, 0.40, 0.45, 0.50, 1.00]
    labels = ["[0.33, 0.40)", "[0.40, 0.45)", "[0.45, 0.50)", "[0.50, 1.00]"]
    trades["band"] = pd.cut(trades["p_buy"], bins=bins, labels=labels, right=False)

    band_040_045 = trades[trades["band"] == "[0.40, 0.45)"]
    assert len(band_040_045) == 181

    # Exact financial invariants
    gross_pnl = band_040_045["gross_pnl"].sum()
    costs = band_040_045["total_costs"].sum()
    net_pnl = band_040_045["net_pnl"].sum()
    net_win_rate = (band_040_045["net_pnl"] > 0).mean() * 100

    assert round(gross_pnl, 2) == 58778.41
    assert round(costs, 2) == 61834.58
    assert round(net_pnl, 2) == -3056.17
    assert net_pnl < 0.0, "Sub-band [0.40, 0.45) was not net negative!"
    assert round(net_win_rate, 2) == 49.17
    assert net_win_rate < 50.0, "Sub-band [0.40, 0.45) net win rate must be below 50%!"

    # Invariant: 181 of 271 trades (66.8%) in P >= 0.40 belong to this loss-making band
    p_ge_040 = trades[trades["p_buy"] >= 0.40]
    assert len(p_ge_040) == 271
    share_of_040 = len(band_040_045) / len(p_ge_040)
    assert round(share_of_040, 4) == 0.6679


def test_sample_size_fragility_in_high_conviction_tiers(audit_resources):
    """Verify sample size fragility of high conviction tiers on both test and validation datasets."""
    trades = audit_resources["trades"].copy()
    test_df = audit_resources["test_df"]
    val_df = audit_resources["val_df"]
    model = audit_resources["model"]

    # Test set lookup
    X_test = test_df[APPROVED_FEATURES]
    test_probs = model.predict_proba(X_test)
    lookup_test = {(r["date"].strftime("%Y-%m-%d"), r["symbol"]): test_probs[i, 2] for i, (_, r) in enumerate(test_df.iterrows())}
    trades["p_buy"] = [lookup_test[(r["signal_date"], r["symbol"])] for _, r in trades.iterrows()]

    trades_50 = trades[trades["p_buy"] >= 0.50]
    assert len(trades_50) == 26
    # 26 trades across 388 sessions is less than 0.07 trades per session
    assert len(trades_50) / 388 < 0.07

    # Validation set predictions
    X_val = val_df[APPROVED_FEATURES]
    val_probs = model.predict_proba(X_val)
    val_p_buy = val_probs[:, 2]

    val_ge_050 = (val_p_buy >= 0.50).sum()
    val_ge_045 = (val_p_buy >= 0.45).sum()

    assert val_ge_050 == 35, f"Expected 35 candidate observations with P>=0.50 in Val, found {val_ge_050}"
    assert val_ge_045 == 238, f"Expected 238 candidate observations with P>=0.45 in Val, found {val_ge_045}"

    # Over 24 months, 35 signals represents fewer than 1.5 signals per month across ALL 49 stocks
    assert val_ge_050 / len(val_df) < 0.002
    assert val_ge_045 / len(val_df) < 0.015


def test_exit_mechanism_asymmetry_invariants(audit_resources):
    """Verify performance divergence between model early exits and calendar max hold exits."""
    trades = audit_resources["trades"]

    early_sell = trades[trades["exit_reason"] == "EARLY_SELL_SIGNAL"]
    max_hold = trades[trades["exit_reason"] == "MAX_HOLD_5D"]
    synth = trades[trades["exit_reason"] == "END_OF_PERIOD_LIQUIDATION"]

    assert len(early_sell) == 337
    assert len(max_hold) == 276
    assert len(synth) == 8
    assert len(early_sell) + len(max_hold) + len(synth) == 621

    assert round(early_sell["net_pnl"].sum(), 2) == 160893.61
    assert round(max_hold["net_pnl"].sum(), 2) == -307827.78
    assert round(synth["net_pnl"].sum(), 2) == -13744.47

    # Early sell net win rate > 50%; Max hold net win rate < 40%
    early_win = (early_sell["net_pnl"] > 0).mean() * 100
    max_hold_win = (max_hold["net_pnl"] > 0).mean() * 100
    assert round(early_win, 2) == 51.63
    assert round(max_hold_win, 2) == 37.32


def test_audit_artifacts_governance_invariants():
    """Verify that Sprint 6.1.2 audit report and JSON artifacts exist and uphold governance invariants."""
    json_path = REPO_ROOT / "data/reports/sprint_6_1_2_holdout_integrity_audit.json"
    md_path = REPO_ROOT / "data/reports/sprint_6_1_2_holdout_integrity_audit_report.md"

    assert json_path.exists(), f"Missing audit JSON artifact: {json_path}"
    assert md_path.exists(), f"Missing audit Markdown report: {md_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Required JSON schema keys
    assert "metadata" in data
    assert "executive_verdict" in data
    assert "research_timeline_reconstruction" in data
    assert "holdout_integrity_assessment" in data
    assert "preregistered_sprint_6_2_protocol" in data
    assert "final_out_of_sample_evaluation_design" in data
    assert "facts_questions_assumptions" in data

    # Governance verdict checks
    verdict = data["executive_verdict"]["verdict"]
    assert verdict == "PASS WITH LIMITATIONS", f"Unexpected verdict: {verdict}"
    assert data["executive_verdict"]["holdout_integrity_status"] == "COMPROMISED_RESEARCH_EXPOSED"
    assert data["executive_verdict"]["sprint_6_2_authorization"] == "AUTHORIZED_VALIDATION_ONLY"

    # Markdown narrative checks
    md_text = md_path.read_text(encoding="utf-8")
    assert "PASS WITH LIMITATIONS" in md_text
    assert "Research Timeline" in md_text
    assert "Test-Set Integrity Assessment" in md_text
    assert "Confirmed Facts" in md_text
    assert "Unresolved Questions" in md_text
    assert "Explicit Assumptions" in md_text
    assert "Preregistered Sprint 6.2 Protocol" in md_text
    assert "Final Out-of-Sample Evaluation Design" in md_text


def test_mutation_detection_fails_on_tampered_trade_date(audit_resources):
    """Mutation test: Ensure that injecting a validation-period trade into trade_ledger fails isolation."""
    trades = audit_resources["trades"].copy()
    # Mutate trade #0 entry_date to fall inside validation period
    trades.loc[0, "entry_date"] = "2023-06-15"

    val_df = audit_resources["val_df"]
    val_start = val_df["date"].min().strftime("%Y-%m-%d")
    val_end = val_df["date"].max().strftime("%Y-%m-%d")

    val_trades = trades[(trades["entry_date"] >= val_start) & (trades["entry_date"] <= val_end)]
    # Mutation must be caught
    assert len(val_trades) == 1
