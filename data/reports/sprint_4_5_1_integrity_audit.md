# Sprint 4.5.1 — Dataset Integrity Audit Report

**Audit Date:** 2026-10-27  
**Auditor:** Quantitative Systems Integrity Team  
**Scope:** Read-Only Audit of `src/ml/dataset_builder.py`, `data/labeled/`, `data/processed/`, and Data Provenance across Workspaces  
**Status:** **AUDIT COMPLETE — FINAL VERDICT: FAIL (CRITICAL DEFECTS DETECTED)**

---

## Executive Summary

Sprint 4.5 implemented `src/ml/dataset_builder.py` and passed all six synthetic unit tests. However, the resulting datasets in `data/processed/` **do not represent the approved 49-stock research universe or the approved 30-feature pipeline from Sprints 1–4**.

The audit identified three major structural failures:
1. **Mock Data Contamination:** The current dataset was generated from synthetic random-walk placeholder files containing only 5 hardcoded stocks (`HDFCBANK`, `ICICIBANK`, `INFY`, `RELIANCE`, `TCS`). The genuine 49-stock labeled datasets generated during Sprint 4 reside in a sibling workspace (`/home/skirataar/Website/QuantResearchLab/data/labeled/`) and were never copied or pointed to by the builder.
2. **Feature & Label Specification Mismatch:** The processed dataset contains 11 toy technical indicators (e.g., `sma_20`, `macd`, `rsi_14`) with an arbitrary ±1.5% signal threshold, completely bypassing the 30 econometric and market-calibrated features and ±2.0% threshold approved in Sprints 3 and 4.
3. **Temporal Horizon Leakage Across Split Boundaries:** Because the prediction target is a 5-trading-day forward return (`forward_return_5d`), splitting strictly on calendar boundary dates (`2022-12-30` to `2023-01-02` and `2024-12-31` to `2025-01-01`) without an embargo purge causes the last 4 trading days of the training set and validation set to leak future prices directly from the evaluation sets.

**Approval Recommendation:** **DO NOT APPROVE SPRINT 4.5.** Immediate corrective actions are required before any model training or baseline development can proceed.

---

## 1. Input File Audit

### 1.1 Discovered Files in `data/labeled/`

A complete scan of `data/labeled/` within the `StockBot_Model` project directory revealed the following:

| Filename | Format | Size (Bytes) | Last Modified | Inferred Symbol |
|---|---|---|---|---|
| `HDFCBANK.parquet` | Apache Parquet | 508,697 | 2026-10-27 23:33:03 | `HDFCBANK` |
| `ICICIBANK.parquet` | Apache Parquet | 508,682 | 2026-10-27 23:33:03 | `ICICIBANK` |
| `INFY.parquet` | Apache Parquet | 508,698 | 2026-10-27 23:33:03 | `INFY` |
| `RELIANCE.parquet` | Apache Parquet | 508,705 | 2026-10-27 23:33:03 | `RELIANCE` |
| `TCS.parquet` | Apache Parquet | 508,669 | 2026-10-27 23:33:03 | `TCS` |

- **Total Files:** 5
- **File Format:** 100% Apache Parquet (`.parquet`)
- **Unique Symbols Discovered:** 5 (`HDFCBANK`, `ICICIBANK`, `INFY`, `RELIANCE`, `TCS`)

### 1.2 Root Cause Analysis: Why Only 5 Stocks?

The dataset builder did not omit, filter, or encounter runtime errors on the remaining 44 stocks. Rather:
- When the `StockBot_Model` directory was initialized, `data/labeled/` was an empty directory.
- During implementation testing of Sprint 4.5, the command `python -m src.ml.dataset_builder --generate-sample` was executed.
- The utility function `generate_sample_labeled_dataset()` in `src/ml/dataset_builder.py` hardcoded a list of 5 stocks (`["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]`) and generated mock geometric Brownian motion data.
- The genuine 49-stock research universe datasets produced in earlier sprints reside in `/home/skirataar/Website/QuantResearchLab/data/labeled/` and were never imported or linked into this project.

**Section Audit Finding:** **FAIL**

---

## 2. Data Provenance Audit

### 2.1 Trace of Current Input Files

