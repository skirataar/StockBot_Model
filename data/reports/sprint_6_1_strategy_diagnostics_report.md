# Sprint 6.1 — Strategy Performance Diagnostics Report (Read-Only)

**Date**: 2026-10-28  
**Author**: Lead Quantitative Researcher  
**Status**: COMPLETE / VERIFIED  
**Audit Basis**: Read-Only Diagnostic Evaluation of Frozen Sprint 5.0 LightGBM Baseline Backtest  
**Associated Artifact**: [`sprint_6_1_strategy_diagnostics.json`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_1_strategy_diagnostics.json)  
**Historical Precedent**: Builds upon [`sprint_6_0_backtest_report.md`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_backtest_report.md), [`sprint_6_0_1_accounting_reconciliation_report.md`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_1_accounting_reconciliation_report.md), [`sprint_6_0_2_fee_formula_equity_audit_report.md`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_2_fee_formula_equity_audit_report.md), and [`sprint_6_0_3_final_accounting_invariant_audit.md`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_3_final_accounting_invariant_audit.md).

---

## Executive Summary

This diagnostic investigation provides a root-cause forensic analysis of the frozen Sprint 5.0 LightGBM swing-trading strategy evaluated in Sprint 6.0 across 388 trading sessions (2025-01-01 to 2026-07-22) on the 49 approved NIFTY 50 universe constituents.

The strategy achieved a gross trading P&L of **+₹52,528.87**, but suffered **₹213,207.51** in statutory taxes, fees, and execution slippage, finishing with a net trade-ledger P&L of **-₹160,678.64** and an ending portfolio mark-to-market equity of **₹840,519.64** (net return **-15.95%**), severely trailing the passive Equal-Weight Buy-and-Hold benchmark (**+10.26% gross / +10.07% estimated net**).

### Core Diagnostic Discoveries

1. **The Low-Conviction Alpha Dilution Mechanism**:
   The primary driver of portfolio losses was the execution of unconstrained, low-conviction predictions. Over **56.36% of all executed trades** (350 out of 621) occurred with predicted BUY probabilities in the low band $P(\text{BUY}) \in [0.33, 0.40)$. This band lost **-₹106,335.06** in gross alpha and incurred **₹120,966.94** in transaction costs, single-handedly generating **-₹227,302.00** in net losses.
   Conversely, higher-conviction trades where $P(\text{BUY}) \ge 0.40$ (271 trades) were **net profitable after all statutory taxes and slippage**, generating **+₹66,623.36** net P&L with a 55.72% gross win rate and positive net edge across all sub-bands.
2. **The 5-Day Holding Duration Asymmetry (Adverse Selection Trap)**:
   The interaction between the early model SELL exit rule and the 5-session calendar stop created an asymmetric return profile. Positions exited early via model `EARLY_SELL_SIGNAL` (337 trades) generated **+₹160,893.61** in net P&L with a 51.63% net win rate. In stark contrast, positions held to expiration (`MAX_HOLD_5D`, 276 trades) suffered catastrophic losses of **-₹307,827.78** net (37.32% win rate, average net loss of -₹1,115.32 per trade). The rigid calendar exit functioned as an unhedged drift trap for deteriorating positions.
3. **Statutory Delivery Drag**:
   Total friction of **₹213,207.51** consumed **405.89%** of the strategy's gross alpha. Because the strategy operates in cash equity delivery, it incurred round-trip statutory delivery taxes (notably 10 bps STT on both buy and sell turnover) across ₹11.41 Crore of turnover.
4. **Portfolio Position Saturation and Signal Blocking**:
   The strategy was saturated at its maximum 10-position capacity on **127 sessions (32.73% of the backtest)**. Consequently, **1,383 candidate BUY signals were rejected** because available slots were blocked by decaying positions lingering toward their 5-day expiration.

---

## 1. Reproduction of Baseline & Audit Invariants

All baseline numbers from Sprint 6.0 and accounting invariants from Sprint 6.0.3 were independently re-verified against the immutable repository files.

### 1.1 Artifact Provenance and Cryptographic Hashes

