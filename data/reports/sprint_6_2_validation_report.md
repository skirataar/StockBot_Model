# Sprint 6.2 — Preregistered Validation-Only Backtest Experiment Report

**Date**: 2026-10-28T21:34:45.077274+00:00  
**Role**: Lead Quantitative Researcher & Backtesting Engineer  
**Repository**: `StockBot_Model` (`main` branch, commit `8450e91288c82c4e68c2aacd076c96141a973f96`)  
**Protocol Version**: `1.2.0-AMENDED`  
**Protocol SHA-256**: `0384d6a1b9ac7738a92e295fd94bfac113a9a99ce2f399f11ffa5d66164223cb`  
**Execution Scope**: `validation_dataset.parquet` (`2023-01-02` through `2024-12-23`, 486 sessions, 49 constituents)  
**Final Verdict**: **`EXPERIMENT COMPLETED — NO CANDIDATE PASSED ALL PREREGISTERED CRITERIA`**  

---

## 1. Executive Summary

This report documents the rigorous execution of the preregistered Sprint 6.2 validation-only backtest experiment, formally authorized under Sprint 6.1.10. Exactly 16 discrete candidate configurations (`CFG-01` through `CFG-16`) and the external reference baseline (`CFG-BASE`) were executed across the authorized 2023–2024 validation window without look-ahead bias, under statutory Indian equity delivery transaction costs (brokerage, STT, exchange fees, SEBI charges, stamp duty, GST) and 5 bps execution slippage per leg.

### Final Experiment Status
**`EXPERIMENT COMPLETED — NO CANDIDATE PASSED ALL PREREGISTERED CRITERIA`**

- **Candidates Evaluated**: 16 preregistered trials + 1 external reference (`CFG-BASE`).
- **Valid Runs**: 16/16 completed with zero data corruption, zero missing dates, zero non-finite returns, and full solvency/capacity compliance.
- **Top Candidate by Net Annualized Sharpe**: **`CFG-16`** (Annualized Sharpe: `1.0283`).
- **Binding Expected-Maximum-Sharpe Hurdle (SR*_ann)**: `0.9698`.
- **Primary DSR Test Statistic**: `0.5369` (p-value: `0.4631`, Significant at alpha=0.05: `False`).
- **Candidates Passing All Mandatory Acceptance Criteria (M1–M8)**: **`0`**.

> [!IMPORTANT]
> **Holdout Governance Boundaries**:
> 1. The test period (`2025-01-01` through `2026-07-22`) in `data/processed/test_dataset.parquet` remained strictly quarantined and was NEVER accessed, read, or evaluated.
> 2. `models/lightgbm.joblib` remained 100% frozen and unmodified (SHA-256: `41e61760fc...`).
> 3. Historical baseline ledgers (`trade_ledger.csv`, `portfolio_ledger.csv`) remained untouched.

---

## 2. Benchmark Reference Performance (2023–2024)

Under Criterion **`M2`**, any acceptable candidate strategy must generate net cumulative returns exceeding the passive equal-weighted buy-and-hold portfolio of the 49 NIFTY 50 universe constituents:

- **Benchmark Name**: NIFTY 50 Equal-Weight Buy & Hold
- **Initial Capital**: Rs. 1,000,000.00
- **Final Ending Equity**: Rs. 1,592,186.81
- **Net Cumulative Return**: **+59.22%**
- **CAGR**: +27.27%
- **Annualized Volatility**: 13.00%
- **Annualized Sharpe Ratio**: 1.64
- **Maximum Drawdown**: 13.02%

---

## 3. Candidate Comparison & Performance Summary Table

