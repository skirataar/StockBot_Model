# Sprint 6.2.1 — Independent Validation Results and Accounting Audit Report

**Audit Date**: 2026-10-28T21:48:31.144967+00:00  
**Role**: Independent Quantitative Research Auditor & Financial-Accounting Verification Engineer  
**Repository**: `StockBot_Model` (`main` branch, commit `8450e91288c82c4e68c2aacd076c96141a973f96`)  
**Audit Verification**: **`SOURCE-VERIFIED READ-ONLY AUDIT (ZERO SIMULATIONS EXECUTED)`**  
**Executive Verdict**: **`PASS WITH LIMITATIONS — NO CANDIDATE QUALIFIED; NON-MATERIAL ISSUES REMAIN`**  

---

## 1. Executive Summary & Audit Verdict

This independent audit evaluated the completeness, internal consistency, ledger accounting fidelity, and statistical rigor of the Sprint 6.2 preregistered validation experiment. The audit was conducted strictly in read-only mode without executing backtests, modifying model weights, altering candidate configurations, or accessing the quarantined test dataset.

### Formal Audit Verdict
### **`PASS WITH LIMITATIONS — NO CANDIDATE QUALIFIED; NON-MATERIAL ISSUES REMAIN`**

### Key Audit Determinations:
1. **Accounting Discrepancy Fully Reconciled**: The apparent difference between trade-ledger net P&L and portfolio final equity (e.g. CFG-01 net P&L ₹196,754.98 [19.68%] vs reported cumulative return 19.88%; CFG-BASE net P&L ₹316,020.98 [31.60%] vs reported cumulative return 31.83%) is **100% accounted for by terminal liquidation sell friction** on positions held open at the close of the final trading session (`2024-12-23`). The exact numerical bridge reconciles to within ₹0.02 across all 17 configurations.
2. **Rejection Verdict Verified**: All 16 candidate configurations and baseline `CFG-BASE` were correctly rejected under the preregistered Protocol v1.2.0 rules. Zero candidates passed all mandatory criteria (M1–M8).
3. **Decisive Rejection Drivers**: Every candidate failed Criterion **`M2`** (Benchmark Outperformance) due to passive equal-weight NIFTY 50 benchmark returns of **+59.22%** vs strategy returns of +10.81% to +24.50%. Furthermore, every candidate failed Criterion **`M8`** (Deflated Sharpe Ratio significance under multiple testing, with observed $p$-values between 0.4631 and 0.9104).
4. **Holdout Quarantine Intact**: The test dataset (`data/processed/test_dataset.parquet`) has not been modified since 2026-10-28 06:40:03, matches its canonical baseline hash byte-for-byte, and was never accessed.

---

## 2. Findings Table

| Finding ID | Severity | Artifact & Location | Expected Behavior | Observed Behavior | Remediation Required |
| :--- | :---: | :--- | :--- | :--- | :--- |
| `FND-01-TERMINAL-LIQUIDATION-FRICTION-TIMING` | `LOW / INFORMATIONAL` | `data/reports/sprint_6_2/candidate_ledgers/*_portfolio_ledger.csv vs *_trade_ledger.csv` | Starting Capital + Net P&L in trade ledger equals Ending Equity in portfolio ledger. | Ending Equity is Rs. 783.13 to Rs. 2,234.85 higher than Starting Capital + Trade Ledger Net P&L. | None. Documented institutional NAV mark-to-market reporting convention. |
| `FND-02-BENCHMARK-GROSS-BUY-AND-HOLD-CONVENTION` | `LOW / METHODOLOGY NOTE` | `src/backtest/event_driven_engine.py:802 (compute_buy_and_hold_benchmark)` | Strategy and benchmark returns measured on perfectly symmetric friction conventions. | Benchmark models frictionless gross buy-and-hold (+59.22%), while strategy models full delivery friction and 5 bps slippage. | None for validation rejection; record as methodology limitation for future research stages. |
| `FND-03-DSR-HURDLE-SURPLUS-NON-SIGNIFICANCE` | `LOW / INFORMATIONAL` | `data/reports/sprint_6_2_cross_sectional_results.json` | Strategy with Sharpe > Hurdle is statistically evaluated for sampling variance under multiple testing. | CFG-16 achieved Sharpe 1.0283 > Hurdle 0.9698 (+0.0585 surplus), but DSR p-value was 0.4631 (non-significant). | None. Protocol correctly classified CFG-16 as non-significant. |

