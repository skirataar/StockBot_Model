# Sprint 4.5.3 — Independent Dataset Integrity Verification Report

**Audit Type:** Independent Quantitative Research & ML Pipeline Audit  
**Scope:** Read-Only Verification of Sprint 4.5.2 Remediation Artifacts, Data Provenance, Features, Labels, Split Boundary Horizons, and Test Evidence  
**Audit Date:** 2026-10-28  
**Auditor:** Quantitative Systems Independent Audit Team  
**Executive Verdict:** **PASS — SPRINT 4.5 OFFICIALLY APPROVED FOR SPRINT 5 BASELINE ML**

---

## 1. Executive Summary

An independent, rigorous, read-only audit of `StockBot_Model` was performed to verify that Sprint 4.5.2 genuine data remediation, feature/label contract enforcement, and split boundary forward-horizon purging satisfy institutional quantitative standards.

Every verification check was executed independently against the physical datasets on disk using Python 3.14 and automated SHA-256 bit-for-bit hash comparisons against the original `QuantResearchLab` research files.

### Key Verification Milestones
1. **Bit-for-Bit Provenance Match (PASS):** All 49 genuine labeled CSV files in `data/labeled/` match the approved source files in `QuantResearchLab/data/labeled/` with **49 out of 49 identical SHA-256 hashes**. All 190,033 historical rows are preserved without alteration.
2. **Mock Data Complete Isolation (PASS):** The 5 synthetic mock `.parquet` datasets are isolated in `data/mock/` and are excluded from all research discovery paths.
3. **Strict 30-Feature Contract Allowlist (PASS):** The model matrix in all exported split datasets (`training_dataset`, `validation_dataset`, `test_dataset`) contains strictly the 30 approved econometric features from Sprint 3. Raw OHLCV prices and identifiers are excluded from the feature space.
4. **Target Calibration & Integrity (PASS):** Continuous target `forward_return_5d` and ternary classification `signal` match the approved ±2.0% threshold ($BUY \ge +2.0\%$, $SELL \le -2.0\%$, $HOLD \in [-2.0\%, +2.0\%]$) with **0 NaN target values**.
5. **Trading-Session Forward-Horizon Purging (PASS):** Evaluated every single observation across all 146,878 training rows and 23,658 validation rows against source date-to-target lookup sequences. **0 target leakage violations exist**. Exactly 5 trading sessions per symbol were purged at the Train $\to$ Val boundary (240 rows across 48 stocks) and Val $\to$ Test boundary (245 rows across 49 stocks).
6. **Mathematical Sample Reconciliation (PASS):**
   $$\text{Train (146,878)} + \text{Val (23,658)} + \text{Test (19,012)} + \text{Purged (485)} = \mathbf{190,033} \text{ (100.00\% exact)}$$
7. **Automated Test Suite (PASS):** All 7 automated unit and integration tests executed on the real data passed in 13.20 seconds with zero failures and zero warnings.

---

## 2. Verification of Actual Artifacts

The following required files were verified to exist on disk, be readable, and have expected non-zero sizes:

| Artifact Path | Format | Size | Record / Item Count | Status |
|---|---|---|---|---|
| `src/ml/dataset_builder.py` | Python Script | 44,784 bytes | 956 lines | Verified |
| `config.yaml` | YAML Configuration | 1,459 bytes | 66 lines | Verified |
| `tests/test_dataset_builder.py` | Pytest Module | 8,592 bytes | 200 lines | Verified |
| `data/labeled/` | Directory | — | 49 CSV files | Verified |
| `data/mock/` | Directory | 2.5 MB | 5 Parquet files | Verified |
| `data/processed/training_dataset.parquet` | Parquet (pyarrow) | 29,844,244 bytes | 146,878 rows, 34 cols | Verified |
| `data/processed/training_dataset.csv` | CSV | 75,288,674 bytes | 146,878 rows, 34 cols | Verified |
| `data/processed/validation_dataset.parquet` | Parquet (pyarrow) | 4,966,439 bytes | 23,658 rows, 34 cols | Verified |
| `data/processed/validation_dataset.csv` | CSV | 12,421,427 bytes | 23,658 rows, 34 cols | Verified |
| `data/processed/test_dataset.parquet` | Parquet (pyarrow) | 3,926,401 bytes | 19,012 rows, 34 cols | Verified |
| `data/processed/test_dataset.csv` | CSV | 9,825,100 bytes | 19,012 rows, 34 cols | Verified |
| `data/processed/dataset_metadata.json` | JSON Metadata | 2,581 bytes | Full metadata payload | Verified |
| `data/processed/dataset_validation.json` | JSON Validation | 1,823 bytes | Status: PASSED | Verified |
| `data/reports/sprint_4_5_2_remediation_report.md` | Markdown Report | 5,117 bytes | Remediation report | Verified |
| `data/reports/sprint_4_5_2_validation.json` | JSON Validation | 1,823 bytes | Status: PASSED | Verified |
| `data/reports/symbol_reconciliation.csv` | CSV Reconciliation | 2,327 bytes | 49 stocks reconciled | Verified |

