"""
Sprint 6.1.3 - Validation Experiment Protocol Normalization and Freeze Tests.

This test module programmatically verifies the protocol artifacts:
1. Candidate grid contains <= 20 configurations with unique stable IDs.
2. Every configuration has valid parameter values within specified domains.
3. The frozen candidate grid is deterministic and reproducible.
4. Continuous or unregistered parameter tuning is strictly prohibited.
5. All 8 mandatory acceptance criteria and 10 rejection triggers are defined.
6. Markdown and JSON protocol representations are consistent in substance.
7. Explicit sample-size and calendar-year trade allocation rules are enforced.
8. Risk-free rate (6.0%) and return annualization conventions (sqrt(252)) are defined.
9. Deflated Sharpe Ratio (DSR) and multiple-comparison requirements are mandatory.
10. Frozen model and dataset cryptographic hashes match canonical values.
11. Test-period optimization and candidate selection are explicitly forbidden.
12. Exit-rule technical feasibility assessment is present.
13. Portfolio, cost, and execution invariants are preserved and blockers disclosed.
14. ZERO strategy backtests are executed in this module.
"""

import hashlib
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_JSON_PATH = REPO_ROOT / "data/reports/sprint_6_2_preregistered_protocol_v1_0_0_frozen.json"
NORMALIZATION_JSON_PATH = REPO_ROOT / "data/reports/sprint_6_1_3_protocol_normalization.json"
REPORT_MD_PATH = REPO_ROOT / "data/reports/sprint_6_1_3_protocol_normalization_report.md"

CANONICAL_HASHES = {
    "models/lightgbm.joblib": "41e61760fc31c72095cd2071fdb843657bd76143ed4535f9b247db78e0c73761",
    "data/processed/validation_dataset.parquet": "a937fde4c039f4e55025a3bb338dd5894879f928efc55fd0a18fbdf43df23cf8",
    "data/processed/training_dataset.parquet": "1d39b686f111e8caecb00cf268de7de00b8fe0dfa5d2073a9173bea0e4b2cf56",
    "data/processed/test_dataset.parquet": "7f9d0ce56b42a7cc2780f90edb4b27d9bc923847c6778e5ba4c6ebc754915381",
}


