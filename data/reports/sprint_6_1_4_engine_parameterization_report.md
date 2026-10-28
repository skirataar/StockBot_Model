# Sprint 6.1.4 — Backtest Engine Parameterization & Statistical Tooling Implementation Report

**Author Role:** Lead Quantitative Research Engineer & Research Governance Auditor  
**Sprint Identifier:** `SPRINT-6-1-4`  
**Execution Timestamp:** `2026-10-28T21:15:00+05:30`  
**Governance Gate Status:** ✅ **READY FOR SPRINT 6.2 ENGINEERING GATE**  
**Execution Nature:** Engineering, Code Architecture, and Synthetic Unit Testing Only  

---

## 1. Executive Summary & Governance Ruling

Sprint 6.1.4 was commissioned to resolve the three critical technical blockers identified in Sprint 6.1.3 (`BLK-01`, `BLK-02`, and `BLK-03`) that prevented the faithful execution of the frozen Sprint 6.2 experimental protocol. 

In strict adherence to research-governance constraints:
1. **Zero Historical Backtests Executed**: Neither `validation_dataset.parquet` nor `test_dataset.parquet` was evaluated through the backtesting engine. Zero strategy simulations, performance comparisons, or parameter optimizations were conducted.
2. **Research-Exposed Period Preserved**: The test period (`2025-01-01` to `2026-07-22`) remains completely untouched and prohibited.
3. **Artifact Immutability Maintained**: The frozen preregistered protocol (`sprint_6_2_preregistered_protocol.json`), the trained model (`lightgbm.joblib`), the dataset parquets, and historical trade/portfolio ledgers were cryptographically verified and remain unchanged to the exact byte.

### Final Governance Ruling:
```
========================================================================================
FINAL GOVERNANCE DECISION: READY FOR SPRINT 6.2 ENGINEERING GATE
========================================================================================
All three technical blockers (BLK-01, BLK-02, BLK-03) are resolved and mathematically 
verified across 23 new unit tests using synthetic fixtures. The repository is now 
technically capable of executing the frozen Sprint 6.2 validation protocol.
This decision authorizes the engineering gate review; it does NOT automatically 
authorize execution of historical backtests.
========================================================================================
```

---

## 2. Preflight and Post-Sprint Cryptographic Verification

The cryptographic SHA-256 fingerprint of `data/reports/sprint_6_2_preregistered_protocol.json` was verified prior to any code modification and re-verified upon sprint completion:

$$\text{Frozen Protocol SHA-256}: \quad \mathtt{a49361b17e619e88d75cb2b9e5c35b41e767f423a8ee2ffe2237f0450ae4ab8a}$$

| Invariant Scope | File Path | Verified SHA-256 Hash | Status |
| :--- | :--- | :--- | :---: |
| **Preregistered Protocol** | [`data/reports/sprint_6_2_preregistered_protocol.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_2_preregistered_protocol.json) | `a49361b17e619e88d75cb2b9e5c35b41e767f423a8ee2ffe2237f0450ae4ab8a` | ✅ **IMMUTABLE MATCH** |
| **Frozen ML Model** | [`models/lightgbm.joblib`](file:///home/skirataar/StockBot/StockBot_Model/models/lightgbm.joblib) | `41e61760fc31c72095cd2071fdb843657bd76143ed4535f9b247db78e0c73761` | ✅ **IMMUTABLE MATCH** |
| **Validation Dataset** | [`data/processed/validation_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/validation_dataset.parquet) | `a937fde4c039f4e55025a3bb338dd5894879f928efc55fd0a18fbdf43df23cf8` | ✅ **IMMUTABLE MATCH** |
| **Training Dataset** | [`data/processed/training_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/training_dataset.parquet) | `1d39b686f111e8caecb00cf268de7de00b8fe0dfa5d2073a9173bea0e4b2cf56` | ✅ **IMMUTABLE MATCH** |
| **Test Dataset** | [`data/processed/test_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/test_dataset.parquet) | `7f9d0ce56b42a7cc2780f90edb4b27d9bc923847c6778e5ba4c6ebc754915381` | ✅ **IMMUTABLE MATCH** |
| **Historical Trade Ledger** | [`data/reports/trade_ledger.csv`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/trade_ledger.csv) | `f5340b8402c198730d53e4126a8b40463c7cdd832fc0919c1b6bafacf501eeff` | ✅ **IMMUTABLE MATCH** |
| **Historical Portfolio Ledger** | [`data/reports/portfolio_ledger.csv`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/portfolio_ledger.csv) | `f565b8c09b958023a243394bfb6e96887dd3588d44d38623c2b24faa43117f78` | ✅ **IMMUTABLE MATCH** |

