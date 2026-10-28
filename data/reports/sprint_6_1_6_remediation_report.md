# Sprint 6.1.6 — Engine Remediation and Preregistered Statistical Protocol Amendment Report

**Author Role:** Senior Quantitative Research Engineer, Statistical Methods Reviewer, and Research Governance Auditor  
**Sprint Identifier:** `SPRINT-6-1-6`  
**Execution Timestamp:** `2026-10-28T21:55:00+05:30`  
**Governance Decision:** ⚖️ **`REMEDIATION COMPLETE — READY FOR INDEPENDENT RE-GATE REVIEW`**  
**Workspace Root:** `/home/skirataar/StockBot/StockBot_Model`  
*(Requested repo path `/home/skirataar/Website/StockBot_Model` resolved to active workspace `/home/skirataar/StockBot/StockBot_Model`)*  

---

## 1. Executive Summary & Governance Overview

Sprint 6.1.6 was commissioned under quantitative research-governance authorization to resolve the two critical blockers identified in Sprint 6.1.5:
1. **`BLK-04-ENGINE-TARGET-ALLOC-NAME-ERROR`**: Engine runtime defect where `run_simulation()` raised `NameError: name 'target_alloc' is not defined` inside the BUY candidate execution loop.
2. **`BLK-05-PROTOCOL-DSR-HURDLE-MISCALIBRATION`**: Protocol statistical defect where the preregistered Deflated Sharpe Ratio (DSR) expected-maximum-Sharpe benchmark hardcoded $\text{SR}^* = \sqrt{2 \ln(16)} \approx 2.355$ without the cross-sectional standard deviation $\sigma_{SR}$ of candidate trial Sharpe ratios required by Bailey & López de Prado (2014), creating an insurmountable hurdle ($\text{Net Sharpe} > 3.54$ to achieve $p < 0.05$) that mathematically guaranteed 100% strategy rejection under Rejection Trigger R8.

