"""
test_reconciliation.py
----------------------
Automated verification tests for Sprint 5.1.1 Explainability Report Reconciliation.

Verifies:
1. Family gain shares reconcile within documented numerical tolerance (sum to 100.0% ± 0.05%).
2. Narrative figures match the canonical importance artifact (data/reports/feature_importance.csv).
3. Every approved feature belongs to exactly one econometric family.
4. market_volatility permutation Macro-F1 drop reconciles to canonical -0.00036.
5. Cryptographic preservation of frozen model and holdout test set hashes.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.ml.dataset_builder import APPROVED_FEATURES
from src.models.model_audit_and_explainability import FEATURE_FAMILIES
from src.models.reconciliation_checker import (
    EXPECTED_LIGHTGBM_SHA256,
    EXPECTED_TEST_PARQUET_SHA256,
    compute_file_sha256,
)


def test_reconciled_family_gain_shares_sum_to_100():
    """Verify that reconciled family gain shares sum to 100.0% within numerical tolerance."""
    json_path = Path("data/reports/sprint_5_1_1_reconciliation.json")
    assert json_path.exists(), "Reconciliation JSON missing!"
    with open(json_path, "r") as f:
        data = json.load(f)

    families = data["family_reconciliation"]
    assert len(families) == 8

    total_gain_pct = sum(f["gain_pct"] for f in families)
    total_split_pct = sum(f["split_pct"] for f in families)

    assert abs(total_gain_pct - 100.0) <= 0.05, f"Gain shares sum to {total_gain_pct}%, expected 100%"
    assert abs(total_split_pct - 100.0) <= 0.05, f"Split shares sum to {total_split_pct}%, expected 100%"


def test_narrative_figures_match_canonical_csv():
    """Verify that reconciled narrative values match canonical feature_importance.csv."""
    csv_path = Path("data/reports/feature_importance.csv")
    assert csv_path.exists(), "feature_importance.csv missing!"
    df = pd.read_csv(csv_path)

    # 1. market_volatility permutation Macro-F1 drop
    mkt_vol = df[df["feature"] == "market_volatility"].iloc[0]
    assert np.isclose(mkt_vol["perm_macro_f1_decrease"], -0.00036, atol=1e-5)

    # 2. Recalculate family shares
    total_gain = df["gain_importance"].sum()
    vol_gain = df[df["family"] == "Volatility"]["gain_importance"].sum()
    bench_gain = df[df["family"] == "Benchmark / Cross-Sectional"]["gain_importance"].sum()

    vol_pct = round(vol_gain / total_gain * 100, 2)
    bench_pct = round(bench_gain / total_gain * 100, 2)

    assert vol_pct == 18.44, f"Volatility gain share mismatch: {vol_pct}% vs expected 18.44%"
    assert bench_pct == 34.27, f"Benchmark gain share mismatch: {bench_pct}% vs expected 34.27%"


def test_feature_family_exact_partition():
    """Verify that each feature is assigned to exactly one approved family without overlap."""
    assigned_features = []
    for fam_name, feats in FEATURE_FAMILIES.items():
        assigned_features.extend(feats)

    assert len(assigned_features) == 30
    assert len(set(assigned_features)) == 30  # No duplicates
    assert set(assigned_features) == set(APPROVED_FEATURES)


def test_reconciliation_json_verdict_and_discrepancies():
    """Verify that sprint_5_1_1_reconciliation.json records PASS and all 8 discrepancies."""
    json_path = Path("data/reports/sprint_5_1_1_reconciliation.json")
    with open(json_path, "r") as f:
        data = json.load(f)

    assert data["metadata"]["status"] == "PASS"
    discrepancies = data["discrepancies"]
    assert len(discrepancies) == 8

    # Ensure every discrepancy has resolution
    for d in discrepancies:
        assert "RESOLVED" in d["resolution"]
        assert d["source_artifact"] != ""
        assert d["canonical_reconciled_value"] != ""


def test_model_and_test_set_hashes_unchanged():
    """Verify that neither the model nor the holdout test set was modified."""
    model_sha = compute_file_sha256(Path("models/lightgbm.joblib"))
    test_sha = compute_file_sha256(Path("data/processed/test_dataset.parquet"))

    assert model_sha == EXPECTED_LIGHTGBM_SHA256, "Frozen LightGBM model hash changed!"
    assert test_sha == EXPECTED_TEST_PARQUET_SHA256, "Holdout test dataset hash changed!"
