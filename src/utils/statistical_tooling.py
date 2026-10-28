"""
Statistical Tooling Module for Sprint 6.1.8 / Sprint 6.2 Experiment Protocol (v1.2.0).

Implements mathematically rigorous, independently verifiable statistical procedures
specified in the preregistered protocol (sprint_6_2_preregistered_protocol.json):
1. Deflated Sharpe Ratio (DSR) (Bailey & López de Prado, 2014)
2. Extreme Value Theory (EVT) Expected Maximum Sharpe Benchmark Calculation
3. Participation Ratio / Kirchhoff Effective Number of Independent Trials (N_eff)
4. Holm-Bonferroni Multiple-Comparison Correction Step-Down Procedure
5. Newey-West / HAC Standard Error and Autocorrelation Diagnostics (max_lags=5)
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


def evt_expected_max_standard_normal(K: Union[int, float]) -> float:
    """
    Computes the analytical expected maximum of K independent standard normal variates
    using the asymptotic Extreme Value Theory (EVT) Gumbel-type quantile approximation:
        EVT(K) = (1 - gamma) * Phi^{-1}(1 - 1/K) + gamma * Phi^{-1}(1 - 1/(K * e))
    where gamma ~ 0.5772156649 is the Euler-Mascheroni constant and e ~ 2.718281828.
    Reference: Bailey and López de Prado (2014), Eq. 1.

    Parameters:
      K: Number of trials (can be integer or continuous effective trial count >= 1.0).

    Returns:
      Expected maximum of standard normal variates (float).
    """
    if K <= 1.0:
        return 0.0

    gamma = 0.5772156649015329
    e_const = np.e

    q1 = 1.0 - (1.0 / float(K))
    q2 = 1.0 - (1.0 / (float(K) * e_const))

    # Bound quantiles safely away from 1.0 for numerical stability
    q1 = min(max(q1, 1e-12), 1.0 - 1e-12)
    q2 = min(max(q2, 1e-12), 1.0 - 1e-12)

    z1 = float(scipy_stats.norm.ppf(q1))
    z2 = float(scipy_stats.norm.ppf(q2))

    return float((1.0 - gamma) * z1 + gamma * z2)


def calculate_expected_max_sharpe(
    candidate_annualized_sharpes: Union[List[float], np.ndarray],
    trial_count_K: Optional[int] = 16,
) -> Dict[str, Any]:
    """
    Computes the Bailey and López de Prado (2014) Eq. 1 Expected Maximum Sharpe Ratio:
        SR_star_ann = max(0.0, mu_SR) + sigma_SR * EVT(K)
    under the preregistered Sprint 6.2 protocol v1.2.0.

    Degeneracy Handling:
      - If sigma_SR < 1e-6: returns status 'INCONCLUSIVE_DEGENERATE_DISPERSION'.
      - If length != trial_count_K: returns status 'INVALID_CANDIDATE_COUNT'.
      - If non-finite values present: returns status 'NON_FINITE_CANDIDATE_SHARPES'.
      - If K < 2: returns status 'INSUFFICIENT_TRIALS'.

    Parameters:
      candidate_annualized_sharpes: Array-like of annualized net Sharpe ratios for candidate trials.
      trial_count_K: Expected number of candidate trials (default 16).

    Returns:
      Dictionary containing cohort moments, EVT factor, SR_star_ann, and status.
    """
    arr = np.asarray(candidate_annualized_sharpes, dtype=np.float64)
    if arr.ndim != 1:
        arr = arr.ravel()

    K = len(arr)
    if trial_count_K is not None and K != trial_count_K:
        return {
            "cohort_mean_mu_sr": float(np.mean(arr)) if K > 0 else np.nan,
            "effective_mean_baseline": np.nan,
            "cohort_std_sigma_sr": np.nan,
            "evt_factor": np.nan,
            "expected_max_sharpe": np.nan,
            "trial_count_K": K,
            "status": "INVALID_CANDIDATE_COUNT",
            "error": f"Expected {trial_count_K} candidate Sharpe ratios, but received {K}.",
        }

    if K < 2:
        return {
            "cohort_mean_mu_sr": float(arr[0]) if K == 1 else np.nan,
            "effective_mean_baseline": np.nan,
            "cohort_std_sigma_sr": np.nan,
            "evt_factor": np.nan,
            "expected_max_sharpe": np.nan,
            "trial_count_K": K,
            "status": "INSUFFICIENT_TRIALS",
            "error": f"Trial count K={K} must be at least 2 to compute cross-sectional dispersion.",
        }

    if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
        return {
            "cohort_mean_mu_sr": np.nan,
            "effective_mean_baseline": np.nan,
            "cohort_std_sigma_sr": np.nan,
            "evt_factor": np.nan,
            "expected_max_sharpe": np.nan,
            "trial_count_K": K,
            "status": "NON_FINITE_CANDIDATE_SHARPES",
            "error": "Candidate Sharpe ratios contain NaN or infinite values.",
        }

    mu_sr = float(np.mean(arr))
    sigma_sr = float(np.std(arr, ddof=1))

    # Check for degenerate / zero dispersion
    if sigma_sr < 1e-6:
        return {
            "cohort_mean_mu_sr": mu_sr,
            "effective_mean_baseline": max(0.0, mu_sr),
            "cohort_std_sigma_sr": sigma_sr,
            "evt_factor": float(evt_expected_max_standard_normal(K)),
            "expected_max_sharpe": np.nan,
            "trial_count_K": K,
            "status": "INCONCLUSIVE_DEGENERATE_DISPERSION",
            "error": f"Cross-sectional Sharpe dispersion sigma_SR={sigma_sr:.2e} < 1e-6 (near-zero dispersion); cannot establish EVT hurdle.",
        }

    evt_k = evt_expected_max_standard_normal(K)
    mu_baseline = max(0.0, mu_sr)
    sr_star = float(mu_baseline + sigma_sr * evt_k)

    return {
        "cohort_mean_mu_sr": mu_sr,
        "effective_mean_baseline": mu_baseline,
        "cohort_std_sigma_sr": sigma_sr,
        "evt_factor": evt_k,
        "expected_max_sharpe": sr_star,
        "trial_count_K": K,
        "status": "CALCULATED",
        "error": None,
    }


def calculate_effective_trial_count(
    returns_or_corr_matrix: Union[np.ndarray, pd.DataFrame],
    is_correlation_matrix: bool = False,
) -> Dict[str, Any]:
    """
    Computes the literature-grounded effective number of independent trials (N_eff)
    from the candidate return correlation matrix via the Participation Ratio (Breuer / Kirchhoff):
        N_eff = K^2 / sum_{i=1}^K sum_{j=1}^K rho_{ij}^2
    where rho_{ij} are the pairwise return correlation coefficients.

    Properties:
      - Uncorrelated trials (rho_ij = 0 for i!=j): sum(rho_ij^2) = K => N_eff = K^2 / K = K.
      - Perfectly correlated trials (rho_ij = 1 for all i,j): sum(rho_ij^2) = K^2 => N_eff = 1.
      - For any valid correlation matrix, 1.0 <= N_eff <= K.

    Parameters:
      returns_or_corr_matrix: T x K array of daily returns OR K x K correlation matrix.
      is_correlation_matrix: True if the input is already a K x K correlation matrix.

    Returns:
      Dictionary containing K, rho_bar, N_eff, EVT(N_eff), and correlation matrix.
    """
    mat = np.asarray(returns_or_corr_matrix, dtype=np.float64)
    if is_correlation_matrix:
        C = mat.copy()
    else:
        if mat.ndim != 2:
            raise ValueError(f"Return matrix must be 2D (T sessions x K candidates), got shape {mat.shape}.")
        if np.any(np.isnan(mat)) or np.any(np.isinf(mat)):
            raise ValueError("Return matrix contains NaN or infinite values.")
        with np.errstate(divide="ignore", invalid="ignore"):
            C = np.corrcoef(mat, rowvar=False)

    if C.ndim != 2 or C.shape[0] != C.shape[1]:
        raise ValueError(f"Correlation matrix must be square (K x K), got shape {C.shape}.")

    K = C.shape[0]
    if K < 2:
        return {
            "candidate_count_K": K,
            "average_correlation_rho_bar": 0.0,
            "effective_trials_N_eff": float(K),
            "evt_factor_eff": 0.0,
            "correlation_matrix": C.tolist(),
            "status": "CALCULATED",
        }

    # Handle any zero-variance columns producing NaNs in correlation matrix
    C = np.nan_to_num(C, nan=0.0)
    np.fill_diagonal(C, 1.0)
    
    # Off-diagonal average correlation
    mask_off_diag = ~np.eye(K, dtype=bool)
    rho_bar = float(np.mean(C[mask_off_diag]))

    # Sum of squared correlation elements
    sum_sq = float(np.sum(C ** 2))
    if sum_sq <= 0.0 or np.isnan(sum_sq):
        n_eff = 1.0
    else:
        n_eff = float((K ** 2) / sum_sq)

    # Bounded strictly within [1.0, float(K)]
    n_eff = float(np.clip(n_eff, 1.0, float(K)))
    evt_eff = evt_expected_max_standard_normal(n_eff)

    return {
        "candidate_count_K": K,
        "average_correlation_rho_bar": rho_bar,
        "effective_trials_N_eff": n_eff,
        "evt_factor_eff": evt_eff,
        "correlation_matrix": C.tolist(),
        "status": "CALCULATED",
    }


def deflated_sharpe_ratio(
    returns: Union[np.ndarray, pd.Series, List[float]],
    trial_count_K: int = 16,
    risk_free_rate_annual: float = 0.06,
    sessions_per_year: int = 252,
    expected_max_sharpe: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Computes the Deflated Sharpe Ratio (DSR) and corresponding p-value following
    Bailey and López de Prado (2014) and the preregistered Sprint 6.2 protocol v1.2.0.

    Mathematical Definition:
      DSR = Phi( ((SR_hat - SR_star) * sqrt(T - 1)) / sqrt(1 - gamma_3 * SR_hat + ((gamma_4 - 1)/4) * SR_hat^2) )
      p_value = 1.0 - DSR
      Significance Criterion: p_value < 0.05 (i.e. DSR > 0.95)

    Annualization & Time Scale Consistency:
      - If returns are daily, SR_hat_daily = mean(excess) / std(excess).
      - SR_hat_annualized = SR_hat_daily * sqrt(sessions_per_year).
      - Under protocol v1.2.0, SR_star is passed via expected_max_sharpe (annualized scale).
      - On the daily scale: SR_star_daily = SR_star / sqrt(sessions_per_year).
      - Note: (SR_hat_daily - SR_star_daily) * sqrt(T - 1) == (SR_hat_annualized - SR_star) * sqrt((T - 1) / sessions_per_year).
        In the Mertens (2002) asymptotic variance term, SR_hat in the denominator
        (1 - gamma_3 * SR_hat + ((gamma_4 - 1)/4) * SR_hat^2) operates on the sample return
        frequency (daily) since gamma_3 (skewness) and gamma_4 (Pearson kurtosis) are computed
        from daily returns.

    Cross-Sectional Requirement:
      - If expected_max_sharpe is None, DSR cannot be evaluated for an individual candidate
        in isolation. The function returns status 'PENDING_CROSS_SECTIONAL_EVALUATION' with
        NaN statistics. The obsolete fallback to sqrt(2*ln(K)) is strictly eliminated.

    Parameters:
      returns: 1D array-like of periodic (daily) mark-to-market net returns.
      trial_count_K: Total number of discrete candidate trials tested (default 16).
      risk_free_rate_annual: Annualized risk-free benchmark rate (default 0.06, 6% p.a.).
      sessions_per_year: Trading sessions per calendar year (default 252).
      expected_max_sharpe: Null benchmark SR_star on annualized scale from cross-sectional evaluation.

    Returns:
      Dict containing sample moments, Mertens variance factor, DSR statistic, z-score,
      p-value, status, and error description.
    """
    # 1. Validation of inputs
    if returns is None:
        raise ValueError("Returns series cannot be None.")

    arr = np.asarray(returns, dtype=np.float64)
    if arr.ndim != 1:
        arr = arr.ravel()

    T = len(arr)
    if T < 2:
        raise ValueError(f"Sample length T must be at least 2, got {T}.")

    if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
        raise ValueError("Returns series contains NaN or infinite values.")

    if trial_count_K < 1:
        raise ValueError(f"trial_count_K must be >= 1, got {trial_count_K}.")

    # 2. Daily risk-free benchmark
    r_f_daily = risk_free_rate_annual / float(sessions_per_year)
    excess_returns = arr - r_f_daily

    mean_excess = float(np.mean(excess_returns))
    std_excess = float(np.std(excess_returns, ddof=1))

    # Zero or near-zero variance handling
    if std_excess < 1e-12:
        return {
            "daily_sharpe": 0.0,
            "annualized_sharpe": 0.0,
            "expected_max_sharpe_null": float(expected_max_sharpe) if expected_max_sharpe is not None else None,
            "sample_size_T": T,
            "skewness_gamma_3": 0.0,
            "kurtosis_gamma_4": 3.0,
            "variance_adjustment_factor": 1.0,
            "dsr_statistic": 0.0 if expected_max_sharpe is not None else np.nan,
            "dsr_z_score": -np.inf if expected_max_sharpe is not None else np.nan,
            "p_value": 1.0,
            "is_significant": False,
            "status": "ZERO_VARIANCE",
            "error": "Zero return variance; Sharpe ratio is undefined.",
        }

    sr_daily = mean_excess / std_excess
    sr_annualized = sr_daily * np.sqrt(sessions_per_year)

    # 3. Higher standardized moments
    # Sample skewness (gamma_3)
    gamma_3 = float(scipy_stats.skew(excess_returns, bias=False))

    # Sample Pearson kurtosis (gamma_4, where normal = 3)
    gamma_4 = float(scipy_stats.kurtosis(excess_returns, fisher=False, bias=False))

    # 4. Expected Maximum Sharpe Ratio under Null (SR_star)
    # Check if cross-sectional hurdle was supplied
    if expected_max_sharpe is None:
        # Obsolete fallback sqrt(2*ln(K)) is strictly removed.
        # Return PENDING status for individual run without cross-sectional hurdle.
        var_factor = 1.0 - (gamma_3 * sr_daily) + (((gamma_4 - 1.0) / 4.0) * (sr_daily ** 2))
        return {
            "daily_sharpe": float(sr_daily),
            "annualized_sharpe": float(sr_annualized),
            "expected_max_sharpe_null": None,
            "sample_size_T": T,
            "skewness_gamma_3": float(gamma_3),
            "kurtosis_gamma_4": float(gamma_4),
            "variance_adjustment_factor": float(var_factor),
            "dsr_statistic": np.nan,
            "dsr_z_score": np.nan,
            "p_value": np.nan,
            "is_significant": False,
            "status": "PENDING_CROSS_SECTIONAL_EVALUATION",
            "error": "Cross-sectional expected_max_sharpe not provided; individual candidate run cannot evaluate DSR in isolation.",
        }

    sr_star_ann = float(expected_max_sharpe)
    sr_star_daily = sr_star_ann / np.sqrt(sessions_per_year)

    # 5. Mertens asymptotic variance adjustment factor V (evaluated on daily scale)
    var_factor = 1.0 - (gamma_3 * sr_daily) + (((gamma_4 - 1.0) / 4.0) * (sr_daily ** 2))

    if var_factor <= 0.0:
        return {
            "daily_sharpe": float(sr_daily),
            "annualized_sharpe": float(sr_annualized),
            "expected_max_sharpe_null": float(sr_star_ann),
            "sample_size_T": T,
            "skewness_gamma_3": float(gamma_3),
            "kurtosis_gamma_4": float(gamma_4),
            "variance_adjustment_factor": float(var_factor),
            "dsr_statistic": np.nan,
            "dsr_z_score": np.nan,
            "p_value": 1.0,
            "is_significant": False,
            "status": "INVALID_VARIANCE_FACTOR",
            "error": f"Non-positive variance adjustment factor V={var_factor:.6f}; DSR uncomputable.",
        }

    # 6. Standardized z-statistic
    z = ((sr_daily - sr_star_daily) * np.sqrt(T - 1.0)) / np.sqrt(var_factor)

    # DSR is standard normal CDF of z
    dsr_stat = float(scipy_stats.norm.cdf(z))
    # p-value = 1.0 - DSR = standard normal survival function of z
    p_val = float(scipy_stats.norm.sf(z))

    return {
        "daily_sharpe": float(sr_daily),
        "annualized_sharpe": float(sr_annualized),
        "expected_max_sharpe_null": float(sr_star_ann),
        "sample_size_T": T,
        "skewness_gamma_3": float(gamma_3),
        "kurtosis_gamma_4": float(gamma_4),
        "variance_adjustment_factor": float(var_factor),
        "dsr_statistic": dsr_stat,
        "dsr_z_score": float(z),
        "p_value": p_val,
        "is_significant": bool(p_val < 0.05),
        "status": "EVALUATED",
        "error": None,
    }