### Mandatory Governance Declarations
- **Zero historical backtests** or portfolio simulations were run against real historical market data.
- **Neither [`validation_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/validation_dataset.parquet) nor [`test_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/test_dataset.parquet) was loaded, evaluated, or inspected.**
- **Zero historical candidate performance results were used** to choose thresholds, exit rules, pacing limits, or acceptance criteria.
- **Zero modifications** were made to the frozen LightGBM model, training data, validation data, test data, or historical trade/portfolio ledgers.
- The original v1.0.0 protocol was preserved byte-for-byte in [`data/reports/sprint_6_2_preregistered_protocol_v1_0_0_frozen.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_2_preregistered_protocol_v1_0_0_frozen.json) with SHA-256 `a49361b17e619e88d75cb2b9e5c35b41e767f423a8ee2ffe2237f0450ae4ab8a`.
- Production changes were strictly confined to [`src/backtest/event_driven_engine.py`](file:///home/skirataar/StockBot/StockBot_Model/src/backtest/event_driven_engine.py). Zero unrelated production files were modified.

```
========================================================================================
FINAL GOVERNANCE DECISION: REMEDIATION COMPLETE — READY FOR INDEPENDENT RE-GATE REVIEW
========================================================================================
1. BLK-04 is RESOLVED: target_alloc calculation is restored in event_driven_engine.py.
   The real run_simulation() entry path was tested across 10 in-memory synthetic scenarios
   with zero runtime errors, zero NameErrors, and exact cost/cash accounting.
2. BLK-05 is RESOLVED VIA PROTOCOL AMENDMENT: Protocol v1.1.0 formally incorporates the
   Bailey & Lopez de Prado (2014) cross-sectional standard deviation formulation across
   the K=16 candidate trials. The independent trial bound (EVT=1.8005) provides a
   conservative upper bound on the hurdle, and empirical correlation diagnostics are defined.
3. Protected artifacts, datasets, and frozen models remain 100% cryptographically intact.
4. Sprint 6.2 backtests are NOT AUTHORIZED by this sprint; an independent re-gate review
   (Sprint 6.1.7) must first audit the remediation and issue the final authorization.
========================================================================================
```

---

## 2. Preflight and Post-Change Cryptographic Audit Invariants

All 10 canonical artifacts were verified via SHA-256 hashing before and after remediation:

| Artifact Scope | File Path | Pre-Change SHA-256 | Post-Change SHA-256 | Audit Status |
| :--- | :--- | :--- | :--- | :---: |
| **Engine Source** | [`src/backtest/event_driven_engine.py`](file:///home/skirataar/StockBot/StockBot_Model/src/backtest/event_driven_engine.py) | `9b5f0a5d4e607cb26a06e404908d839edf8c06cb67ca9d2178442571d860539a` | `30d5b11a69d9f2b91580fdd4c9b42eee8e7df865a8ac7138fa059740a7cb41d0` | ✅ **AUTHORIZED MODIFICATION** |
| **Statistical Tooling** | [`src/utils/statistical_tooling.py`](file:///home/skirataar/StockBot/StockBot_Model/src/utils/statistical_tooling.py) | `9e2dc17045e7533a1b70fe3e4ea3cb0cca18ff2addcbefccda418fddc3656e96` | `9e2dc17045e7533a1b70fe3e4ea3cb0cca18ff2addcbefccda418fddc3656e96` | ✅ **IMMUTABLE MATCH** |
| **Preregistered Protocol** | [`data/reports/sprint_6_2_preregistered_protocol.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_2_preregistered_protocol.json) | `a49361b17e619e88d75cb2b9e5c35b41e767f423a8ee2ffe2237f0450ae4ab8a` | `40de4d4cb60cffaa7e4e54fc9602e15019cd5ccdd3f5017ac48cc2ec560ac19a` | ✅ **AUTHORIZED AMENDMENT** |
| **Preserved v1.0.0 Protocol** | [`data/reports/sprint_6_2_preregistered_protocol_v1_0_0_frozen.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_2_preregistered_protocol_v1_0_0_frozen.json) | *(New versioned artifact)* | `a49361b17e619e88d75cb2b9e5c35b41e767f423a8ee2ffe2237f0450ae4ab8a` | ✅ **CANONICAL V1.0.0 PRESERVED** |
| **Frozen ML Model** | [`models/lightgbm.joblib`](file:///home/skirataar/StockBot/StockBot_Model/models/lightgbm.joblib) | `41e61760fc31c72095cd2071fdb843657bd76143ed4535f9b247db78e0c73761` | `41e61760fc31c72095cd2071fdb843657bd76143ed4535f9b247db78e0c73761` | ✅ **IMMUTABLE MATCH** |
| **Validation Dataset** | [`data/processed/validation_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/validation_dataset.parquet) | `a937fde4c039f4e55025a3bb338dd5894879f928efc55fd0a18fbdf43df23cf8` | `a937fde4c039f4e55025a3bb338dd5894879f928efc55fd0a18fbdf43df23cf8` | ✅ **IMMUTABLE MATCH** |
| **Training Dataset** | [`data/processed/training_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/training_dataset.parquet) | `1d39b686f111e8caecb00cf268de7de00b8fe0dfa5d2073a9173bea0e4b2cf56` | `1d39b686f111e8caecb00cf268de7de00b8fe0dfa5d2073a9173bea0e4b2cf56` | ✅ **IMMUTABLE MATCH** |
| **Test Dataset** | [`data/processed/test_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/test_dataset.parquet) | `7f9d0ce56b42a7cc2780f90edb4b27d9bc923847c6778e5ba4c6ebc754915381` | `7f9d0ce56b42a7cc2780f90edb4b27d9bc923847c6778e5ba4c6ebc754915381` | ✅ **IMMUTABLE MATCH** |
| **Historical Trade Ledger** | [`data/reports/trade_ledger.csv`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/trade_ledger.csv) | `f5340b8402c198730d53e4126a8b40463c7cdd832fc0919c1b6bafacf501eeff` | `f5340b8402c198730d53e4126a8b40463c7cdd832fc0919c1b6bafacf501eeff` | ✅ **IMMUTABLE MATCH** |
| **Historical Portfolio Ledger** | [`data/reports/portfolio_ledger.csv`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/portfolio_ledger.csv) | `f565b8c09b958023a243394bfb6e96887dd3588d44d38623c2b24faa43117f78` | `f565b8c09b958023a243394bfb6e96887dd3588d44d38623c2b24faa43117f78` | ✅ **IMMUTABLE MATCH** |

---

## 3. Remediation of BLK-04: Missing Target Allocation in Engine

