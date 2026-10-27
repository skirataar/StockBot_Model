"""
test_dataset_builder.py
-----------------------
Unit and integration tests for Sprint 4.5.2 Dataset Integrity Remediation.
Tests cover:
- Approved 49-stock discovery and schema conformance
- Strict 30-feature contract allowlist
- Label verification (±2.0% ternary threshold, zero NaN targets)
- Mock data isolation (never mixes mock datasets into research data)
- Forward-label horizon trading-session purging at split boundaries
- Zero leakage mathematical verification
- Edge cases: stocks listed after train period (e.g. JIOFIN)
- Export formats (Parquet & CSV) and metadata integrity
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.ml.dataset_builder import (
    APPROVED_FEATURES,
    APPROVED_TARGETS,
    EXPECTED_49_SYMBOLS,
    DatasetBuilder,
    WarmUpPolicy,
)


@pytest.fixture
def genuine_labeled_dir():
    """Path to imported genuine 49-stock labeled datasets."""
    p = Path("data/labeled")
    if not p.exists() or len(list(p.glob("*_labeled.csv"))) < 49:
        pytest.skip("Genuine 49-stock labeled datasets not available in data/labeled/")
    return p


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for test exports."""
    out_dir = tmp_path / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


@pytest.fixture
def temp_reports_dir(tmp_path):
    """Temporary reports directory for test exports."""
    rep_dir = tmp_path / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    return rep_dir


def test_genuine_49_symbols_discovery(genuine_labeled_dir, temp_output_dir, temp_reports_dir):
    """Verify all 49 expected Nifty 50 research symbols are discovered."""
    builder = DatasetBuilder(data_dir=genuine_labeled_dir, output_dir=temp_output_dir, reports_dir=temp_reports_dir)
    df = builder.discover_and_load_labeled_data()

    symbols = sorted(df["symbol"].unique())
    assert len(symbols) == 49
    assert symbols == sorted(EXPECTED_49_SYMBOLS)
    assert len(df) == 190033


def test_approved_30_feature_contract(genuine_labeled_dir, temp_output_dir, temp_reports_dir):
    """Verify strict adherence to the 30 approved econometric features."""
    builder = DatasetBuilder(data_dir=genuine_labeled_dir, output_dir=temp_output_dir, reports_dir=temp_reports_dir)
    df = builder.discover_and_load_labeled_data()

    # Check that builder feature_columns strictly matches APPROVED_FEATURES
    assert builder.feature_columns == APPROVED_FEATURES
    assert len(builder.feature_columns) == 30

    # Ensure no raw OHLCV prices enter the feature list
    for raw_col in ["open", "high", "low", "close", "adj close", "volume"]:
        assert raw_col not in builder.feature_columns
        assert raw_col.capitalize() not in builder.feature_columns


def test_approved_label_thresholds_and_integrity(genuine_labeled_dir, temp_output_dir, temp_reports_dir):
    """Verify approved signal thresholds (±2.0%) and zero NaN target values."""
    builder = DatasetBuilder(data_dir=genuine_labeled_dir, output_dir=temp_output_dir, reports_dir=temp_reports_dir)
    df = builder.discover_and_load_labeled_data()

    # Zero NaN targets in input
    assert df["forward_return_5d"].isna().sum() == 0
    assert df["signal"].isna().sum() == 0

    # Class values must be {-1, 0, 1}
    assert set(df["signal"].unique()) == {-1, 0, 1}

    # Verify thresholds
    buy_min = df[df["signal"] == 1]["forward_return_5d"].min()
    sell_max = df[df["signal"] == -1]["forward_return_5d"].max()
    hold_min = df[df["signal"] == 0]["forward_return_5d"].min()
    hold_max = df[df["signal"] == 0]["forward_return_5d"].max()

    assert buy_min >= 0.02, f"BUY min {buy_min} is below +2.0%"
    assert sell_max <= -0.02, f"SELL max {sell_max} is above -2.0%"
    assert hold_min >= -0.02, f"HOLD min {hold_min} is below -2.0%"
    assert hold_max <= 0.02, f"HOLD max {hold_max} is above +2.0%"


def test_mock_data_isolation(genuine_labeled_dir, temp_output_dir, temp_reports_dir):
    """Verify mock datasets in data/mock are isolated and never loaded."""
    mock_dir = Path("data/mock")
    if mock_dir.exists():
        mock_files = list(mock_dir.glob("*.parquet"))
        assert len(mock_files) > 0, "Mock files should exist in data/mock"

    builder = DatasetBuilder(data_dir=genuine_labeled_dir, output_dir=temp_output_dir, reports_dir=temp_reports_dir)
    df = builder.discover_and_load_labeled_data()

    # Confirm loaded data does NOT come from mock parquet files
    assert len(df) == 190033
    assert df["symbol"].nunique() == 49