---

## 3. Input Provenance & Universe Coverage Audit

### 3.1 Bit-for-Bit Hash Verification
Every file in `StockBot_Model/data/labeled/` was compared directly against its counterpart in `/home/skirataar/Website/QuantResearchLab/data/labeled/`:
- **Total Source Files:** 49 files (`ADANIENT_labeled.csv` through `WIPRO_labeled.csv`)
- **Total Target Files:** 49 files
- **SHA-256 Bit-for-Bit Matches:** **49 / 49 (100.0%)**
- **Discrepancies / Content Drift:** 0

### 3.2 Symbol Universe Coverage
The research universe contains 49 active constituents. All 49 expected symbols are present:
```text
ADANIENT, ADANIPORTS, APOLLOHOSP, ASIANPAINT, AXISBANK, BAJAJ-AUTO, BAJAJFINSV,
BAJFINANCE, BEL, BHARTIARTL, CIPLA, COALINDIA, DRREDDY, EICHERMOT, ETERNAL,
GRASIM, HCLTECH, HDFCBANK, HDFCLIFE, HEROMOTOCO, HINDALCO, HINDUNILVR,
ICICIBANK, INDUSINDBK, INFY, ITC, JIOFIN, JSWSTEEL, KOTAKBANK, LT,
M&M, MARUTI, NESTLEIND, NTPC, ONGC, POWERGRID, RELIANCE, SBILIFE,
SBIN, SHRIRAMFIN, SUNPHARMA, TATACONSUM, TATASTEEL, TCS, TECHM,
TITAN, TRENT, ULTRACEMCO, WIPRO
```
*(Note: As verified in QuantResearchLab Sprint 4 metadata, `TATAMOTORS` was excluded in earlier research data collection due to incomplete corporate action adjustment; 49 symbols constitute the official active research universe).*

### 3.3 Mock Data Isolation
- Inspection of `data/mock/` confirms exactly 5 mock Parquet files (`HDFCBANK.parquet`, `ICICIBANK.parquet`, `INFY.parquet`, `RELIANCE.parquet`, `TCS.parquet`).
- Inspection of `DatasetBuilder.discover_and_load_labeled_data()` in `src/ml/dataset_builder.py` confirms that the file pattern is strictly `*_labeled.csv` in `data/labeled/`.
- No mock file is discovered or included.

### 3.4 Input Row Count Reconciliation
Summing row counts directly across all 49 source files:
$$\sum_{i=1}^{49} \text{Rows}(\text{Symbol}_i) = \mathbf{190,033}$$
Matches the reported count in `label_metadata.json` and `sprint_4_5_2_remediation_report.md` with zero error.

---

## 4. Independent Verification of Features and Labels

### 4.1 Feature Space Conformance
All split datasets (`training_dataset`, `validation_dataset`, `test_dataset`) share the exact 34-column schema:
- **Identifiers (2):** `symbol`, `date`
- **Features (30):**
  1. Returns (6): `ret_1d`, `ret_5d`, `ret_10d`, `ret_20d`, `ret_60d`, `ret_120d`
  2. Momentum (4): `mom_5d`, `mom_10d`, `mom_20d`, `mom_60d`
  3. Volatility (4): `realised_vol_10d`, `realised_vol_20d`, `realised_vol_60d`, `vol_ratio_20d_60d`
  4. Volume (3): `vol_ma_30d`, `volume_z_score_30d`, `volume_spike_flag`
  5. Price Position (4): `high_52w`, `low_52w`, `dist_52w_high`, `dist_52w_low`
  6. Market Event (1): `crash_flag`
  7. Calendar (4): `month`, `quarter`, `month_sin`, `month_cos`
  8. Benchmark Alpha (4): `market_return`, `market_volatility`, `excess_return`, `beta_60d`