### 3.1 Defect Analysis & Root Cause
In Sprint 6.1.4, when parameterizing the BUY candidate execution loop in [`src/backtest/event_driven_engine.py`](file:///home/skirataar/StockBot/StockBot_Model/src/backtest/event_driven_engine.py#L605-L612), the sizing line:
```python
target_alloc = min(cash, current_equity * self.max_single_stock_pct)
```
was accidentally omitted when adding daily entry pacing checks. When line 610 executed:
```python
shares = int(target_alloc / (exec_entry_price * 1.002))
```
Python raised a fatal `NameError: name 'target_alloc' is not defined`. Because unit tests in Sprint 6.1.4 tested isolated subroutines and mocked dictionary lookups rather than running `run_simulation()` through the Step B execution loop with BUY signals, this defect escaped detection until the Sprint 6.1.5 end-to-end audit.

### 3.2 Engineering Remediation
1. **Restored Calculation**:
   Inserted `target_alloc = min(cash, current_equity * self.max_single_stock_pct)` directly before share sizing.
   - `current_equity`: Evaluated at the start of the morning session ($Equity_t = Cash_t + \sum_i Qty_i \times Close_{i, t}$).
   - `self.max_single_stock_pct`: 10% maximum portfolio allocation per name.
   - `min(cash, ...)`: Guarantees the allocation never exceeds available cash.
2. **Dynamic Cash Tracking**:
   As orders fill within the candidate loop on the same morning, `cash` decrements by `required_cash = (shares * exec_entry_price) + buy_fees`. Subsequent candidates on that morning evaluate `target_alloc` against the updated remaining `cash`.
3. **Execution Guards**:
   - Zero shares (`shares < 1`): Order rejected with `INSUFFICIENT_CASH_FOR_ONE_SHARE`.
   - Post-fee solvency: If `cash < required_cash`, order rejected with `INSUFFICIENT_CASH_AFTER_EXACT_FEE_CALCULATION`.
   - Rejected orders do **not** decrement available position slots or increment the daily pacing count.
4. **Synthetic Execution Support in `run_simulation()`**:
   Enhanced `run_simulation()` to accept an in-memory `pd.DataFrame` fixture (or `custom_df`), allowing isolated synthetic integration tests without reading parquet files from disk. Also added an empty `trading_dates` guard to gracefully handle zero-session inputs.
5. **DSR Benchmark Plumbing**:
   Added `expected_max_sharpe: Optional[float] = None` to `run_simulation()` and forwarded it to `calculate_performance_metrics()`, enabling passing the empirical cross-sectional hurdle $\text{SR}^*$ during multi-candidate validation evaluation.

```diff
--- a/src/backtest/event_driven_engine.py
+++ b/src/backtest/event_driven_engine.py
@@ -605,6 +605,9 @@
                     continue
 
+                    # Sizing: max 10% of portfolio equity constrained by available cash
+                    target_alloc = min(cash, current_equity * self.max_single_stock_pct)
+
                     # Exec price with slippage (add slippage on buy)
                     exec_entry_price = raw_entry_open * (1.0 + self.slippage_rate)
 
                     # Estimate cost rate ~ 0.20%
                     shares = int(target_alloc / (exec_entry_price * 1.002))
```

---

## 4. Remediation of BLK-05: Formal DSR Protocol Amendment (v1.1.0)

### 4.1 Statistical Method Analysis & Defect Identification
In protocol v1.0.0, the Deflated Sharpe Ratio specification in [`data/reports/sprint_6_2_preregistered_protocol.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_2_preregistered_protocol.json#L308-L309) defined:
$$\text{SR}^* = \sqrt{2 \ln(K)}$$
with $K = 16$.

As established in the Sprint 6.1.5 mathematical audit:
1. $\sqrt{2 \ln(K)}$ is the leading asymptotic term of the extreme value of $K$ **independent standard normal variables $Z_k \sim \mathcal{N}(0, 1)$**. It is a standardized $z$-score, NOT an unscaled Sharpe ratio hurdle.
2. In Bailey & López de Prado (2014) (*The Deflated Sharpe Ratio*, Journal of Portfolio Management, Equation 1):
   $$\mathbb{E}[\max_{k=1,\dots,K} \widehat{\text{SR}}_k] \approx \hat{\sigma}_{SR} \left( (1 - \gamma)\Phi^{-1}\left(1 - \frac{1}{K}\right) + \gamma \Phi^{-1}\left(1 - \frac{1}{Ke}\right) \right)$$
   where:
   - $\hat{\sigma}_{SR} = \sqrt{\mathbb{V}[\{\widehat{\text{SR}}_k\}]}$ is the **cross-sectional sample standard deviation of candidate Sharpe ratios across the $K$ trials**.
   - $\gamma \approx 0.5772156649$ is the Euler-Mascheroni constant.
   - $\Phi^{-1}$ is the inverse standard normal cumulative distribution function.
   - $e \approx 2.7182818285$ is Euler's number.
3. By omitting $\hat{\sigma}_{SR}$ (implicitly setting $\hat{\sigma}_{SR} = 1.0$), protocol v1.0.0 set an unscaled annualized hurdle of $\text{SR}^* = 2.3548$. For sample length $T = 490$ validation sessions ($\sqrt{(T-1)/252} \approx 1.393$), achieving statistical significance ($p < 0.05 \iff z > 1.6449$) required:
   $$\widehat{\text{SR}}_{\text{ann}} > 2.3548 + \frac{1.6449}{1.393} = \mathbf{3.5356}$$
4. In Indian equity cash delivery swing trading, an annualized Sharpe ratio $> 3.54$ is economically unattainable with statutory taxes (0.1% STT on both buy and sell legs). Combined with Rejection Trigger R8 ($p \ge 0.05 \implies \text{rejection}$), this ensured **100% of candidate configurations would be rejected**, creating an irreconcilable conflict with Mandatory Acceptance Criterion M1 ($\text{Net Sharpe} > 0.50$).

### 4.2 Amended Formulation in Protocol v1.1.0
The protocol has been formally amended in [`data/reports/sprint_6_2_preregistered_protocol.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_2_preregistered_protocol.json) to specify:

1. **Annualized Null Hurdle**:
   $$\text{SR}^*_{\text{ann}} = \hat{\sigma}_{SR} \left( (1 - \gamma)\Phi^{-1}\left(1 - \frac{1}{K}\right) + \gamma \Phi^{-1}\left(1 - \frac{1}{Ke}\right) \right)$$
   For $K = 16$:
   $$\text{EVT}(16) = (1 - 0.577216)\Phi^{-1}(1 - 1/16) + 0.577216\,\Phi^{-1}(1 - 1/(16e)) = \mathbf{1.800454}$$
   Therefore:
   $$\text{SR}^*_{\text{ann}} = 1.800454 \times \hat{\sigma}_{SR}$$

2. **Cross-Sectional Dispersion Estimation**:
   $\hat{\sigma}_{SR}$ is the empirical sample standard deviation of the 16 candidate validation annualized Net Sharpe ratios:
   $$\hat{\sigma}_{SR} = \sqrt{\frac{1}{16 - 1} \sum_{k=1}^{16} (\widehat{\text{SR}}_{\text{ann}, k} - \bar{\text{SR}})^2}$$
   computed upon completion of the Sprint 6.2 validation backtests. If $\hat{\sigma}_{SR} = 0$ or $K < 2$, $\text{SR}^*_{\text{ann}}$ defaults to $0.0$, reducing DSR to the Probabilistic Sharpe Ratio (PSR) testing against zero alpha.

3. **Daily Scale Scaling**:
   $$\text{SR}^*_{\text{daily}} = \frac{\text{SR}^*_{\text{ann}}}{\sqrt{252}}$$

4. **Standardized Test Statistic ($z$) & DSR**:
   $$z = \frac{(\widehat{\text{SR}}_{\text{daily}} - \text{SR}^*_{\text{daily}})\sqrt{T - 1}}{\sqrt{V}} \equiv \frac{(\widehat{\text{SR}}_{\text{ann}} - \text{SR}^*_{\text{ann}})\sqrt{\frac{T - 1}{252}}}{\sqrt{V}}$$
   where Mertens (2002) asymptotic variance factor on the daily frequency is:
   $$V = 1 - \hat{\gamma}_3 \widehat{\text{SR}}_{\text{daily}} + \frac{\hat{\gamma}_4 - 1}{4} \widehat{\text{SR}}_{\text{daily}}^2$$
   $$\text{DSR} = \Phi(z), \quad p\text{-value} = 1.0 - \text{DSR}$$
   Significance criterion: $p < 0.05$ (Trigger R8 fires if $p \ge 0.05$).

### 4.3 Trial Universe and Dependence Assumptions
- **Candidate Trial Universe ($K=16$)**: The 16 configurations (`CFG-01` through `CFG-16`) form the exact candidate search grid. `CFG-BASE` is an external historical reference anchor from Sprint 6.0 and is excluded from the candidate selection search space.
- **Sensitivity Trial Universe ($K=17$)**: As an audited sensitivity diagnostic, Sprint 6.2 reports will also compute DSR using $K=17$ ($\text{EVT}(17) = 1.828094$).
- **Conservative Independence Bound**: Under extreme value theory for multivariate normals with positive pairwise correlation $\bar{\rho} > 0$ (Berman 1962, Bailey & López de Prado 2014):
  $$\mathbb{E}[\max_{k=1,\dots,K} X_k] = \sqrt{1 - \bar{\rho}}\,\, \mathbb{E}[\max_{k=1,\dots,K} Z_k] \le \mathbb{E}[\max_{k=1,\dots,K} Z_k]$$
  Assuming independent trials ($\bar{\rho} = 0$, multiplier $= 1.0$) imposes the **strictest, most conservative multiple-testing penalty** against false discoveries.
- **Empirical Correlation Diagnostic**: Sprint 6.2 diagnostics will calculate the full $16 \times 16$ correlation matrix of candidate daily returns, reporting average correlation $\bar{\rho}$ and the correlation-adjusted hurdle $\text{SR}^*_{\text{corr}} = \hat{\sigma}_{SR}\sqrt{1 - \bar{\rho}}\times 1.8005$ for full transparency.

---

## 5. Synthetic Integration and Regression Test Execution

A comprehensive test suite was executed in [`tests/test_sprint_6_1_6_remediation.py`](file:///home/skirataar/StockBot/StockBot_Model/tests/test_sprint_6_1_6_remediation.py):

```bash
python3 -m pytest -v tests/test_sprint_6_1_6_remediation.py
```

### 5.1 Test Results Summary (25/25 Passed)

| Scope | Test Name | Scenario Description | Outcome |
| :--- | :--- | :--- | :---: |
| **BLK-04 Engine** | `test_single_eligible_buy_candidate` | 1 BUY signal reaches sizing, fills 987 shares, no NameError | ✅ **PASSED** |
| **BLK-04 Engine** | `test_multiple_candidates_deterministic_priority` | Deterministic sorting: highest `prob_buy`, tie-break alphabetical | ✅ **PASSED** |
| **BLK-04 Engine** | `test_zero_share_quantity_rejected` | Share price ₹2M with ₹100k cap -> `shares < 1` rejected cleanly | ✅ **PASSED** |
| **BLK-04 Engine** | `test_insufficient_available_cash` | Cash ₹99.10 < required cash ₹99.20 -> rejected post-fee solvency | ✅ **PASSED** |
| **BLK-04 Engine** | `test_single_stock_allocation_cap_enforcement` | Sizing strictly obeys 10% portfolio equity cap (₹100k) | ✅ **PASSED** |
| **BLK-04 Engine** | `test_daily_entry_pacing_and_rejections` | Daily cap 2: halted symbol rejected; 2 filled; 4th capped; slots preserved | ✅ **PASSED** |
| **BLK-04 Engine** | `test_transaction_cost_and_cash_accounting` | Statutory fees and slippage reconcile to exact penny | ✅ **PASSED** |
| **BLK-04 Engine** | `test_empty_candidate_case` | Zero-signal input runs without index out of range error | ✅ **PASSED** |
| **BLK-04 Engine** | `test_no_eligible_buy_candidates` | Signals below threshold bypass entries cleanly | ✅ **PASSED** |
| **BLK-04 Engine** | `test_full_synthetic_lifecycle_and_termination` | Entry -> holding -> EOD ATR trailing stop exit -> clean liquidation | ✅ **PASSED** |
| **BLK-05 DSR** | `test_zero_mean_synthetic_series` | Zero excess return -> DSR low, $p > 0.05$ (insignificant) | ✅ **PASSED** |
| **BLK-05 DSR** | `test_positive_mean_synthetic_series` | High Sharpe series passes amended hurdle $\text{SR}^* = 0.36$ ($p < 0.05$) | ✅ **PASSED** |
| **BLK-05 DSR** | `test_negative_mean_synthetic_series` | Negative Sharpe series rejected ($p > 0.95$) | ✅ **PASSED** |
| **BLK-05 DSR** | `test_skewed_synthetic_series` | Negative skewness increases variance factor $V > 1.0$ | ✅ **PASSED** |
| **BLK-05 DSR** | `test_heavy_tailed_synthetic_series` | $t(5)$ kurtosis $\gamma_4 > 4.0$ contributes positively to quadratic term | ✅ **PASSED** |
| **BLK-05 DSR** | `test_constant_return_series` | Zero variance handled gracefully without division by zero | ✅ **PASSED** |
| **BLK-05 DSR** | `test_too_short_series` | Sample size $T < 2$ raises explicit `ValueError` | ✅ **PASSED** |
| **BLK-05 DSR** | `test_nan_and_infinite_values` | `NaN` / `inf` in returns raises explicit `ValueError` | ✅ **PASSED** |
| **BLK-05 DSR** | `test_daily_vs_annualized_sharpe_consistency` | Daily vs annualized $z$-score scaling exact identity verified | ✅ **PASSED** |
| **BLK-05 DSR** | `test_dsr_pvalue_interpretation` | Standard normal survival function identity $p = 1 - \Phi(z)$ verified | ✅ **PASSED** |
| **BLK-05 DSR** | `test_expected_max_sharpe_bailey_lopez_de_prado` | EVT expansion factor $\text{EVT}(16) = 1.800454$ verified | ✅ **PASSED** |
| **BLK-05 DSR** | `test_trial_count_handling_k16_vs_k17` | $K=16$ (1.8005) vs $K=17$ (1.8281) sensitivity verified | ✅ **PASSED** |
| **BLK-05 DSR** | `test_dependence_and_correlation_bound` | Independent trial hurdle proven conservative upper bound for $\bar{\rho} > 0$ | ✅ **PASSED** |
| **BLK-05 DSR** | `test_holm_bonferroni_correction_and_monotonicity` | Step-down procedure preserves non-decreasing adjusted $p$-values | ✅ **PASSED** |
| **BLK-05 DSR** | `test_newey_west_hac_reference_comparison` | Bartlett kernel and HAC variance match independent Python reference | ✅ **PASSED** |

### 5.2 Broader Regression Suites Verified
- [`tests/test_sprint_6_1_4_engine_parameterization.py`](file:///home/skirataar/StockBot/StockBot_Model/tests/test_sprint_6_1_4_engine_parameterization.py): **23/23 PASSED**
- [`tests/test_sprint_6_1_3_protocol_normalization.py`](file:///home/skirataar/StockBot/StockBot_Model/tests/test_sprint_6_1_3_protocol_normalization.py): **14/14 PASSED**
- [`tests/test_sprint_6_1_2_holdout_integrity.py`](file:///home/skirataar/StockBot/StockBot_Model/tests/test_sprint_6_1_2_holdout_integrity.py): **9/9 PASSED**
- **Total Tests Across All Isolated Suites:** **71/71 PASSED (100%)**

---

## 6. Scope Compliance & Governance Limitations

1. **Strict Research-Governance Adherence:**
   - No historical backtest was executed.
   - Neither `validation_dataset.parquet` nor `test_dataset.parquet` was accessed or evaluated.
   - The frozen LightGBM model was not loaded for prediction or retrained.
   - Historical trade and portfolio ledgers were preserved untouched.
   - No claim of profitability or market edge is made.
2. **Remaining Governance Boundaries:**
   - Sprint 6.1.6 is strictly an engineering remediation and protocol amendment sprint.
   - **Sprint 6.2 backtests are NOT AUTHORIZED by this sprint.**
   - An independent re-gate review (Sprint 6.1.7) must formally audit the remediated code, amended protocol, and test results to issue the final `READY FOR SPRINT 6.2 VALIDATION BACKTESTS` ruling.

---

## 7. Deliverables Generated

1. Markdown Report: [`data/reports/sprint_6_1_6_remediation_report.md`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_1_6_remediation_report.md)
2. JSON Summary: [`data/reports/sprint_6_1_6_remediation.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_1_6_remediation.json)
3. Preserved v1.0.0 Protocol: [`data/reports/sprint_6_2_preregistered_protocol_v1_0_0_frozen.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_2_preregistered_protocol_v1_0_0_frozen.json)
4. Amended v1.1.0 Protocol: [`data/reports/sprint_6_2_preregistered_protocol.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_2_preregistered_protocol.json)
5. Comprehensive Test Suite: [`tests/test_sprint_6_1_6_remediation.py`](file:///home/skirataar/StockBot/StockBot_Model/tests/test_sprint_6_1_6_remediation.py)

---

## 8. Next Recommended Action

**Commission Sprint 6.1.7 — Independent Re-Gate Audit & Authorization Review for Sprint 6.2 Validation Experiments.**  
Once Sprint 6.1.7 verifies that `BLK-04` and `BLK-05` are satisfactorily resolved and all cryptographic invariants remain intact, formal authorization for Sprint 6.2 validation backtests can be granted.