| Candidate ID | Buy Thresh | Exit Mechanism | Daily Pacing | Net Return | Ann. Sharpe | Max DD | Total Trades | Win Rate | Profit Factor | Friction % Alpha | vs Benchmark | DSR p-val | Status | Rejection Triggers |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `CFG-01` | `0.35` | `fixed_5d` | `uncon` | +19.88% | 0.23 | 12.80% | 848 | 52.4% | 1.53 | 64.2% | Under | 0.8239 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R8_DSR_INSIGNIFICANT` |
| `CFG-02` | `0.38` | `fixed_5d` | `uncon` | +16.12% | 0.14 | 11.27% | 524 | 50.4% | 1.60 | 56.7% | Under | 0.8554 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R8_DSR_INSIGNIFICANT` |
| `CFG-03` | `0.40` | `fixed_5d` | `uncon` | +23.70% | 0.43 | 10.77% | 349 | 52.7% | 1.88 | 38.5% | Under | 0.7522 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R8_DSR_INSIGNIFICANT` |
| `CFG-04` | `0.42` | `fixed_5d` | `uncon` | +10.81% | -0.05 | 11.16% | 222 | 53.6% | 1.61 | 45.4% | Under | 0.9104 | **REJECTED** | `R1_NON_POSITIVE_SHARPE;R2_BENCHMARK_UNDERPERFORMANCE;R8_DSR_INSIGNIFICANT` |
| `CFG-05` | `0.45` | `fixed_5d` | `uncon` | +22.07% | 0.69 | 3.89% | 113 | 59.3% | 2.87 | 17.7% | Under | 0.6785 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R8_DSR_INSIGNIFICANT` |
| `CFG-06` | `0.48` | `fixed_5d` | `uncon` | +23.18% | 1.13 | 2.33% | 47 | 66.0% | 7.99 | 8.0% | Under | 0.4680 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R4_INSUFFICIENT_TOTAL_TRADES;R5_INSUFFICIENT_ANNUAL_TRADES;R8_DSR_INSIGNIFICANT` |
| `CFG-07` | `0.50` | `fixed_5d` | `uncon` | +13.86% | 0.31 | 1.30% | 24 | 66.7% | 9.73 | 6.7% | Under | 0.8534 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R4_INSUFFICIENT_TOTAL_TRADES;R5_INSUFFICIENT_ANNUAL_TRADES;R8_DSR_INSIGNIFICANT` |
| `CFG-08` | `0.40` | `1.5x_ATR` | `uncon` | +22.32% | 0.38 | 10.74% | 371 | 52.8% | 1.70 | 41.1% | Under | 0.7720 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R8_DSR_INSIGNIFICANT` |
| `CFG-09` | `0.40` | `2.0x_ATR` | `uncon` | +24.02% | 0.44 | 10.79% | 360 | 54.2% | 1.80 | 38.8% | Under | 0.7470 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R8_DSR_INSIGNIFICANT` |
| `CFG-10` | `0.40` | `2.5x_ATR` | `uncon` | +24.50% | 0.46 | 10.75% | 356 | 53.6% | 1.82 | 38.1% | Under | 0.7389 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R8_DSR_INSIGNIFICANT` |
| `CFG-11` | `0.40` | `fixed_5d` | `2` | +18.56% | 0.33 | 6.79% | 265 | 54.0% | 1.91 | 36.7% | Under | 0.8031 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R8_DSR_INSIGNIFICANT` |
| `CFG-12` | `0.40` | `fixed_5d` | `3` | +22.92% | 0.48 | 8.21% | 300 | 53.7% | 1.93 | 35.6% | Under | 0.7435 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R8_DSR_INSIGNIFICANT` |
| `CFG-13` | `0.42` | `2.0x_ATR` | `uncon` | +11.41% | -0.02 | 11.15% | 232 | 54.3% | 1.55 | 45.1% | Under | 0.9050 | **REJECTED** | `R1_NON_POSITIVE_SHARPE;R2_BENCHMARK_UNDERPERFORMANCE;R8_DSR_INSIGNIFICANT` |
| `CFG-14` | `0.45` | `2.0x_ATR` | `uncon` | +22.45% | 0.71 | 3.88% | 116 | 60.3% | 2.63 | 17.8% | Under | 0.6672 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R8_DSR_INSIGNIFICANT` |
| `CFG-15` | `0.45` | `2.0x_ATR` | `2` | +14.45% | 0.21 | 3.28% | 96 | 59.4% | 2.18 | 21.1% | Under | 0.8565 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R4_INSUFFICIENT_TOTAL_TRADES;R5_INSUFFICIENT_ANNUAL_TRADES;R8_DSR_INSIGNIFICANT` |
| `CFG-16` | `0.48` | `2.0x_ATR` | `uncon` | +23.27% | 1.13 | 2.33% | 48 | 66.7% | 6.70 | 8.1% | Under | 0.4631 | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R4_INSUFFICIENT_TOTAL_TRADES;R5_INSUFFICIENT_ANNUAL_TRADES;R8_DSR_INSIGNIFICANT` |
| `CFG-BASE` | `argmax` | `fixed_5d` | `uncon` | +31.83% | 0.61 | 10.42% | 711 | 53.5% | 1.66 | 50.5% | Under | N/A | **REJECTED** | `R2_BENCHMARK_UNDERPERFORMANCE;R8_DSR_INSIGNIFICANT` |

