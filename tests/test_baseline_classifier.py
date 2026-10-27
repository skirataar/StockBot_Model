"""
test_baseline_classifier.py
---------------------------
Unit and integration tests for Sprint 5.0 Baseline ML Classification.
Tests cover:
- Preflight validation and exact 30-feature space
- Strict exclusion of identifiers (symbol, date) and targets (forward_return_5d, signal)
- Pipeline leakage safety (imputers and scalers fitted strictly on training data)
- Native NaN handling for tree-based models (LightGBM)
- Deterministic reproducibility under fixed random seeds
- Class label mapping (-1: SELL, 0: HOLD, 1: BUY) and confusion matrix structure
- Metric calculation consistency and artifact serializability
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

from src.models.baseline_classifier import (
    APPROVED_30_FEATURES,
    EXCLUDED_COLUMNS,
    CLASS_LABELS,
    CLASS_NAMES,
    BaselineClassifier,
    BaselineMLExperiment,
    compute_comprehensive_metrics,
)


@pytest.fixture
def test_datasets_exist():
    """Verify that processed splits exist before running dataset-dependent tests."""
    train_path = Path("data/processed/training_dataset.parquet")
    val_path = Path("data/processed/validation_dataset.parquet")
    test_path = Path("data/processed/test_dataset.parquet")
    if not (train_path.exists() and val_path.exists() and test_path.exists()):
        pytest.skip("Processed datasets not present in data/processed/")
    return train_path, val_path, test_path


@pytest.fixture
def synthetic_split_data():
    """Generate minimal synthetic train, val, and test splits with NaNs for fast isolated testing."""
    np.random.seed(42)
    n_train = 200
    n_val = 50
    n_test = 50

    def make_df(n_samples):
        data = {feat: np.random.randn(n_samples) for feat in APPROVED_30_FEATURES}
        # Inject realistic warm-up NaNs in select features
        data["dist_52w_high"][:10] = np.nan
        data["vol_ratio_20d_60d"][:15] = np.nan

        # Identifiers and targets
        data["symbol"] = np.random.choice(["RELIANCE", "TCS", "INFY"], size=n_samples)
        data["date"] = pd.date_range("2020-01-01", periods=n_samples, freq="D")
        data["forward_return_5d"] = np.random.randn(n_samples) * 0.03
        data["signal"] = np.random.choice([-1, 0, 1], size=n_samples, p=[0.25, 0.50, 0.25])
        return pd.DataFrame(data)

    return make_df(n_train), make_df(n_val), make_df(n_test)


# ==============================================================================
# 1. Feature Exclusion & Schema Tests
# ==============================================================================

def test_feature_list_exact_30():
    """Ensure exactly 30 features are approved and no extras exist."""
    assert len(APPROVED_30_FEATURES) == 30
    assert len(set(APPROVED_30_FEATURES)) == 30
    # Spot-check core econometric indicators from Sprint 3 specification
    assert "ret_1d" in APPROVED_30_FEATURES
    assert "mom_5d" in APPROVED_30_FEATURES
    assert "realised_vol_10d" in APPROVED_30_FEATURES
    assert "vol_ratio_20d_60d" in APPROVED_30_FEATURES
    assert "dist_52w_high" in APPROVED_30_FEATURES
    assert "beta_60d" in APPROVED_30_FEATURES


def test_target_and_identifier_exclusion(test_datasets_exist):
    """Ensure symbol, date, forward_return_5d, signal, and raw OHLCV are strictly excluded."""
    experiment = BaselineMLExperiment()
    experiment.load_and_preflight()

    for split_name, df in [("train", experiment.train_df), ("val", experiment.val_df), ("test", experiment.test_df)]:
        # Extract feature matrix exactly as used during model fitting
        X = df[APPROVED_30_FEATURES]
        y = df["signal"]

        assert set(X.columns) == set(APPROVED_30_FEATURES)
        for col in EXCLUDED_COLUMNS:
            assert col not in X.columns, f"Leaked column '{col}' found in {split_name} feature matrix!"

        assert y.name == "signal"
        assert "signal" not in X.columns
        assert "forward_return_5d" not in X.columns


# ==============================================================================
# 2. Leakage-Safe Preprocessing Pipeline Tests
# ==============================================================================

def test_pipeline_fitted_on_training_data_only(synthetic_split_data):
    """Verify that imputer and scaler statistics reflect training data only."""
    df_train, df_val, _ = synthetic_split_data
    experiment = BaselineMLExperiment()
    pipelines = experiment.build_candidate_pipelines()

    X_train = df_train[APPROVED_30_FEATURES]
    y_train = df_train["signal"]
    X_val = df_val[APPROVED_30_FEATURES]

    # Fit LogisticRegression pipeline on training set only
    lr_pipeline = pipelines["logistic_regression"]
    lr_pipeline.fit(X_train, y_train)

    imputer: SimpleImputer = lr_pipeline.named_steps["imputer"]
    scaler: StandardScaler = lr_pipeline.named_steps["scaler"]

    # Calculate expected training medians and means
    expected_medians = X_train.median().values
    expected_means = SimpleImputer(strategy="median").fit_transform(X_train).mean(axis=0)

    # Imputer statistics must exactly match training set medians
    np.testing.assert_allclose(imputer.statistics_, expected_medians, rtol=1e-5)
    # Scaler mean must match training imputed means
    np.testing.assert_allclose(scaler.mean_, expected_means, rtol=1e-5)

    # Transforming val must NOT alter imputer or scaler learned statistics
    prev_imputer_stats = imputer.statistics_.copy()
    prev_scaler_mean = scaler.mean_.copy()
    _ = lr_pipeline.predict(X_val)

    np.testing.assert_array_equal(imputer.statistics_, prev_imputer_stats)
    np.testing.assert_array_equal(scaler.mean_, prev_scaler_mean)


def test_tree_native_nan_support(synthetic_split_data):
    """Verify LightGBM handles feature NaNs natively during fit and predict without failing."""
    df_train, df_val, _ = synthetic_split_data
    experiment = BaselineMLExperiment()
    pipelines = experiment.build_candidate_pipelines()

    X_train = df_train[APPROVED_30_FEATURES]
    y_train = df_train["signal"]
    X_val = df_val[APPROVED_30_FEATURES]

    # Ensure test data actually has NaNs
    assert X_train.isna().sum().sum() > 0
    assert X_val.isna().sum().sum() > 0

    lgb_pipeline = pipelines["lightgbm"]
    # Must fit and predict without raising ValueError about NaNs
    lgb_pipeline.fit(X_train, y_train)
    preds = lgb_pipeline.predict(X_val)

    assert len(preds) == len(X_val)
    assert set(preds).issubset({-1, 0, 1})


# ==============================================================================
# 3. Deterministic Reproducibility
# ==============================================================================

def test_deterministic_reproducibility(synthetic_split_data):
    """Verify identical predictions and metrics are produced with fixed random seed."""
    df_train, df_val, _ = synthetic_split_data

    X_train = df_train[APPROVED_30_FEATURES]
    y_train = df_train["signal"]
    X_val = df_val[APPROVED_30_FEATURES]

    exp1 = BaselineMLExperiment(random_seed=42)
    pipe1 = exp1.build_candidate_pipelines()["lightgbm"]
    pipe1.fit(X_train, y_train)
    preds1 = pipe1.predict(X_val)

    exp2 = BaselineMLExperiment(random_seed=42)
    pipe2 = exp2.build_candidate_pipelines()["lightgbm"]
    pipe2.fit(X_train, y_train)
    preds2 = pipe2.predict(X_val)

    np.testing.assert_array_equal(preds1, preds2)


# ==============================================================================
# 4. Class Label Mapping & Metrics Generation
# ==============================================================================

def test_class_label_mapping():
    """Verify class labels match the specified ternary swing convention (-1, 0, 1)."""
    assert CLASS_LABELS == [-1, 0, 1]
    assert CLASS_NAMES[-1] == "SELL"
    assert CLASS_NAMES[0] == "HOLD"
    assert CLASS_NAMES[1] == "BUY"


def test_metric_calculation_structure(synthetic_split_data):
    """Verify evaluation metric dictionary schema and confusion matrix shape."""
    df_train, df_val, _ = synthetic_split_data
    experiment = BaselineMLExperiment()
    pipelines = experiment.build_candidate_pipelines()

    X_train = df_train[APPROVED_30_FEATURES]
    y_train = df_train["signal"]
    X_val = df_val[APPROVED_30_FEATURES]
    y_val = df_val["signal"]

    pipe = pipelines["dummy_most_frequent"]
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_val)

    metrics = compute_comprehensive_metrics(y_val, preds, "val", "dummy_most_frequent")

    assert "accuracy" in metrics
    assert "balanced_accuracy" in metrics
    assert "macro_f1" in metrics
    assert "weighted_f1" in metrics
    assert "confusion_matrix" in metrics
    assert "distributions" in metrics
    assert "predicted" in metrics["distributions"]
    assert "actual" in metrics["distributions"]

    # Confusion matrix must be 3x3
    cm_matrix = metrics["confusion_matrix"]["matrix"]
    assert len(cm_matrix) == 3
    assert all(len(row) == 3 for row in cm_matrix)

    # Per-class metrics must cover all three classes: -1, 0, 1
    assert set(metrics["per_class"].keys()) == {"-1", "0", "1"}


# ==============================================================================
# 5. Saved Artifacts Verification
# ==============================================================================

def test_saved_artifacts_loadable():
    """Verify that exported joblib models exist, are loadable, and can run predictions."""
    for model_name in ["dummy_most_frequent", "logistic_regression", "lightgbm"]:
        path = Path(f"models/{model_name}.joblib")
        assert path.exists(), f"Model artifact {path} is missing!"
        loaded_model = joblib.load(path)
        assert hasattr(loaded_model, "predict")

    metrics_file = Path("data/reports/baseline_model_metrics.json")
    assert metrics_file.exists()
    with open(metrics_file, "r") as f:
        data = json.load(f)

    assert "models" in data
    assert "final_test" in data
    assert data["model_selection"]["selected_model"] == "lightgbm"
    assert data["final_test"]["model_name"] == "lightgbm"