- **Targets (2):** `forward_return_5d`, `signal`

**Verification:**
- Raw non-stationary prices (`open`, `high`, `low`, `close`, `adj close`, `volume`) are **100% absent** from the feature matrix.
- No synthetic or unapproved features exist.

### 4.2 Independent Recomputation of Features and Targets
Selected random observations across multiple stocks (`RELIANCE`, `TCS`, `INFY`) were cross-checked by recomputing formulas from raw close prices:
- **`forward_return_5d`**: $\frac{Close_{t+5} - Close_t}{Close_t}$ matched source and exported values to 8 decimal places ($|diff| < 10^{-8}$).
- **`signal`**: $1 \text{ if } forward\_return\_5d \ge 0.02 \text{ else } (-1 \text{ if } \le -0.02 \text{ else } 0)$ verified across all observations.
- **`ret_1d`**: $\frac{Close_t - Close_{t-1}}{Close_{t-1}} \times 100$ verified against source features.
- **Warm-Up Policy:** Confirmed that early rows preserve `NaN` feature values (`WARMUP_POLICY = "KEEP"`). No historical observations from 2010 were discarded during ingestion.

---

## 5. Temporal Leakage Audit Using Actual Target Dates

To rigorously verify zero target leakage, an exhaustive audit evaluated **every single retained row** in `training_dataset` (146,878 rows) and `validation_dataset` (23,658 rows).

For each row, the observation date $t$ was mapped to its actual target valuation date $t+5$ using the symbol's true ordered trading session calendar.

### 5.1 Leakage Audit Summary
- **Overall Validation Period Start:** `2023-01-02`
- **Overall Test Period Start:** `2025-01-01`
- **Total Training Rows Checked:** 146,878
- **Training Rows with Target Valuation $\ge \text{2023-01-02}$:** **0 (ZERO LEAKAGE)**
- **Total Validation Rows Checked:** 23,658
- **Validation Rows with Target Valuation $\ge \text{2025-01-01}$:** **0 (ZERO LEAKAGE)**
- **Terminal Test Set NaN Targets:** **0**

### 5.2 Stock-by-Stock Boundary Verification (All 49 Symbols)

The table below confirms the exact source observation date and target-end valuation date for the final retained row of every symbol at both split boundaries:

| Symbol | Train Last Obs Date | Train Target-End Date | Train Leak-Free? | Val Last Obs Date | Val Target-End Date | Val Leak-Free? |
|---|---|---|---|---|---|---|
| `ADANIENT` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `ADANIPORTS` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `APOLLOHOSP` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `ASIANPAINT` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `AXISBANK` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `BAJAJ-AUTO` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `BAJAJFINSV` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `BAJFINANCE` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `BEL` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `BHARTIARTL` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `CIPLA` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `COALINDIA` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `DRREDDY` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `EICHERMOT` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `ETERNAL` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `GRASIM` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `HCLTECH` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `HDFCBANK` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `HDFCLIFE` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `HEROMOTOCO` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `HINDALCO` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `HINDUNILVR` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `ICICIBANK` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `INDUSINDBK` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `INFY` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `ITC` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `JIOFIN` | N/A (listed 2023) | N/A | ✅ Yes (0 train rows) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `JSWSTEEL` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `KOTAKBANK` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `LT` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `M&M` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `MARUTI` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `NESTLEIND` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `NTPC` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `ONGC` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `POWERGRID` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `RELIANCE` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `SBILIFE` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `SBIN` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `SHRIRAMFIN` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `SUNPHARMA` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `TATACONSUM` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `TATASTEEL` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `TCS` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `TECHM` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `TITAN` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `TRENT` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `ULTRACEMCO` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |
| `WIPRO` | 2022-12-23 | 2022-12-30 | ✅ Yes (< 2023-01-02) | 2024-12-23 | 2024-12-31 | ✅ Yes (< 2025-01-01) |

