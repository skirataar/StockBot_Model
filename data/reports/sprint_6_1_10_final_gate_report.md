# Sprint 6.1.10 — Final Statistical Gate and Validation-Experiment Preregistration Review

**Date**: 2026-10-29T02:50:00+05:30  
**Role**: Lead Quantitative Research Auditor & Governance Authority  
**Repository**: `StockBot_Model`  
**Audit Verification**: **`SOURCE-VERIFIED READ-ONLY AUDIT`**  
**Final Decision**: **`AUTHORIZED — SPRINT 6.2 VALIDATION-ONLY BACKTESTS MAY BEGIN`**  

---

## 1. Executive Summary & Authorization Decision

This sprint conducted the final pre-experiment governance review following Sprint 6.1.9. The purpose was to independently establish whether the preregistered Sprint 6.2 validation experiment can be formally authorized without compromising statistical validity, research integrity, or holdout governance.

### Formal Authorization Decision
**`AUTHORIZED — SPRINT 6.2 VALIDATION-ONLY BACKTESTS MAY BEGIN`**

All prior blocking defects (`BLK-01` through `BLK-05`, `DEF-01` through `DEF-03`) have been rigorously remediated, mathematically proven, and independently audited. The experiment protocol ([`data/reports/sprint_6_2_preregistered_protocol.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_2_preregistered_protocol.json)) and its versioned freeze ([`data/reports/sprint_6_2_preregistered_protocol_v1_2_0.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_2_preregistered_protocol_v1_2_0.json)) are byte-identical and internally consistent. The execution engine ([`src/backtest/event_driven_engine.py`](file:///home/skirataar/StockBot/StockBot_Model/src/backtest/event_driven_engine.py)) and multi-candidate evaluation harness ([`src/backtest/cross_sectional_evaluation.py`](file:///home/skirataar/StockBot/StockBot_Model/src/backtest/cross_sectional_evaluation.py)) are verified against 23 dedicated synthetic test cases and 94 repository-wide regression tests with zero failures.

> [!IMPORTANT]
> **Scope Boundaries of this Authorization**:
> 1. Authorization applies strictly and exclusively to [`data/processed/validation_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/validation_dataset.parquet) across the preregistered period (`2023-01-02` through `2024-12-23`).
> 2. The 2025–2026 test period remains classified as **`RESEARCH-EXPOSED`** and is **strictly quarantined**. Zero test-set backtests are permitted.
> 3. This authorization is for a validation experiment only. It does not establish that the strategy has demonstrated profitability or trading alpha, and it does not authorize live trading deployment.

---

## 2. Repository Identity and Working-Tree Verification

The canonical repository environment was verified before inspecting any code or test files:

- **Current Working Directory**: `/home/skirataar/StockBot/StockBot_Model`
- **Git Repository Root**: `/home/skirataar/StockBot/StockBot_Model`
- **Git Commit**: `8450e91288c82c4e68c2aacd076c96141a973f96` (`main` branch)
- **Path Discrepancy Reconciliation**: The requested path `/home/skirataar/Website/StockBot_Model` is verified non-existent. The active canonical repository is confirmed to be `/home/skirataar/StockBot/StockBot_Model`.

---

## 3. Inspected Artifacts & Hash Integrity Verification

All file bytes were hashed independently using raw-byte `sha256sum`. Zero historical parquet datasets were loaded.

### 3.1 Protected Baseline Artifacts (100% Immutable Match)
| Artifact Name | Relative Path | Canonical Baseline Hash | Post-Audit Hash | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Frozen ML Model** | [`models/lightgbm.joblib`](file:///home/skirataar/StockBot/StockBot_Model/models/lightgbm.joblib) | `41e61760fc...` | `41e61760fc...` | ✅ **IMMUTABLE MATCH** |
| **Training Dataset** | [`data/processed/training_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/training_dataset.parquet) | `1d39b686f1...` | `1d39b686f1...` | ✅ **IMMUTABLE MATCH** |
| **Validation Dataset** | [`data/processed/validation_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/validation_dataset.parquet) | `a937fde4c0...` | `a937fde4c0...` | ✅ **IMMUTABLE MATCH** |
| **Test Dataset** | [`data/processed/test_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/test_dataset.parquet) | `7f9d0ce56b...` | `7f9d0ce56b...` | ✅ **IMMUTABLE MATCH** |
| **Historical Trade Ledger** | [`data/reports/trade_ledger.csv`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/trade_ledger.csv) | `f5340b8402...` | `f5340b8402...` | ✅ **IMMUTABLE MATCH** |
| **Historical Portfolio Ledger** | [`data/reports/portfolio_ledger.csv`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/portfolio_ledger.csv) | `f565b8c09b...` | `f565b8c09b...` | ✅ **IMMUTABLE MATCH** |
| **Preserved Protocol v1.0.0** | [`data/reports/sprint_6_2_preregistered_protocol_v1_0_0_frozen.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_2_preregistered_protocol_v1_0_0_frozen.json) | `a49361b17e...` | `a49361b17e...` | ✅ **IMMUTABLE MATCH** |

### 3.2 Protocol Byte-Identity Verification
Byte comparison was executed directly between the active protocol and versioned v1.2.0:
```bash
cmp data/reports/sprint_6_2_preregistered_protocol.json data/reports/sprint_6_2_preregistered_protocol_v1_2_0.json
# Result: returncode 0 (PROTOCOLS ARE BYTE-IDENTICAL)
```
- **Active Protocol Hash**: `0384d6a1b9ac7738a92e295fd94bfac113a9a99ce2f399f11ffa5d66164223cb`
- **v1.2.0 Frozen Hash**: `0384d6a1b9ac7738a92e295fd94bfac113a9a99ce2f399f11ffa5d66164223cb`

### 3.3 Core Implementation & Test Artifacts
| Component | Relative File Path | SHA-256 Hash |
| :--- | :--- | :--- |
| **Cross-Sectional Evaluator** | [`src/backtest/cross_sectional_evaluation.py`](file:///home/skirataar/StockBot/StockBot_Model/src/backtest/cross_sectional_evaluation.py) | `8017860e4e0c245928eee4e1c44317036136b2121665734ecfb913795a375b6c` |
| **Statistical Tooling** | [`src/utils/statistical_tooling.py`](file:///home/skirataar/StockBot/StockBot_Model/src/utils/statistical_tooling.py) | `8819d31a1ded2e09dd22be2269730fd22eca05244cc0a79a8f4487b9dbf30b0e` |
| **Backtest Engine** | [`src/backtest/event_driven_engine.py`](file:///home/skirataar/StockBot/StockBot_Model/src/backtest/event_driven_engine.py) | `30d5b11a69d9f2b91580fdd4c9b42eee8e7df865a8ac7138fa059740a7cb41d0` |
| **Dedicated Synthetic Suite** | [`tests/test_sprint_6_1_8_cross_sectional_evaluation.py`](file:///home/skirataar/StockBot/StockBot_Model/tests/test_sprint_6_1_8_cross_sectional_evaluation.py) | `550bf92fc5824480dd070f8d70e4330a767bb1c4f2159324f9989c5283ec4870` |
| **Sprint 6.1.9 Audit Report** | [`data/reports/sprint_6_1_9_independent_verification_report.md`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_1_9_independent_verification_report.md) | `2d8a19e340801dfe143aa745d9633a01bc3ec36494e37bc0c7778a69da051fbf` |
| **Sprint 6.1.9 JSON Report** | [`data/reports/sprint_6_1_9_independent_verification.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_1_9_independent_verification.json) | `edc2f6f979c811c214ff5ff8fe47a13617432bf063fb0ba2034a28c99d6e5017` |

---

## 4. Statistical Decision-Rule Review

The 12 statistical governance requirements specified in Section 4 were systematically verified against Protocol v1.2.0:

1. **Primary Hypothesis**:
   $$H_0: SR \le SR^*_{\text{ann}} \quad \text{vs.} \quad H_1: SR > SR^*_{\text{ann}}$$
   Under $H_0$, the selected candidate's Sharpe ratio is no greater than the expected maximum Sharpe ratio under multiple testing across $K=16$ trials drawn from a normal distribution with cohort mean $\mu_{\text{baseline}}$ and standard deviation $\sigma_{SR}$.
2. **Candidate Selection Procedure**:
   The candidate with the highest Net Annualized Sharpe Ratio ($\widehat{SR}_{\max}$) among the 16 preregistered configurations on the validation dataset (2023-01-02 to 2024-12-23) is evaluated as the primary strategy endpoint.
3. **Observed Sharpe Ratio & Units**:
   Evaluated on daily excess returns $x_t = R_t - r_{f, \text{daily}}$ where $r_{f, \text{daily}} = 0.06/252$. Daily Sharpe $\widehat{SR}_{\text{daily}} = \bar{x}/s_x$. Annualized Sharpe $\widehat{SR}_{\text{ann}} = \widehat{SR}_{\text{daily}}\sqrt{252}$ in units of $\text{year}^{-1/2}$.
4. **Expected-Maximum-Sharpe Hurdle**:
   $$SR^*_{\text{ann}} = \max\left(0.0, \bar{\mu}_{SR}\right) + \hat{\sigma}_{SR} \cdot \text{EVT}(16)$$
   where $\text{EVT}(16) = (1 - \gamma)\Phi^{-1}(1 - 1/16) + \gamma\Phi^{-1}(1 - 1/(16e)) \approx 1.800454$.
5. **Role of Cohort Mean and Standard Deviation**:
   $\bar{\mu}_{SR} = \frac{1}{16}\sum_{k=1}^{16}\widehat{SR}_{\text{ann}, k}$ centers the trial distribution. $\hat{\sigma}_{SR} = \sqrt{\frac{1}{15}\sum_{k=1}^{16}(\widehat{SR}_{\text{ann}, k} - \bar{\mu}_{SR})^2}$ scales the dispersion of the search grid.
6. **Assumptions Behind Expected-Maximum Approximation**:
   Trial Sharpe estimates are approximately Gaussian with mean $\mu_{SR}$ and standard deviation $\sigma_{SR}$, with non-negative pairwise return correlations ($\rho_{ij} \ge 0$).
7. **Zero-Skill Floor as a Governance Choice**:
   The protocol explicitly documents that $\max(0.0, \bar{\mu}_{SR})$ is a **risk governance constraint**, distinct from Bailey & López de Prado (2014) Equation 1 ($\mu_{SR} + \sigma_{SR}\text{EVT}(N)$). It guarantees that an unprofitable cohort average ($\bar{\mu}_{SR} < 0$) cannot generate a negative hurdle that permits false passes.
8. **DSR Probability & p-value Interpretation**:
   $$z = \frac{(\widehat{SR}_{\text{daily}} - SR^*_{\text{daily}})\sqrt{T - 1}}{\sqrt{V}}, \quad \text{DSR} = \Phi(z), \quad p = 1.0 - \text{DSR}$$
   $p$-value represents the probability that an un-skilled strategy sampled from the candidate search space would achieve a Sharpe ratio $\ge \widehat{SR}_{\max}$ purely through selection bias and sampling variation.
9. **Significance Threshold**:
   $p < 0.05 \iff \text{DSR} > 0.95 \iff z > \Phi^{-1}(0.95) \approx 1.644853$.
10. **Multiple-Testing Family Separation**:
    - DSR is the binding primary test for selection bias across the 16 trials on the primary endpoint.
    - Holm–Bonferroni step-down correction is applied across the family of 16 secondary candidate hypotheses to control Family-Wise Error Rate (FWER) at $\alpha = 0.05$.
    - Holm–Bonferroni is NOT combined with or applied twice to DSR.
11. **Treatment of Failed and Degenerate Candidates**:
    - Missing or failed candidates: fail closed (`INVALID_CANDIDATE_SET`).
    - Zero-trade candidates: daily return is 0.0, Sharpe is 0.0, evaluated cleanly.
    - Zero cross-sectional dispersion ($\hat{\sigma}_{SR} < 10^{-6}$): returns status `INCONCLUSIVE_DEGENERATE_DISPERSION`, failing closed.
12. **Limitations from Serial Dependence & Correlation**:
    - Mertens variance accounts for skewness and kurtosis, but assumes serially uncorrelated returns. Autocorrelation induced by up to 5-day holding periods is monitored via mandatory reporting of Newey–West / HAC standard errors with 5 lags.
    - Slepian's lemma bound (fixed $K=16$) is conditionally conservative under non-negative correlations. Effective trials $N_{\text{eff}}$ is evaluated as an audited diagnostic.

---

## 5. Candidate Grid Inventory and Hash Verification

The candidate search universe is fixed to exactly 16 discrete configurations plus the external baseline anchor `CFG-BASE`:

| Config ID | Buy Threshold ($\theta$) | Exit Mechanism | Entry Pacing | Role | Canonical Config SHA-256 (Prefix) |
| :--- | :---: | :---: | :---: | :--- | :---: |
| `CFG-BASE` | `0.334` | `fixed_5d` | `unconstrained` | Baseline argmax reference | `e837f415...` |
| `CFG-01` | `0.35` | `fixed_5d` | `unconstrained` | Threshold sweep low | `463c667f...` |
| `CFG-02` | `0.38` | `fixed_5d` | `unconstrained` | Threshold sweep sub-anchor | `c0ff481d...` |
| `CFG-03` | `0.40` | `fixed_5d` | `unconstrained` | Central experimental anchor | `85e6aa90...` |
| `CFG-04` | `0.42` | `fixed_5d` | `unconstrained` | Threshold sweep moderate | `1f99754f...` |
| `CFG-05` | `0.45` | `fixed_5d` | `unconstrained` | Threshold sweep high | `1204b785...` |
| `CFG-06` | `0.48` | `fixed_5d` | `unconstrained` | Threshold sweep very high | `748c7287...` |
| `CFG-07` | `0.50` | `fixed_5d` | `unconstrained` | Threshold sweep extreme | `bd70a975...` |
| `CFG-08` | `0.40` | `1.5x_ATR` | `unconstrained` | Exit sweep tight ATR | `2380bc4a...` |
| `CFG-09` | `0.40` | `2.0x_ATR` | `unconstrained` | Exit sweep medium ATR | `ec15f30d...` |
| `CFG-10` | `0.40` | `2.5x_ATR` | `unconstrained` | Exit sweep loose ATR | `858e4bd8...` |
| `CFG-11` | `0.40` | `fixed_5d` | `2` | Pacing sweep tight cap | `9ad2880a...` |
| `CFG-12` | `0.40` | `fixed_5d` | `3` | Pacing sweep medium cap | `2dc06ff5...` |
| `CFG-13` | `0.42` | `2.0x_ATR` | `unconstrained` | Interaction threshold + ATR | `af74c4ea...` |
| `CFG-14` | `0.45` | `2.0x_ATR` | `unconstrained` | Interaction high threshold + ATR | `467170ca...` |
| `CFG-15` | `0.45` | `2.0x_ATR` | `2` | Triple interaction paced ATR | `6020acb5...` |
| `CFG-16` | `0.48` | `2.0x_ATR` | `unconstrained` | Interaction very high threshold + ATR | `78cf65b8...` |

---

## 6. Validation-Experiment Execution Scope

The authorized experiment must adhere to the following execution constraints:

1. **Dataset Scope**:
   - Strictly restricted to [`data/processed/validation_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/validation_dataset.parquet).
   - Date range: `2023-01-02` through `2024-12-23` (490 trading sessions, 49 constituent symbols).
2. **Execution Timing & Sizing Rules**:
   - Signal generated at session $t$ Close (15:30 IST); filled at session $t+1$ Open (09:15 IST) with 5 bps slippage.
   - Initial Capital: INR 1,000,000.00.
   - Max concurrent positions: 10 names.
   - Sizing: `target_alloc = min(cash, current_equity * 0.10)`. Integer shares only. Cash floor INR 0.0.
3. **Statutory Delivery Cost Model**:
   - STT: 0.10% buy and sell.
   - Stamp Duty: 0.015% buy leg.
   - NSE Turnover Fee: 0.00297%.
   - SEBI Turnover Fee: 0.0001% (Rs 10/Crore).
   - Brokerage: $\min(0.03\%, \text{Rs } 20.00)$ per order.
   - GST: 18.0% of (Brokerage + Exchange Fee + SEBI Fee).
4. **Candidate Run Pipeline**:
   - Execute all 16 candidate backtests plus `CFG-BASE` independently using [`EventDrivenBacktestEngine`](file:///home/skirataar/StockBot/StockBot_Model/src/backtest/event_driven_engine.py).
   - In individual candidate runs, `expected_max_sharpe=None` will cleanly output status `PENDING_CROSS_SECTIONAL_EVALUATION`.
   - Once all 16 runs are complete, invoke [`CrossSectionalEvaluator`](file:///home/skirataar/StockBot/StockBot_Model/src/backtest/cross_sectional_evaluation.py) to compute cohort moments, evaluate unified DSR statistics, and apply Holm–Bonferroni corrections.

---

## 7. Acceptance Criteria and Automatic Rejection Triggers

The validation experiment is bound by deterministic criteria:

### Mandatory Acceptance Criteria (All Must Pass)
- **`M1_SHARPE_RATIO`**: Net Annualized Sharpe Ratio $> 0.50$.
- **`M2_BENCHMARK_OUTPERFORMANCE`**: Net Cumulative Return $>$ Net Equal-Weight Benchmark Return.
- **`M3_MAX_DRAWDOWN`**: Maximum Drawdown $\le 15.00\%$.
- **`M4_MIN_TOTAL_TRADES`**: Total Completed Trades $\ge 100$.
- **`M5_MIN_ANNUAL_TRADES`**: Completed Trades $\ge 40$ in 2023 AND $\ge 40$ in 2024.
- **`M6_NET_PROFIT_FACTOR`**: Net Profit Factor $\ge 1.15$.
- **`M7_FRICTION_EFFICIENCY`**: Total Friction $\le 100.00\%$ of Gross Alpha (Gross Alpha $> 0$).
- **`M8_DEFLATED_SHARPE`**: DSR $p$-value $< 0.05$ (under $SR^*_{\text{ann}} = \max(0, \bar{\mu}_{SR}) + \hat{\sigma}_{SR}\text{EVT}(16)$).

### Automatic Rejection Triggers (Any Single Trigger Rejects Candidate)
- **`R1`**: Net Annualized Sharpe $\le 0.0$.
- **`R2`**: Net Cumulative Return $\le$ Benchmark Cumulative Return.
- **`R3`**: Maximum Drawdown $> 15.00\%$.
- **`R4`**: Total Trades $< 100$.
- **`R5`**: Completed Trades in 2023 $< 40$ OR in 2024 $< 40$.
- **`R6`**: Net Profit Factor $< 1.15$.
- **`R7`**: Total Friction $> 100\%$ of Gross Alpha OR Gross Alpha $\le 0$.
- **`R8`**: DSR $p$-value $\ge 0.05$ OR DSR undefined/uncomputable.
- **`R9`**: Cash $< 0.0$ on any date OR Concurrent Positions $> 10$.
- **`R10`**: Any mandatory metric is NaN, division-by-zero, or cannot be reliably computed.

---

## 8. Final Authorization Verdict

**`AUTHORIZED — SPRINT 6.2 VALIDATION-ONLY BACKTESTS MAY BEGIN`**

### Summary of Completed Governance Requirements
1. Engine BUY sizing and fee solvency verified (`BLK-04` resolved).
2. Protocol DSR hurdle aligned with Bailey & López de Prado (2014) Eq. 1 with zero-skill governance floor (`BLK-05` / `DEF-01` resolved).
3. Ungrounded correlation heuristic eliminated in favor of fixed $K=16$ bound and $N_{\text{eff}}$ participation ratio diagnostic (`DEF-02` resolved).
4. Obsolete $\sqrt{2\ln K}$ engine fallback eliminated and deterministic multi-candidate evaluation harness implemented (`DEF-03` resolved).
5. All 7 protected baseline artifacts match canonical hashes byte-for-byte.
6. 100% test pass rate across 94 repository tests in synthetic isolation.
7. Zero historical backtests executed; zero parquet datasets accessed.

**Sprint 6.2 validation backtests are hereby formally authorized.**