def holm_bonferroni_correction(
    p_values: Dict[str, float],
    alpha: float = 0.05,
) -> Dict[str, Dict[str, Any]]:
    """
    Applies the Holm-Bonferroni step-down procedure across a family of candidate hypotheses
    to control the Family-Wise Error Rate (FWER) at nominal level alpha.

    Mathematical Algorithm:
      1. Given M hypotheses with p-values p_1, ..., p_M.
      2. Sort p-values in ascending order: p_(1) <= p_(2) <= ... <= p_(M).
      3. For rank k in 1..M:
           adjusted_p_(k) = min(1.0, max_{j <= k} ( (M - j + 1) * p_(j) ))
      4. Reject H_0(k) if adjusted_p_(k) <= alpha.

    Parameters:
      p_values: Dictionary mapping candidate identifiers (e.g. "CFG-01") to raw p-values.
      alpha: Family-wise significance threshold (default 0.05).

    Returns:
      Dictionary mapping each candidate ID to raw p-value, rank, multiplier, adjusted p-value,
      and significance status.
    """
    if not p_values:
        return {}

    results: Dict[str, Dict[str, Any]] = {}
    valid_candidates = []

    for cid, p in p_values.items():
        if p is None or np.isnan(p) or p < 0.0 or p > 1.0:
            results[cid] = {
                "raw_p_value": p,
                "rank": None,
                "multiplier": None,
                "adjusted_p_value": np.nan,
                "is_significant": False,
                "status": "INVALID_INPUT",
            }
        else:
            valid_candidates.append((cid, float(p)))

    M = len(valid_candidates)
    if M == 0:
        return results

    # Deterministic sort: ascending p-value, then alphabetical by candidate ID for ties
    valid_candidates.sort(key=lambda x: (x[1], x[0]))

    # Step-down adjusted p-values with cumulative maximum constraint
    running_max_adj = 0.0
    for rank_idx, (cid, raw_p) in enumerate(valid_candidates):
        k = rank_idx + 1  # 1-indexed rank
        multiplier = M - k + 1
        adj_p = min(1.0, float(multiplier * raw_p))
        # Ensure monotonicity: adjusted p cannot decrease as rank increases
        running_max_adj = max(running_max_adj, adj_p)
        final_adj_p = min(1.0, running_max_adj)

        results[cid] = {
            "raw_p_value": raw_p,
            "rank": k,
            "multiplier": multiplier,
            "adjusted_p_value": final_adj_p,
            "is_significant": bool(final_adj_p <= alpha),
            "status": "EVALUATED",
        }

    return results


