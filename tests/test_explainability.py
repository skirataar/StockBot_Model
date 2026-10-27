"""
test_explainability.py
----------------------
Unit and integration tests for Sprint 5.1 Model Integrity Audit & Explainability.
Tests cover:
- Feature allowlisting and 8-family taxonomy coverage
- Artifact & config consistency with Sprint 5.0 report
- Mathematical integrity of feature importance outputs (split, gain, permutation)
- SVG visual figure generation
- Cryptographic preservation of frozen model and holdout test set
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest

from src.ml.dataset_builder import APPROVED_FEATURES
from src.models.model_audit_and_explainability import (
    EXPECTED_LIGHTGBM_SHA256,
    EXPECTED_TEST_PARQUET_SHA256,
    FEATURE_FAMILIES,
    FEATURE_TO_FAMILY,
    ModelIntegrityAuditor,
    compute_file_sha256,
)


# ==============================================================================
# 1. Feature Allowlisting & Family Taxonomy Tests
# ==============================================================================

def test_feature_allowlist_exact_30():
    """Verify that feature_importance.csv contains exactly the 30 approved features."""
    csv_path = Path("data/reports/feature_importance.csv")
    assert csv_path.exists(), "data/reports/feature_importance.csv is missing!"
    df = pd.read_csv(csv_path)

    assert len(df) == 30
    assert set(df["feature"]) == set(APPROVED_FEATURES)
    for col in ["symbol", "date", "forward_return_5d", "signal", "Open", "High", "Low", "Close", "Volume"]:
        assert col not in df["feature"].values


def test_feature_family_taxonomy_coverage():
    """Verify that all 30 approved features map cleanly into the 8 approved families."""
    assert len(FEATURE_FAMILIES) == 8
    all_family_features = [feat for feats in FEATURE_FAMILIES.values() for feat in feats]
    assert len(all_family_features) == 30
    assert set(all_family_features) == set(APPROVED_FEATURES)

    # Ensure no unclassified features exist in the lookup map
    for feat in APPROVED_FEATURES:
        assert feat in FEATURE_TO_FAMILY
        assert FEATURE_TO_FAMILY[feat] in FEATURE_FAMILIES


# ==============================================================================
# 2. Artifact & Config Consistency Tests
# ==============================================================================

def test_lightgbm_hyperparameter_consistency():
    """Verify that frozen LightGBM parameters match the Sprint 5.0 configuration exactly."""
    lgbm_path = Path("models/lightgbm.joblib")
    assert lgbm_path.exists()
    model = joblib.load(lgbm_path)
    params = model.get_params()

    assert params.get("n_estimators") == 100
    assert params.get("learning_rate") == 0.05
    assert params.get("max_depth") == 6
    assert params.get("num_leaves") == 31
    assert params.get("class_weight") == "balanced"
    assert params.get("subsample") == 0.8
    assert params.get("colsample_bytree") == 0.8
    assert params.get("random_state") == 42


def test_audit_summary_verdict_pass():
    """Verify that all 10 integrity checks passed in the audit summary JSON."""
    json_path = Path("data/reports/sprint_5_1_audit_summary.json")
    assert json_path.exists(), "Audit summary JSON is missing!"
    with open(json_path, "r") as f:
        data = json.load(f)

    assert data["verdict"] == "PASS"
    checks = data["checks"]
    assert len(checks) == 10
    for check_id, check_data in checks.items():
        assert check_data["status"] == "PASS", f"Check {check_id} failed: {check_data}"


# ==============================================================================
# 3. Importance Output Integrity Tests
# ==============================================================================

def test_feature_importance_shares_sum_to_100():
    """Verify that gain_pct and split_pct sum to approximately 100%."""
    df = pd.read_csv("data/reports/feature_importance.csv")

    assert np.isclose(df["gain_pct"].sum(), 100.0, atol=0.2)
    assert np.isclose(df["split_pct"].sum(), 100.0, atol=0.2)


def test_top_feature_rankings():
    """Verify top features by gain and validation permutation Macro-F1 drop."""
    df = pd.read_csv("data/reports/feature_importance.csv")

    top_gain = df.sort_values("gain_importance", ascending=False).iloc[0]
    assert top_gain["feature"] == "market_volatility"
    assert top_gain["gain_rank"] == 1

    top_perm = df.sort_values("perm_macro_f1_decrease", ascending=False).iloc[0]
    assert top_perm["feature"] == "realised_vol_60d"
    assert top_perm["perm_macro_f1_decrease"] > 0.01  # Significant drop


# ==============================================================================
# 4. Visual SVG Figures Tests
# ==============================================================================

def test_svg_figures_exist_and_valid():
    """Verify that all 3 diagnostic SVG figures exist and contain valid XML/SVG markup."""
    figures_dir = Path("data/reports/figures")
    for fname in [
        "feature_importance_gain.svg",
        "feature_importance_permutation.svg",
        "feature_family_importance.svg",
    ]:
        path = figures_dir / fname
        assert path.exists(), f"Figure {fname} is missing!"
        content = path.read_text(encoding="utf-8")
        assert len(content) > 200
        assert "<svg" in content
        assert "</svg>" in content


# ==============================================================================
# 5. Cryptographic Preservation of Model and Holdout Test Set
# ==============================================================================

def test_frozen_model_and_holdout_test_preservation():
    """Verify that neither the frozen model nor the holdout test set was modified."""
    actual_test_sha256 = compute_file_sha256("data/processed/test_dataset.parquet")
    actual_model_sha256 = compute_file_sha256("models/lightgbm.joblib")

    assert actual_test_sha256 == EXPECTED_TEST_PARQUET_SHA256, "Holdout test dataset hash altered!"
    assert actual_model_sha256 == EXPECTED_LIGHTGBM_SHA256, "Frozen LightGBM model hash altered!"