---

## 6. Output Counts & Metadata Reconciliation

All row counts and metrics were verified across the four independent sources:
1. Physical parquet/csv datasets on disk.
2. `dataset_metadata.json`.
3. `dataset_validation.json`.
4. `symbol_reconciliation.csv`.

| Metric | Physical File Count | Metadata JSON | Validation JSON | Reconciliation CSV | Agreement |
|---|---|---|---|---|---|
| **Raw Input Rows** | 190,033 | 190,033 | 190,033 | 190,033 | 100% Exact |
| **Train Retained Rows** | 146,878 | 146,878 | 146,878 | 146,878 | 100% Exact |
| **Train Purged Rows** | 240 | 240 | 240 | 240 | 100% Exact |
| **Val Retained Rows** | 23,658 | 23,658 | 23,658 | 23,658 | 100% Exact |
| **Val Purged Rows** | 245 | 245 | 245 | 245 | 100% Exact |
| **Test Retained Rows** | 19,012 | 19,012 | 19,012 | 19,012 | 100% Exact |
| **Total Post-Purge ML Rows** | 189,548 | 189,548 | 189,548 | 189,548 | 100% Exact |
| **Duplicate (symbol, date) Keys** | 0 | 0 | 0 | 0 | 100% Exact |
| **NaN Target Values** | 0 | 0 | 0 | 0 | 100% Exact |
| **Feature Count** | 30 | 30 | 30 | — | 100% Exact |
| **Target Count** | 2 | 2 | 2 | — | 100% Exact |

---

## 7. Automated Test Suite Audit

Execution command:
```bash
./venv/bin/python -m pytest tests/test_dataset_builder.py -v
```

Execution environment: Linux, Python 3.14.5, pytest-9.1.1.

### Test Results Table
| Test Name | Target Verified | Test Nature | Result |
|---|---|---|---|
| `test_genuine_49_symbols_discovery` | 49 symbols & 190,033 raw rows | **Real Data** | ✅ PASSED (0.98s) |
| `test_approved_30_feature_contract` | 30 econometric features, 0 raw price features | **Real Data** | ✅ PASSED (0.97s) |
| `test_approved_label_thresholds_and_integrity` | ±2.0% threshold, 0 NaN targets | **Real Data** | ✅ PASSED (0.96s) |
| `test_mock_data_isolation` | Mock Parquet isolated in `data/mock/` | **Real Data** | ✅ PASSED (0.95s) |
| `test_trading_session_forward_horizon_purging` | 240 train + 245 val purged rows, zero leakage | **Real Data** | ✅ PASSED (1.45s) |
| `test_irregular_listing_handling_jiofin` | `JIOFIN` late listing (0 train rows, 5 val purged) | **Real Data** | ✅ PASSED (1.35s) |
| `test_full_pipeline_build_and_artefacts` | Full build, parquet/csv exports, JSON & CSV reports | **Real Data** | ✅ PASSED (6.54s) |

**Overall Test Result:** **7 passed in 13.20 seconds (100% passing)**.

---

## 8. Remaining Considerations & Discrepancies

1. **Feature NaNs in Early Warm-Up Periods (Documented Design Decision):**
   - 58,441 rows (30.75% of raw observations) contain `NaN` in one or more rolling feature columns (principally `beta_60d` and `dist_52w_*`).
   - This directly reflects the approved Sprint 3 design decision (`WARMUP_POLICY = "KEEP"`).
   - In Sprint 5, ML algorithms like LightGBM and XGBoost natively handle missing feature values at tree split nodes. If models requiring dense feature matrices (e.g. Ridge Regression, MLP) are used, feature imputation or a trailing dropna must be applied within the model training pipeline.
2. **`TATAMOTORS` Universe Exclusion:**
   - `TATAMOTORS` was omitted during Sprint 3 / Sprint 4 data collection due to corporate action adjustments. The 49 stocks present form the approved research universe.

---

## 9. Final Auditor Recommendation

### Verdict: **PASS**

Sprint 4.5.2 satisfies all data-integrity, provenance, feature-contract, label-calibration, and temporal-leakage requirements. The datasets in `data/processed/` are sound, verified, and leak-free.

**Sprint 5 (Baseline ML Model Training) is officially cleared to proceed.**
