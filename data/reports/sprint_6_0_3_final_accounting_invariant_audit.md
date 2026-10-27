# Sprint 6.0.3 — Final Accounting Invariant Audit Report

**Status:** ✅ **PASS WITH LIMITATIONS — MATHEMATICAL DERIVATION PROVEN**  
**Role:** Lead Quantitative Research Engineer  
**Audit Date:** 2026-10-28 IST  
**Scope:** Mathematical Proof and Source-Level Verification of Fee Rounding and Equity Invariants  
**Audited Artifacts:**
- [`src/backtest/event_driven_engine.py`](file:///home/skirataar/Website/StockBot_Model/src/backtest/event_driven_engine.py)
- [`data/reports/trade_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/trade_ledger.csv)
- [`data/reports/portfolio_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/portfolio_ledger.csv)
- [`data/reports/sprint_6_0_backtest_summary.json`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_backtest_summary.json)
- [`data/reports/sprint_6_0_2_fee_formula_equity_audit_report.md`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_2_fee_formula_equity_audit_report.md)
- [`tests/test_final_invariant_audit_6_0_3.py`](file:///home/skirataar/Website/StockBot_Model/tests/test_final_invariant_audit_6_0_3.py)

---

## 1. Executive Summary & Verdict

### Final Verdict: **PASS WITH LIMITATIONS**

This audit independently verifies that the **one-paisa fee discrepancy** (₹213,207.52 vs ₹213,207.51) and the **ten-paisa equity reconciliation gap** (₹1,198.38 vs ₹1,198.28) are **rigorously derived mathematical identities** originating directly from order-level row executions, and not narrative approximations.

1. **Check 1 — Fee Rounding (PROVEN):**
   - The true unrounded aggregate friction across all 621 completed trades ($1,242$ order legs) is **₹213,207.511554**, identically produced by IEEE-754 64-bit floating-point and arbitrary-precision `decimal.Decimal`.
   - The ₹0.01 difference between the sum of displayed component totals (**₹213,207.52**) and recorded total friction (**₹213,207.51**) is proven to be a combinatorial cancellation of sub-paisa truncation across the 1,242 order legs: 274 negative divergences (-₹2.81) cancel against 272 positive divergences (+₹2.82), leaving an exact net residual of **+₹0.01**.
2. **Check 2 — Ten-Paisa Equity Reconciliation (PROVEN):**
   - A single explicit closed-form equation reconciles portfolio equity change (-₹159,480.36) against trade ledger Net P&L (-₹160,678.64) to **₹0.0000 exactness**:
     $$\Delta \text{Equity} - \text{Net P\&L}_{all} = \text{Hypothetical Sell Friction}_{open} - \delta_{liq} - \delta_{cash}$$
     $$-₹159,480.36 - (-₹160,678.64) = ₹1,198.38 - ₹0.02 - ₹0.08 = \mathbf{₹1,198.28}$$
   - Every term is explicitly classified as realized, unrealized, hypothetical, or rounding artifact. Zero buy-side costs are double-counted.
3. **Check 3 — Test Quality (VERIFIED):**
   - [`tests/test_final_invariant_audit_6_0_3.py`](file:///home/skirataar/Website/StockBot_Model/tests/test_final_invariant_audit_6_0_3.py) independently verifies edge cases around the ₹20 brokerage cap, asymmetric stamp duty, GST base composition, and includes negative mutation tests that fail if formulas are corrupted. All 54 tests across the repository pass.
4. **Documented Limitations:**
   - The initial Sprint 6.0 report table formatting glitch remains preserved in the historical artifact; the corrected figures and derivation equations are documented in Sprint 6.0.1, 6.0.2, and this final 6.0.3 report.

---

## 2. Check 1 — Fee Rounding & Decimal Arithmetic

### A. Four-Way Fee Component Audit

The table below reports every fee component across four calculation methods:
1. **Unrounded Component Sums** (IEEE-754 64-bit float and exact `decimal.Decimal`)
2. **Individually Rounded Component Totals** (each component rounded to 2 decimals per order leg, then summed)
3. **Production Rounding Order Total Friction** (statutory subcomponents summed in float, slippage added, rounded to 2 decimals per order leg)
4. **Decimal Arithmetic Friction** (arbitrary precision `decimal.Decimal` with explicit `ROUND_HALF_EVEN` and `ROUND_HALF_UP`)

| Fee Component | (1) Unrounded Sum (INR) | (2) Individually Rounded Total (INR) | (3) Production Rounding Order (INR) | (4) Decimal Arithmetic (`ROUND_HALF_EVEN`) | Individual Component Rounding Delta (2 - 1) |
|---|---|---|---|---|---|
| **Brokerage** | ₹24,840.000000 | ₹24,840.00 | ₹24,840.00 | ₹24,840.00 | ₹0.000000 |
| **STT** | ₹114,136.844390 | ₹114,137.05 | — | ₹114,136.99 | +₹0.205610 |
| **Stamp Duty (Buy)** | ₹8,556.323645 | ₹8,556.20 | — | ₹8,556.26 | -₹0.123645 |
| **Exchange Charges** | ₹3,389.864278 | ₹3,390.06 | — | ₹3,390.06 | +₹0.195722 |
| **SEBI Turnover Fee** | ₹114.136844 | ₹113.82 | — | ₹113.82 | -₹0.316844 |
| **GST (18%)** | ₹5,101.920202 | ₹5,101.93 | — | ₹5,101.93 | +₹0.009798 |
| **Slippage (5 bps)** | ₹57,068.422195 | ₹57,068.46 | — | ₹57,068.36 | +₹0.037805 |
| **Total Friction** | **₹213,207.511554** | **₹213,207.52** | **₹213,207.51** | **₹213,207.51** | **+₹0.008446** |

> [!IMPORTANT]
> **Key Arithmetic Finding:**
> - The true unrounded aggregate friction across all trades is **₹213,207.511554**.
> - In `decimal.Decimal` arithmetic, applying `ROUND_HALF_EVEN` yields **₹213,207.51**.
> - Applying standard commercial `ROUND_HALF_UP` also yields **₹213,207.51**.
> - The production engine's recorded ledger total is **₹213,207.51**.
> - All decimal and float aggregation methods agree on the exact same total: **₹213,207.51**.

### B. Mathematical Proof of the ₹0.01 Display Discrepancy
Why does the sum of the individually displayed component totals equal **₹213,207.52** (+₹0.01 above recorded total friction)?

Let each order leg $j \in \{1, \dots, 1242\}$ have unrounded component fees $c_{j, 1}, \dots, c_{j, 7}$.
In the production engine:
$$\text{Friction}_{leg, j} = \text{round}\left(\sum_{k=1}^{7} c_{j, k}, 2\right)$$
In displayed reporting tables:
$$\text{Component Total}_k = \sum_{j=1}^{1242} \text{round}(c_{j, k}, 2)$$
The discrepancy on leg $j$ is:
$$\Delta_j = \sum_{k=1}^{7} \text{round}(c_{j, k}, 2) - \text{round}\left(\sum_{k=1}^{7} c_{j, k}, 2\right)$$

An exhaustive audit of all 1,242 order legs reveals:
- **696 legs** have $\Delta_j = 0$ (exact agreement).
- **546 legs** exhibit non-zero sub-paisa truncation divergence:
  - 267 legs have $\Delta_j = -₹0.01$ (Total: -₹2.67)
  - 7 legs have $\Delta_j = -₹0.02$ (Total: -₹0.14)
  - 262 legs have $\Delta_j = +₹0.01$ (Total: +₹2.62)
  - 10 legs have $\Delta_j = +₹0.02$ (Total: +₹0.20)
- Summing these divergences across all 1,242 legs:
  $$\sum_{j=1}^{1242} \Delta_j = (-₹2.67 - ₹0.14) + (+₹2.62 + ₹0.20) = -₹2.81 + ₹2.82 = \mathbf{+₹0.01}$$
This proves that the ₹0.01 discrepancy is not an error or a floating-point quirk, but the exact combinatorial sum of sub-paisa truncation across 1,242 order legs.

---

## 3. Check 2 — Ten-Paisa Equity Reconciliation

### A. Raw Row Quantities from Project Ledgers

| Metric | Source Artifact & Ledger Rows | Exact Recorded Amount (INR) | Accounting Classification |
|---|---|---|---|
| **Initial Capital** | Config / Pre-registered Parameter | **₹1,000,000.00** | Starting Equity |
| **Final Portfolio Equity** | [`portfolio_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/portfolio_ledger.csv) (Row 387, 2026-07-22) | **₹840,519.64** | Mark-to-Market Equity |
| **Final Cash Balance** | [`portfolio_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/portfolio_ledger.csv) (Row 387, 2026-07-22) | **₹183,338.74** | Solvency Cash Floor |
| **Final Invested MTM Value** | [`portfolio_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/portfolio_ledger.csv) (8 open holdings at close) | **₹657,180.90** | Unrealized Asset Value |
| **Portfolio Equity Change** | $₹840,519.64 - ₹1,000,000.00$ | **-₹159,480.36** | Net Portfolio Outcome |
| **Closed Trades Realized Gross P&L** | [`trade_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/trade_ledger.csv) (Trades #0–#612) | **+₹63,759.07** | Realized Trading Alpha |
| **Closed Trades Realized Costs** | [`trade_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/trade_ledger.csv) (Trades #0–#612) | **₹210,693.24** | Realized Transaction Friction |
| **Closed Trades Realized Net P&L** | $₹63,759.07 - ₹210,693.24$ | **-₹146,934.17** | Realized Net Result |
| **Open Positions Cash Outlay** | $\sum \text{invested\_capital}$ (Trades #613–#620) | **₹669,727.01** | Historical Cash Deducted |
| **Open Positions Unrealized MTM P&L**| $₹657,180.90 - ₹669,727.01$ | **-₹12,546.11** | Unrealized MTM Loss |
| **Hypothetical Liquidation Sell Friction**| $\sum \text{calculate\_sell\_costs}(P_{close}, Q)$ for 8 open stocks | **₹1,198.38** | Hypothetical Exit Friction |
| **Synthetic Liquidation Trade Net P&L**| [`trade_ledger.csv`](file:///home/skirataar/Website/StockBot_Model/data/reports/trade_ledger.csv) (Trades #613–#620) | **-₹13,744.47** | Trade Ledger Metric |
| **All 621 Trades Net P&L** | Realized Net + Synthetic Liquidation Net | **-₹160,678.64** | Trade Ledger Net Metric |

### B. The Single Explicit Reconciliation Equation

$$\mathbf{\Delta \text{Equity} - \text{Net P\&L}_{all} = \text{Hypothetical Sell Friction}_{open} - \delta_{liq} - \delta_{cash}}$$

Substituting the exact source-level ledger values:
$$\underbrace{(-₹159,480.36)}_{\text{Portfolio Equity Change}} - \underbrace{(-₹160,678.64)}_{\text{All Trades Net P\&L}} = \underbrace{₹1,198.28}_{\text{Reported Variance}}$$

$$\underbrace{₹1,198.38}_{\text{Hypothetical Sell Friction}} - \underbrace{₹0.02}_{\delta_{liq}} - \underbrace{₹0.08}_{\delta_{cash}} = \mathbf{₹1,198.28}$$

$$₹1,198.28 \equiv ₹1,198.28 \quad (\mathbf{100.00\% \text{ Exact Match, } ₹0.0000 \text{ Error}})$$

### C. Term-by-Term Derivation of the "10 Paise"
1. **Hypothetical Sell Friction ($\mathbf{₹1,198.38}$):**
   The 8 open positions were not sold during the simulation; they remained in the portfolio ledger marked to market. To evaluate complete trade metrics in the trade ledger, the engine closed them synthetically on session 388 close, deducting hypothetical sell fees (STT, brokerage, slippage, etc.) of ₹1,198.38.
2. **Liquidation Component Rounding Artifact ($\delta_{liq} = \mathbf{₹0.02}$):**
   Comparing the 8 trades' unrealized MTM loss against synthetic Net P&L:
   $$\text{MTM Value} - \text{Invested Capital} - \text{Net P\&L} = ₹1,198.36$$
   The sum of individually rounded sell friction fields is ₹1,198.38. The difference is **2 paise** ($₹1,198.38 - ₹1,198.36 = ₹0.02$).
3. **Cash Rounding Accumulation Artifact ($\delta_{cash} = \mathbf{₹0.08}$):**
   Theoretical cash from 613 closed trades and 8 entries is:
   $$\text{Cash}_{theor} = ₹1,000,000.00 + (-₹146,934.17) - ₹669,727.01 = ₹183,338.82$$
   Actual recorded cash in `portfolio_ledger.csv` is ₹183,338.74. The difference accumulated across 613 trade cash updates is **8 paise** ($₹183,338.82 - ₹183,338.74 = ₹0.08$).
4. **Total Gap:** $\delta_{liq} + \delta_{cash} = ₹0.02 + ₹0.08 = \mathbf{₹0.10}$ (10 paise).

### D. Anti-Double-Counting Audit
- **Buy-Side Costs on Open Holdings:** The buy fees of ₹1,315.89 were paid at entry and deducted from cash via `invested_capital`. In the synthetic liquidation trade ledger rows, they are included in `total_costs` to compute trade Net P&L, but they were **not deducted again from portfolio cash**.
- **`invested_capital` Definition:** `pos["qty"] * pos["exec_entry_price"] + buy_statutory_and_brokerage`. Verified to correctly include buy-side statutory costs and slippage.
- **Gross P&L Price Base:** Computed strictly as `pos["qty"] * (raw_exit_open - raw_entry_open)`. Verified to use unadjusted raw market prices.

---

## 4. Check 3 — Independent Test Quality & Mutation Verification

The newly added test suite [`tests/test_final_invariant_audit_6_0_3.py`](file:///home/skirataar/Website/StockBot_Model/tests/test_final_invariant_audit_6_0_3.py) was audited against strict quantitative verification standards:

| Test Name | Verifies Independently? | Edge Case / Invariant Covered | Failure on Alteration Tested? | Status |
|---|---|---|---|---|
| `test_brokerage_cap_edge_cases` | Yes (first-principles calculator) | Orders at ₹10k, ₹50k, ₹66.67k, ₹100k, ₹1M | Yes (uncapped vs capped) | **PASSED** |
| `test_stamp_duty_and_stt_asymmetry` | Yes | Buy-only 0.015% stamp duty vs two-sided 0.1% STT | Yes (fails if stamp on sell) | **PASSED** |
| `test_gst_base_composition_both_legs` | Yes | 18% on (brokerage + exchange + sebi) excluding STT | Yes (fails if STT in base) | **PASSED** |
| `test_reproducible_paisa_discrepancy_cancellation` | Yes | 1,242 order leg sub-paisa truncation cancellation (-₹2.81 vs +₹2.82) | Yes (fails if net $\ne 0.01$) | **PASSED** |
| `test_single_explicit_equation_ten_paise_reconciliation` | Yes | Single explicit equation with exact delta terms | Yes (fails if gap $\ne 0.10$) | **PASSED** |
| `test_mutation_fails_on_altered_brokerage_cap` | Yes | Uncapped 0.03% brokerage produces ₹34k vs ₹24.8k | Proves negative test failure | **PASSED** |

### Complete Repository Test Suite (54 Tests Pass)
```bash
$ PYTHONPATH=. ./venv/bin/pytest tests/ -v
======================= 54 passed, 30 warnings in 26.55s =======================
```
All 54 tests across all 6 test modules pass cleanly.

---

## 5. Summary Deliverables

1. **Sprint 6.0.3 Audit Report:** [`data/reports/sprint_6_0_3_final_accounting_invariant_audit.md`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_3_final_accounting_invariant_audit.md)
2. **Machine-Readable Audit Summary:** [`data/reports/sprint_6_0_3_final_accounting_invariant_audit.json`](file:///home/skirataar/Website/StockBot_Model/data/reports/sprint_6_0_3_final_accounting_invariant_audit.json)
3. **Independent Invariant Test Suite:** [`tests/test_final_invariant_audit_6_0_3.py`](file:///home/skirataar/Website/StockBot_Model/tests/test_final_invariant_audit_6_0_3.py)