*Note: `CFG-BASE` is evaluated as an external comparative anchor and is not counted among the 16 multiple-testing trial hypotheses.*

---

## 4. Cross-Sectional Statistical Evaluation & Multiple Testing

### 4.1 Cohort Moments & Expected-Maximum Sharpe Hurdle
- **Trial Count (K)**: `16` discrete candidate configurations.
- **Cohort Sample Mean Sharpe (mu_SR)**: `0.4332`
- **Governance Baseline Floor (max(0, mu_SR))**: `0.4332`
- **Cohort Sample Std Sharpe (sigma_SR)**: `0.2980`
- **EVT Hurdle Factor (EVT(16))**: `1.800454`
- **Binding Primary Hurdle (SR*_ann)**: `0.9698`

### 4.2 Primary Gate Evaluation (Top Candidate)
- **Selected Candidate**: **`CFG-16`**
- **Observed Annualized Sharpe**: `1.0283`
- **Hurdle Surplus**: `+0.0585`
- **Mertens Variance (V)**: `0.7662` (daily scale)
- **Skewness (gamma_3)**: `4.1900` | **Kurtosis (gamma_4)**: `36.8813`
- **DSR Test Statistic (z)**: `0.5369`
- **DSR p-value**: **`0.4631`**
- **Statistically Significant (p < 0.05)**: `False`
- **Primary Gate Verdict**: **`PRIMARY_DSR_REJECTED`**

### 4.3 Secondary Correlation Diagnostics & Participation Ratio
- **Average Pairwise Return Correlation (rho_bar)**: `0.8033`
- **Participation Ratio Effective Trials (N_eff)**: `1.45`
- **Effective Trials Hurdle (SR*(N_eff))**: `0.4847`
- **Top Candidate Diagnostic p-value under N_eff**: `0.1945`

### 4.4 Holm-Bonferroni Family-Wise Error Rate (FWER) Step-Down
The 16 candidate hypotheses were evaluated under Holm-Bonferroni step-down at FWER alpha = 0.05 across the family of trials:

| Candidate ID | Raw DSR p-value | Holm Rank | Target alpha / (K - i + 1) | Adjusted p-value | Significant (FWER <= 0.05) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `CFG-01` | `0.8239` | `11` | `0.0083` | `1.0000` | `NO` |
| `CFG-02` | `0.8554` | `13` | `0.0125` | `1.0000` | `NO` |
| `CFG-03` | `0.7522` | `8` | `0.0056` | `1.0000` | `NO` |
| `CFG-04` | `0.9104` | `16` | `0.0500` | `1.0000` | `NO` |
| `CFG-05` | `0.6785` | `4` | `0.0038` | `1.0000` | `NO` |
| `CFG-06` | `0.4680` | `2` | `0.0033` | `1.0000` | `NO` |
| `CFG-07` | `0.8534` | `12` | `0.0100` | `1.0000` | `NO` |
| `CFG-08` | `0.7720` | `9` | `0.0063` | `1.0000` | `NO` |
| `CFG-09` | `0.7470` | `7` | `0.0050` | `1.0000` | `NO` |
| `CFG-10` | `0.7389` | `5` | `0.0042` | `1.0000` | `NO` |
| `CFG-11` | `0.8031` | `10` | `0.0071` | `1.0000` | `NO` |
| `CFG-12` | `0.7435` | `6` | `0.0045` | `1.0000` | `NO` |
| `CFG-13` | `0.9050` | `15` | `0.0250` | `1.0000` | `NO` |
| `CFG-14` | `0.6672` | `3` | `0.0036` | `1.0000` | `NO` |
| `CFG-15` | `0.8565` | `14` | `0.0167` | `1.0000` | `NO` |
| `CFG-16` | `0.4631` | `1` | `0.0031` | `1.0000` | `NO` |

