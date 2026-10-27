# Sprint 6.1.1 — Independent Diagnostic Reconciliation Audit Report

**Date**: 2026-10-28  
**Auditor**: Lead Quantitative Researcher & Forensic Audit Engineer  
**Audit Target**: [`sprint_6_1_strategy_diagnostics_report.md`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_1_strategy_diagnostics_report.md) and [`sprint_6_1_strategy_diagnostics.json`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_1_strategy_diagnostics.json)  
**Authoritative Source Artifacts**:
- Frozen Model: [`models/lightgbm.joblib`](file:///home/skirataar/Website/StockBot_Model/models/lightgbm.joblib)
- Test Dataset: [`data/processed/test_dataset.parquet`](file:///home/skirataar/Website/StockBot_Model/data/processed/test_dataset.parquet)
- Backtest Trade Ledger: [`data/reports/trade_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/trade_ledger.csv)
- Portfolio Mark-to-Market Ledger: [`data/reports/portfolio_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/portfolio_ledger.csv)
- Baseline Reports: [`sprint_6_0_backtest_summary.json`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_backtest_summary.json), [`sprint_6_0_1_accounting_reconciliation.json`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_1_accounting_reconciliation.json), and [`sprint_6_0_3_final_accounting_invariant_audit.json`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_3_final_accounting_invariant_audit.json)  
**Audit Output Artifact**: [`sprint_6_1_1_diagnostic_reconciliation.json`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_1_1_diagnostic_reconciliation.json)  
**Dedicated Test Suite**: [`tests/test_sprint_6_1_1_diagnostic_reconciliation.py`](file:///home/skirataar/Website/StockBot_Model/tests/test_sprint_6_1_1_diagnostic_reconciliation.py)

---

## 1. Executive Summary & Audit Verdict

### Final Verdict: **PASS WITH LIMITATIONS**

An independent, read-only forensic quantitative audit of the Sprint 6.1 diagnostic artifacts has been conducted. The audit compared every metric reported in the narrative Markdown report against the structured JSON artifact and recomputed all values from the underlying immutable model, dataset, and ledgers.

### Key Audit Findings

1. **Reconciliation Status of Core Metrics**:
   The primary portfolio invariants—**621 completed trades, Gross P&L of +₹52,528.87, Total Friction of ₹213,207.51, Net P&L of -₹160,678.64, and Ending Mark-to-Market Equity of ₹840,519.64 (-15.95% return)**—are **100% mathematically verified** across both artifacts and all source ledgers.
2. **Identification of Metric Divergence**:
   Twelve (12) discrete discrepancies were identified between the Markdown report and the JSON artifact. Forensic tracing revealed that `sprint_6_1_strategy_diagnostics.json` was generated via direct programmatic computation from the authoritative ledgers and scikit-learn functions, whereas `sprint_6_1_strategy_diagnostics_report.md` inadvertently incorporated uncalibrated, draft numbers from pre-compaction scratch scripts (notably in quarterly trade slicing, calibration deciles, open-position distribution, and standard deviation calculations).
3. **Core Economic Hypotheses Remain Fully Validated**:
   Despite narrative discrepancies, the central strategic findings of Sprint 6.1 are **fully confirmed by the underlying ground-truth data**:
   - **Low-conviction dilution**: Trades entered with $P(\text{BUY}) \in [0.33, 0.40)$ generated **100% of the portfolio's net loss (-₹227,302.00 across 350 trades)**.
   - **High-conviction edge**: Trades with $P(\text{BUY}) \ge 0.40$ were **net profitable (+₹66,623.36 net across 271 trades)** after full statutory delivery taxes and slippage.
   - **Asymmetric exit drag**: Model-triggered `EARLY_SELL_SIGNAL` exits produced **+₹160,893.61 net**, whereas rigid 5-day calendar exits (`MAX_HOLD_5D`) produced catastrophic losses of **-₹307,827.78 net**.
4. **Authorization for Sprint 6.2**:
   Sprint 6.2 is **AUTHORIZED TO PROCEED**. All erroneous narrative figures are cataloged, corrected, and placed under 13 new automated regression and mutation tests (with all 67 repository tests passing).

---

## 2. Research Governance & Cryptographic Provenance

In strict compliance with quantitative research governance:
- The frozen Sprint 5.0 LightGBM classifier (`models/lightgbm.joblib`) was treated as strictly immutable and was **not retrained, tuned, or modified**.
- No thresholds, position sizing, holding periods, or execution rules were altered.
- The holdout test set was not used for strategy selection or optimization.
- Cryptographic SHA-256 hashes of all input artifacts were verified prior to computation:

| Artifact | File Path | Verified SHA-256 Hash | Verification Status |
| :--- | :--- | :--- | :--- |
| **Frozen LightGBM Model** | [`models/lightgbm.joblib`](file:///home/skirataar/Website/StockBot_Model/models/lightgbm.joblib) | `41e61760fc31c72095cd2071fdb843657bd76143ed4535f9b247db78e0c73761` | **MATCH (Immutable)** |
| **Processed Test Dataset** | [`data/processed/test_dataset.parquet`](file:///home/skirataar/Website/StockBot_Model/data/processed/test_dataset.parquet) | `7f9d0ce56b42a7cc2780f90edb4b27d9bc923847c6778e5ba4c6ebc754915381` | **MATCH (Immutable)** |
| **Trade Ledger** | [`data/reports/trade_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/trade_ledger.csv) | `f5340b8402c198730d53e4126a8b40463c7cdd832fc0919c1b6bafacf501eeff` | **MATCH (Canonical)** |
| **Portfolio Ledger** | [`data/reports/portfolio_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/portfolio_ledger.csv) | `f565b8c09b958023a243394bfb6e96887dd3588d44d38623c2b24faa43117f78` | **MATCH (Canonical)** |

---

## 3. Master Discrepancy Register

The following register details all 12 identified discrepancies, comparing the existing Markdown report, the existing JSON artifact, and the independently recomputed ground truth:

| ID | Metric Name | Markdown Value | JSON Value | Recomputed Ground Truth | Severity | Root Cause & Resolution |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| **DISC-01** | **Trade P&L Sample Std Dev** | Gross: ₹2,476.43<br>Net: ₹2,467.42 | Gross: ₹3,541.45<br>Net: ₹3,537.21 | **Gross: ₹3,541.45**<br>**Net: ₹3,537.21** | **MEDIUM** | **Root Cause**: Markdown copied placeholder draft numbers. JSON computed exact sample std ($ddof=1$).<br>**Status**: RESOLVED (Reconciled to JSON). |
| **DISC-02** | **Gross / Net Dollar Gains & Losses** | Gross Gains: ₹821,080.08<br>Gross Losses: -₹768,551.21<br>Losses Count: 315 | Gross Gains: ₹820,960.96<br>Gross Losses: -₹768,432.09<br>Losses Count: 314 | **Gross Gains: ₹820,960.96**<br>**Gross Losses: -₹768,432.09**<br>**Losses Count: 314** (Flat: 1) | **MEDIUM** | **Root Cause**: Trade #583 (TCS) had Gross=₹0.00 and Net=-₹309.86. Markdown assumed binary partition $N - 306 = 315$ losses.<br>**Status**: RESOLVED (Reconciled to JSON). |
| **DISC-03** | **Quantile Calibration Curve Bins** | Decile 1: (0.2078, 0.2219)<br>... Decile 10: (0.4217, 0.3749) | Decile 1: (0.1680, 0.2219)<br>... Decile 10: (0.4306, 0.3749) | **Decile 1: (0.1680, 0.2219)**<br>... **Decile 10: (0.4306, 0.3749)** | **HIGH** | **Root Cause**: Markdown narrative copied synthetic deciles from an early script rather than scikit-learn quantile output.<br>**Status**: RESOLVED (Reconciled to JSON). |
| **DISC-04** | **Probability-Band Win Rates & PF** | $[0.33, 0.40)$: WR=44.86%, Gross PF=0.8037, Net PF=0.6272 | $[0.33, 0.40)$: WR=45.43%, Gross PF=0.7524, Net PF=0.5440 | **$[0.33, 0.40)$: WR=45.43%**, **Gross PF=0.7524**, **Net PF=0.5440** | **HIGH** | **Root Cause**: Markdown table contained draft win rates (157 vs 159 wins). JSON correctly mapped trades by `signal_date`.<br>**Status**: RESOLVED (Reconciled to JSON). |
| **DISC-05** | **Invested Market Value & Cash Max** | Mean Inv: ₹498,393.59<br>Max Inv: ₹1,003,506.77<br>Max Cash: ₹1,000,000.00 | Mean Inv: ₹504,048.42<br>Max Inv: ₹1,022,577.89<br>Max Cash: ₹1,032,613.52 | **Mean Inv: ₹504,048.42**<br>**Max Inv: ₹1,022,577.89**<br>**Max Cash: ₹1,032,613.52** | **MEDIUM** | **Root Cause**: Markdown computed invested value via exposure proxy and overlooked Q2 2025 cash profits reaching ₹1.03M.<br>**Status**: RESOLVED (Reconciled to JSON). |
| **DISC-06** | **Open Positions Distribution** | 0 positions: 2 sessions<br>10 positions: 127 sessions | 0 positions: 67 sessions<br>10 positions: 127 sessions | **0 positions: 67 sessions**<br>**10 positions: 127 sessions** | **HIGH** | **Root Cause**: Markdown contained placeholder counts that omitted the 67 empty-portfolio sessions during the Q4 2025 lull.<br>**Status**: RESOLVED (Reconciled to JSON). |
| **DISC-07** | **Drawdown Trough Equity & Duration** | Trough: ₹788,604.28<br>Session 299<br>Duration: 220 sessions | Trough: ₹788,652.53<br>Session index 304<br>Duration: 226 sessions | **Trough: ₹788,652.53**<br>**Session 305 (idx 304)**<br>**Duration: 226 sessions** | **MEDIUM** | **Root Cause**: Markdown had a ₹48.25 transcription error and miscounted session offsets by 6 sessions.<br>**Status**: RESOLVED (Reconciled to JSON). |
| **DISC-08** | **Annual Breakdown (2025 vs 2026)** | 2025: Gross=+₹70.61K, Net=-₹41.33K, Exp=54.38%<br>2026: Gross=-₹18.08K, Net=-₹119.35K, Exp=54.83% | 2025: Gross=+₹76.53K, Net=-₹41.62K, Exp=41.26%<br>2026: Gross=-₹24.00K, Net=-₹119.06K, Exp=78.34% | **2025: Gross=+₹76,529.90, Net=-₹41,620.44, Exp=41.26%**<br>**2026: Gross=-₹24,001.03, Net=-₹119,058.20, Exp=78.34%** | **HIGH** | **Root Cause**: Markdown report narrative copied draft numbers from an uncalibrated scratch script.<br>**Status**: RESOLVED (Reconciled to JSON). |
| **DISC-09** | **Quarterly Performance Breakdown** | 2025Q1: 61s/87t/-₹14.25K/53% ...<br>2025Q4: 63s/87t/+₹3.23K/57% ...<br>2026Q3: 15s/24t/+₹16.00K/39% | 2025Q1: 62s/138t/-₹18.50K/67% ...<br>2025Q4: 62s/7t/-₹466.30/2.7% ...<br>2026Q3: 16s/34t/+₹1.42K/94% | **2025Q1: 62s / 138t / -₹18,503.11**<br>**2025Q4: 62s / 7t / -₹466.30**<br>**2026Q3: 16s / 34t / +₹1,423.63** | **CRITICAL** | **Root Cause**: Markdown report table contained corrupted trade/session slices (e.g. 2025Q4 had 7 trades, not 87 trades).<br>**Status**: RESOLVED (Reconciled to JSON). |
| **DISC-10** | **Market Regime Breakdown** | BULL: Gross=-₹45.62K, Costs=₹58.38K<br>SIDEWAYS: Gross=₹14.92K, Costs=₹90.62K<br>UNCLASS: WinRate=42.86% | BULL: Gross=-₹43.86K, Costs=₹60.14K<br>SIDEWAYS: Gross=₹14.05K, Costs=₹89.74K<br>UNCLASS: WinRate=40.82% | **BULL: Gross=-₹43,858.24, Costs=₹60,142.76**<br>**SIDEWAYS: Gross=₹14,050.05, Costs=₹89,744.95**<br>**UNCLASS: WinRate=40.82%** | **HIGH** | **Root Cause**: Markdown report copied shifted gross/costs figures from an earlier run (net P&L matched).<br>**Status**: RESOLVED (Reconciled to JSON). |
| **DISC-11** | **Equal-Weight Benchmark Sizing & Equity** | 47 constituents trading on Day 1 (₹21.28K each)<br>Gross Equity: ₹1,102,636.19 | 49 approved universe constituents (₹20.41K each)<br>Gross Equity: ₹1,102,607.68 | **Canonical Benchmark (49 stocks): ₹1,102,607.68**<br>Day 1 Active Sizing (47 stocks): ₹1,102,636.19<br>Variance: ₹28.51 (0.0026%) | **LOW** | **Root Cause**: Engine allocated $1/49$ across all approved constituents, whereas Markdown filtered to Day 1 active volume.<br>**Status**: RESOLVED (Canonical baseline confirmed). |
| **DISC-12** | **Top-10 Alphabetical Static Baseline 10th Stock** | 10th stock listed as BPCL<br>Ending Equity: ₹1,284,411.33 | 10th stock listed as BPCL<br>Ending Equity: ₹1,284,411.33 | **Canonical 10th stock: BHARTIARTL**<br>**Ending Equity: ₹1,284,448.74 (+28.44%)**<br>BPCL is constituent #12 | **LOW** | **Root Cause**: Both Sprint 6.1 artifacts misidentified constituent #10 as BPCL, causing a -₹37.41 variance against canonical baseline.<br>**Status**: RESOLVED (Corrected to BHARTIARTL). |

---

## 4. Forensic Deep-Dives into Material Discrepancies

### 4.1 Calibration Curve: Scikit-Learn Deciles vs Draft Placeholder (DISC-03)
In Section 2.4 of the Markdown report, Decile 1 was reported as having a mean predicted probability of `0.2078` against an empirical win rate of `0.2219`. However, executing `sklearn.calibration.calibration_curve(y_buy_binary, p_buy, n_bins=10, strategy='quantile')` reveals that Decile 1 mean predicted probability is actually **`0.1680`**.

The recomputed deciles prove that the model is **underconfident in Deciles 1 and 2** (empirical frequency exceeds predicted probability), and **overconfident in Deciles 3 through 10** (predicted probability exceeds empirical win rate by 1.10% to 7.12%).

```
Calibration Decile Comparison (Mean Predicted P(BUY)):
Decile:       1       2       3       4       5       6       7       8       9       10
Markdown:   0.2078  0.2443  0.2642  0.2796  0.2936  0.3082  0.3235  0.3409  0.3644  0.4217
Recomputed: 0.1680  0.2159  0.2477  0.2694  0.2868  0.3025  0.3192  0.3395  0.3673  0.4306
Actual Win: 0.2219  0.2204  0.2367  0.2367  0.2367  0.2462  0.2567  0.2735  0.2962  0.3749
Bias:       +5.38%  +0.45%  -1.10%  -3.27%  -5.00%  -5.63%  -6.25%  -6.59%  -7.12%  -5.57%
```

### 4.2 The TCS Flat-Trade Classification (DISC-02)
Markdown Section 3.2 reported 306 wins and 315 losses. Direct ledger audit of `trade_ledger.csv` revealed that `gross_pnl` contains **exactly one trade with 0.00 gross P&L**:
- **Trade ID #583**: Symbol `TCS`, Entry Date `2026-06-29`, Exit Date `2026-07-06`, Quantity `23 shares`, Entry Price with Slippage `₹3,889.34`, Exit Price with Slippage `₹3,889.34`.
- Gross P&L = `₹0.00`. Statutory Costs = `₹309.86`. Net P&L = `-₹309.86`.

Because this trade produced exactly zero gross profit, it is neither a gross win nor a gross loss:
- Gross Wins (`gross_pnl > 0`): **306 trades** (Sum = **+₹820,960.96**)
- Gross Losses (`gross_pnl < 0`): **314 trades** (Sum = **-₹768,432.09**)
- Gross Flat (`gross_pnl == 0`): **1 trade** (Trade #583, TCS)
- Total Trades: $306 + 314 + 1 = \mathbf{621\text{ trades}}$.

Markdown’s assumption of 315 losses caused an erroneous positive/negative gross leg summation (+₹821,080.08 / -₹768,551.21). The correct ground-truth sums match the JSON artifact (+₹820,960.96 / -₹768,432.09).

### 4.3 Quarterly Slicing Corruption (DISC-09)
The most severe divergence in the Markdown report occurred in Section 5.2 (Table of Quarterly Performance). Slicing the trade ledger by `entry_date` quarter confirms the true quarterly trade activity:

| Calendar Quarter | Sessions | Recomputed Trades | Markdown Claimed Trades | Recomputed Net P&L (INR) | Markdown Claimed Net P&L |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **2025 Q1** | 62 | **138** | 87 | **-₹18,503.11** | -₹14,248.88 |
| **2025 Q2** | 61 | **106** | 71 | **+₹51,088.32** | +₹39,019.53 |
| **2025 Q3** | 64 | **73** | 79 | **-₹73,739.35** | -₹69,328.66 |
| **2025 Q4** | 62 | **7** | 87 | **-₹466.30** | +₹3,229.44 |
| **2026 Q1** | 60 | **117** | 144 | **-₹149,823.38** | -₹169,458.11 |
| **2026 Q2** | 63 | **146** | 129 | **+₹29,341.55** | +₹34,106.63 |
| **2026 Q3** | 16 | **34** | 24 | **+₹1,423.63** | +₹16,001.41 |
| **Total** | **388** | **621** | **621** | **-₹160,678.64** | **-₹160,678.64** |

- In 2025 Q4, market volatility and signal counts compressed drastically; only **7 trades were entered across the entire 62 sessions** (net loss -₹466.30, average gross exposure 2.70%). Markdown falsely reported 87 trades and positive net P&L (+₹3,229.44).
- In 2026 Q3, exactly **16 sessions occurred** (2026-07-01 to 2026-07-22), executing **34 trades** (+₹1,423.63 net P&L). Markdown falsely reported 15 sessions and 24 trades.
- Recomputed quarterly Net P&Ls sum to exactly **-₹160,678.64**, and quarterly sessions sum to **388**.

### 4.4 Open Positions Distribution: The 67 Zero-Position Sessions (DISC-06)
Markdown Section 4.3 reported that the strategy held 0 open positions on only 2 sessions. Direct frequency counts of `portfolio_ledger['open_positions_count']` reveal that **the portfolio was completely in cash on 67 sessions (17.27% of the entire backtest)**:

```
Open Positions Distribution:
Positions:    0    1    2    3    4    5    6    7    8    9   10 (Cap)  Total
Markdown:     2   10   21   29   33   40   38   28   25   35     127     388
Recomputed:  67   28   25   16   34   22   22   13   22   12     127     388
Variance:   +65  +18   +4  -13   +1  -18  -16  -15   -3  -23       0       0
```
The 67 zero-position sessions occurred primarily during the low-volatility period of Q4 2025, where the model generated virtually zero BUY signals. The Markdown table completely masked this regime of inactivity.

---

## 5. Canonical Reconciled Diagnostics Reference

This section provides the authoritative, reconciled benchmark tables governing future work:

### 5.1 Reconciled Classification Diagnostics ($N = 19,012$)

```
                 Predicted SELL (-1)   Predicted HOLD (0)   Predicted BUY (1)    Total Actual
Actual SELL (-1)              1,625                2,075                 915           4,615
Actual HOLD  (0)              2,762                5,356               1,336           9,454
Actual BUY   (1)              1,618                2,178               1,147           4,943
Total Predicted               6,005                9,609               3,398          19,012
```
- Accuracy: **42.75%** | Macro-F1: **0.3810** | Binary BUY Brier Score: **0.1927**
- True BUY Mean $P(\text{BUY})$: **0.3069** vs Non-BUY Mean $P(\text{BUY})$: **0.2904** (Separation: **+1.65%**)

### 5.2 Reconciled Conviction Tiers ($N = 621$)

| Probability Band | Trades | Share | Gross P&L (INR) | Friction (INR) | Net P&L (INR) | Gross Win % | Net Win % | Net PF | Mean Net P&L |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$[0.33, 0.40)$** | 350 | 56.36% | -₹106,335.06 | ₹120,966.94 | **-₹227,302.00** | 45.43% | 40.00% | 0.5440 | -₹649.43 |
| **$[0.40, 0.45)$** | 181 | 29.15% | +₹58,778.41 | ₹61,834.58 | -₹3,056.17 | 53.59% | 49.17% | 0.9877 | -₹16.88 |
| **$[0.45, 0.50)$** | 64 | 10.31% | +₹48,676.56 | ₹21,635.19 | **+₹27,041.37** | 54.69% | 54.69% | 1.2773 | +₹422.52 |
| **$[0.50, 1.00]$** | 26 | 4.19% | +₹51,408.96 | ₹8,770.80 | **+₹42,638.16** | 57.69% | 50.00% | 2.2155 | +₹1,639.93 |
| **Subtotal $P \ge 0.40$** | **271** | **43.64%** | **+₹158,863.93** | **₹92,240.57** | **+₹66,623.36** | **54.24%** | **50.55%** | **1.1449** | **+₹245.84** |

### 5.3 Reconciled Exit Mechanisms ($N = 621$)

| Exit Reason | Trades | Share | Gross P&L (INR) | Friction (INR) | Net P&L (INR) | Gross Win % | Net Win % | Mean Net P&L |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`EARLY_SELL_SIGNAL`** | 337 | 54.27% | +₹278,313.73 | ₹117,420.12 | **+₹160,893.61** | 56.38% | 51.63% | +₹477.43 |
| **`MAX_HOLD_5D`** | 276 | 44.44% | -₹214,554.66 | ₹93,273.12 | **-₹307,827.78** | 40.94% | 37.32% | -₹1,115.32 |
| **`SYNTHETIC_LIQUIDATION`** | 8 | 1.29% | -₹11,230.20 | ₹2,514.27 | -₹13,744.47 | 0.00% | 0.00% | -₹1,718.06 |

---

## 6. Regression Testing & Verification

A dedicated automated test suite was constructed: [`tests/test_sprint_6_1_1_diagnostic_reconciliation.py`](file:///home/skirataar/Website/StockBot_Model/tests/test_sprint_6_1_1_diagnostic_reconciliation.py).

### 6.1 Test Suite Execution Log

```bash
PYTHONPATH=. /home/skirataar/Website/StockBot/venv/bin/pytest tests/test_sprint_6_1_1_diagnostic_reconciliation.py -v
```

```
============================= test session starts ==============================
platform linux -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/skirataar/Website/StockBot_Model
collected 13 items

tests/test_sprint_6_1_1_diagnostic_reconciliation.py::test_provenance_and_immutable_hashes PASSED [  7%]
tests/test_sprint_6_1_1_diagnostic_reconciliation.py::test_classification_metrics_and_confusion_matrix PASSED [ 15%]
tests/test_sprint_6_1_1_diagnostic_reconciliation.py::test_calibration_decile_reconciliation PASSED [ 23%]
tests/test_sprint_6_1_1_diagnostic_reconciliation.py::test_trade_ledger_standard_deviation_reconciliation PASSED [ 30%]
tests/test_sprint_6_1_1_diagnostic_reconciliation.py::test_gross_net_gains_and_flat_trade_partition PASSED [ 38%]
tests/test_sprint_6_1_1_diagnostic_reconciliation.py::test_probability_band_reconciliation PASSED [ 46%]
tests/test_sprint_6_1_1_diagnostic_reconciliation.py::test_portfolio_ledger_exposure_and_cash_extremes PASSED [ 53%]
tests/test_sprint_6_1_1_diagnostic_reconciliation.py::test_drawdown_trough_and_duration PASSED [ 61%]
tests/test_sprint_6_1_1_diagnostic_reconciliation.py::test_quarterly_reconciliation_identities PASSED [ 69%]
tests/test_sprint_6_1_1_diagnostic_reconciliation.py::test_regime_reconciliation_identities PASSED [ 76%]
tests/test_sprint_6_1_1_diagnostic_reconciliation.py::test_benchmark_reconciliation PASSED [ 84%]
tests/test_sprint_6_1_1_diagnostic_reconciliation.py::test_mutation_detection_fails_on_tampered_trade_ledger PASSED [ 92%]
tests/test_sprint_6_1_1_diagnostic_reconciliation.py::test_mutation_detection_fails_on_tampered_calibration_decile PASSED [100%]

======================== 13 passed, 2 warnings in 1.59s ========================
```

### 6.2 Full Repository Regression Run
```bash
PYTHONPATH=. /home/skirataar/Website/StockBot/venv/bin/pytest tests/ -v
# Result: 67 passed, 32 warnings in 27.99s (100% test pass rate)
```

---

## 7. Final Verdict & Sprint 6.2 Authorization

### Verdict: **PASS WITH LIMITATIONS**

### Justification
1. **Mathematical Consistency Restored**: Every numerical contradiction between `sprint_6_1_strategy_diagnostics_report.md` and `sprint_6_1_strategy_diagnostics.json` has been forensically explained and reconciled to authoritative underlying ledgers.
2. **Accounting Invariants Upheld**: Zero accounting identities failed. All quarterly sums, regime sums, and probability band sums match the verified totals: Gross P&L = +₹52,528.87, Total Friction = ₹213,207.51, Net P&L = -₹160,678.64, Ending Equity = ₹840,519.64.
3. **Core Economic Mechanisms Validated**: The low-conviction drag (-₹2.27L in $[0.33, 0.40)$), high-conviction alpha (+₹66.6K in $P \ge 0.40$), and time-stop penalty (-₹307.8K in `MAX_HOLD_5D`) are authentic empirical realities of the trading strategy.

### Findings Withdrawn or Corrected
- **WITHDRAWN**: Stale calibration decile values in Markdown Table 2.4 (corrected in DISC-03).
- **WITHDRAWN**: Corrupted quarterly trade counts and P&L in Markdown Table 5.2 (corrected in DISC-09).
- **WITHDRAWN**: Fabricated open-position distribution in Markdown Section 4.3 (corrected in DISC-06).
- **CORRECTED**: Sample standard deviation of trade P&L (Gross: ₹3,541.45, Net: ₹3,537.21 in DISC-01).
- **CORRECTED**: Top-10 alphabetical static baseline 10th constituent is `BHARTIARTL` (ending equity ₹1,284,448.74 in DISC-12).

### Authorization for Sprint 6.2
**Sprint 6.2 is formally AUTHORIZED TO PROCEED.** Quantitative researchers may now utilize the verified validation dataset to pre-register and test probability threshold filtering ($P(\text{BUY}) \ge \theta$) and dynamic stop-loss mechanisms.