def newey_west_hac_sharpe(
    returns: Union[np.ndarray, pd.Series, List[float]],
    risk_free_rate_annual: float = 0.06,
    sessions_per_year: int = 252,
    max_lags: int = 5,
) -> Dict[str, Any]:
    """
    Computes Newey-West / Heteroskedasticity and Autocorrelation Consistent (HAC)
    standard error diagnostics for daily portfolio returns and Sharpe ratio.

    As noted in Sprint 6.1.3 Protocol (line 320):
      Positions held for up to 5 trading sessions induce positive serial correlation
      in daily portfolio equity returns. A Newey-West / HAC adjustment with 5 lags
      must be reported in diagnostics alongside the classical Sharpe ratio.

    Parameters:
      returns: 1D array-like of daily net returns.
      risk_free_rate_annual: Annualized risk-free benchmark rate (default 0.06).
      sessions_per_year: Trading sessions per year (default 252).
      max_lags: Number of autocorrelation lags to evaluate (default 5).

    Returns:
      Dict containing HAC variance, HAC mean standard error, inflation factor, and HAC Sharpe SE.
    """
    if returns is None:
        raise ValueError("Returns series cannot be None.")

    arr = np.asarray(returns, dtype=np.float64)
    if arr.ndim != 1:
        arr = arr.ravel()

    T = len(arr)
    if T <= max_lags + 1:
        raise ValueError(f"Sample length T={T} must exceed max_lags + 1 = {max_lags + 1}.")

    if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
        raise ValueError("Returns series contains NaN or infinite values.")

    r_f_daily = risk_free_rate_annual / float(sessions_per_year)
    excess = arr - r_f_daily
    mean_excess = float(np.mean(excess))
    std_excess = float(np.std(excess, ddof=1))

    if std_excess < 1e-12:
        return {
            "sample_size_T": T,
            "max_lags": max_lags,
            "sample_mean_excess": 0.0,
            "classical_sample_std": 0.0,
            "classical_annualized_sharpe": 0.0,
            "autocovariances": {0: 0.0},
            "bartlett_weights": {},
            "hac_variance": 0.0,
            "hac_mean_standard_error": 0.0,
            "classical_mean_standard_error": 0.0,
            "hac_inflation_factor": 1.0,
            "hac_annualized_sharpe_se": 0.0,
            "error": "Zero return variance.",
        }

    demeaned = excess - mean_excess

    # Sample autocovariances: gamma(l) = (1/T) * sum_{t=l}^{T-1} demeaned[t] * demeaned[t-l]
    autocovs: Dict[int, float] = {}
    for l in range(max_lags + 1):
        if l == 0:
            autocovs[0] = float(np.dot(demeaned, demeaned) / T)
        else:
            autocovs[l] = float(np.dot(demeaned[l:], demeaned[:-l]) / T)

    # Bartlett kernel weights: w_l = 1 - l / (L + 1)
    weights: Dict[int, float] = {}
    hac_var = autocovs[0]
    for l in range(1, max_lags + 1):
        w = 1.0 - (float(l) / float(max_lags + 1))
        weights[l] = w
        hac_var += 2.0 * w * autocovs[l]

    # Ensure non-negative HAC variance
    hac_var = max(0.0, hac_var)
    hac_se_mean = float(np.sqrt(hac_var / T))
    classical_se_mean = float(std_excess / np.sqrt(T))

    gamma_0 = autocovs[0]
    if gamma_0 > 1e-14 and hac_var > 0:
        inflation_factor = float(np.sqrt(hac_var / gamma_0))
    else:
        inflation_factor = 1.0

    classical_ann_sr = float((mean_excess / std_excess) * np.sqrt(sessions_per_year))
    hac_sr_se = float(np.sqrt(sessions_per_year / T) * inflation_factor)

    return {
        "sample_size_T": T,
        "max_lags": max_lags,
        "sample_mean_excess": mean_excess,
        "classical_sample_std": std_excess,
        "classical_annualized_sharpe": classical_ann_sr,
        "autocovariances": autocovs,
        "bartlett_weights": weights,
        "hac_variance": float(hac_var),
        "hac_mean_standard_error": hac_se_mean,
        "classical_mean_standard_error": classical_se_mean,
        "hac_inflation_factor": inflation_factor,
        "hac_annualized_sharpe_se": hac_sr_se,
        "error": None,
    }