| Stock Symbol | Source File Path | Raw Rows | Date Range | Column Count |
|---|---|---|---|---|
| `HDFCBANK` | `data/labeled/HDFCBANK.parquet` | 2,999 | 2015-01-01 to 2026-06-30 | 20 |
| `ICICIBANK` | `data/labeled/ICICIBANK.parquet` | 2,999 | 2015-01-01 to 2026-06-30 | 20 |
| `INFY` | `data/labeled/INFY.parquet` | 2,999 | 2015-01-01 to 2026-06-30 | 20 |
| `RELIANCE` | `data/labeled/RELIANCE.parquet` | 2,999 | 2015-01-01 to 2026-06-30 | 20 |
| `TCS` | `data/labeled/TCS.parquet` | 2,999 | 2015-01-01 to 2026-06-30 | 20 |
| **Combined** | — | **14,995** | **2015-01-01 to 2026-06-30** | **20** |

Columns in these files:
`['symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'sma_20', 'sma_50', 'sma_200', 'ratio_close_sma_50', 'ratio_close_sma_200', 'volatility_20', 'return_5d', 'return_20d', 'rsi_14', 'macd', 'macd_signal', 'forward_return_5d', 'signal']`

### 2.2 Comparison with Earlier Feature and Label Engineering Pipelines

The true historical outputs from Sprints 1–4 are located in `/home/skirataar/Website/QuantResearchLab/`:
- **Location:** `/home/skirataar/Website/QuantResearchLab/data/labeled/*_labeled.csv`
- **Universe Count:** 49 unique Nifty 50 constituent stocks
- **Total Historical Rows:** 190,033 rows
- **Date Span:** 2010-01-04 to 2026-07-22
- **File Format:** `.csv` with naming pattern `<SYMBOL>_labeled.csv`
- **Total Columns:** 39 columns per stock

The 49 actual research stocks include:
`ADANIENT`, `ADANIPORTS`, `APOLLOHOSP`, `ASIANPAINT`, `AXISBANK`, `BAJAJ-AUTO`, `BAJAJFINSV`, `BAJFINANCE`, `BEL`, `BHARTIARTL`, `CIPLA`, `COALINDIA`, `DRREDDY`, `EICHERMOT`, `ETERNAL`, `GRASIM`, `HCLTECH`, `HDFCBANK`, `HDFCLIFE`, `HEROMOTOCO`, `HINDALCO`, `HINDUNILVR`, `ICICIBANK`, `INDUSINDBK`, `INFY`, `ITC`, `JIOFIN`, `JSWSTEEL`, `KOTAKBANK`, `LT`, `M&M`, `MARUTI`, `NESTLEIND`, `NTPC`, `ONGC`, `POWERGRID`, `RELIANCE`, `SBILIFE`, `SBIN`, `SHRIRAMFIN`, `SUNPHARMA`, `TATACONSUM`, `TATASTEEL`, `TCS`, `TECHM`, `TITAN`, `TRENT`, `ULTRACEMCO`, `WIPRO`.

**Discrepancy:** The current dataset was **NOT** built from the intended `data/labeled/` files. It was built from mock files created by the sample generator.

**Section Audit Finding:** **FAIL**

---

## 3. Feature & Label Provenance Audit

### 3.1 Feature Comparison: Current vs. Approved Specification

| Feature Name in Current Output | Present in Approved Pipeline (v3.1)? | Origin / Source File | Evaluation |
|---|---|---|---|
| `sma_20` | ❌ No | `src/ml/dataset_builder.py` (line 384) | Synthetic placeholder; unapproved |
| `sma_50` | ❌ No | `src/ml/dataset_builder.py` (line 385) | Synthetic placeholder; unapproved |
| `sma_200` | ❌ No | `src/ml/dataset_builder.py` (line 386) | Synthetic placeholder; unapproved |
| `ratio_close_sma_50` | ❌ No | `src/ml/dataset_builder.py` (line 387) | Synthetic placeholder; unapproved |
| `ratio_close_sma_200` | ❌ No | `src/ml/dataset_builder.py` (line 388) | Synthetic placeholder; unapproved |
| `volatility_20` | ❌ No (diff formula) | `src/ml/dataset_builder.py` (line 391) | Non-annualized standard deviation |
| `return_5d` | ❌ No (named `ret_5d`) | `src/ml/dataset_builder.py` (line 392) | Naming mismatch vs approved `ret_5d` |
| `return_20d` | ❌ No (named `ret_20d`) | `src/ml/dataset_builder.py` (line 393) | Naming mismatch vs approved `ret_20d` |
| `rsi_14` | ❌ No | `src/ml/dataset_builder.py` (line 399) | Unapproved heuristic RSI |
| `macd` | ❌ No | `src/ml/dataset_builder.py` (line 403) | Unapproved non-stationary MACD |
| `macd_signal` | ❌ No | `src/ml/dataset_builder.py` (line 404) | Unapproved MACD signal |