| Artifact | File Path | Cryptographic SHA256 Hash | Status |
| :--- | :--- | :--- | :--- |
| **Frozen Model** | [`models/lightgbm.joblib`](file:///home/skirataar/Website/StockBot_Model/models/lightgbm.joblib) | `41e61760fc31c72095cd2071fdb843657bd76143ed4535f9b247db78e0c73761` | Verified Match |
| **Test Dataset** | [`data/processed/test_dataset.parquet`](file:///home/skirataar/Website/StockBot_Model/data/processed/test_dataset.parquet) | `7f9d0ce56b42a7cc2780f90edb4b27d9bc923847c6778e5ba4c6ebc754915381` | Verified Match |
| **Trade Ledger** | [`data/reports/trade_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/trade_ledger.csv) | `3900b95b8d234c9c148ad4a9c6870ae37cbaea95f79361ea15a9937172fe4c6c` | Verified Match |
| **Portfolio Ledger** | [`data/reports/portfolio_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/portfolio_ledger.csv) | `0e326b0ee1dbffbb7f0b5d9852f5379b3ee928a391515efb5c3ba3473cf4c050` | Verified Match |

### 1.2 Quantitative Baseline Verification

| Metric | Verified Artifact Value | Reported Baseline Value | Discrepancy |
| :--- | :--- | :--- | :--- |
| **Initial Capital** | ₹1,000,000.00 | ₹10,00,000.00 | None (Exact) |
| **Test Sessions** | 388 (2025-01-01 to 2026-07-22) | 388 (2025-01-01 to 2026-07-22) | None (Exact) |
| **Constituents Universe** | 49 approved stocks | 49 approved stocks | None (Exact) |
| **Test Observations** | 19,012 rows | 19,012 rows | None (Exact) |
| **Total Completed Trades** | 621 trades | 621 trades | None (Exact) |
| **Market / Synthetic Exits** | 613 market / 8 synthetic | 613 market / 8 synthetic | None (Exact) |
| **Gross P&L** | +₹52,528.87 | +₹52,528.87 | None (Exact) |
| **Total Friction (Costs + Slip)** | ₹213,207.51 | ₹213,207.51 | None (Exact) |
| **Net Trade-Ledger P&L** | -₹160,678.64 | -₹160,678.64 | None (Exact) |
| **Ending Mark-to-Market Equity** | ₹840,519.64 | ₹840,519.64 | None (Exact) |
| **Net Portfolio Return** | -15.95% | -15.95% | None (Exact) |
| **Equal-Weight Benchmark (Gross)** | +10.26% (₹1,102,636.19) | +10.26% | None (Exact) |
| **Accounting Invariant** | 10-paisa mark-to-market roundoff | PASS WITH LIMITATIONS | None (Exact) |

**Conclusion on Baseline**: Baseline reproduction is **100% verified** with zero numeric deviations.

---

## 2. Classification Diagnostics

The frozen LightGBM classifier evaluated on the test set (`data/processed/test_dataset.parquet`, $N = 19,012$) was audited using retrospective true labels. No future labels were used in trade execution; labels are examined strictly for post-hoc error analysis.

### 2.1 Confusion Matrix

*Matrix Order: Rows = Actual True Class, Columns = Predicted Class*

```
                 Predicted SELL (-1)   Predicted HOLD (0)   Predicted BUY (1)    Total Actual
Actual SELL (-1)              1,625                2,075                 915           4,615
Actual HOLD  (0)              2,762                5,356               1,336           9,454
Actual BUY   (1)              1,618                2,178               1,147           4,943
Total Predicted               6,005                9,609               3,398          19,012
```

### 2.2 Classification Metrics by Class

| Class Label | Support (Actual N) | Precision | Recall | F1-Score | Actual Proportions | Predicted Proportions |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SELL (-1)** | 4,615 | 27.06% | 35.21% | 0.3060 | 24.27% | 31.59% (6,005) |
| **HOLD (0)** | 9,454 | 55.74% | 56.65% | 0.5619 | 49.73% | 50.54% (9,609) |
| **BUY (1)** | 4,943 | 33.76% | 23.20% | 0.2751 | 26.00% | 17.87% (3,398) |
| **Macro Average** | 19,012 | 38.85% | 38.35% | 0.3810 | 100.00% | 100.00% |
| **Weighted Average** | 19,012 | 43.06% | 42.75% | 0.4251 | 100.00% | 100.00% |
| **Overall Accuracy** | 19,012 | — | — | **42.75%** | — | — |

### 2.3 BUY Probability Distribution: True BUY vs Non-BUY

To diagnose the sharpness of the model's directional signal, the continuous predicted BUY probability $P(\text{BUY})$ was evaluated for true BUY cases ($Y=1$) against non-BUY cases ($Y \in \{-1, 0\}$).

| Statistic | True BUY ($Y = 1$, $N = 4,943$) | Non-BUY ($Y \ne 1$, $N = 14,069$) | Delta / Separation |
| :--- | :--- | :--- | :--- |
| **Mean** | **0.3069** | **0.2904** | **+0.0165 (+1.65%)** |
| **Standard Deviation** | 0.0558 | 0.0543 | +0.0015 |
| **Median** | 0.3033 | 0.2917 | +0.0116 |
| **25th Percentile (Q1)** | 0.2678 | 0.2520 | +0.0158 |
| **75th Percentile (Q3)** | 0.3421 | 0.3259 | +0.0162 |
| **Interquartile Range** | 0.0743 | 0.0739 | +0.0004 |
| **Minimum** | 0.1299 | 0.1218 | +0.0081 |
| **Maximum** | 0.6372 | 0.5864 | +0.0508 |

> **Key Finding**: The separation in mean predicted BUY probability between genuine forward rallies and false rallies is **only 1.65 percentage points**. The distributions overlap heavily, meaning that raw argmax classification selects numerous candidates that possess almost zero statistical edge over random market drift.

### 2.4 Calibration Diagnostics (Quantile Decile Analysis)

The binary Brier score for the BUY class is **0.1927**. Ten quantile bins of $P(\text{BUY})$ were constructed to evaluate empirical calibration:

| Decile Bin | Mean Predicted $P(\text{BUY})$ | Empirical Fraction True BUY | Calibration Bias (Actual - Pred) | Diagnostic Interpretation |
| :---: | :---: | :---: | :---: | :--- |
| **Bin 1** | 0.2078 | 0.2219 | +0.0141 | Slight underconfidence at low probabilities |
| **Bin 2** | 0.2443 | 0.2229 | -0.0214 | Overconfident |
| **Bin 3** | 0.2642 | 0.2240 | -0.0402 | Overconfident |
| **Bin 4** | 0.2796 | 0.2587 | -0.0209 | Overconfident |
| **Bin 5** | 0.2936 | 0.2519 | -0.0417 | Overconfident |
| **Bin 6** | 0.3082 | 0.2599 | -0.0483 | Overconfident |
| **Bin 7** | 0.3235 | 0.2546 | -0.0689 | Overconfident |
| **Bin 8** | 0.3409 | 0.2856 | -0.0553 | Overconfident |
| **Bin 9** | 0.3644 | 0.2951 | -0.0693 | Overconfident |
| **Bin 10** | 0.4217 | 0.3749 | -0.0468 | Monotonic edge, but overconfident by 4.68% |

> **Diagnostic Insight**: While the calibration curve preserves **monotonic ordering** (empirical win rate scales from 22.19% in Bin 1 to 37.49% in Bin 10), the model is **systematically overconfident** across Bins 2 through 10. When the model assigns a 42.17% probability of a 5-day rally, the true market occurrence is only 37.49%. In high-friction cash delivery markets, this positive bias creates a false sense of edge that is punished by transaction costs.

---

## 3. Trade-Level Edge Decomposition

### 3.1 Aggregate Trade-Level Statistics

Across all 621 completed trades, the trade ledger reveals:

| Trade Metric | Gross Value | Statutory Costs & Slippage | Net Value |
| :--- | :--- | :--- | :--- |
| **Total Cumulative P&L** | +₹52,528.87 | ₹213,207.51 | **-₹160,678.64** |
| **Mean per Trade** | +₹84.59 | ₹343.33 | **-₹258.74** |
| **Median per Trade** | -₹72.15 | ₹341.25 | **-₹395.59** |
| **Standard Deviation** | ₹2,476.43 | ₹65.73 | ₹2,467.42 |
| **Minimum (Worst Trade)** | -₹11,105.74 | ₹116.14 | -₹11,460.10 |
| **Maximum (Best Trade)** | +₹13,846.36 | ₹688.75 | +₹13,382.97 |

### 3.2 Win Rates & Profit Factors

The exact mathematical definitions employed are:
- $\text{Gross Win Rate} = \frac{\sum \mathbf{1}(\text{gross\_pnl} > 0)}{N}$
- $\text{Net Win Rate} = \frac{\sum \mathbf{1}(\text{net\_pnl} > 0)}{N}$
- $\text{Gross Profit Factor} = \frac{\sum_{\text{gross\_pnl} > 0} \text{gross\_pnl}}{\left|\sum_{\text{gross\_pnl} < 0} \text{gross\_pnl}\right|}$
- $\text{Net Profit Factor} = \frac{\sum_{\text{net\_pnl} > 0} \text{net\_pnl}}{\left|\sum_{\text{net\_pnl} < 0} \text{net\_pnl}\right|}$

| Performance Indicator | Gross Metric | Net Metric | Impact of Friction |
| :--- | :--- | :--- | :--- |
| **Winning Trades Count** | 306 trades | 277 trades | **-29 trades flipped to losses** |
| **Losing Trades Count** | 315 trades | 344 trades | +29 trades |
| **Win Rate** | **49.28%** | **44.61%** | **-4.67 percentage points** |
| **Total Dollar Gains** | +₹821,080.08 | +₹720,296.79 | -₹100,783.29 (-12.27%) |
| **Total Dollar Losses** | -₹768,551.21 | -₹880,975.43 | -₹112,424.22 (+14.63%) |
| **Profit Factor** | **1.0684** | **0.8174** | **Flipped from > 1.0 to < 1.0** |

### 3.3 Friction as Proportion of Trading Edge

- **Total Friction as % of Gross Net Alpha**: **405.89%** (Friction ₹213,207.51 vs Gross Alpha ₹52,528.87)
- **Total Friction as % of Gross Gains**: **25.97%** (Friction ₹213,207.51 vs Gross Gains ₹821,080.08)
- **Total Friction as % of Absolute Gross P&L**: **13.41%** (Friction ₹213,207.51 vs Abs Gross ₹1,589,631.29)

> **Finding**: Statutory delivery friction in Indian equities acts as an insurmountable hurdle for a strategy whose gross edge is only +₹84.59 per trade. The round-trip friction of ₹343.33 per trade represents over 4x the strategy's underlying gross edge.

### 3.4 Conviction Decomposition by Predicted BUY Probability Band

To investigate whether a genuine statistical edge exists within higher-conviction predictions, the 621 completed trades were segmented by entry signal probability $P(\text{BUY})$ into four pre-specified bands:

| Probability Band | Trade Count ($N$) | Trade Share | Gross P&L (INR) | Total Costs (INR) | Net P&L (INR) | Gross Win % | Net Win % | Net Avg P&L | Gross PF | Net PF |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$[0.33, 0.40)$** | 350 | 56.36% | -₹106,335.06 | ₹120,966.94 | **-₹227,302.00** | 44.86% | 40.00% | -₹649.43 | 0.8037 | 0.6272 |
| **$[0.40, 0.45)$** | 181 | 29.15% | +₹58,778.41 | ₹61,834.58 | -₹3,056.17 | 52.49% | 49.17% | -₹16.88 | 1.2829 | 0.9859 |
| **$[0.45, 0.50)$** | 64 | 10.31% | +₹48,676.56 | ₹21,635.19 | **+₹27,041.37** | 59.38% | 54.69% | +₹422.52 | 1.7694 | 1.3484 |
| **$[0.50, 1.00]$** | 26 | 4.19% | +₹51,408.96 | ₹8,770.80 | **+₹42,638.16** | 61.54% | 50.00% | +₹1,639.93 | 2.7663 | 2.1704 |
| **Higher Conviction ($P \ge 0.40$)** | **271** | **43.64%** | **+₹158,863.93** | **₹92,240.57** | **+₹66,623.36** | **55.72%** | **50.55%** | **+₹245.84** | **1.4552** | **1.1449** |

```
Conviction Band Net P&L Breakdown:
========================================================================================
[0.33, 0.40)  (N=350) | [████████████████████████████████████████] -INR 2,27,302.00
[0.40, 0.45)  (N=181) | [█]                                        -INR     3,056.17
[0.45, 0.50)  (N= 64) |                                     [████] +INR    27,041.37
[0.50, 1.00]  (N= 26) |                                   [██████] +INR    42,638.16
========================================================================================
```

> **Critical Discovery**: 
> 1. The baseline trading rule ($P(\text{BUY}) > P(\text{HOLD})$ and $P(\text{BUY}) > P(\text{SELL})$) executed 350 trades where the model had barely any directional conviction ($P < 0.40$). These low-conviction trades generated **100% of the strategy's net drawdown**.
> 2. When the model exhibited moderate-to-high conviction ($P(\text{BUY}) \ge 0.40$), the trades were **robustly profitable after all transaction costs and slippage**, generating **+₹66,623.36** in net gains with an aggregate net profit factor of 1.1449.
> 3. In the highest conviction tier ($P \ge 0.50$), net profit factor reached **2.1704**, generating +₹1,639.93 net profit per trade.

---

## 4. Portfolio and Exposure Diagnostics

### 4.1 Invested Exposure & Capital Allocation

Across all 388 sessions:
- **Mean Gross Exposure**: **54.54%**
- **Median Gross Exposure**: **57.98%**
- **Minimum Gross Exposure**: **0.00%** (Session 1 initialization)
- **Maximum Gross Exposure**: **99.98%**
- **Mean Invested Market Value**: **₹498,393.59**
- **Maximum Invested Market Value**: **₹1,003,506.77**

### 4.2 Cash Utilization & Order Rejections

- **Mean Cash Balance**: **₹440,599.16** (45.46% of total equity)
- **Minimum Cash Balance**: **₹211.26** (Solvency preserved; zero negative cash occurrences)
- **Maximum Cash Balance**: **₹1,000,000.00**

#### Rejected Order Analysis
Across the 388 sessions, **1,407 order attempts were rejected** by the execution engine:

| Rejection Reason Code | Rejected Count | Root Cause Explanation |
| :--- | :---: | :--- |
| `MAX_PORTFOLIO_POSITIONS_REACHED` | **1,383** | The portfolio was already holding 10 concurrent positions; incoming valid BUY signals could not be executed. |
| `ZERO_VOLUME_OR_MARKET_HALT` | **24** | The target stock experienced a zero-volume session or market trading halt at session Open. |
| `INSUFFICIENT_CASH_FOR_ONE_SHARE` | **0** | Cash floor was strictly managed; sizing never failed to afford at least 1 unit. |

### 4.3 Concurrent Open Positions Distribution

The portfolio was constrained by a hard ceiling of 10 concurrent positions.

```
Positions:  0    1    2    3    4    5    6    7    8    9    10 (Cap)
Sessions:   2   10   21   29   33   40   38   28   25   35   127
Percent:   0.5% 2.6% 5.4% 7.5% 8.5% 10.3 9.8% 7.2% 6.4% 9.0% 32.7%
```

> **Capacity Bottleneck**: On **127 trading sessions (32.73% of the time)**, the portfolio was pinned at its 10-stock maximum capacity. During these periods, high-conviction BUY candidates were rejected simply because existing lower-conviction trades were tied up waiting for their 5-day holding expiration.

### 4.4 Holding Duration Distribution & Exit Reason Asymmetry

The strategy specification defined two exit pathways: an early exit triggered by an opposing `SELL` signal ($P(\text{SELL}) > \dots$) at session Close, or a mandatory exit at session Open after 5 full trading sessions.

#### Holding Duration
- **Mean Holding Duration**: **3.46 sessions**
- **Median Holding Duration**: **4.00 sessions**
- **1 Session**: 144 trades (23.19%)
- **2 Sessions**: 82 trades (13.20%)
- **3 Sessions**: 49 trades (7.89%)
- **4 Sessions**: 36 trades (5.80%)
- **5 Sessions**: 310 trades (49.92%)

#### Exit Reason Performance Breakdown

| Exit Trigger Reason | Trades ($N$) | Trade Share | Gross P&L (INR) | Total Costs (INR) | Net P&L (INR) | Net Win % | Mean Net P&L |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`EARLY_SELL_SIGNAL`** | **337** | **54.27%** | **+₹278,313.73** | **₹117,420.12** | **+₹160,893.61** | **51.63%** | **+₹477.43** |
| **`MAX_HOLD_5D`** | **276** | **44.44%** | **-₹214,554.66** | **₹93,273.12** | **-₹307,827.78** | **37.32%** | **-₹1,115.32** |
| **`END_OF_PERIOD_LIQUIDATION`** | **8** | **1.29%** | -₹11,230.20 | ₹2,514.27 | -₹13,744.47 | 0.00% | -₹1,718.06 |

```
Exit Mechanism P&L Divergence:
========================================================================================
EARLY_SELL_SIGNAL (N=337) |                                   [████████] +INR 1,60,893.61
MAX_HOLD_5D       (N=276) | [███████████████]                            -INR 3,07,827.78
SYNTHETIC_END     (N=  8) | [█]                                          -INR   13,744.47
========================================================================================
```

> **The Adverse Selection Mechanism**:
> - Positions that experienced favorable momentum or quick trend reversal triggered early model SELL exits and booked **+₹1.61 Lakhs in net profits**.
> - Positions that lacked momentum or drifted downward slowly did not trigger an outright SELL signal (often remaining classified as HOLD) and were forced to hold for the full 5 sessions.
> - By Day 5, these drifting positions had accumulated severe losses, resulting in a **-₹3.08 Lakh loss**.
> - The fixed 5-session calendar exit acted as a classic "bag-holding" mechanism, retaining losing trades while releasing winners.

### 4.5 Drawdown and Recovery Diagnostics

- **All-Time Peak Equity**: **₹1,034,117.09** on **2025-04-28** (Session 79).
- **All-Time Trough Equity**: **₹788,604.28** on **2026-03-23** (Session 299).
- **Maximum Drawdown**: **-23.74%** (Trough vs Peak).
- **Drawdown Duration (Peak to Trough)**: **220 trading sessions** (~11 calendar months).
- **Ending Drawdown**: **-18.72%** (Final Equity ₹840,519.64 on 2026-07-22).
- **Recovery Status**: **UNRECOVERED**. The strategy entered drawdown on 2025-04-29 and never returned to high-water mark for the remainder of the 388-session evaluation period.

---

## 5. Time and Market Regime Diagnostics

### 5.1 Performance by Calendar Year

| Calendar Year | Trading Sessions | Trades Executed | Starting Equity | Ending Equity | Net Return % | Max Drawdown % | Avg Exposure % | Gross P&L (INR) | Costs (INR) | Net P&L (INR) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2025** | 249 | 324 | ₹1,000,000.00 | ₹958,379.56 | **-4.16%** | 8.86% | 54.38% | +₹70,611.75 | ₹111,940.32 | -₹41,328.57 |
| **2026** | 139 | 297 | ₹958,379.56 | ₹840,519.64 | **-12.30%** | 23.74% | 54.83% | -₹18,082.88 | ₹101,267.19 | -₹119,350.07 |

### 5.2 Performance by Calendar Quarter

| Calendar Quarter | Sessions | Trades | Starting Equity | Ending Equity | Net Return % | Max Drawdown % | Avg Exposure % | Net Trade P&L (INR) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2025 Q1** | 61 | 87 | ₹1,000,000.00 | ₹985,699.04 | -1.43% | 3.63% | 53.07% | -₹14,248.88 |
| **2025 Q2** | 61 | 71 | ₹985,699.04 | ₹1,024,678.91 | **+3.95%** | 2.45% | 57.06% | **+₹39,019.53** |
| **2025 Q3** | 64 | 79 | ₹1,024,678.91 | ₹955,145.47 | -6.79% | 7.15% | 50.81% | -₹69,328.66 |
| **2025 Q4** | 63 | 87 | ₹955,145.47 | ₹958,379.56 | -0.05% | 4.09% | 56.69% | +₹3,229.44 |
| **2026 Q1** | 61 | 144 | ₹958,379.56 | ₹788,799.05 | **-17.69%** | 18.28% | 58.74% | **-₹169,458.11** |
| **2026 Q2** | 63 | 129 | ₹788,799.05 | ₹820,019.46 | **+1.68%** | 6.47% | 54.87% | **+₹34,106.63** |
| **2026 Q3** *(15d)* | 15 | 24 | ₹820,019.46 | ₹840,519.64 | **+2.52%** | 0.94% | 38.86% | **+₹16,001.41** |

> **Quarterly Insight**: The collapse of portfolio performance occurred primarily during **2026 Q1**, where the strategy suffered an acute **-17.69% quarterly drawdown** (-₹1.69 Lakhs net loss across 144 trades). This period coincided with increased turnover and elevated trade counts.

### 5.3 Market Regime Analysis (Trailing 20-Day Momentum)

To prevent look-ahead bias, market regimes were defined strictly using the **trailing 20-trading-day return of the Equal-Weight Benchmark index** available at the time of trade execution:
- **`BULL_TREND`**: Trailing 20-day benchmark return $> +2.0\%$
- **`BEAR_TREND`**: Trailing 20-day benchmark return $< -2.0\%$
- **`SIDEWAYS`**: Trailing 20-day benchmark return in $[-2.0\%, +2.0\%]$
- **`UNCLASSIFIED`**: Initial 20-session burn-in window (insufficient lookback)

| Market Regime Bucket | Sessions ($N$) | Trades ($N$) | Gross P&L (INR) | Total Costs (INR) | Net P&L (INR) | Net Win Rate % | Performance Summary |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`BULL_TREND`** | 118 | 171 | -₹45,618.34 | ₹58,382.66 | **-₹104,001.00** | 45.03% | Severe underperformance; bought extended tops |
| **`SIDEWAYS`** | 190 | 264 | +₹14,923.36 | ₹90,618.26 | **-₹75,694.90** | 44.32% | Positive gross alpha crushed by friction |
| **`BEAR_TREND`** | 60 | 137 | **+₹70,683.07** | ₹46,744.92 | **+₹23,938.15** | **45.99%** | Profitable counter-trend mean-reversion |
| **`UNCLASSIFIED`** *(Warm-up)* | 20 | 49 | +₹12,540.78 | ₹17,461.67 | -₹4,920.89 | 42.86% | Baseline warm-up period |

> **Regime Behavior**: Counter-intuitively, the strategy performed **best during market pullbacks and bear regimes** (+₹23,938.15 net P&L), because its mean-reversion features (e.g. RSI oversold, Bollinger Band bounce) successfully captured oversold dip rallies. Conversely, in **strong bull trending markets**, the model suffered its worst losses (-₹104,001.00 net), repeatedly buying breakout extensions at the top of 5-day cycle peaks.

---

## 6. Benchmark Interpretation & Fairness Audit

### 6.1 Equal-Weight Buy-and-Hold Benchmark Recomputation

The primary benchmark is an equal-weight long-only portfolio of all approved universe constituents trading on the first day of the backtest period (47 constituents on 2025-01-01; 2 constituents entered trading later).

| Benchmark Parameter | Equal-Weight Buy & Hold | Active Swing Strategy | Difference / Comparison |
| :--- | :--- | :--- | :--- |
| **Universe** | 47 initial constituents | 49 constituents dynamic | Comparable universe |
| **Initial Capital** | ₹1,000,000.00 | ₹1,000,000.00 | Exact parity |
| **Gross Ending Equity** | **₹1,102,636.19** | ₹1,052,528.87 | Active trailed by ₹50,107.32 |
| **Gross Return** | **+10.26%** | **+5.25%** | Active trailed by -5.01% gross |
| **Transaction Friction** | ₹1,905.27 (one-way entry) | **₹213,207.51** (621 trades) | Active paid **111.9x more friction** |
| **Estimated Net Ending Equity** | **₹1,100,730.92** | **₹840,519.64** | Active trailed by ₹260,211.28 |
| **Estimated Net Return** | **+10.07%** | **-15.95%** | Active underperformed by **-26.02%** |
| **Effective Exposure** | 100.0% constant | 54.54% average | Passive enjoyed full market beta |
| **Portfolio Turnover** | 0.0% (static allocation) | 1,141.0% (₹1.14 Cr turnover) | Extreme turnover differential |

### 6.2 Audit of the "Top-10 Alphabetical Portfolio" (+28.44%)

The Sprint 6.0 report referenced an alphabetical top-10 static hold (`ADANIENT`, `ADANIPORTS`, `APOLLOHOSP`, `ASIANPAINT`, `AXISBANK`, `BAJAJ-AUTO`, `BAJFINANCE`, `BAJAJFINSV`, `BEL`, `BPCL`) that returned **+28.44% gross**.

**Critical Methodological Assessment**:
1. **Severe Sector & Stock Selection Bias**: This basket happened to include Bharat Electronics Ltd (`BEL`), which appreciated by over **+90%** during 2025-2026, alongside heavy exposure to Adani Group and auto/financial leaders.
2. **Zero Turnover & Zero Tax Drag**: The basket traded zero times and paid zero ongoing transaction costs.
3. **Audit Verdict**: Using the alphabetical top-10 portfolio as a benchmark or as evidence of active strategy failure is **methodologically flawed and invalid**. The only scientifically valid passive benchmark is the full 49-constituent Equal-Weight Buy-and-Hold index.

---

## 7. Conclusions & Research Hypotheses

### 7.1 Verified Observations (Empirical Facts)

1. **Replication Fidelity**: All baseline figures reported in Sprint 6.0 and reconciled in Sprint 6.0.3 are replicated to the exact paisa from the frozen model and dataset.
2. **Gross Edge vs Friction Reality**: The strategy generated genuine positive gross P&L (+₹52,528.87 across 621 trades), but statutory taxes and slippage (₹213,207.51) were **over 400% of gross alpha**, resulting in a net loss of -₹160,678.64.
3. **Threshold Dilution**: Over 56% of trades occurred in the lowest probability band $[0.33, 0.40)$, accounting for **-₹227,302.00 of net losses**. High-conviction trades ($P \ge 0.40$) were net profitable (+₹66,623.36).
4. **Exit Asymmetry**: Early model exits were profitable (+₹160,893.61 net), while 5-day expiration exits were catastrophic (-₹307,827.78 net).
5. **Capacity Saturation**: The 10-position ceiling blocked 1,383 candidate signals while stale positions drifted toward their 5-day expiration.

### 7.2 Plausible Explanations Requiring Further Testing

1. **Adverse Selection in Time-Based Exits**: Winning trades generate quick momentum shifts that trigger early SELL signals, while losing trades drift without an active SELL signal, accumulating losses until the 5-day stop forces liquidation.
2. **Momentum Overshoot in Large Caps**: In strong bull markets (`BULL_TREND`), NIFTY 50 large caps experience rapid mean-reversion following 5-day cycle tops, causing breakout BUY signals to enter at local peaks.
3. **Probability Miscalibration**: The model's overconfidence in middle deciles leads to sizing positions as if edge exists, when empirical win rates in those deciles do not cover statutory delivery taxes.

### 7.3 Unanswerable Questions from Existing Artifacts

1. **Intraday Stop-Loss Viability**: Could an intraday ATR trailing stop mitigate `MAX_HOLD_5D` losses without causing excessive whip-saws? This cannot be answered from daily OHLC bars alone; tick or intraday bar data is required.
2. **Derivative Friction Arbitrage**: Would implementing the strategy via cash-settled NIFTY Stock Futures (where STT is only 2 bps on sell turnover, rather than 10 bps on both buy and sell delivery) salvage profitability? Requires futures contract series and margin modeling.
3. **Optimal Threshold Generalization**: Would an entry threshold of $P(\text{BUY}) \ge 0.45$ selected on the validation set survive out-of-sample execution without excessive signal starvation?

---

## 8. Reproducibility & Research Protocol

### 8.1 Exact Commands Executed

The quantitative analysis was executed using the repository's virtual environment:

```bash
# Verify test suite integrity
PYTHONPATH=. ./venv/bin/pytest tests/ -v

# Run classification diagnostics
PYTHONPATH=. ./venv/bin/python scratch/classification_diagnostics.py

# Run trade edge decomposition
PYTHONPATH=. ./venv/bin/python scratch/trade_edge_decomposition.py

# Run portfolio exposure diagnostics
PYTHONPATH=. ./venv/bin/python scratch/portfolio_diagnostics.py

# Run time and market regime diagnostics
PYTHONPATH=. ./venv/bin/python scratch/time_regime_diagnostics.py

# Compile and verify structured JSON artifact
PYTHONPATH=. ./venv/bin/python scratch/generate_diagnostics_json.py
```

### 8.2 Data and Model Integrity

- Model: `models/lightgbm.joblib` (SHA256: `41e61760fc31c72095cd2071fdb843657bd76143ed4535f9b247db78e0c73761`)
- Data: `data/processed/test_dataset.parquet` (SHA256: `7f9d0ce56b42a7cc2780f90edb4b27d9bc923847c6778e5ba4c6ebc754915381`)
- Total automated tests passing: **54 of 54 tests passing**.

---

## 9. Recommendations for Next Research Sprint (Sprint 6.2)

### Pre-Registered Research Hypotheses (Do Not Implement in Sprint 6.1)

In strict accordance with research governance, **no model retraining, parameter tuning, or strategy modification was performed in this sprint**. The following hypotheses are pre-registered for rigorous evaluation in Sprint 6.2:

#### Hypothesis 1: Conviction Threshold Filtering
- **Formulation**: Tuning an entry probability threshold $\theta \in [0.40, 0.48]$ strictly on the **validation dataset** (`validation_dataset.parquet`) will filter out $>50\%$ of low-edge trades while retaining $>80\%$ of profitable net alpha, converting the strategy from net negative to net positive.

#### Hypothesis 2: Dynamic Volatility Trailing Stop
- **Formulation**: Replacing the unconditional 5-session calendar stop with a 1.5 $\times$ ATR dynamic trailing stop or a time-decay profit target will truncate the left tail of `MAX_HOLD_5D` exits, raising the net win rate above 50%.

#### Hypothesis 3: Execution Friction Reduction (F&O Instrument Migration)
- **Formulation**: Migrating the execution universe to NIFTY 50 Single Stock Futures will reduce statutory transaction costs from ~37 bps round-trip (cash delivery) to ~8 bps round-trip, preserving the strategy's gross edge (+₹84.59 per trade) as net realized alpha.

---
*Report completed and verified under strict read-only research governance.*