---

## 5. Detailed Accounting & Ledger Reconciliation

To verify strict accounting fidelity, portfolio cash, mark-to-market valuations, statutory transaction costs, and trade ledgers were reconciled for all 16 candidates and the baseline:

| Candidate ID | Starting Capital | Ending Equity | Gross P&L | Total Costs (Friction) | Net P&L | P&L Reconciled | Min Cash | Max Positions | Solvency / Capacity |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `CFG-01` | Rs. 1,000,000.00 | Rs. 1,198,811.21 | Rs. 549,853.81 | Rs. 353,098.83 | Rs. 196,754.98 | Exact | Rs. 139.11 | 10/10 | Compliant |
| `CFG-02` | Rs. 1,000,000.00 | Rs. 1,161,181.08 | Rs. 367,869.94 | Rs. 208,683.90 | Rs. 159,186.04 | Exact | Rs. 148.20 | 10/10 | Compliant |
| `CFG-03` | Rs. 1,000,000.00 | Rs. 1,237,031.09 | Rs. 381,689.68 | Rs. 146,767.95 | Rs. 234,921.73 | Exact | Rs. 49.78 | 10/10 | Compliant |
| `CFG-04` | Rs. 1,000,000.00 | Rs. 1,108,058.63 | Rs. 194,263.26 | Rs. 88,106.60 | Rs. 106,156.66 | Exact | Rs. 8,289.49 | 10/10 | Compliant |
| `CFG-05` | Rs. 1,000,000.00 | Rs. 1,220,669.93 | Rs. 265,741.42 | Rs. 46,943.85 | Rs. 218,797.57 | Exact | Rs. 16,195.08 | 10/10 | Compliant |
| `CFG-06` | Rs. 1,000,000.00 | Rs. 1,231,763.71 | Rs. 250,521.17 | Rs. 20,015.90 | Rs. 230,505.27 | Exact | Rs. 241,854.18 | 8/10 | Compliant |
| `CFG-07` | Rs. 1,000,000.00 | Rs. 1,138,636.57 | Rs. 147,684.85 | Rs. 9,831.41 | Rs. 137,853.44 | Exact | Rs. 661,368.39 | 4/10 | Compliant |
| `CFG-08` | Rs. 1,000,000.00 | Rs. 1,223,236.25 | Rs. 375,807.30 | Rs. 154,655.87 | Rs. 221,151.43 | Exact | Rs. 44.74 | 10/10 | Compliant |
| `CFG-09` | Rs. 1,000,000.00 | Rs. 1,240,241.74 | Rs. 389,038.36 | Rs. 150,911.95 | Rs. 238,126.41 | Exact | Rs. 45.21 | 10/10 | Compliant |
| `CFG-10` | Rs. 1,000,000.00 | Rs. 1,244,982.49 | Rs. 392,259.22 | Rs. 149,395.67 | Rs. 242,863.55 | Exact | Rs. 188.12 | 10/10 | Compliant |
| `CFG-11` | Rs. 1,000,000.00 | Rs. 1,185,632.95 | Rs. 291,072.48 | Rs. 106,856.04 | Rs. 184,216.44 | Exact | Rs. 4,147.48 | 10/10 | Compliant |
| `CFG-12` | Rs. 1,000,000.00 | Rs. 1,229,240.72 | Rs. 352,786.97 | Rs. 125,643.66 | Rs. 227,143.31 | Exact | Rs. 375.84 | 10/10 | Compliant |
| `CFG-13` | Rs. 1,000,000.00 | Rs. 1,114,130.97 | Rs. 204,217.52 | Rs. 92,011.08 | Rs. 112,206.44 | Exact | Rs. 132.25 | 10/10 | Compliant |
| `CFG-14` | Rs. 1,000,000.00 | Rs. 1,224,520.35 | Rs. 270,843.87 | Rs. 48,203.45 | Rs. 222,640.42 | Exact | Rs. 1,556.37 | 10/10 | Compliant |
| `CFG-15` | Rs. 1,000,000.00 | Rs. 1,144,470.00 | Rs. 181,901.80 | Rs. 38,411.43 | Rs. 143,490.37 | Exact | Rs. 470,374.49 | 6/10 | Compliant |
| `CFG-16` | Rs. 1,000,000.00 | Rs. 1,232,717.42 | Rs. 251,885.07 | Rs. 20,426.10 | Rs. 231,458.97 | Exact | Rs. 228,409.44 | 8/10 | Compliant |
| `CFG-BASE` | Rs. 1,000,000.00 | Rs. 1,318,255.83 | Rs. 638,763.47 | Rs. 322,742.49 | Rs. 316,020.98 | Exact | Rs. 70.15 | 10/10 | Compliant |