### 3.2 The Approved 30-Feature Pipeline (Sprint 3 Specification)

The genuine feature engineering pipeline (`QuantResearchLab/src/features/feature_engineering.py`, metadata version 3.1) establishes 30 mathematically sound features:
1. **Returns (6):** `ret_1d`, `ret_5d`, `ret_10d`, `ret_20d`, `ret_60d`, `ret_120d`
2. **Momentum (4):** `mom_5d`, `mom_10d`, `mom_20d`, `mom_60d`
3. **Volatility (4):** `realised_vol_10d`, `realised_vol_20d`, `realised_vol_60d`, `vol_ratio_20d_60d` (annualized factor: 15.87)
4. **Volume (3):** `vol_ma_30d`, `volume_z_score_30d`, `volume_spike_flag` (2.0x threshold)
5. **Price Position (4):** `high_52w`, `low_52w`, `dist_52w_high`, `dist_52w_low` (252-day window)
6. **Market Events (1):** `crash_flag` (expanding 5th percentile, look-ahead safe)
7. **Calendar (4):** `month`, `quarter`, `month_sin`, `month_cos` (cyclical harmonics)
8. **Benchmark / Cross-Sectional Alpha (4):** `market_return`, `market_volatility`, `excess_return`, `beta_60d` (vs `^NSEI`)

**None of these 30 approved features exist in the current dataset.**

### 3.3 Label Verification: Target Definition and Thresholds

| Parameter | Current Output | Approved Sprint 4 Specification | Status |
|---|---|---|---|
| Target Column 1 | `forward_return_5d` | `forward_return_5d` | Match |
| Target Column 2 | `signal` | `signal` | Match |
| Buy Threshold | **+1.5% (+0.015)** | **+2.0% (+0.02)** | **MISMATCH** |
| Sell Threshold | **-1.5% (-0.015)** | **-2.0% (-0.02)** | **MISMATCH** |
| Class Mapping | 1 (Buy), 0 (Hold), -1 (Sell) | 1 (Buy), 0 (Hold), -1 (Sell) | Match |
| Total Labelled Samples | 13,975 | 190,033 | **MISMATCH** |

In Sprint 4 (`QuantResearchLab/data/reports/label_metadata.json`), econometric volatility calibration mandated a **±2.0% threshold** to yield an institutional 30.64% BUY / 44.22% HOLD / 25.14% SELL distribution. The current dataset used an arbitrary ±1.5% threshold.

**Section Audit Finding:** **FAIL**

---

## 4. Date Range Audit

### 4.1 Why the Current Data Starts on 2015-10-07

The discrepancy between the expected 2010 start date and the current 2015-10-07 start date is explained by two cumulative factors:
1. **Generator Input Date:** `generate_sample_labeled_dataset()` had a hardcoded `start_date="2015-01-01"`. It did not generate dates between 2010-01-01 and 2014-12-31.
2. **Warm-Up Trimming Window:** The feature `sma_200` has a 200-business-day rolling lookback. Under policy `WARMUP_POLICY = "DROP"`, the first 199 trading days had `NaN` feature values and were dropped. 
   - 2015-01-01 + 199 trading days = **2015-10-07**.

### 4.2 Stock-by-Stock Date Range in Current Dataset