def test_trading_session_forward_horizon_purging(genuine_labeled_dir, temp_output_dir, temp_reports_dir):
    """
    Test that forward-label horizon purging removes exactly 5 trading sessions per symbol
    at split boundaries and prevents target-horizon leakage.
    """
    builder = DatasetBuilder(
        data_dir=genuine_labeled_dir,
        output_dir=temp_output_dir,
        reports_dir=temp_reports_dir,
        forward_horizon_sessions=5,
        purge_overlapping_horizon=True,
    )
    df = builder.discover_and_load_labeled_data()
    splits, purge_audit = builder.time_based_split_with_purging(df)

    # 48 stocks have train observations (JIOFIN listed in 2023, so 0 in train)
    assert purge_audit["train_to_val"]["total_purged_rows"] == 48 * 5  # 240 rows
    # All 49 stocks have validation observations
    assert purge_audit["val_to_test"]["total_purged_rows"] == 49 * 5   # 245 rows

    # Leakage verification flag
    assert purge_audit["verification_passed"] is True
    assert len(purge_audit["boundary_checks"]) == 0

    # Cross-check for RELIANCE
    rel_train_audit = purge_audit["train_to_val"]["per_symbol"]["RELIANCE"]
    assert rel_train_audit["purged_count"] == 5
    assert rel_train_audit["last_retained_date"] == "2022-12-23"
    assert rel_train_audit["target_horizon_of_last_retained"] == "2022-12-30"  # <= 2022-12-31

    rel_val_audit = purge_audit["val_to_test"]["per_symbol"]["RELIANCE"]
    assert rel_val_audit["purged_count"] == 5
    assert rel_val_audit["last_retained_date"] == "2024-12-23"
    assert rel_val_audit["target_horizon_of_last_retained"] == "2024-12-31"  # <= 2024-12-31


def test_irregular_listing_handling_jiofin(genuine_labeled_dir, temp_output_dir, temp_reports_dir):
    """Verify that JIOFIN (listed in 2023) is handled gracefully without errors."""
    builder = DatasetBuilder(data_dir=genuine_labeled_dir, output_dir=temp_output_dir, reports_dir=temp_reports_dir)
    df = builder.discover_and_load_labeled_data()
    splits, purge_audit = builder.time_based_split_with_purging(df)

    # JIOFIN has 0 train rows
    jiofin_train = splits["train"][splits["train"]["symbol"] == "JIOFIN"]
    assert len(jiofin_train) == 0

    # JIOFIN has val rows and 5 rows were purged
    jiofin_val_audit = purge_audit["val_to_test"]["per_symbol"]["JIOFIN"]
    assert jiofin_val_audit["purged_count"] == 5

    # JIOFIN has test rows
    jiofin_test = splits["test"][splits["test"]["symbol"] == "JIOFIN"]
    assert len(jiofin_test) > 0


def test_full_pipeline_build_and_artefacts(genuine_labeled_dir, temp_output_dir, temp_reports_dir):
    """Verify end-to-end build exports datasets, metadata, validation, and reconciliation reports."""
    builder = DatasetBuilder(data_dir=genuine_labeled_dir, output_dir=temp_output_dir, reports_dir=temp_reports_dir)
    splits, metadata, val_result = builder.build()

    assert val_result["status"] == "PASSED"
    assert val_result["ready_for_baseline_ml"] is True

    # Check exported files exist
    assert (temp_output_dir / "training_dataset.parquet").exists()
    assert (temp_output_dir / "training_dataset.csv").exists()
    assert (temp_output_dir / "validation_dataset.parquet").exists()
    assert (temp_output_dir / "validation_dataset.csv").exists()
    assert (temp_output_dir / "test_dataset.parquet").exists()
    assert (temp_output_dir / "test_dataset.csv").exists()
    assert (temp_output_dir / "dataset_metadata.json").exists()
    assert (temp_output_dir / "dataset_validation.json").exists()

    # Check reports exist
    assert (temp_reports_dir / "symbol_reconciliation.csv").exists()
    assert (temp_reports_dir / "sprint_4_5_2_remediation_report.md").exists()
    assert (temp_reports_dir / "sprint_4_5_2_validation.json").exists()

    # Verify reconciliation row sums
    rec_df = pd.read_csv(temp_reports_dir / "symbol_reconciliation.csv")
    assert len(rec_df) == 49
    assert rec_df["reconciled"].all()
    assert rec_df["raw_rows"].sum() == 190033
