# Sprint 6.0.1 — Backtest Accounting Reconciliation & Benchmark Audit Report

**Status:** ✅ **PASS WITH LIMITATIONS — FINANCIAL ACCOUNTING VERIFIED**  
**Role:** Lead Quantitative Research Engineer  
**Audit Date:** 2026-10-28 IST  
**Scope:** Read-Only Audit of Sprint 6.0 Event-Driven Backtesting & Execution Engine  
**Subject Files:**
- [`data/reports/sprint_6_0_backtest_report.md`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_backtest_report.md)
- [`data/reports/sprint_6_0_strategy_specification.md`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_strategy_specification.md)
- [`data/reports/trade_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/trade_ledger.csv)
- [`data/reports/portfolio_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/portfolio_ledger.csv)
- [`data/reports/sprint_6_0_backtest_summary.json`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_backtest_summary.json)
- [`src/backtest/event_driven_engine.py`](file:///home/skirataar/Website/StockBot_Model/src/backtest/event_driven_engine.py)

---

## 1. Executive Summary & Audit Verdict

This audit independently reconciles the event-driven backtesting engine implemented in Sprint 6.0. The audit verified trade-level execution logs, daily cash and equity ledgers, transaction fee arithmetic, and benchmark construction against the frozen LightGBM classifier on the 49-constituent NIFTY 50 universe across 388 trading sessions (2025-01-01 to 2026-07-22).

### Summary Audit Verdict: **PASS WITH LIMITATIONS**

1. **Trade Engine & Accounting Integrity (PASS):**
   - The trade engine and daily portfolio ledger are **100% mathematically sound**.
   - Total friction incurred across 621 completed trades reconciles to the exact penny: **₹213,207.51**.
   - Total Gross P&L (**₹52,528.87**), Total Friction (**₹213,207.51**), and Net Realized P&L (**-₹160,678.64**) satisfy `Gross - Friction = Net` to $1.8 \times 10^{-12}$ precision.
   - Zero look-ahead leakage: all entries executed strictly at session $t+1$ Open with 5 bps slippage. Zero true labels were accessed during trade generation.
2. **Identified Report Inconsistency (DOCUMENTED LIMITATION):**
   - In Section 3 of `sprint_6_0_backtest_report.md`, the Markdown table presented an itemized breakdown of cost components that differed from the true recomputed component sums (e.g. reporting Brokerage as ₹12,420.00 instead of the true two-way ₹24,840.00, and percentages summing to 112.28%).
   - **Root Cause:** In `generate_backtest_report()`, the Markdown generator used analytical string estimations based on one-way turnover and hardcoded prototype percentage strings, rather than summing the exact pre-calculated breakdown fields.
   - **Crucial Finding:** This was strictly a **reporting formatting defect**. The core simulation engine, trade ledger, and portfolio ledger executed and deducted the exact, correct two-way fees.

---

## 2. Transaction Cost Reconciliation

### A. Comparison Table: Reported vs. Recomputed Components

| Cost Component | Original Reported Value (INR) | Reported Share (%) | Independently Recomputed Value (INR) | Recomputed Share (%) | Difference (INR) | Audit Status | Likely Cause / Mechanism |
|---|---|---|---|---|---|---|---|
| **Brokerage** | ₹12,420.00 | 5.82% | **₹24,840.00** | **11.65%** | +₹12,420.00 | **RESOLVED** | Report multiplied 621 trades by ₹20 (one leg only); engine charged ₹20 on buy AND ₹20 on sell. |
| **STT** | ₹114,306.00 | 65.42% | **₹114,137.05** | **53.53%** | -₹168.95 | **RESOLVED** | Report estimated STT from invested capital; recomputed uses exact buy (₹57,042.34) and sell (₹57,094.71) turnovers. |
| **Stamp Duty** | ₹8,572.95 | 4.91% | **₹8,556.20** | **4.01%** | -₹16.75 | **RESOLVED** | Report approximated from invested capital; true duty is 0.015% of raw buy turnover. |
| **Exchange Turnover Fee** | ₹3,394.89 | 1.94% | **₹3,390.06** | **1.59%** | -₹4.83 | **RESOLVED** | Report turnover base approximation vs exact NSE 0.00297% schedule. |
| **SEBI Turnover Fee** | ₹114.31 | 0.07% | **₹113.82** | **0.05%** | -₹0.49 | **RESOLVED** | Report turnover base approximation vs exact ₹10/Crore schedule. |
| **GST (18%)** | ₹2,867.25 | 1.41% | **₹5,101.93** | **2.39%** | +₹2,234.68 | **RESOLVED** | Report formula omitted GST on sell-side brokerage (18% of ₹12,420 = ₹2,235.60). |
| **Slippage (5 bps)** | ₹57,068.45 | 32.71% | **₹57,068.46** | **26.77%** | +₹0.01 | **PASS** | Exact match (1 paisa floating-point rounding). |
| **Total Friction** | **₹213,207.51** | **100.00%** | **₹213,207.51** | **100.00%** | **₹0.00** | **PASS** | **Exact match to ₹0.00 across all 621 trades.** |

### B. Summary of Cost Reconciliation Findings
1. **Sum of Listed Components:**
   - In the Sprint 6.0 Markdown report, the sum of listed component numbers was:
     $$₹114,306.00 + ₹57,068.45 + ₹8,572.95 + ₹3,394.89 + ₹12,420.00 + ₹114.31 + ₹2,867.25 = ₹198,743.85$$
   - The reported total friction was **₹213,207.51**, creating an apparent internal deficit of **₹14,463.66**.
   - The recomputed audit reveals that the missing ₹14,463.66 represents:
     $$\text{Sell-Side Brokerage (₹12,420.00)} + \text{Sell-Side Brokerage GST (18\% of ₹12,420 = ₹2,235.60)} + \text{Rounding Adjustments (-₹191.94)} = ₹14,463.66$$
2. **Percentage Share Sum:**
   - The reported shares summed to **112.28%** ($65.42\% + 32.71\% + 4.91\% + 1.94\% + 5.82\% + 0.07\% + 1.41\%$).
   - The independently recomputed percentage shares sum to **100.00%**, with STT representing **53.53%**, slippage **26.77%**, brokerage **11.65%**, stamp duty **4.01%**, GST **2.39%**, exchange fees **1.59%**, and SEBI fees **0.05%**.
3. **Turnover Base Verification:**
   - STT is levied at 0.10% on both Buy and Sell delivery turnover.
   - Stamp duty is levied at 0.015% on the Buy leg only (₹0 on sell).
   - Exchange and SEBI charges apply to both legs.
   - GST (18%) applies to brokerage + exchange + SEBI charges.
   - Zero double-counting occurred in the trade ledger.

---

## 3. P&L, Turnover, and Portfolio Accounting Reconciliation

### A. Core Mathematical Identities

| Accounting Dimension | Reported / Ledger Value | Independently Recomputed Value | Discrepancy | Status |
|---|---|---|---|---|
| **Initial Capital** | ₹1,000,000.00 | ₹1,000,000.00 | ₹0.00 | **PASS** |
| **Total Gross P&L** | ₹52,528.87 | ₹52,528.87 | ₹0.00 | **PASS** |
| **Total Costs / Friction** | ₹213,207.51 | ₹213,207.51 | ₹0.00 | **PASS** |
| **Trade Ledger Net P&L** | -₹160,678.64 | -₹160,678.64 | ₹0.00 | **PASS** |
| **Gross - Costs Identity** | -₹160,678.64 | -₹160,678.64 | $1.8 \times 10^{-12}$ | **PASS** |
| **Ending Portfolio Equity** | ₹840,519.64 | ₹840,519.64 | ₹0.00 | **PASS** |
| **Portfolio Net Return (%)** | -15.95% | -15.95% | 0.00% | **PASS** |
| **Completed Trades Count** | 621 | 621 | 0 | **PASS** |
| **Rejected Orders Count** | 1,407 | 1,407 | 0 | **PASS** |

### B. Daily Mark-to-Market Identity
The daily equity reconciliation:
$$\text{Portfolio Equity}_t = \text{Cash}_t + \sum_{i} \text{Shares}_i \times \text{Close}_{i,t}$$
was audited across all 388 sessions in [`data/reports/portfolio_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/portfolio_ledger.csv).
- Maximum discrepancy across all 388 sessions: **₹0.0100** (1 paisa, attributable strictly to two-decimal float rounding).
- Zero sessions exhibited negative cash balances (Minimum Cash: **₹211.26**).

### C. Reconciliation Between Ending Equity and Trade Ledger Net P&L
- **Ending Portfolio Equity Change:** $₹840,519.64 - ₹1,000,000.00 = -₹159,480.36$.
- **Cumulative Net P&L from Trade Ledger:** $-₹160,678.64$.
- **Variance:** $(-₹159,480.36) - (-₹160,678.64) = +₹1,198.28$.
- **Audit Explanation:**
  - On the final session close (2026-07-22), **8 positions remained open** in the portfolio ledger, valued mark-to-market at ₹657,180.90 without deducting liquidation costs.
  - In the trade ledger, those 8 positions were synthetically liquidated at the final close to compute complete trade-level statistics (`exit_reason="END_OF_PERIOD_LIQUIDATION"`), deducting **₹1,198.28 in hypothetical sell-side transaction friction and slippage**.
  - Subtracting this un-incurred sell friction from ending portfolio equity:
    $$₹840,519.64 - ₹1,198.28 = ₹839,321.36 \implies ₹839,321.36 - ₹1,000,000.00 = -₹160,678.64$$
  - The reconciliation matches the trade ledger Net P&L to **10 paise**.

### D. Turnover Clarification
In the Sprint 6.0 narrative, turnover was described as "₹5.72 Crore in cumulative turnover." The audit establishes the exact figures:
- **Raw Buy-Side Turnover:** **₹57,042,157.63** (~₹5.70 Crore).
- **Raw Sell-Side Turnover:** **₹57,094,686.76** (~₹5.71 Crore).
- **Reported Turnover Metric:** **₹57,152,998.81** (~₹5.72 Crore), which represents **One-Way Buy-Side Invested Capital** (Turnover + Buy Fees).
- **Combined Two-Way Turnover (Buy + Sell):** **₹114,136,844.39** (~₹11.41 Crore).
- **Average One-Way Turnover:** **₹57,068,422.20** (~₹5.71 Crore).

---

## 4. Benchmark Fairness & Reproducibility Audit

### A. NIFTY 50 Equal-Weight Buy & Hold Benchmark
- **Universe:** 49 approved constituent CSVs in `data/labeled/`.
- **Implementation:** Equal capital allocation ($\frac{₹1,000,000}{49} = ₹20,408.16$) on Day 1 (2025-01-01 Close), held passively until Day 388 Close.
- **Return & Equity:** +10.26% cumulative return, ending equity ₹1,102,607.68, Sharpe 0.04.
- **Fairness Note:** The benchmark is computed gross of execution friction. Since buy-and-hold involves only 49 one-off entries, total friction would be approximately ~₹1,920 (0.19%), which does not materially alter the benchmark (+10.07% net).

### B. Non-ML Top-10 Static Baseline
- **Construction Method:** Selects the first 10 constituents alphabetically from `price_dict`:
  `['ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJAJFINSV', 'BAJFINANCE', 'BEL', 'BHARTIARTL']`
- **Execution:** Static buy-and-hold on Day 1 Close (₹100,000 per stock, 10% weight), held continuously with zero rebalancing and zero turnover.
- **Return & Equity:** +28.44% cumulative return, ending equity ₹1,284,448.74, Sharpe 0.71.
- **Fairness Disclosures:**
  1. **Not an Active Swing Baseline:** This baseline did not execute 5-session swing trades or dynamic rotations; it was a static buy-and-hold portfolio.
  2. **Fortuitous Large-Cap Outperformance:** In 2025–2026, all 10 alphabetical large-caps achieved strong positive gains (e.g. BAJFINANCE +52.88%, ADANIPORTS +49.29%, BEL +38.40%, BAJAJ-AUTO +25.83%).
  3. **Zero Friction:** Incurred 0 turnover after Day 1, avoiding the ₹2.13 Lakhs delivery tax burden suffered by the active swing strategy.
  4. **Exposure Mismatch:** Held 100% continuous equity exposure, compared to 54.54% average gross exposure for the model-driven strategy.
  5. **Conclusion:** It serves as a benchmark for passive large-cap holding, but must not be interpreted as an active rule-based trading baseline.

---

## 5. Execution & Trade Ledger Invariants Audit

Representative trades across the 621-trade sequence (e.g. Trade #0, #10, #50, #100, #300, #600) were verified against the raw OHLCV price series:

| Check | Requirement | Audit Evidence | Status |
|---|---|---|---|
| **Entry Timing** | Staged at $t$ close, executes at $t+1$ Open | Trade #0: Signal 2025-01-01, Entry 2025-01-02 Open. Verified across all 621 trades (`entry_date > signal_date`). | **PASS** |
| **Slippage Application** | Buy: $+5\text{ bps}$, Sell: $-5\text{ bps}$ | Trade #0: Raw Open 294.45 $\rightarrow$ Exec 294.60 (+5 bps). Raw Exit 296.50 $\rightarrow$ Exec 296.35 (-5 bps). | **PASS** |
| **Holding Duration** | Max 5 sessions or early sell signal | 337 trades exited via `EARLY_SELL_SIGNAL` (1–4 sessions); 276 trades exited at `MAX_HOLD_5D` (5 sessions); 8 liquidated at end of period. | **PASS** |
| **Position Overlap** | Max 1 open position per symbol | No duplicate trades opened while symbol had an active holding (`next_entry >= curr_exit`). | **PASS** |
| **Share Allocation** | Integer shares only ($\ge 1$) | Quantities range from 5 to 645 shares; zero fractional shares. | **PASS** |
| **Cash Solvency** | Cash $\ge 0$ at all times | Cash balance remained positive in all 388 sessions (Minimum: ₹211.26). | **PASS** |
| **True Label Independence** | Zero reliance on `signal` / `forward_return_5d` | Mutating true labels produces identical orders and P&L. | **PASS** |

---

## 6. Known Limitations & Recommendations

1. **Formatting Discrepancies in Section 3 of Sprint 6.0 Report:**
   - The table in Sprint 6.0 displayed approximate one-way fees and unnormalized percentage shares.
   - *Recommendation:* Future reporting scripts should compute itemized tables by aggregating pre-computed ledger columns directly rather than using inline interpolation estimates.
2. **Delivery Tax Friction in Cash Equities:**
   - The audit confirms that Indian cash equity swing trading faces an insurmountable statutory barrier (~37 bps round trip on delivery vs ~6 bps in equity futures).
   - *Recommendation for Sprint 6.1:* Transition execution research to F&O equity futures (single-sided 0.02% STT) or implement confidence threshold gating ($P(\text{BUY}) \ge 0.55$).

---

## 7. Automated Test Results

Automated reconciliation tests added in [`tests/test_reconciliation_6_0_1.py`](file:///home/skirataar/Website/StockBot_Model/tests/test_reconciliation_6_0_1.py) confirm:
- `test_total_friction_and_pnl_exact_reconciliation`: Reconciles Gross P&L, Total Friction, and Net P&L to $10^{-12}$ precision.
- `test_exact_cost_component_reconstruction`: Re-evaluates all 621 trades through statutory cost formulas, confirming exact match to ₹213,207.51.
- `test_portfolio_ledger_daily_mtm_solvency`: Confirms MTM identity across all 388 sessions within ₹0.01.
- `test_liquidation_equity_variance_reconciliation`: Explains the ₹1,198.28 ending equity variance to 10 paise.
- `test_turnover_breakdown_consistency`: Verifies raw buy, raw sell, and combined turnover figures.
- `test_benchmark_reproducibility`: Re-computes B&H (+10.26%) and Non-ML Top-10 (+28.44%) deterministically.

```bash
$ PYTHONPATH=. ./venv/bin/pytest tests/ -v
======================= 44 passed, 28 warnings in 26.50s =======================
```
All 44 automated tests in the repository pass cleanly.