| Stock Symbol | Raw Source Start | Raw Source End | Post Warm-Up Start | Post Target Drop End | Warm-Up Dropped Rows | Target Dropped Rows | Final Rows |
|---|---|---|---|---|---|---|---|
| `HDFCBANK` | 2015-01-01 | 2026-06-30 | 2015-10-07 | 2026-06-23 | 199 | 5 | 2,795 |
| `ICICIBANK` | 2015-01-01 | 2026-06-30 | 2015-10-07 | 2026-06-23 | 199 | 5 | 2,795 |
| `INFY` | 2015-01-01 | 2026-06-30 | 2015-10-07 | 2026-06-23 | 199 | 5 | 2,795 |
| `RELIANCE` | 2015-01-01 | 2026-06-30 | 2015-10-07 | 2026-06-23 | 199 | 5 | 2,795 |
| `TCS` | 2015-01-01 | 2026-06-30 | 2015-10-07 | 2026-06-23 | 199 | 5 | 2,795 |
| **Combined** | **2015-01-01** | **2026-06-30** | **2015-10-07** | **2026-06-23** | **995** | **25** | **13,975** |

### 4.3 Provenance of Dates in the Actual Research Universe

In the genuine dataset (`QuantResearchLab/data/labeled/`):
- **44 stocks** start on **2010-01-04**.
- **5 stocks** start later due to actual exchange listing dates:
  - `COALINDIA`: 2010-11-04 (IPO)
  - `SBILIFE`: 2017-10-03 (IPO)
  - `HDFCLIFE`: 2017-11-17 (IPO)
  - `ETERNAL` (Zomato): 2021-07-23 (IPO)
  - `JIOFIN`: 2023-08-21 (Demerger listing)
- **All 49 stocks** end on **2026-07-22**.
- Under Sprint 3 feature engineering, `WARMUP_POLICY = "KEEP"` was preserved, retaining all early dates with `NaN` feature values intact in the labeled files.

**Section Audit Finding:** **FAIL**

---

## 5. Row Count Reconciliation

### 5.1 Verification of Reported Current Counts

| Processing Stage | Expected Formula | Audited Count | Discrepancy |
|---|---|---|---|
| Raw combined input | 5 stocks × 2,999 days | 14,995 | 0 |
| Feature warm-up drop | 5 stocks × 199 initial rows (`sma_200` NaNs) | 995 | 0 |
| Remaining after warm-up | 14,995 − 995 | 14,000 | 0 |
| Trailing unlabelled target drop | 5 stocks × 5 horizon days (`shift(-5)`) | 25 | 0 |
| Final ML sample count | 14,000 − 25 | 13,975 | 0 |

### 5.2 Split Reconciliation

| Split Name | Date Range | Sample Count | % of Total | Unique Stocks |
|---|---|---|---|---|
| `train` | 2015-10-07 to 2022-12-30 | 9,440 | 67.55% | 5 |
| `val` | 2023-01-02 to 2024-12-31 | 2,610 | 18.68% | 5 |
| `test` | 2025-01-01 to 2026-06-23 | 1,925 | 13.77% | 5 |
| **Total** | — | **13,975** | **100.00%** | **5** |

The mathematical counts within the synthetic dataset reconcile with zero error. However, when reconciled against the **true historical database** (190,033 labelled rows), **176,058 rows (92.65% of the data) are absent**.

**Section Audit Finding:** **PASS (Internally Reconciled) / FAIL (Universe Incomplete)**

---

## 6. Temporal Leakage Audit

### 6.1 Prediction Target Mechanics

The target variable is `forward_return_5d`:
$$R_{t \to t+5} = \frac{Close_{t+5} - Close_t}{Close_t}$$

For any observation recorded on date $T$, calculating its label requires knowledge of the close price on trading day $T+5$. 

### 6.2 Split Boundary Examination

#### Boundary 1: Train to Validation
- **Train Maximum Date:** `2022-12-30` (Friday)
- **Validation Minimum Date:** `2023-01-02` (Monday)
- **Calendar Gap:** 3 days (1 weekend)
- **Trading Day Gap:** **0 trading days**

**Leakage Mechanism:**
- A sample in `training_dataset` on `2022-12-30` uses the close price from trading day $T+5$, which is **2023-01-06 (Friday)**.
- `2023-01-06` is the 5th trading day of the `validation_dataset`.
- **4 full trading days** of training samples directly leak future validation prices:
  - Train row `2022-12-27` looks ahead to validation date `2023-01-03`.
  - Train row `2022-12-28` looks ahead to validation date `2023-01-04`.
  - Train row `2022-12-29` looks ahead to validation date `2023-01-05`.
  - Train row `2022-12-30` looks ahead to validation date `2023-01-06`.