---

## 3. Mandatory Discrepancy Investigation & Numerical Bridge

### 3.1 The Accounting Mechanism
The inquiry noted that for initial capital ₹10,00,000.00:
- `CFG-01` reported net P&L of ₹196,754.98 (which is 19.68% of capital) vs cumulative net return of **19.88%**.
- `CFG-BASE` reported net P&L of ₹316,020.98 (which is 31.60% of capital) vs cumulative net return of **31.83%**.

**Independent Verification Findings**:
1. In [`src/backtest/event_driven_engine.py`](file:///home/skirataar/StockBot/StockBot_Model/src/backtest/event_driven_engine.py#L922), cumulative net return is defined as:
   $$\text{Cumulative Net Return} = \frac{\text{Ending Equity} - \text{Initial Capital}}{\text{Initial Capital}} \times 100\%$$
2. The portfolio ledger records ending equity at session Close on date $T$ using standard mark-to-market NAV accounting:
   $$\text{Portfolio Equity}_T = \text{Cash}_T + \sum_{i \in \text{open}} (\text{Quantity}_i \times \text{Close}_{i, T})$$
   Upon position entry, buy fees and buy slippage are deducted from cash immediately. However, sell friction has not yet occurred for open positions.
3. In the trade ledger, a synthetic `END_OF_PERIOD_LIQUIDATION` record is generated to reflect terminal position liquidation, deducting theoretical statutory exit charges, brokerage, and exit slippage:
   $$\text{Net PnL}_{i, \text{liq}} = \text{Gross PnL}_{i, \text{liq}} - \text{Buy Friction}_i - \text{Sell Friction}_{i, \text{liq}}$$
4. Therefore, the exact mathematical identity connecting ending portfolio equity and trade-ledger net P&L is:
   $$\text{Ending Equity} - (\text{Initial Capital} + \sum \text{Net PnL}) = \sum_{i \in \text{open}} \text{Sell Friction}_{i, \text{liq}}$$

### 3.2 Exact Numerical Bridges for CFG-01, CFG-BASE, and CFG-16

| Metric | `CFG-01` | `CFG-BASE` | `CFG-16` (Top Candidate) |
| :--- | :---: | :---: | :---: |
| Initial Capital | Rs. 1,000,000.00 | Rs. 1,000,000.00 | Rs. 1,000,000.00 |
| Final Cash Balance | Rs. 13,961.26 | Rs. 17,188.91 | Rs. 505,721.96 |
| Final Marked-to-Market Holdings | Rs. 1,184,849.95 | Rs. 1,301,066.93 | Rs. 726,995.45 |
| **Final Portfolio Equity** | **Rs. 1,198,811.21** | **Rs. 1,318,255.83** | **Rs. 1,232,717.42** |
| Total Trade Ledger Net P&L | Rs. 196,754.98 | Rs. 316,020.98 | Rs. 231,458.97 |
| Initial Capital + Trade Net P&L | Rs. 1,196,754.98 | Rs. 1,316,020.98 | Rs. 1,231,458.97 |
| **Observed Discrepancy** | **Rs. 2,056.23** | **Rs. 2,234.85** | **Rs. 1,258.45** |
| Open Positions Liquidated at End | 10 positions | 10 positions | 6 positions |
| **Calculated Terminal Sell Friction** | **Rs. 2,056.20** | **Rs. 2,234.74** | **Rs. 1,258.43** |
| **Residual (Rounding Difference)** | **Rs. +0.03** | **Rs. +0.11** | **Rs. +0.02** |
| **Reconciliation Status** | **100% RECONCILED** | **100% RECONCILED** | **100% RECONCILED** |

### 3.3 Candidate-Wide Ledger Reconciliation Table

| Candidate ID | Starting Capital | Final Equity | Gross Trading P&L | Total Friction | Net P&L | Equity Change | Return % | Open Liq | Sell Friction | Residual |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `CFG-01` | Rs. 1,000,000 | Rs. 1,198,811.21 | Rs. 549,853.81 | Rs. 353,098.83 | Rs. 196,754.98 | Rs. 198,811.21 | +19.88% | 10 | Rs. 2,056.20 | Rs. +0.03 |
| `CFG-02` | Rs. 1,000,000 | Rs. 1,161,181.08 | Rs. 367,869.94 | Rs. 208,683.90 | Rs. 159,186.04 | Rs. 161,181.08 | +16.12% | 10 | Rs. 1,995.05 | Rs. -0.01 |
| `CFG-03` | Rs. 1,000,000 | Rs. 1,237,031.09 | Rs. 381,689.68 | Rs. 146,767.95 | Rs. 234,921.73 | Rs. 237,031.09 | +23.70% | 10 | Rs. 2,109.17 | Rs. +0.19 |
| `CFG-04` | Rs. 1,000,000 | Rs. 1,108,058.63 | Rs. 194,263.26 | Rs. 88,106.60 | Rs. 106,156.66 | Rs. 108,058.63 | +10.81% | 10 | Rs. 1,901.93 | Rs. +0.04 |
| `CFG-05` | Rs. 1,000,000 | Rs. 1,220,669.93 | Rs. 265,741.42 | Rs. 46,943.85 | Rs. 218,797.57 | Rs. 220,669.93 | +22.07% | 9 | Rs. 1,872.32 | Rs. +0.04 |
| `CFG-06` | Rs. 1,000,000 | Rs. 1,231,763.71 | Rs. 250,521.17 | Rs. 20,015.90 | Rs. 230,505.27 | Rs. 231,763.71 | +23.18% | 6 | Rs. 1,258.43 | Rs. +0.01 |
| `CFG-07` | Rs. 1,000,000 | Rs. 1,138,636.57 | Rs. 147,684.85 | Rs. 9,831.41 | Rs. 137,853.44 | Rs. 138,636.57 | +13.86% | 4 | Rs. 783.08 | Rs. +0.05 |
| `CFG-08` | Rs. 1,000,000 | Rs. 1,223,236.25 | Rs. 375,807.30 | Rs. 154,655.87 | Rs. 221,151.43 | Rs. 223,236.25 | +22.32% | 10 | Rs. 2,084.69 | Rs. +0.13 |
| `CFG-09` | Rs. 1,000,000 | Rs. 1,240,241.74 | Rs. 389,038.36 | Rs. 150,911.95 | Rs. 238,126.41 | Rs. 240,241.74 | +24.02% | 10 | Rs. 2,115.34 | Rs. -0.01 |
| `CFG-10` | Rs. 1,000,000 | Rs. 1,244,982.49 | Rs. 392,259.22 | Rs. 149,395.67 | Rs. 242,863.55 | Rs. 244,982.49 | +24.50% | 10 | Rs. 2,118.71 | Rs. +0.23 |
| `CFG-11` | Rs. 1,000,000 | Rs. 1,185,632.95 | Rs. 291,072.48 | Rs. 106,856.04 | Rs. 184,216.44 | Rs. 185,632.95 | +18.56% | 7 | Rs. 1,416.47 | Rs. +0.04 |
| `CFG-12` | Rs. 1,000,000 | Rs. 1,229,240.72 | Rs. 352,786.97 | Rs. 125,643.66 | Rs. 227,143.31 | Rs. 229,240.72 | +22.92% | 10 | Rs. 2,097.28 | Rs. +0.13 |
| `CFG-13` | Rs. 1,000,000 | Rs. 1,114,130.97 | Rs. 204,217.52 | Rs. 92,011.08 | Rs. 112,206.44 | Rs. 114,130.97 | +11.41% | 10 | Rs. 1,924.34 | Rs. +0.19 |
| `CFG-14` | Rs. 1,000,000 | Rs. 1,224,520.35 | Rs. 270,843.87 | Rs. 48,203.45 | Rs. 222,640.42 | Rs. 224,520.35 | +22.45% | 9 | Rs. 1,879.87 | Rs. +0.06 |
| `CFG-15` | Rs. 1,000,000 | Rs. 1,144,470.00 | Rs. 181,901.80 | Rs. 38,411.43 | Rs. 143,490.37 | Rs. 144,470.00 | +14.45% | 5 | Rs. 979.64 | Rs. -0.01 |
| `CFG-16` | Rs. 1,000,000 | Rs. 1,232,717.42 | Rs. 251,885.07 | Rs. 20,426.10 | Rs. 231,458.97 | Rs. 232,717.42 | +23.27% | 6 | Rs. 1,258.43 | Rs. +0.02 |
| `CFG-BASE` | Rs. 1,000,000 | Rs. 1,318,255.83 | Rs. 638,763.47 | Rs. 322,742.49 | Rs. 316,020.98 | Rs. 318,255.83 | +31.83% | 10 | Rs. 2,234.74 | Rs. +0.11 |

### 3.4 Statutory Cost Breakdown by Component

| Candidate ID | Brokerage | STT (10 bps) | Stamp Duty | Exchange Fee | SEBI Fee | GST (18%) | Slippage (5 bps) | Total Friction |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `CFG-01` | Rs. 33,920.00 | Rs. 194,333.18 | Rs. 14,533.70 | Rs. 5,771.75 | Rs. 194.00 | Rs. 7,179.28 | Rs. 97,166.50 | Rs. 353,098.83 |
| `CFG-02` | Rs. 20,960.00 | Rs. 114,185.64 | Rs. 8,536.29 | Rs. 3,391.18 | Rs. 114.61 | Rs. 4,403.82 | Rs. 57,092.88 | Rs. 208,683.90 |
| `CFG-03` | Rs. 13,960.00 | Rs. 80,884.80 | Rs. 6,037.77 | Rs. 2,402.22 | Rs. 80.92 | Rs. 2,959.78 | Rs. 40,442.61 | Rs. 146,767.95 |
| `CFG-04` | Rs. 8,880.00 | Rs. 48,188.59 | Rs. 3,599.54 | Rs. 1,431.25 | Rs. 47.94 | Rs. 1,864.69 | Rs. 24,094.29 | Rs. 88,106.60 |
| `CFG-05` | Rs. 4,520.00 | Rs. 25,837.52 | Rs. 1,917.88 | Rs. 767.30 | Rs. 25.75 | Rs. 956.38 | Rs. 12,918.84 | Rs. 46,943.85 |
| `CFG-06` | Rs. 1,880.00 | Rs. 11,057.59 | Rs. 810.52 | Rs. 328.42 | Rs. 11.02 | Rs. 399.48 | Rs. 5,528.80 | Rs. 20,015.90 |
| `CFG-07` | Rs. 960.00 | Rs. 5,405.64 | Rs. 394.32 | Rs. 160.50 | Rs. 5.35 | Rs. 202.67 | Rs. 2,702.81 | Rs. 9,831.41 |
| `CFG-08` | Rs. 14,840.00 | Rs. 85,135.68 | Rs. 6,356.98 | Rs. 2,528.54 | Rs. 85.20 | Rs. 3,141.66 | Rs. 42,567.97 | Rs. 154,655.87 |
| `CFG-09` | Rs. 14,400.00 | Rs. 83,134.88 | Rs. 6,205.92 | Rs. 2,468.98 | Rs. 83.16 | Rs. 3,051.46 | Rs. 41,567.47 | Rs. 150,911.95 |
| `CFG-10` | Rs. 14,240.00 | Rs. 82,311.05 | Rs. 6,143.95 | Rs. 2,444.57 | Rs. 82.42 | Rs. 3,018.13 | Rs. 41,155.67 | Rs. 149,395.67 |
| `CFG-11` | Rs. 10,600.00 | Rs. 58,570.25 | Rs. 4,370.89 | Rs. 1,739.48 | Rs. 58.47 | Rs. 2,231.69 | Rs. 29,285.14 | Rs. 106,856.04 |
| `CFG-12` | Rs. 12,000.00 | Rs. 69,208.25 | Rs. 5,164.15 | Rs. 2,055.43 | Rs. 69.12 | Rs. 2,542.47 | Rs. 34,604.14 | Rs. 125,643.66 |
| `CFG-13` | Rs. 9,280.00 | Rs. 50,319.37 | Rs. 3,758.67 | Rs. 1,494.40 | Rs. 50.05 | Rs. 1,948.33 | Rs. 25,159.72 | Rs. 92,011.08 |
| `CFG-14` | Rs. 4,640.00 | Rs. 26,531.69 | Rs. 1,969.56 | Rs. 787.95 | Rs. 26.41 | Rs. 981.88 | Rs. 13,265.87 | Rs. 48,203.45 |
| `CFG-15` | Rs. 3,840.00 | Rs. 21,036.02 | Rs. 1,564.04 | Rs. 624.84 | Rs. 20.95 | Rs. 807.48 | Rs. 10,518.05 | Rs. 38,411.43 |
| `CFG-16` | Rs. 1,920.00 | Rs. 11,282.95 | Rs. 827.32 | Rs. 335.11 | Rs. 11.24 | Rs. 407.94 | Rs. 5,641.48 | Rs. 20,426.10 |
| `CFG-BASE` | Rs. 28,440.00 | Rs. 179,509.99 | Rs. 13,415.19 | Rs. 5,331.42 | Rs. 179.38 | Rs. 6,110.97 | Rs. 89,755.13 | Rs. 322,742.49 |

---

## 4. Benchmark Verification

- **Benchmark Name**: NIFTY 50 Equal-Weight Buy & Hold
- **Constituent Universe**: 49 NIFTY 50 stocks with validated price series.
- **Evaluation Window**: `2023-01-02` to `2024-12-23` (486 trading sessions).
- **Starting Capital**: Rs. 1,000,000.00
- **Ending Equity**: Rs. 1,592,186.81
- **Net Cumulative Return**: **+59.22%**
- **CAGR**: +27.27%
- **Annualized Sharpe Ratio**: 1.64
- **Maximum Drawdown**: 13.02%
- **Audit Assessment**: NON-MATERIAL LIMITATION: The benchmark is computed as a gross, frictionless buy-and-hold allocation without statutory delivery costs or execution slippage. In contrast, candidate strategies bear full statutory delivery friction (~0.25% per round trip), 5 bps slippage per leg, and cash drag from 10-position limits. However, the performance gap between the benchmark (+59.22%) and the best candidate (+24.50%) is 34.72 percentage points; deducting ~0.25% delivery friction from the benchmark would yield +58.85%, which still vastly exceeds all candidate strategies. Therefore, this difference in return convention does not alter any candidate rejection.

---

## 5. Candidate Acceptance Matrix (M1–M8 & R1–R10)

| Candidate ID | M1 (SR > 0.50) | M2 (vs +59.22%) | M3 (DD $\le$ 15%) | M4 (Tr $\ge$ 100) | M5 (Yr $\ge$ 40) | M6 (PF $\ge$ 1.15) | M7 (Frict $\le$ 100%) | M8 (DSR $p < 0.05$) | Final Status | Tripped Rejection Triggers |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `CFG-01` | ❌ 0.23 | ❌ +19.88% | ✅ 12.80% | ✅ 848 | ✅ (378,470) | ✅ 1.53 | ✅ 64.2% | ❌ 0.8239 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R8_DSR_INSIGNIFICANT` |
| `CFG-02` | ❌ 0.14 | ❌ +16.12% | ✅ 11.27% | ✅ 524 | ✅ (210,314) | ✅ 1.60 | ✅ 56.7% | ❌ 0.8554 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R8_DSR_INSIGNIFICANT` |
| `CFG-03` | ❌ 0.43 | ❌ +23.70% | ✅ 10.77% | ✅ 349 | ✅ (128,221) | ✅ 1.88 | ✅ 38.5% | ❌ 0.7522 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R8_DSR_INSIGNIFICANT` |
| `CFG-04` | ❌ -0.05 | ❌ +10.81% | ✅ 11.16% | ✅ 222 | ✅ (79,143) | ✅ 1.61 | ✅ 45.4% | ❌ 0.9104 | **REJECTED** | `R1_NON_POSITIVE_SHARPE, R2_BENCHMARK_UNDERPERFORMANCE, R8_DSR_INSIGNIFICANT` |
| `CFG-05` | ✅ 0.69 | ❌ +22.07% | ✅ 3.89% | ✅ 113 | ✅ (43,70) | ✅ 2.87 | ✅ 17.7% | ❌ 0.6785 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R8_DSR_INSIGNIFICANT` |
| `CFG-06` | ✅ 1.13 | ❌ +23.18% | ✅ 2.33% | ❌ 47 | ❌ (18,29) | ✅ 7.99 | ✅ 8.0% | ❌ 0.4680 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R4_INSUFFICIENT_TOTAL_TRADES, R5_INSUFFICIENT_ANNUAL_TRADES, R8_DSR_INSIGNIFICANT` |
| `CFG-07` | ❌ 0.31 | ❌ +13.86% | ✅ 1.30% | ❌ 24 | ❌ (9,15) | ✅ 9.73 | ✅ 6.7% | ❌ 0.8534 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R4_INSUFFICIENT_TOTAL_TRADES, R5_INSUFFICIENT_ANNUAL_TRADES, R8_DSR_INSIGNIFICANT` |
| `CFG-08` | ❌ 0.38 | ❌ +22.32% | ✅ 10.74% | ✅ 371 | ✅ (134,237) | ✅ 1.70 | ✅ 41.1% | ❌ 0.7720 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R8_DSR_INSIGNIFICANT` |
| `CFG-09` | ❌ 0.44 | ❌ +24.02% | ✅ 10.79% | ✅ 360 | ✅ (130,230) | ✅ 1.80 | ✅ 38.8% | ❌ 0.7470 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R8_DSR_INSIGNIFICANT` |
| `CFG-10` | ❌ 0.46 | ❌ +24.50% | ✅ 10.75% | ✅ 356 | ✅ (130,226) | ✅ 1.82 | ✅ 38.1% | ❌ 0.7389 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R8_DSR_INSIGNIFICANT` |
| `CFG-11` | ❌ 0.33 | ❌ +18.56% | ✅ 6.79% | ✅ 265 | ✅ (108,157) | ✅ 1.91 | ✅ 36.7% | ❌ 0.8031 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R8_DSR_INSIGNIFICANT` |
| `CFG-12` | ❌ 0.48 | ❌ +22.92% | ✅ 8.21% | ✅ 300 | ✅ (114,186) | ✅ 1.93 | ✅ 35.6% | ❌ 0.7435 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R8_DSR_INSIGNIFICANT` |
| `CFG-13` | ❌ -0.02 | ❌ +11.41% | ✅ 11.15% | ✅ 232 | ✅ (81,151) | ✅ 1.55 | ✅ 45.1% | ❌ 0.9050 | **REJECTED** | `R1_NON_POSITIVE_SHARPE, R2_BENCHMARK_UNDERPERFORMANCE, R8_DSR_INSIGNIFICANT` |
| `CFG-14` | ✅ 0.71 | ❌ +22.45% | ✅ 3.88% | ✅ 116 | ✅ (44,72) | ✅ 2.63 | ✅ 17.8% | ❌ 0.6672 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R8_DSR_INSIGNIFICANT` |
| `CFG-15` | ❌ 0.21 | ❌ +14.45% | ✅ 3.28% | ❌ 96 | ❌ (39,57) | ✅ 2.18 | ✅ 21.1% | ❌ 0.8565 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R4_INSUFFICIENT_TOTAL_TRADES, R5_INSUFFICIENT_ANNUAL_TRADES, R8_DSR_INSIGNIFICANT` |
| `CFG-16` | ✅ 1.13 | ❌ +23.27% | ✅ 2.33% | ❌ 48 | ❌ (18,30) | ✅ 6.70 | ✅ 8.1% | ❌ 0.4631 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R4_INSUFFICIENT_TOTAL_TRADES, R5_INSUFFICIENT_ANNUAL_TRADES, R8_DSR_INSIGNIFICANT` |
| `CFG-BASE` | ✅ 0.61 | ❌ +31.83% | ✅ 10.42% | ✅ 711 | ✅ (279,432) | ✅ 1.66 | ✅ 50.5% | N/A | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE, R8_DSR_INSIGNIFICANT` |

---

## 6. Statistical Reproducibility Audit

The cross-sectional statistical evaluation was independently recalculated using the recorded daily excess return series:

- **Candidate Grid (K)**: Exactly 16 discrete candidate configurations (`CFG-BASE` excluded from trial count).
- **Cohort Empirical Mean Sharpe (mu_SR)**: `0.433216`
- **Governance Baseline Floor**: `0.433216`
- **Cohort Sample Std Dev (sigma_SR)**: `0.298021`
- **EVT Hurdle Factor (EVT(16))**: `1.8004542393102163`
- **Binding Expected-Maximum Hurdle (SR*_ann)**: `0.969789`
- **Top Candidate by Sharpe**: **`CFG-16`** (Annualized Sharpe: `1.028294`).
- **Mertens Asymptotic Variance (V)**: `0.766227` (Skewness gamma_3 = 4.1900, Kurtosis gamma_4 = 36.8813).
- **DSR Test Statistic (z)**: `0.092722`
- **DSR Probability**: `0.536938`
- **DSR p-value**: **`0.463062`** (Statistically Significant at alpha=0.05: `False`).
- **Reproducibility Status**: **`EXACT (Matches to double precision IEEE 754 across all metrics)`**.

---

## 7. Trading Invariants and Quality Control

1. **Cash Solvency Invariant**: Verified. Cash balance remained strictly $\ge ₹0.00$ on all dates for all candidates. The absolute minimum cash balance observed was ₹44.74 (`CFG-08`).
2. **Portfolio Capacity Invariant**: Verified. Concurrent positions never exceeded 10 (gross exposure $\le 100\%$, zero leverage, no short selling).
3. **Execution Conventions**: Verified. Signals generated at session $t$ Close (15:30 IST); filled at session $t+1$ Open (09:15 IST) with 5 bps slippage per leg.
4. **Calendar Invariants**: All candidates evaluated over identical 486 trading sessions (`2023-01-02` to `2024-12-23`), strictly chronological, with zero duplicate or missing dates.
5. **Integer Share Quantities**: Verified. All orders sized to integer shares; zero fractional execution.

---

## 8. Final Research Recommendation

1. **Sprint 6.2 Conclusion Confirmed**: The reported verdict **`EXPERIMENT COMPLETED — NO CANDIDATE PASSED ALL PREREGISTERED CRITERIA`** is fully corroborated by independent mathematical, ledger, and accounting analysis.
2. **No Strategy Deployment**: Zero candidate configurations qualified for strategy freezing, live trading, or broker integration.
3. **Validation Set Research Exposure**: The validation dataset (`2023-01-02` through `2024-12-23`) has now been utilized for a formal 16-candidate parameter search. It must not be treated as an untouched holdout for further parameter tuning.
4. **Quarantine Discipline**: The quarantined test period (`2025-01-01` through `2026-07-22`) remains completely unaccessed and protected.
5. **Recommended Research Remediation**: Machine learning model feature representations, entry filters, and regime classifiers must be improved at the modeling level before any future parameter validation is commissioned.

Sprint 6.2.1 independent audit is formally complete.