@pytest.fixture(scope="module")
def protocol_data():
    """Load and parse the frozen protocol JSON."""
    assert PROTOCOL_JSON_PATH.exists(), f"Missing protocol JSON: {PROTOCOL_JSON_PATH}"
    with open(PROTOCOL_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def normalization_data():
    """Load and parse the normalization JSON."""
    assert NORMALIZATION_JSON_PATH.exists(), f"Missing normalization JSON: {NORMALIZATION_JSON_PATH}"
    with open(NORMALIZATION_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def report_markdown():
    """Load the Markdown report text."""
    assert REPORT_MD_PATH.exists(), f"Missing report Markdown: {REPORT_MD_PATH}"
    return REPORT_MD_PATH.read_text(encoding="utf-8")


def test_candidate_grid_count_cap(protocol_data):
    """Verify that the candidate grid resolves the 84-combination contradiction and enforces <= 20 configurations."""
    grid = protocol_data["candidate_grid"]
    assert grid["full_cartesian_product_count"] == 84
    assert grid["max_permitted_candidates"] == 20
    candidates = grid["configurations"]
    assert len(candidates) <= 20
    assert len(candidates) == 16  # Exactly 16 normalized candidates
    assert grid["frozen_candidate_count"] == 16


def test_candidate_grid_stable_identifiers(protocol_data):
    """Verify that every configuration has a unique, deterministic, stable identifier."""
    candidates = protocol_data["candidate_grid"]["configurations"]
    config_ids = [c["config_id"] for c in candidates]
    assert len(config_ids) == len(set(config_ids)), "Duplicate config_ids found in candidate grid!"
    expected_ids = [f"CFG-{i:02d}" for i in range(1, 17)]
    assert config_ids == expected_ids


def test_candidate_parameter_domain_validity(protocol_data):
    """Verify that every configuration specifies valid parameters within authorized domains."""
    valid_thresholds = {0.35, 0.38, 0.40, 0.42, 0.45, 0.48, 0.50}
    valid_exits = {"1.5x_ATR", "2.0x_ATR", "2.5x_ATR", "fixed_5d"}
    valid_pacings = {"2", "3", "unconstrained"}

    candidates = protocol_data["candidate_grid"]["configurations"]
    for c in candidates:
        assert c["threshold"] in valid_thresholds, f"Invalid threshold {c['threshold']} in {c['config_id']}"
        assert c["exit_rule"] in valid_exits, f"Invalid exit_rule {c['exit_rule']} in {c['config_id']}"
        assert c["pacing"] in valid_pacings, f"Invalid pacing {c['pacing']} in {c['config_id']}"


def test_candidate_grid_determinism_and_reproducibility(protocol_data, normalization_data):
    """Verify that the candidate grid matches identically between the protocol JSON and normalization JSON."""
    proto_candidates = protocol_data["candidate_grid"]["configurations"]
    norm_candidates = normalization_data["candidate_grid_normalization"]["frozen_candidates"]

    assert len(proto_candidates) == len(norm_candidates)
    for p_c, n_c in zip(proto_candidates, norm_candidates):
        assert p_c["config_id"] == n_c["config_id"]
        assert p_c["threshold"] == n_c["threshold"]
        assert p_c["exit_rule"] == n_c["exit_rule"]
        assert p_c["pacing"] == n_c["pacing"]


def test_prohibition_of_continuous_tuning(protocol_data):
    """Verify that protocol explicitly prohibits continuous tuning and random searches."""
    prohibitions = protocol_data["prohibited_actions"]
    prohibitions_str = " ".join(prohibitions).lower()
    assert "continuous parameter tuning" in prohibitions_str
    assert "random search" in prohibitions_str
    assert "third-decimal" in prohibitions_str


def test_mandatory_acceptance_criteria_completeness(protocol_data):
    """Verify that all 8 mandatory acceptance criteria and 10 rejection triggers are canonically defined."""
    crit = protocol_data["acceptance_and_rejection_criteria"]
    mandatory = crit["mandatory_acceptance_criteria"]
    rejections = crit["automatic_rejection_triggers"]

    assert len(mandatory) == 8
    assert len(rejections) == 10

    mandatory_ids = [m["id"] for m in mandatory]
    expected_m_ids = [
        "M1_SHARPE_RATIO",
        "M2_BENCHMARK_OUTPERFORMANCE",
        "M3_MAX_DRAWDOWN",
        "M4_MIN_TOTAL_TRADES",
        "M5_MIN_ANNUAL_TRADES",
        "M6_NET_PROFIT_FACTOR",
        "M7_FRICTION_EFFICIENCY",
        "M8_DEFLATED_SHARPE",
    ]
    assert mandatory_ids == expected_m_ids

    # Maximum drawdown must be strictly <= 15.00%
    m3 = next(m for m in mandatory if m["id"] == "M3_MAX_DRAWDOWN")
    assert "<= 15.00%" in m3["condition"]

    # Rejection trigger for drawdown must trigger above 15.00%
    r3 = next(r for r in rejections if r["id"] == "R3_EXCESSIVE_DRAWDOWN")
    assert "15.00%" in r3["trigger"]


def test_markdown_and_json_protocol_consistency(report_markdown, protocol_data):
    """Verify that Markdown report and JSON protocol representations are consistent in substance."""
    assert "CFG-01" in report_markdown
    assert "CFG-16" in report_markdown
    assert "CFG-BASE" in report_markdown
    assert "84 candidate configurations" in report_markdown
    assert "16 deterministic, stable configurations" in report_markdown
    assert "BLOCKED — PROTOCOL OR IMPLEMENTATION ISSUES REMAIN" in report_markdown
    assert "BLK-01" in report_markdown
    assert "BLK-02" in report_markdown
    assert "BLK-03" in report_markdown

    # Canonical hash of frozen protocol must be documented in Markdown
    proto_bytes = PROTOCOL_JSON_PATH.read_bytes()
    expected_hash = hashlib.sha256(proto_bytes).hexdigest()
    assert expected_hash in report_markdown


def test_sample_size_and_annual_trade_rules(protocol_data):
    """Verify explicit trade counting rules, calendar year assignment, and liquidation rules."""
    sample_spec = protocol_data["sample_size_and_benchmark_specifications"]
    assert sample_spec["calendar_year_assignment"]["assignment_rule"] == "Every trade is assigned to a calendar year based strictly on its ENTRY_DATE."
    assert sample_spec["calendar_year_assignment"]["annual_trade_minimum"] == 40

    completed_spec = sample_spec["completed_trade_definition"]
    assert "partial_fills" in completed_spec
    assert "Prohibited" in completed_spec["partial_fills"]
    assert "rejected_orders" in completed_spec


def test_risk_free_rate_and_annualization_conventions(protocol_data):
    """Verify that risk-free rate (6.0%) and annualization convention (sqrt(252)) are explicit."""
    stat_spec = protocol_data["statistical_testing_procedure"]
    assert stat_spec["risk_free_rate_annual"] == 0.06
    assert stat_spec["annualization_factor"] == "sqrt(252)"
    assert stat_spec["frequency"] == "Daily trading sessions (T = 490 trading sessions in 2023-2024 validation period)"


def test_dsr_and_multiple_comparison_requirements(protocol_data):
    """Verify Deflated Sharpe Ratio (DSR) trial parameter K=16 and Holm-Bonferroni correction."""
    stat_spec = protocol_data["statistical_testing_procedure"]
    dsr_spec = stat_spec["deflated_sharpe_ratio_specification"]
    assert dsr_spec["number_of_trials_K"] == 16
    assert dsr_spec["significance_threshold"] == 0.05
    assert "Holm-Bonferroni" in stat_spec["multiple_comparisons_correction"]["method"]


def test_frozen_model_and_dataset_hashes(protocol_data):
    """Verify that local files exist and match canonical cryptographic hashes."""
    for rel_path, expected_hash in CANONICAL_HASHES.items():
        file_path = REPO_ROOT / rel_path
        assert file_path.exists(), f"Missing file: {file_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}!"


def test_prohibition_of_test_period_optimization(protocol_data):
    """Verify that protocol explicitly forbids test-period evaluation or optimization in Sprint 6.2."""
    prohibitions = protocol_data["prohibited_actions"]
    assert any("test_dataset.parquet" in p for p in prohibitions)
    disclosure = protocol_data["research_exposure_disclosure"]
    assert disclosure["classification"] == "RESEARCH-EXPOSED"


def test_exit_rule_technical_feasibility_assessment(protocol_data):
    """Verify presence of exit-rule technical feasibility assessment and gap handling specification."""
    feasibility = protocol_data["exit_rule_technical_feasibility"]
    assert "Daily OHLCV bars only" in feasibility["bar_resolution"]
    assert "End-of-Day Close Inspection" in feasibility["trailing_stop_logic_under_daily_bars"]["trigger_evaluation_timing"]
    assert "STRICTLY REJECTED" in feasibility["trailing_stop_logic_under_daily_bars"]["intraday_stop_rejection"]
    assert "BLOCKED" in feasibility["backtest_engine_implementation_status"]


def test_portfolio_invariants_and_blocker_disclosure(protocol_data):
    """Verify portfolio invariants and explicit disclosure of unresolved implementation blockers."""
    inv = protocol_data["portfolio_and_execution_invariants"]
    assert inv["initial_capital_inr"] == 1000000.0
    assert inv["max_concurrent_positions"] == 10
    assert inv["target_allocation_per_stock_pct"] == 0.10
    assert inv["integer_shares_only"] is True
    assert inv["zero_leverage"] is True
    assert inv["execution_slippage_bps"] == 5.0

    blockers = protocol_data["freeze_status_and_blockers"]["unresolved_blockers"]
    assert len(blockers) == 3
    blocker_ids = [b["blocker_id"] for b in blockers]
    assert any("ATR" in b_id for b_id in blocker_ids)
    assert any("THRESHOLD" in b_id for b_id in blocker_ids)
    assert any("DSR" in b_id for b_id in blocker_ids)