- **Affected Samples:** 4 trading days × 5 stocks = **20 training samples** containing target leakage from the validation set.

#### Boundary 2: Validation to Test
- **Validation Maximum Date:** `2024-12-31` (Tuesday)
- **Test Minimum Date:** `2025-01-01` (Wednesday)
- **Calendar Gap:** 1 day
- **Trading Day Gap:** **0 trading days**

**Leakage Mechanism:**
- Validation samples from `2024-12-26`, `2024-12-27`, `2024-12-30`, and `2024-12-31` evaluate their labels using close prices from January 2025 (inside `test_dataset`).
- **Affected Samples:** 4 trading days × 5 stocks = **20 validation samples** containing target leakage from the test set.

### 6.3 Audit Finding on Chronological Ordering

> [!CAUTION]
> **Strict chronological sorting alone does not prevent data leakage when targets are forward-looking.**
> If $T_{train, max} < T_{val, min}$, feature values do not leak past into future, but **target values at the tail of the earlier split peer directly into the prices of the subsequent split**.

To guarantee zero leakage:
An **embargo purge of at least 5 trading days** must be removed from the end of each preceding split, or each subsequent split must begin after a 5-trading-day buffer.

**Section Audit Finding:** **FAIL (Critical Leakage Hazard)**

---

## 7. Findings Matrix & Final Verdict

### 7.1 Summary of Findings

| ID | Audit Area | Status | Core Finding |
|---|---|---|---|
| **F-01** | Input Universe | **FAIL** | Only 5 stocks discovered; actual 49 stocks reside in `QuantResearchLab` and were not loaded. |
| **F-02** | Data Provenance | **FAIL** | Datasets built from synthetic random-walk files rather than historical market data. |
| **F-03** | Feature Specification | **FAIL** | 11 toy features processed instead of the approved 30-feature econometric specification. |
| **F-04** | Label Specification | **FAIL** | Arbitrary ±1.5% signal threshold used instead of the approved ±2.0% volatility-calibrated threshold. |
| **F-05** | Date Range Coverage | **FAIL** | Data spans 2015-10-07 to 2026-06-23 instead of the 2010–2026 historical horizon. |
| **F-06** | Row Count Internal Math | **PASS** | Internal math (14,995 raw − 995 warm-up − 25 unlabelled = 13,975) reconciles exactly. |
| **F-07** | Target Horizon Leakage | **FAIL** | Boundary dates lack an embargo purge; 4 trading days per stock overlap across train/val and val/test splits. |

---

### 7.2 Final Verdict

### ❌ **DO NOT APPROVE SPRINT 4.5**

The current implementation is an operational skeleton that passes unit tests on mock data, but the resulting dataset is **completely invalid for machine learning research or baseline training**.

---

## 8. Recommended Corrective Action Plan

Before requesting re-audit and proceeding to model training (Sprint 5):

1. **Import True Research Data:**
   - Copy or symlink all 49 files from `/home/skirataar/Website/QuantResearchLab/data/labeled/*_labeled.csv` into `data/labeled/`.
2. **Remove Synthetic Data Generation from Core Pipeline:**
   - Isolate or delete `generate_sample_labeled_dataset()` from `dataset_builder.py` so mock data cannot be generated into `data/labeled/`.
3. **Harmonize Column Naming & Target Thresholds:**
   - Ensure `DatasetBuilder` loads and retains all 30 approved features (`ret_1d` through `ret_120d`, `mom_5d` through `mom_60d`, `realised_vol_*`, `volume_z_score_30d`, `dist_52w_*`, `crash_flag`, calendar encodings, and benchmark alpha metrics).
   - Enforce the approved ±2.0% threshold for `signal`.
4. **Implement Mandatory Embargo Purging:**
   - Update `DatasetBuilder.time_based_split()` to automatically drop the last $N$ trading days (where $N = 5$) from the end of the `train` and `val` splits.
   - Verify that $T_{train, max} + 5\text{ trading days} < T_{val, min}$ and $T_{val, max} + 5\text{ trading days} < T_{test, min}$.
5. **Re-run Dataset Building & Verification:**
   - Generate true `training_dataset.parquet`, `validation_dataset.parquet`, and `test_dataset.parquet` covering ~175,000+ samples across all 49 stocks from 2010 through 2026.
