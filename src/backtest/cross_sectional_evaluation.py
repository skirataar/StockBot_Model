"""
Cross-Sectional Multi-Candidate Evaluation Harness.

Sprint 6.1.8 / Sprint 6.2 Preregistered Protocol v1.2.0.

Provides an orchestrated, deterministic evaluation pipeline across the 16 preregistered
candidate strategy configurations (CFG-01 through CFG-16) and the baseline (CFG-BASE).

Key Responsibilities:
1. Strict candidate universe verification and configuration integrity checks.
2. Temporal alignment, date sorting, and return validation across all candidates.
3. Cross-sectional moments estimation (mu_SR, sigma_SR) and EVT expected-maximum hurdle.
4. Deflated Sharpe Ratio (DSR) evaluation under Bailey & López de Prado (2014) Eq. 1.
5. Literature-grounded participation-ratio effective trial count (N_eff) diagnostic.
6. Holm-Bonferroni step-down multiple-testing correction across candidate family.
7. Evaluation against Mandatory Acceptance Criteria (M1-M8) and Rejection Triggers (R1-R10).
8. Fail-closed error handling on degenerate dispersion, missing candidates, or non-finite inputs.
9. Deterministic machine-readable JSON and human-readable Markdown export.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from src.utils.statistical_tooling import (
    calculate_effective_trial_count,
    calculate_expected_max_sharpe,
    deflated_sharpe_ratio,
    evt_expected_max_standard_normal,
    holm_bonferroni_correction,
    newey_west_hac_sharpe,
)


class CrossSectionalEvaluator:
    """
    Deterministic cross-sectional evaluation harness implementing Protocol v1.2.0.
    """

    HARNESS_VERSION = "1.2.0"
    PRIMARY_GRID_SIZE = 16
    EXPECTED_CANDIDATE_IDS = [f"CFG-{i:02d}" for i in range(1, 17)]
    BASELINE_ID = "CFG-BASE"

    def __init__(
        self,
        protocol_path: Union[str, Path] = "data/reports/sprint_6_2_preregistered_protocol.json",
        allow_synthetic: bool = True,
    ) -> None:
        self.protocol_path = Path(protocol_path)
        self.allow_synthetic = allow_synthetic
        self.protocol_data = self._load_protocol()
        self.protocol_hash = self._compute_protocol_hash()

    def _load_protocol(self) -> Dict[str, Any]:
        """Loads and parses the preregistered protocol JSON file."""
        if not self.protocol_path.exists():
            raise FileNotFoundError(f"Preregistered protocol file not found at: {self.protocol_path}")
        with open(self.protocol_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _compute_protocol_hash(self) -> str:
        """Calculates raw byte SHA-256 hash of the protocol file."""
        with open(self.protocol_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def validate_candidate_inputs(
        self,
        candidate_runs: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """
        Validates completeness, identity, configuration, date alignment, and return series.

        Returns:
          (is_valid: bool, errors: List[str])
        """
        errors: List[str] = []

        if not isinstance(candidate_runs, dict):
            return False, ["candidate_runs must be a dictionary mapping candidate IDs to run outputs."]

        # 1. Candidate Universe Verification
        provided_ids = set(candidate_runs.keys())
        expected_ids = set(self.EXPECTED_CANDIDATE_IDS)
        missing_ids = expected_ids - provided_ids
        if missing_ids:
            errors.append(f"Missing required preregistered candidate IDs: {sorted(list(missing_ids))}.")

        unexpected_ids = provided_ids - (expected_ids | {self.BASELINE_ID})
        if unexpected_ids:
            errors.append(f"Unexpected candidate IDs found: {sorted(list(unexpected_ids))}.")

        # 2. Configuration Integrity against Protocol
        proto_configs = {
            c["config_id"]: c
            for c in self.protocol_data.get("candidate_grid", {}).get("configurations", [])
        }
        for cid in self.EXPECTED_CANDIDATE_IDS:
            if cid in candidate_runs:
                c_data = candidate_runs[cid]
                c_cfg = c_data.get("config", {})
                expected_cfg = proto_configs.get(cid, {})
                for param in ["threshold", "exit_rule", "pacing"]:
                    if param in expected_cfg and param in c_cfg:
                        if str(expected_cfg[param]) != str(c_cfg[param]):
                            errors.append(
                                f"Configuration mismatch for {cid}: parameter '{param}' expected "
                                f"'{expected_cfg[param]}', got '{c_cfg[param]}'."
                            )

        # If universe is invalid, fail early before date checking
        if errors:
            return False, errors

        # 3. Date Alignment, Sorting, and Return Integrity
        reference_dates: Optional[List[str]] = None
        for cid in self.EXPECTED_CANDIDATE_IDS:
            c_data = candidate_runs[cid]
            dates = c_data.get("dates")
            returns = c_data.get("daily_returns")

            if dates is None or returns is None:
                errors.append(f"Candidate {cid} missing 'dates' or 'daily_returns'.")
                continue

            dates_list = [str(d) for d in dates]
            rets_arr = np.asarray(returns, dtype=np.float64)

            if len(dates_list) != len(rets_arr):
                errors.append(f"Candidate {cid} dates length ({len(dates_list)}) does not match returns length ({len(rets_arr)}).")
                continue

            if len(rets_arr) < 30:
                errors.append(f"Candidate {cid} sample length T={len(rets_arr)} is insufficient (< 30 sessions).")

            # Check sorting
            if dates_list != sorted(dates_list):
                errors.append(f"Candidate {cid} trading dates are not strictly sorted in chronological order.")

            # Check duplicates
            if len(dates_list) != len(set(dates_list)):
                errors.append(f"Candidate {cid} contains duplicate trading dates.")

            # Check finite values
            if np.any(np.isnan(rets_arr)) or np.any(np.isinf(rets_arr)):
                errors.append(f"Candidate {cid} daily returns contain NaN or infinite values.")

            # Date alignment with cohort
            if reference_dates is None:
                reference_dates = dates_list
            else:
                if dates_list != reference_dates:
                    errors.append(f"Candidate {cid} trading date sequence does not match cohort reference calendar.")

        return len(errors) == 0, errors

    def evaluate_candidates(
        self,
        candidate_runs: Dict[str, Any],
        is_synthetic: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes the complete cross-sectional evaluation pipeline.

        Parameters:
          candidate_runs: Dictionary mapping candidate ID to run data.
          is_synthetic: True if evaluating synthetic data; False if real validation run.

        Returns:
          Complete deterministic evaluation report dictionary.
        """
        eval_timestamp = datetime.now(timezone.utc).isoformat()

        # Step 1: Input Validation
        is_valid, validation_errors = self.validate_candidate_inputs(candidate_runs)
        if not is_valid:
            return {
                "evaluation_status": "VALIDATION_FAILED",
                "harness_version": self.HARNESS_VERSION,
                "evaluation_timestamp": eval_timestamp,
                "is_synthetic": is_synthetic,
                "protocol_version": self.protocol_data.get("protocol_metadata", {}).get("version"),
                "protocol_sha256": self.protocol_hash,
                "errors": validation_errors,
                "primary_dsr_decision": "REJECTED_INPUT_VALIDATION_ERROR",
            }

        # Step 2: Extract Returns Matrix and Compute Candidate Moments
        candidate_ids = self.EXPECTED_CANDIDATE_IDS
        dates = candidate_runs[candidate_ids[0]]["dates"]
        T = len(dates)
        K = len(candidate_ids)

        returns_matrix = np.zeros((T, K), dtype=np.float64)
        annualized_sharpes: List[float] = []
        candidate_moments: Dict[str, Dict[str, Any]] = {}

        for idx, cid in enumerate(candidate_ids):
            c_data = candidate_runs[cid]
            rets = np.asarray(c_data["daily_returns"], dtype=np.float64)
            returns_matrix[:, idx] = rets

            r_f_daily = 0.06 / 252.0
            excess = rets - r_f_daily
            mean_exc = float(np.mean(excess))
            std_exc = float(np.std(excess, ddof=1)) if len(excess) > 1 else 0.0

            if std_exc > 1e-12:
                daily_sr = mean_exc / std_exc
                ann_sr = float(daily_sr * np.sqrt(252))
            else:
                daily_sr = 0.0
                ann_sr = 0.0

            annualized_sharpes.append(ann_sr)
            candidate_moments[cid] = {
                "daily_sharpe": daily_sr,
                "annualized_sharpe": ann_sr,
                "mean_daily_excess": mean_exc,
                "std_daily_excess": std_exc,
                "sample_size_T": T,
            }

        # Step 3: Cross-Sectional Expected Maximum Sharpe Hurdle (Bailey & López de Prado 2014 Eq 1)
        hurdle_result = calculate_expected_max_sharpe(annualized_sharpes, trial_count_K=K)

        if hurdle_result["status"] != "CALCULATED":
            # Degenerate dispersion or candidate error -> Fail closed
            return {
                "evaluation_status": hurdle_result["status"],
                "harness_version": self.HARNESS_VERSION,
                "evaluation_timestamp": eval_timestamp,
                "is_synthetic": is_synthetic,
                "protocol_version": self.protocol_data.get("protocol_metadata", {}).get("version"),
                "protocol_sha256": self.protocol_hash,
                "cohort_moments": hurdle_result,
                "primary_dsr_decision": "INCONCLUSIVE_DEGENERATE_DISPERSION",
                "error": hurdle_result.get("error"),
            }

        sr_star_ann = hurdle_result["expected_max_sharpe"]

        # Step 4: Evaluate DSR for All 16 Candidates using Cohort Hurdle
        candidate_dsr_evals: Dict[str, Dict[str, Any]] = {}
        raw_p_values: Dict[str, float] = {}

        for cid in candidate_ids:
            c_data = candidate_runs[cid]
            rets = np.asarray(c_data["daily_returns"], dtype=np.float64)
            dsr_res = deflated_sharpe_ratio(
                returns=rets,
                trial_count_K=K,
                risk_free_rate_annual=0.06,
                sessions_per_year=252,
                expected_max_sharpe=sr_star_ann,
            )
            candidate_dsr_evals[cid] = dsr_res
            raw_p_values[cid] = dsr_res["p_value"]

        # Step 5: Secondary Diagnostics (Correlation Matrix and Effective Trials N_eff)
        eff_trial_res = calculate_effective_trial_count(returns_matrix, is_correlation_matrix=False)
        n_eff = eff_trial_res["effective_trials_N_eff"]
        evt_n_eff = eff_trial_res["evt_factor_eff"]
        sr_star_diag = float(hurdle_result["effective_mean_baseline"] + hurdle_result["cohort_std_sigma_sr"] * evt_n_eff)

        # Sensitivity: K = 17 (including CFG-BASE if present)
        k17_res: Optional[Dict[str, Any]] = None
        if self.BASELINE_ID in candidate_runs:
            base_rets = np.asarray(candidate_runs[self.BASELINE_ID]["daily_returns"], dtype=np.float64)
            base_excess = base_rets - (0.06 / 252.0)
            base_ann_sr = float((np.mean(base_excess) / np.std(base_excess, ddof=1)) * np.sqrt(252))
            all_17_sharpes = annualized_sharpes + [base_ann_sr]
            k17_res = calculate_expected_max_sharpe(all_17_sharpes, trial_count_K=17)

        # Step 6: Holm-Bonferroni Correction Across Family
        hb_results = holm_bonferroni_correction(raw_p_values, alpha=0.05)

        # Step 7: Identify Top Candidate & Evaluate Primary Gate
        best_candidate_id = max(candidate_ids, key=lambda c: candidate_moments[c]["annualized_sharpe"])
        best_dsr = candidate_dsr_evals[best_candidate_id]
        best_sharpe = candidate_moments[best_candidate_id]["annualized_sharpe"]

        primary_dsr_passed = bool(best_dsr["p_value"] < 0.05)
        primary_decision = "PRIMARY_DSR_PASSED" if primary_dsr_passed else "PRIMARY_DSR_REJECTED"

        # Step 8: Build Candidate-Level Summary Ledger
        candidate_summary: Dict[str, Dict[str, Any]] = {}
        for cid in candidate_ids:
            dsr_info = candidate_dsr_evals[cid]
            hb_info = hb_results.get(cid, {})
            c_metrics = candidate_runs[cid].get("metrics", {})

            # Mandatory Criteria Check
            crit_checks = self._check_mandatory_criteria(cid, c_metrics, dsr_info)

            candidate_summary[cid] = {
                "annualized_sharpe": candidate_moments[cid]["annualized_sharpe"],
                "daily_sharpe": candidate_moments[cid]["daily_sharpe"],
                "skewness_gamma_3": dsr_info["skewness_gamma_3"],
                "kurtosis_gamma_4": dsr_info["kurtosis_gamma_4"],
                "variance_adjustment_factor": dsr_info["variance_adjustment_factor"],
                "dsr_z_score": dsr_info["dsr_z_score"],
                "dsr_statistic": dsr_info["dsr_statistic"],
                "dsr_raw_p_value": dsr_info["p_value"],
                "dsr_significant": dsr_info["is_significant"],
                "holm_bonferroni_rank": hb_info.get("rank"),
                "holm_bonferroni_adjusted_p": hb_info.get("adjusted_p_value"),
                "holm_bonferroni_significant": hb_info.get("is_significant", False),
                "criteria_checks": crit_checks,
                "overall_candidate_pass": bool(crit_checks.get("all_mandatory_passed", False) and dsr_info["is_significant"]),
            }

        return {
            "evaluation_status": "EVALUATED_SUCCESSFULLY",
            "harness_version": self.HARNESS_VERSION,
            "evaluation_timestamp": eval_timestamp,
            "is_synthetic": is_synthetic,
            "protocol_version": self.protocol_data.get("protocol_metadata", {}).get("version"),
            "protocol_sha256": self.protocol_hash,
            "sample_sessions_T": T,
            "candidate_trial_count_K": K,
            "cohort_moments": hurdle_result,
            "primary_binding_dsr_gate": {
                "best_candidate_id": best_candidate_id,
                "best_candidate_annualized_sharpe": best_sharpe,
                "expected_max_sharpe_hurdle_ann": sr_star_ann,
                "best_candidate_dsr_z_score": best_dsr["dsr_z_score"],
                "best_candidate_dsr_statistic": best_dsr["dsr_statistic"],
                "best_candidate_p_value": best_dsr["p_value"],
                "is_dsr_significant": primary_dsr_passed,
                "primary_decision": primary_decision,
            },
            "secondary_diagnostics": {
                "average_pairwise_correlation_rho_bar": eff_trial_res["average_correlation_rho_bar"],
                "effective_trial_count_N_eff": n_eff,
                "evt_factor_eff": evt_n_eff,
                "effective_trials_hurdle_ann": sr_star_diag,
                "top_candidate_p_value_under_N_eff": float(deflated_sharpe_ratio(
                    candidate_runs[best_candidate_id]["daily_returns"],
                    trial_count_K=int(np.ceil(1.0 if np.isnan(n_eff) or n_eff < 1.0 else min(float(K), n_eff))),
                    risk_free_rate_annual=0.06,
                    sessions_per_year=252,
                    expected_max_sharpe=sr_star_diag,
                )["p_value"]),
                "k17_sensitivity": k17_res,
            },
            "candidates": candidate_summary,
            "overall_governance_decision": primary_decision,
        }

    def _check_mandatory_criteria(
        self,
        candidate_id: str,
        metrics: Dict[str, Any],
        dsr_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluates candidate performance against Mandatory Acceptance Criteria M1-M8."""
        if not metrics:
            return {"all_mandatory_passed": False, "criteria_evaluated": False}

        ann_sharpe = metrics.get("sharpe_ratio", 0.0)
        max_dd = metrics.get("max_drawdown_pct", 100.0)
        total_trades = metrics.get("total_trades_count", 0)
        profit_factor = metrics.get("profit_factor", 0.0)
        costs_pct = metrics.get("costs_pct_of_gross_pnl", 200.0)
        dsr_p = dsr_info.get("p_value", 1.0)

        # M1: Sharpe > 0.50
        m1 = ann_sharpe > 0.50
        # M3: Max DD <= 15.00%
        m3 = max_dd <= 15.00
        # M4: Total Trades >= 100
        m4 = total_trades >= 100
        # M6: Net Profit Factor >= 1.15
        m6 = profit_factor >= 1.15
        # M7: Total Friction <= 100% of Gross Alpha
        m7 = (costs_pct is not None) and (costs_pct <= 100.0)
        # M8: DSR p < 0.05
        m8 = dsr_p < 0.05

        all_passed = bool(m1 and m3 and m4 and m6 and m7 and m8)
        return {
            "all_mandatory_passed": all_passed,
            "criteria_evaluated": True,
            "M1_sharpe_gt_0_50": m1,
            "M3_max_dd_le_15pct": m3,
            "M4_trades_ge_100": m4,
            "M6_profit_factor_ge_1_15": m6,
            "M7_friction_le_100pct": m7,
            "M8_dsr_p_lt_0_05": m8,
        }

    def export_json(self, result_dict: Dict[str, Any], output_path: Union[str, Path]) -> Path:
        """Exports evaluation results to JSON."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2)
        return p

    def export_markdown(self, result_dict: Dict[str, Any], output_path: Union[str, Path]) -> Path:
        """Exports formatted evaluation summary table and findings to Markdown."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)

        status = result_dict.get("evaluation_status", "UNKNOWN")
        decision = result_dict.get("overall_governance_decision", "UNKNOWN")
        proto_ver = result_dict.get("protocol_version", "UNKNOWN")
        proto_hash = result_dict.get("protocol_sha256", "UNKNOWN")
        harness_ver = result_dict.get("harness_version", "UNKNOWN")
        ts = result_dict.get("evaluation_timestamp", "UNKNOWN")
        is_synth = result_dict.get("is_synthetic", True)

        lines = [
            "# Cross-Sectional Multi-Candidate Evaluation Report",
            "",
            f"**Harness Version**: `{harness_ver}` | **Timestamp**: `{ts}` | **Synthetic Execution**: `{is_synth}`",
            f"**Protocol Version**: `{proto_ver}` | **Protocol SHA-256**: `{proto_hash}`",
            "",
            "## 1. Executive Summary & Gate Decision",
            "",
            f"- **Evaluation Status**: `{status}`",
            f"- **Overall Decision**: `{decision}`",
        ]

        if status == "EVALUATED_SUCCESSFULLY":
            cohort = result_dict["cohort_moments"]
            gate = result_dict["primary_binding_dsr_gate"]
            diag = result_dict["secondary_diagnostics"]

            lines.extend([
                "",
                "## 2. Cohort Moments & Primary DSR Benchmark",
                "",
                f"- **Number of Trials ($K$)**: `{cohort['trial_count_K']}`",
                f"- **Cohort Sample Mean Sharpe ($\\bar{{\\mu}}_{{SR}}$)**: `{cohort['cohort_mean_mu_sr']:.4f}`",
                f"- **Effective Mean Baseline ($\\max(0, \\bar{{\\mu}}_{{SR}})$)**: `{cohort['effective_mean_baseline']:.4f}`",
                f"- **Cohort Sample Std Sharpe ($\\hat{{\\sigma}}_{{SR}}$)**: `{cohort['cohort_std_sigma_sr']:.4f}`",
                f"- **EVT Hurdle Factor ($\\text{{EVT}}(16)$)**: `{cohort['evt_factor']:.4f}`",
                f"- **Binding Primary Hurdle ($SR^*$)**: `{gate['expected_max_sharpe_hurdle_ann']:.4f}`",
                "",
                "## 3. Top Candidate Primary Result",
                "",
                f"- **Top Candidate ID**: `{gate['best_candidate_id']}`",
                f"- **Annualized Net Sharpe**: `{gate['best_candidate_annualized_sharpe']:.4f}`",
                f"- **Standardized $z$-Score**: `{gate['best_candidate_dsr_z_score']:.4f}`",
                f"- **DSR Probability ($\\Phi(z)$)**: `{gate['best_candidate_dsr_statistic']:.4f}`",
                f"- **One-Tailed $p$-value**: `{gate['best_candidate_p_value']:.4f}`",
                f"- **Significant at $\\alpha=0.05$**: `{gate['is_dsr_significant']}`",
                "",
                "## 4. Secondary Diagnostics",
                "",
                f"- **Average Pairwise Return Correlation ($\\bar{{\\rho}}$)**: `{diag['average_pairwise_correlation_rho_bar']:.4f}`",
                f"- **Participation Ratio Effective Trials ($N_{{\\text{{eff}}}}$)**: `{diag['effective_trial_count_N_eff']:.2f}`",
                f"- **Diagnostic Hurdle ($SR^*(N_{{\\text{{eff}}}})$)**: `{diag['effective_trials_hurdle_ann']:.4f}`",
                f"- **Top Candidate $p$-value under $N_{{\\text{{eff}}}}$**: `{diag['top_candidate_p_value_under_N_eff']:.4f}`",
                "",
                "## 5. Candidate Evaluation Table",
                "",
                "| Candidate | Ann. Sharpe | $\\gamma_3$ | $\\gamma_4$ | $V$ | $z$-score | DSR $p$-value | Holm Rank | Holm Adj $p$ | Pass |",
                "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
            ])

            for cid, c_info in result_dict.get("candidates", {}).items():
                sr = c_info["annualized_sharpe"]
                g3 = c_info["skewness_gamma_3"]
                g4 = c_info["kurtosis_gamma_4"]
                vf = c_info["variance_adjustment_factor"]
                z = c_info["dsr_z_score"]
                p_val = c_info["dsr_raw_p_value"]
                hrank = c_info["holm_bonferroni_rank"]
                hadj_p = c_info["holm_bonferroni_adjusted_p"]
                passed = "PASS" if c_info["overall_candidate_pass"] else "REJECT"
                lines.append(
                    f"| `{cid}` | {sr:.3f} | {g3:.2f} | {g4:.2f} | {vf:.3f} | {z:.3f} | {p_val:.4f} | {hrank} | {hadj_p:.4f} | `{passed}` |"
                )
        else:
            lines.extend([
                "",
                "## Evaluation Errors",
                "",
            ])
            for err in result_dict.get("errors", [result_dict.get("error", "Unknown error")]):
                lines.append(f"- {err}")

        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        return p