---

## 3. Technical Design and Implementation Details

### 3.1 Scope A — Parameterize Entry Threshold (`BLK-02`)

1. **Configuration Interface**:
   Introduced the [`StrategyConfig`](file:///home/skirataar/StockBot/StockBot_Model/src/backtest/event_driven_engine.py#L197-L285) dataclass supporting:
   - `prob_buy_threshold: Optional[float]` (allowed values: $0.0 \le \theta \le 1.0$ or `None`).
   - When `prob_buy_threshold is None` (or `config_id == "CFG-BASE"`), the engine strictly preserves the original baseline argmax logic (`predicted_signal == 1`).
2. **Model Probability Mapping**:
   The engine maps model class probabilities using the canonical LightGBM class list:
   ```python
   classes = list(self.model.classes_)  # [-1, 0, 1]
   buy_class_idx = classes.index(1)
   df_data["prob_buy"] = probs[:, buy_class_idx]
   ```
3. **Threshold Qualification Rule**:
   For candidates with parameter $\theta$, eligibility requires:
   $$\text{Candidate Eligible} \iff P(\text{BUY}) \ge \theta$$
   Equality is explicitly accepted as required by the preregistered protocol.
4. **Input Validation**:
   - `prob_buy_threshold < 0.0`, `> 1.0`, or `np.nan` raises `ValueError`.
   - Non-numeric threshold types raise `TypeError`.
   - Any malformed probability value ($P < 0$, $P > 1$, or `NaN`) encountered in the signal series raises an explicit `ValueError`.
5. **Look-Ahead Prevention**:
   Signals generated at session $t-1$ Close are evaluated for entry strictly at session $t$ Open. Zero same-day or future information is accessible.

---

### 3.2 Scope B — Daily Entry Pacing (`BLK-02`)

1. **Pacing Constraints**:
   Implemented support for:
   - Strict 2-entry daily cap (`max_daily_entries = 2`, e.g., `CFG-11`, `CFG-15`).
   - Strict 3-entry daily cap (`max_daily_entries = 3`, e.g., `CFG-12`).
   - Unconstrained pacing (`max_daily_entries = None`, e.g., `CFG-BASE`, `CFG-01` through `CFG-10`, `CFG-13`, `CFG-14`, `CFG-16`).
2. **Filled Order Counting**:
   The pacing counter `daily_entries_count` tracks **actual filled trades**, not merely eligible signals:
   - Orders rejected due to `MAX_PORTFOLIO_POSITIONS_REACHED` do NOT increment the daily pacing count.
   - Orders rejected due to `ZERO_VOLUME_OR_MARKET_HALT` do NOT increment the daily pacing count.
   - Orders rejected due to `INSUFFICIENT_CASH_FOR_ONE_SHARE` do NOT increment the daily pacing count.
   - When `daily_entries_count >= max_daily_entries`, subsequent candidate orders are rejected with the explicit reason:
     $$\mathtt{"DAILY\_ENTRY\_PACING\_LIMIT\_REACHED"}$$
3. **Deterministic Candidate Priority**:
   Competing BUY signals are ranked deterministically:
   ```python
   buy_candidates.sort(key=lambda x: (-x[1], x[0]))
   ```
   Highest $P(\text{BUY})$ has absolute priority; ties are broken strictly by alphabetical constituent ticker symbol.
4. **Portfolio Invariants Preserved**:
   - Maximum 10 concurrent open positions.
   - Target allocation: 10% of portfolio equity per position.
   - Integer shares only (`int(target_alloc / (open * 1.0005 * 1.002))`).
   - Zero leverage and non-negative cash floor.

---

### 3.3 Scope C — End-of-Day ATR Trailing Exits (`BLK-01`)

1. **ATR Calculation**:
   Implemented [`compute_atr_series()`](file:///home/skirataar/StockBot/StockBot_Model/src/backtest/event_driven_engine.py#L327-L354) matching the exact protocol specification:
   $$\text{TR}_t = \max(\text{High}_t - \text{Low}_t, |\text{High}_t - \text{Close}_{t-1}|, |\text{Low}_t - \text{Close}_{t-1}|)$$
   $$\text{ATR}_{14, t} = \frac{1}{14} \sum_{i=0}^{13} \text{TR}_{t-i}$$
   For session $t=0$, $\text{TR}_0 = \text{High}_0 - \text{Low}_0$. For sessions $t < 13$, $\text{ATR}_{14, t} = \text{NaN}$.
2. **Peak Close State Tracking**:
   Each open position independently maintains its maximum closing price observed since entry:
   $$\text{Peak\_Close}_t = \max(\text{Peak\_Close}_{t-1}, \text{Close}_t)$$
3. **Zero Look-Ahead Close Inspection**:
   At session $t$ Close (15:30 IST):
   $$\text{Stop\_Level}_t = \text{Peak\_Close}_t - m \times \text{ATR}_{14, t} \quad (m \in \{1.5, 2.0, 2.5\})$$
   $$\text{Trigger Condition}: \quad \text{Close}_t \le \text{Stop\_Level}_t$$
   If triggered, an exit order is staged for execution at **session $t+1$ Open** with reason `ATR_TRAILING_STOP`.
4. **Adverse Morning Gap Handling**:
   Execution occurs at session $t+1$ Open:
   $$\text{Fill Price} = \text{Open}_{t+1} \times (1 - \text{slippage})$$
   If $\text{Open}_{t+1} < \text{Stop\_Level}_t$, the full adverse gap is absorbed. Fictitious fills at unattainable stop levels are strictly prohibited.
5. **Warm-Up and Missing Data Fallback**:
   If $\text{ATR}_{14, t}$ is `NaN` (< 14 sessions or missing data), the trailing stop remains inactive, and the position relies safely on the calendar 5-day exit or model SELL signal.
6. **Deterministic Exit Precedence**:
   When multiple exit conditions coincide at session $t$ Close, the engine applies strict deterministic hierarchy:
   1. `ATR_TRAILING_STOP` (Risk management stop; highest precedence)
   2. `EARLY_SELL_SIGNAL` (Model signal deterioration; `predicted_signal == -1`)
   3. `MAX_HOLD_5D` (Scheduled calendar duration limit; `holding_sessions >= 5`)
7. **State Isolation & Reset**:
   Position metadata (`peak_close`, `atr_stop_level`, `staged_exit_reason`) is isolated per position and cleanly purged upon closure.

---

### 3.4 Scope D — Statistical Tooling Module (`BLK-03`)

Created a dedicated module [`src/utils/statistical_tooling.py`](file:///home/skirataar/StockBot/StockBot_Model/src/utils/statistical_tooling.py) implementing three core quantitative procedures:

#### 1. Deflated Sharpe Ratio (DSR) (Bailey & López de Prado, 2014)
- **Null Benchmark**:
  $$\text{SR}^* = \sqrt{2 \ln(K)} \quad (K = 16 \implies \text{SR}^* \approx 2.354820)$$
- **Mertens Non-Normality Variance Factor**:
  $$V = 1 - \hat{\gamma}_3 \hat{\text{SR}}_d + \frac{\hat{\gamma}_4 - 1}{4} \hat{\text{SR}}_d^2$$
  where $\hat{\gamma}_3$ is sample skewness and $\hat{\gamma}_4$ is sample Pearson kurtosis (normal distribution = 3.0).
- **Standardized Test Statistic ($z$)**:
  $$z = \frac{(\hat{\text{SR}}_d - \text{SR}^*_d) \sqrt{T - 1}}{\sqrt{V}} \equiv \frac{(\hat{\text{SR}}_{\text{ann}} - \text{SR}^*) \sqrt{\frac{T - 1}{252}}}{\sqrt{V}}$$
- **DSR & Statistical $p$-value**:
  $$\text{DSR} = \Phi(z), \quad p\text{-value} = 1.0 - \text{DSR} = 1.0 - \Phi(z)$$
  $$\text{Significance Criterion}: \quad p\text{-value} < 0.05 \iff \text{DSR} > 0.95$$

#### 2. Holm-Bonferroni Step-Down FWER Correction
Controls Family-Wise Error Rate at $\alpha = 0.05$ across all $M$ valid candidate comparisons:
1. Sort raw $p$-values: $p_{(1)} \le p_{(2)} \le \dots \le p_{(M)}$.
2. Step-down adjusted $p$-value with cumulative maximum monotonicity constraint:
   $$\tilde{p}_{(k)} = \min\left(1.0, \, \max_{j \le k} \left[ (M - j + 1) \, p_{(j)} \right]\right)$$
3. Deterministic tie-breaking by candidate ID; explicit error flagging (`INVALID_INPUT`) for `NaN` or negative $p$-values.

#### 3. Newey-West / HAC Standard Error Diagnostics
Addresses serial correlation induced by overlapping 5-session holding periods:
- Bartlett kernel weights for lags $l \in \{1, \dots, 5\}$:
  $$w_l = 1 - \frac{l}{6} \quad \left(w = \left[\frac{5}{6}, \frac{4}{6}, \frac{3}{6}, \frac{2}{6}, \frac{1}{6}\right]\right)$$
- HAC Variance of excess returns:
  $$\hat{\sigma}^2_{\text{HAC}} = \hat{\gamma}(0) + 2 \sum_{l=1}^5 \left(1 - \frac{l}{6}\right) \hat{\gamma}(l)$$
- HAC Sharpe standard error inflation factor:
  $$\eta = \sqrt{\frac{\hat{\sigma}^2_{\text{HAC}}}{\hat{\gamma}(0)}}, \quad \text{SE}_{\text{HAC}}(\hat{\text{SR}}_{\text{ann}}) \approx \sqrt{\frac{252}{T}} \times \eta$$

---

## 4. Comprehensive Unit Testing & Verification Results

All tests were executed using **100% synthetic, in-memory fixtures**. No parquet files were loaded during execution.

### Test Execution Command:
```bash
PYTHONPATH=. pytest -v tests/test_sprint_6_1_4_engine_parameterization.py
```

### Results Breakdown (23 / 23 PASSED in 2.33s):
```
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeA_EntryThreshold::test_threshold_equality_and_boundary PASSED [  4%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeA_EntryThreshold::test_baseline_argmax_compatibility PASSED [  8%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeA_EntryThreshold::test_invalid_threshold_rejection PASSED [ 13%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeA_EntryThreshold::test_malformed_probability_input PASSED [ 17%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeB_DailyEntryPacing::test_pacing_2_entry_cap_and_rejections PASSED [ 21%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeB_DailyEntryPacing::test_pacing_3_entry_cap PASSED [ 26%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeB_DailyEntryPacing::test_unconstrained_pacing_baseline PASSED [ 30%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeB_DailyEntryPacing::test_deterministic_priority_ranking_and_tie_breaking PASSED [ 34%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeB_DailyEntryPacing::test_rejected_orders_do_not_increment_daily_entry_count PASSED [ 39%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeC_ATRExits::test_14_period_sma_atr_calculation PASSED [ 43%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeC_ATRExits::test_eod_stop_trigger_and_next_open_execution PASSED [ 47%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeC_ATRExits::test_adverse_gap_down_execution_no_artificial_stop_fill PASSED [ 52%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeC_ATRExits::test_warmup_fallback_no_stop_trigger PASSED [ 56%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeC_ATRExits::test_deterministic_exit_precedence PASSED [ 60%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeC_ATRExits::test_position_state_isolation_and_reset PASSED [ 65%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeD_StatisticalTooling::test_dsr_deterministic_known_values PASSED [ 69%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeD_StatisticalTooling::test_dsr_zero_variance_and_edge_cases PASSED [ 73%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeD_StatisticalTooling::test_holm_bonferroni_step_down_procedure PASSED [ 78%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeD_StatisticalTooling::test_holm_bonferroni_handles_ties_and_invalids PASSED [ 82%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeD_StatisticalTooling::test_newey_west_hac_deterministic_properties PASSED [ 86%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeE_ConfigurationCompatibility::test_load_all_16_protocol_configurations PASSED [ 91%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeE_ConfigurationCompatibility::test_unknown_config_raises_key_error PASSED [ 95%]
tests/test_sprint_6_1_4_engine_parameterization.py::TestScopeE_ConfigurationCompatibility::test_invalid_exit_rule_fails_validation PASSED [100%]
```

### Non-Backtest Regression Verification (23 / 23 PASSED in 6.51s):
Executed previous governance suites to ensure zero regression in protocol or holdout invariants:
```bash
PYTHONPATH=. pytest -v tests/test_sprint_6_1_3_protocol_normalization.py tests/test_sprint_6_1_2_holdout_integrity.py
```
Outcome: **23 passed, 0 failed**.

---

## 5. Technical Blocker Closure Matrix

With the successful completion and verification of Sprint 6.1.4, all three implementation blockers from Sprint 6.1.3 are formally closed:

| Blocker ID | Affected Component | Description | Resolution Artifact & Verification | Status |
| :--- | :--- | :--- | :--- | :---: |
| **`BLK-01`** | `src/backtest/event_driven_engine.py` | Missing ATR calculation, trailing stop tracking, and stop exit staging | `compute_atr_series()`, EOD Close inspection, next-open gap-down execution; verified across 6 unit tests in `TestScopeC_ATRExits`. | ✅ **RESOLVED** |
| **`BLK-02`** | `src/backtest/event_driven_engine.py` | Hardcoded argmax signal (`sig == 1`) and missing daily entry pacing | `StrategyConfig` dataclass, `prob_buy_threshold` filtering, `max_daily_entries` pacing counter; verified across 9 unit tests in `TestScopeA` & `TestScopeB`. | ✅ **RESOLVED** |
| **`BLK-03`** | `src/utils/statistical_tooling.py` | Missing Deflated Sharpe Ratio (DSR), Holm-Bonferroni, and HAC tooling | `deflated_sharpe_ratio()`, `holm_bonferroni_correction()`, `newey_west_hac_sharpe()`; verified across 5 unit tests in `TestScopeD`. | ✅ **RESOLVED** |

---

## 6. Files Created or Modified

1. **[`src/utils/statistical_tooling.py`](file:///home/skirataar/StockBot/StockBot_Model/src/utils/statistical_tooling.py)** (NEW):
   - Implements `deflated_sharpe_ratio`, `holm_bonferroni_correction`, and `newey_west_hac_sharpe`.
2. **[`src/backtest/event_driven_engine.py`](file:///home/skirataar/StockBot/StockBot_Model/src/backtest/event_driven_engine.py)** (MODIFIED):
   - Added `StrategyConfig` dataclass and protocol loading classmethods.
   - Added `compute_atr_series()` and `get_symbol_atr()`.
   - Parameterized `run_simulation()` to accept `strategy_config`, `prob_buy_threshold`, `max_daily_entries`, and `exit_rule`.
   - Added EOD Close trailing stop evaluation, next-open execution, and deterministic exit precedence.
   - Integrated DSR and HAC metrics into `calculate_performance_metrics()`.
3. **[`tests/test_sprint_6_1_4_engine_parameterization.py`](file:///home/skirataar/StockBot/StockBot_Model/tests/test_sprint_6_1_4_engine_parameterization.py)** (NEW):
   - 23 synthetic unit tests covering Scopes A through E.
4. **[`data/reports/sprint_6_1_4_engine_parameterization.json`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_1_4_engine_parameterization.json)** (NEW):
   - Structured JSON audit summary reconciling with this markdown report.
5. **[`data/reports/sprint_6_1_4_engine_parameterization_report.md`](file:///home/skirataar/StockBot/StockBot_Model/data/reports/sprint_6_1_4_engine_parameterization_report.md)** (NEW):
   - This governance and implementation document.

---

## 7. Next Actions

1. Present this report and the passing unit test suite to the quantitative research oversight gate.
2. Formally authorize **Sprint 6.2: Validation-Only Parameter Experimentation**.
3. Under Sprint 6.2, execute the 16 frozen candidate configurations plus `CFG-BASE` strictly against [`data/processed/validation_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/validation_dataset.parquet) (`2023-01-02` to `2024-12-23`).
4. Re-confirm that [`data/processed/test_dataset.parquet`](file:///home/skirataar/StockBot/StockBot_Model/data/processed/test_dataset.parquet) remains unexecuted and prohibited.