### Explicit Arithmetic Explanation of Liquidation Accounting:
1. **Gross P&L vs Net P&L**: For every candidate, `Gross P&L - Total Friction (Statutory Fees + Brokerage + Slippage) = Net P&L` reconciles to exact rupee precision.
2. **Portfolio Equity vs Cumulative Net P&L**:
   - The daily portfolio ledger records mark-to-market equity at session Close:
     $$\text{Ending Equity} = \text{Cash} + \sum (\text{Quantity} \times \text{Close Price})$$
   - Buy friction (statutory delivery taxes, exchange fees, brokerage, buy slippage) was already deducted from cash upon position entry.
   - For positions still open on the final date (`2024-12-23`), the trade ledger generates synthetic `END_OF_PERIOD_LIQUIDATION` records to account for theoretical terminal liquidation. These records deduct hypothetical terminal sell friction (statutory exit taxes, brokerage, and exit slippage).
   - Therefore, the exact difference between terminal portfolio equity and $(\text{Starting Capital} + \sum \text{Net P\&L})$ is precisely equal to the un-deducted sell friction of the positions open at the close of the final session:
     $$\text{Ending Equity} - (\text{Starting Capital} + \sum \text{Net P\&L}) = \sum_{\text{open positions}} \text{Sell Friction}$$
     For example, in `CFG-16`:
     $$\text{Ending Equity} = \text{Rs. } 1,232,717.42$$
     $$\text{Starting Capital} + \sum \text{Net P\&L} = \text{Rs. } 1,000,000.00 + \text{Rs. } 231,458.97 = \text{Rs. } 1,231,458.97$$
     $$\text{Difference} = \text{Rs. } 1,258.45$$
     The exact sell friction calculated on the 6 terminal open positions equals **Rs. 1,258.43** (0.02 INR rounding across 6 individual trade records).
3. **Solvency & Capacity Compliance**:
   - Cash remained strictly non-negative on 100% of trading dates across all 17 configurations. The absolute minimum cash balance observed across any configuration was Rs. 44.74 (`CFG-08`), safely above the Rs. 0.00 solvency floor.
   - Gross exposure remained strictly $\le 100\%$ on all dates (zero leverage, no short selling).
   - Concurrent portfolio holdings never exceeded the hard limit of 10 positions.

---

## 6. Analysis of Performance & Criteria Evaluation

- **Benchmark Comparison (Criterion M2)**: Passive equal-weighted NIFTY 50 benchmark generated **+59.22%**. The 16 candidate configurations generated returns between **+10.81%** and **+24.50%**. Outperforming candidates: **0/16**.
- **Risk-Adjusted Performance (Criterion M1)**: Net annualized Sharpe ratios ranged between **-0.05** and **1.13** (Threshold: > 0.50). Candidates passing M1: **4/16**.
- **Statistical Significance (Criterion M8)**: Binding expected-maximum hurdle is SR*_ann = 0.9698. Best candidate observed Sharpe is 1.0283 with DSR p-value = 0.4631. Candidates passing M8: **0/16**.

---

## 7. Final Governance Decision & Next Steps

**Verdict**: **`EXPERIMENT COMPLETED — NO CANDIDATE PASSED ALL PREREGISTERED CRITERIA`**

### Governance Takeaways:
1. **Execution Validity**: The event-driven backtesting engine and cross-sectional evaluation harness functioned flawlessly with 100% mathematical, ledger, and accounting reconciliation.
2. **Research Integrity**: Empirical findings are fully reported without data mining, post-hoc metric tuning, or threshold loosening.
3. **Quarantine Preserved**: The test dataset (`2025-01-01` through `2026-07-22`) remains completely untouched.
4. **No Deployment**: No candidate configuration is authorized for live trading, broker connectivity, or deployment.

Sprint 6.2 validation experiment execution is formally complete.