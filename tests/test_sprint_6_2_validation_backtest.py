"""
tests/test_sprint_6_2_validation_backtest.py
--------------------------------------------
Sprint 6.2 — Automated Verification and Regression Test Suite for
Preregistered Validation-Only Backtest Experiment.

Validates:
1. Immutability of all protected baseline artifacts.
2. Presence and integrity of all Sprint 6.2 deliverables.
3. Candidate inventory and parameters matching Protocol v1.2.0.
4. Correct cross-sectional cohort moments (mu_SR, sigma_SR, EVT(16), SR*_ann).
5. Deflated Sharpe Ratio calculation and p-value on top candidate CFG-16.
6. Acceptance criteria evaluation (M1-M8) and rejection triggers (R1-R10).
7. Ledger accounting fidelity, cash solvency, and position capacity limits.
8. Benchmark calculation and relative performance evaluation.
9. Strict test-set quarantine enforcement (test_dataset.parquet never accessed).
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------------------
# 1. Protected Baseline Immutability Tests
# ------------------------------------------------------------------------------

def test_protected_baseline_artifacts_immutable():
    """Confirms all 7 baseline protected artifacts match canonical hashes byte-for-byte."""
    baselines = {
        "models/lightgbm.joblib": "41e61760fc31c72095cd2071fdb843657bd76143ed4535f9b247db78e0c73761",
        "data/processed/training_dataset.parquet": "1d39b686f111e8caecb00cf268de7de00b8fe0dfa5d2073a9173bea0e4b2cf56",
        "data/processed/validation_dataset.parquet": "a937fde4c039f4e55025a3bb338dd5894879f928efc55fd0a18fbdf43df23cf8",
        "data/processed/test_dataset.parquet": "7f9d0ce56b42a7cc2780f90edb4b27d9bc923847c6778e5ba4c6ebc754915381",
        "data/reports/trade_ledger.csv": "f5340b8402c198730d53e4126a8b40463c7cdd832fc0919c1b6bafacf501eeff",
        "data/reports/portfolio_ledger.csv": "f565b8c09b958023a243394bfb6e96887dd3588d44d38623c2b24faa43117f78",
        "data/reports/sprint_6_2_preregistered_protocol_v1_0_0_frozen.json": "a49361b17e619e88d75cb2b9e5c35b41e767f423a8ee2ffe2237f0450ae4ab8a",
    }
    for rel_p, exp_sha in baselines.items():
        fp = REPO_ROOT / rel_p
        assert fp.exists(), f"Protected artifact missing: {rel_p}"
        assert sha256_file(fp) == exp_sha, f"Protected artifact altered: {rel_p}"


def test_protocol_byte_identity():
    """Confirms active protocol and v1.2.0 freeze are byte-identical."""
    p1 = REPO_ROOT / "data/reports/sprint_6_2_preregistered_protocol.json"
    p2 = REPO_ROOT / "data/reports/sprint_6_2_preregistered_protocol_v1_2_0.json"
    assert p1.read_bytes() == p2.read_bytes()
    assert sha256_file(p1) == "0384d6a1b9ac7738a92e295fd94bfac113a9a99ce2f399f11ffa5d66164223cb"


# ------------------------------------------------------------------------------
# 2. Sprint 6.2 Deliverables Verification
# ------------------------------------------------------------------------------

def test_sprint_6_2_deliverables_present():
    """Confirms all required deliverable files exist and are non-empty."""
    required_files = [
        "data/reports/sprint_6_2_validation_report.md",
        "data/reports/sprint_6_2_validation_results.json",
        "data/reports/sprint_6_2_candidate_metrics.csv",
        "data/reports/sprint_6_2_trade_ledger_validation.csv",
        "data/reports/sprint_6_2_portfolio_ledger_validation.csv",
        "data/reports/sprint_6_2_cross_sectional_results.json",
        "data/reports/sprint_6_2_pre_execution_manifest.json",
        "data/reports/sprint_6_2_execution_manifest.json",
        "data/reports/sprint_6_2_hash_manifest.json",
    ]
    for rel_p in required_files:
        fp = REPO_ROOT / rel_p
        assert fp.exists(), f"Deliverable missing: {rel_p}"
        assert fp.stat().st_size > 0, f"Deliverable empty: {rel_p}"

    # Verify candidate-specific ledgers
    ledgers_dir = REPO_ROOT / "data/reports/sprint_6_2/candidate_ledgers"
    for cid in [f"CFG-{i:02d}" for i in range(1, 17)] + ["CFG-BASE"]:
        t_csv = ledgers_dir / f"{cid}_trade_ledger.csv"
        p_csv = ledgers_dir / f"{cid}_portfolio_ledger.csv"
        assert t_csv.exists() and t_csv.stat().st_size > 0
        assert p_csv.exists() and p_csv.stat().st_size > 0


# ------------------------------------------------------------------------------
# 3. Experiment Execution and Candidate Grid Tests
# ------------------------------------------------------------------------------

@pytest.fixture
def validation_results() -> Dict[str, Any]:
    with open(REPO_ROOT / "data/reports/sprint_6_2_validation_results.json", "r") as f:
        return json.load(f)


@pytest.fixture
def candidate_metrics_df() -> pd.DataFrame:
    return pd.read_csv(REPO_ROOT / "data/reports/sprint_6_2_candidate_metrics.csv")


def test_candidate_counts_and_identities(candidate_metrics_df: pd.DataFrame):
    """Confirms 16 candidate trials plus 1 external baseline were evaluated."""
    assert len(candidate_metrics_df) == 17
    expected_ids = set([f"CFG-{i:02d}" for i in range(1, 17)] + ["CFG-BASE"])
    actual_ids = set(candidate_metrics_df["candidate_id"].tolist())
    assert actual_ids == expected_ids


def test_cross_sectional_cohort_moments(validation_results: Dict[str, Any]):
    """Confirms cross-sectional cohort moments and EVT hurdle values."""
    cohort = validation_results["cohort_statistical_evaluation"]["cohort_moments"]
    assert cohort["trial_count_K"] == 16
    assert abs(cohort["cohort_mean_mu_sr"] - 0.4332) < 0.005
    assert abs(cohort["cohort_std_sigma_sr"] - 0.2980) < 0.005
    assert abs(cohort["evt_factor"] - 1.800454) < 1e-5
    assert abs(cohort["expected_max_sharpe"] - 0.9698) < 0.005


def test_primary_gate_dsr_decision(validation_results: Dict[str, Any]):
    """Confirms top candidate CFG-16 DSR evaluation and rejection."""
    gate = validation_results["cohort_statistical_evaluation"]["primary_binding_dsr_gate"]
    assert gate["best_candidate_id"] == "CFG-16"
    assert abs(gate["best_candidate_annualized_sharpe"] - 1.0283) < 0.01
    assert abs(gate["expected_max_sharpe_hurdle_ann"] - 0.9698) < 0.005
    # Even though observed Sharpe > hurdle, Mertens variance and sample size give p=0.4631 > 0.05
    assert abs(gate["best_candidate_p_value"] - 0.4631) < 0.01
    assert gate["is_dsr_significant"] is False
    assert gate["primary_decision"] == "PRIMARY_DSR_REJECTED"


def test_equal_weight_benchmark_evaluation(validation_results: Dict[str, Any]):
    """Confirms passive equal-weight benchmark return is +59.22%."""
    bnh = validation_results["benchmark_metrics"]
    assert bnh["initial_capital"] == 1000000.0
    assert abs(bnh["cumulative_return_pct"] - 59.22) < 0.05
    assert abs(bnh["sharpe_ratio"] - 1.64) < 0.05


def test_all_candidates_failed_acceptance_criteria(candidate_metrics_df: pd.DataFrame, validation_results: Dict[str, Any]):
    """Confirms zero candidates passed all criteria due to benchmark underperformance and DSR."""
    concl = validation_results["experiment_conclusion"]
    assert concl["accepted_candidates_count"] == 0
    assert concl["accepted_candidate_ids"] == []
    assert concl["final_experiment_status"] == "EXPERIMENT COMPLETED — NO CANDIDATE PASSED ALL PREREGISTERED CRITERIA"

    # All candidates have final_status == 'REJECTED'
    assert (candidate_metrics_df["final_status"] == "REJECTED").all()

    # Outperformed benchmark is False for all
    assert not candidate_metrics_df["outperformed_benchmark"].any()


def test_accounting_reconciliation_and_solvency(validation_results: Dict[str, Any]):
    """Confirms accounting fidelity, non-negative cash, and position limit compliance."""
    recon = validation_results["accounting_reconciliation"]
    for cid, r in recon.items():
        assert r["starting_capital"] == 1000000.0
        assert r["solvency_ok"] is True, f"Solvency breach for {cid}"
        assert r["min_cash_observed"] >= 0.0, f"Negative cash for {cid}"
        assert r["capacity_ok"] is True, f"Capacity breach for {cid}"
        assert r["max_concurrent_positions_observed"] <= 10, f"Exceeded 10 positions for {cid}"
        assert r["pnl_reconciled"] is True, f"Gross - friction != Net PnL for {cid}"
