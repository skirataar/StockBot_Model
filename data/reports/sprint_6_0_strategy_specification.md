# Sprint 6.0 — Strategy Specification: NIFTY 50 Directional Swing Trading Strategy

**Document Status:** 🔒 **FROZEN SPECIFICATION (PRE-REGISTERED BEFORE BACKTEST EXECUTION)**  
**Author:** Lead Quantitative Research Engineer  
**Date:** 2026-10-28 01:05:00 IST  
**Strategy ID:** `STRAT-NIFTY50-SWING-LGBM-V1`  
**Underlying Model:** Frozen LightGBM Classifier (`models/lightgbm.joblib`, SHA256: `41e61760fc31c72095cd2071fdb843657bd76143ed4535f9b247db78e0c73761`)  
**Target Research Universe:** 49 Approved Constituent Equities of NIFTY 50  

---

## 1. Executive Strategy Summary

This specification establishes the formal, deterministic rules of engagement for translating the Sprint 5.0 frozen LightGBM directional classifications into an event-driven cash equity swing trading strategy.

The strategy trades **long-only cash equity** across the NIFTY 50 universe, entering positions at the open of session $t+1$ following a BUY classification at session $t$ close, and holding for a target duration of **5 trading sessions** (with early exit on a SELL signal).

> [!IMPORTANT]
> **Pre-Registration & Zero Optimization Rule:**
> All rules, portfolio sizing constraints, transaction cost parameters, and execution timing conventions defined herein are frozen prior to running the backtesting engine. No parameters, thresholds, or portfolio constraints may be tuned or altered in response to holdout test results.

---

## 2. Signal Generation & Decision Timing

### 2.1 Chronological Information Flow
The machine learning classifier was trained on 30 approved econometric features computed up to the closing price of session $t$:
$$\mathcal{F}_t = \sigma\left(\{\text{OHLCV}_{s}\}_{s \le t}\right)$$

1. **Signal Timestamp:** At the end of trading session $t$ (after official market close at 15:30 IST), the feature vector $X_{i,t} \in \mathbb{R}^{30}$ is computed for each active stock $i \in \{1 \dots 49\}$.
2. **Model Inference:** The frozen LightGBM model predicts the directional signal and class probabilities:
   $$\hat{y}_{i,t} = \text{argmax}_{c \in \{-1, 0, 1\}} P(\text{signal} = c \mid X_{i,t})$$
   where:
   - $\hat{y}_{i,t} = +1$: **BUY** signal
   - $\hat{y}_{i,t} = 0$: **HOLD** signal
   - $\hat{y}_{i,t} = -1$: **SELL** signal

### 2.2 Execution Timing (Zero Look-Ahead Guarantee)
- **No Same-Close Execution:** Trades **cannot** execute at the same closing price used to compute technical indicators. Market-on-Close (MOC) execution at the exact final closing print without slippage is physically impossible when indicators require the closing print to finalize.
- **Next-Session Entry:** All valid entry orders generated at session $t$ close are submitted for execution at the **Open of session $t+1$** (09:15 IST).
- **Execution Price with Modeled Slippage:**
  $$\text{ExecPrice}_{\text{Buy}} = \text{Open}_{i, t+1} \times (1 + \text{Slippage})$$
  where default $\text{Slippage} = 0.05\%$ (5 bps).

### 2.3 Difference Between Label Returns and Achievable Strategy Returns
- **Label Return:** The continuous target `forward_return_5d` in the training dataset was defined as:
  $$R_{\text{label}} = \frac{\text{Close}_{i, t+5} - \text{Close}_{i, t}}{\text{Close}_{i, t}}$$
- **Achievable Strategy Return:** Realizable return under next-session execution is:
  $$R_{\text{realized}} = \frac{\text{Open}_{i, t+6} \times (1 - \text{Slippage}) - \text{Open}_{i, t+1} \times (1 + \text{Slippage})}{\text{Open}_{i, t+1} \times (1 + \text{Slippage})} - \text{Transaction Costs}$$
- **Discrepancy Sources:**
  1. Overnight gap risk between $t$ Close and $t+1$ Open.
  2. Exit gap risk between $t+5$ Close and $t+6$ Open.
  3. Bid-ask spread and execution slippage on entry and exit.
  4. Statutory taxes and brokerage fees.

---

## 3. Trading Policy & Position Lifecycle

### 3.1 Long-Only Cash Equity Mandate
1. **BUY Signals ($\hat{y}_{i,t} = +1$):**
   - Initiates a long position if capital is available and portfolio constraints are satisfied.
   - If stock $i$ is already held in the portfolio, a subsequent BUY signal is **ignored** (no averaging down, no duplicate overlapping positions).
2. **HOLD Signals ($\hat{y}_{i,t} = 0$):**
   - Neutral signal; does not open new positions. Existing positions remain open until scheduled or early exit.
3. **SELL Signals ($\hat{y}_{i,t} = -1$):**
   - Triggers an early exit from an existing long position in stock $i$ at session $t+1$ Open.
   - In cash equity, SELL signals **never** initiate short positions.

### 3.2 Position Holding Period & Exit Rules
- **Maximum Holding Period:** Exactly **5 active trading sessions**.
  - Entered: Session $t+1$ Open.
  - Held during: Sessions $t+1, t+2, t+3, t+4, t+5$.
  - Scheduled Exit: Session $t+6$ Open (first trading session following 5 full holding sessions).
- **Early Exit Rule:** If a SELL signal ($\hat{y}_{i, t+k} = -1$) occurs at session $t+k$ (where $k \in \{1, 2, 3, 4, 5\}$), the position exits immediately at the **Open of session $t+k+1$**.
- **Exit Price with Modeled Slippage:**
  $$\text{ExecPrice}_{\text{Sell}} = \text{Open}_{i, \text{exit}} \times (1 - \text{Slippage})$$

### 3.3 Non-Trading Session & Market Halt Handling
- If a scheduled execution session (entry or exit) has $\text{Volume} = 0$, $\text{High} == \text{Low}$, or the exchange is closed for a holiday/trading suspension, the order **rolls forward** to the first subsequent active session where $\text{Volume} > 0$.
- Under no circumstances are orders executed on zero-volume days or missing price timestamps.

---

## 4. Portfolio Construction, Risk & Capital Allocation

### 4.1 Capital & Leverage Parameters
- **Initial Portfolio Capital:** ₹1,000,000 (₹10 Lakhs INR).
- **Maximum Gross Exposure:** 100% of Portfolio Equity (Zero leverage / No borrowing).
- **Maximum Single-Stock Weight:** **10% of portfolio equity** at position inception.
- **Maximum Concurrent Positions:** **10 active positions**.

### 4.2 Sizing Formula & Integer Share Accounting
For eligible BUY signal on stock $i$ at session $t$:
$$\text{Target Allocation} = \min\left(\text{Available Cash}_t, 0.10 \times \text{Portfolio Equity}_t\right)$$
$$\text{Estimated Cost Rate} = \text{Slippage} + \text{STT}_{\text{buy}} + \text{StampDuty} + \text{ExchangeRate} + \text{BrokerageRate}$$
$$\text{Quantity}_i = \left\lfloor \frac{\text{Target Allocation}}{\text{Open}_{i, t+1} \times (1 + \text{Estimated Cost Rate})} \right\rfloor$$
- **Capital Solvency Check:** If $\text{Quantity}_i < 1$ share, the trade is rejected for insufficient capital.
- **Cash Floor:** Portfolio cash $\text{Cash}_t \ge 0$ at all times.

### 4.3 Concurrent Signal Priority & Tie-Breaking
When multiple valid BUY signals appear on the same date and available cash/slots cannot accommodate all of them:
1. **Primary Ranking:** Ranked in descending order by model predicted probability of the BUY class:
   $$\text{Score}_{i,t} = P(\text{signal} = +1 \mid X_{i,t})$$
2. **Deterministic Tie-Breaker:** If probabilities are identical, ties are broken alphabetically by stock `symbol`.
3. **No Look-Ahead:** Sizing and ranking use strictly pre-trade session $t$ features and model outputs.

---

## 5. Indian Cash Equity Transaction Cost Model

All transaction charges are modeled in accordance with the current Indian equity delivery schedule (NSE / SEBI / Ministry of Finance):

| Charge Component | Statutory Authority / Broker | Rate Applied on Buy Leg | Rate Applied on Sell Leg | Taxable Base |
|---|---|---|---|---|
| **Brokerage** | Institutional / Discount Broker | 0.03% or ₹20 (whichever lower) | 0.03% or ₹20 (whichever lower) | Executed Trade Turnover |
| **Securities Transaction Tax (STT)** | Ministry of Finance, Govt of India | **0.10%** (10 bps) | **0.10%** (10 bps) | Executed Trade Turnover |
| **Exchange Transaction Fee** | National Stock Exchange (NSE) | **0.00297%** (0.297 bps) | **0.00297%** (0.297 bps) | Executed Trade Turnover |
| **SEBI Turnover Fee** | Securities & Exchange Board of India | **0.00010%** (₹10 / Crore) | **0.00010%** (₹10 / Crore) | Executed Trade Turnover |
| **Stamp Duty** | Indian Stamp Act (State Govt) | **0.01500%** (1.5 bps) | **0.00000%** (0 bps) | Buy Leg Turnover Only |
| **GST** | Central & State GST (18%) | 18% of (Brokerage + Exchange + SEBI) | 18% of (Brokerage + Exchange + SEBI) | Fee Subtotal |
| **Execution Slippage** | Modeled Market Impact / Spread | **0.05000%** (5 bps) | **0.05000%** (5 bps) | Executed Trade Turnover |

### Total Friction Summary
- **Average Buy Friction:** ~0.192% (~19.2 bps) of purchase value.
- **Average Sell Friction:** ~0.177% (~17.7 bps) of sale value.
- **Round-Trip Friction:** **~0.369% (~37 bps)** of trade capital.
- Both Gross P&L (before fees/slippage) and Net P&L (after all costs) are recorded for every trade.

---

## 6. Benchmarks & Comparative Reference Portfolios

To judge strategy performance objectively, the backtest evaluates three reference implementations on identical dates and starting capital:
1. **Benchmark 1 — Equal-Weighted Buy-and-Hold NIFTY 50 Universe:**
   Starting capital (₹1,000,000) allocated equally across all available constituent equities on day 1, held passively through the evaluation period.
2. **Benchmark 2 — Non-ML Naive Baseline Strategy:**
   A systematic baseline allocating capital to randomly selected or fixed-cadence rotational stocks without machine learning predictions.
3. **Model Strategy Gross:**
   The identical frozen LightGBM trading decisions before deducting transaction costs and execution slippage.
4. **Model Strategy Net:**
   The primary real-world strategy after full cost modeling.

---

## 7. Performance Evaluation Metrics

Every backtest evaluation computes the following standardized quantitative metrics:
1. **Cumulative Net Return:** $\frac{\text{Final Equity} - \text{Initial Capital}}{\text{Initial Capital}}$
2. **CAGR (Compound Annual Growth Rate):** $\left(\frac{\text{Final Equity}}{\text{Initial Capital}}\right)^{\frac{252}{N_{\text{days}}}} - 1$
3. **Annualized Volatility:** $\text{Std}(\text{Daily Returns}) \times \sqrt{252}$
4. **Sharpe Ratio:** $\frac{\text{CAGR} - R_f}{\text{Annualized Volatility}}$ (Assumed $R_f = 6.0\%$ per annum, Indian 91-day T-Bill rate)
5. **Maximum Drawdown (MDD):** $\max_{t} \left(\frac{\text{Peak}_t - \text{Equity}_t}{\text{Peak}_t}\right)$
6. **Calmar Ratio:** $\frac{\text{CAGR}}{\text{Maximum Drawdown}}$
7. **Win Rate:** $\frac{N_{\text{profitable trades}}}{N_{\text{total trades}}}$
8. **Profit Factor:** $\frac{\sum \text{Gross Gains}}{\sum |\text{Gross Losses}|}$
9. **Average Trade P&L:** Net profit per completed trade.
10. **Turnover & Total Costs:** Sum of all brokerage, statutory taxes, and slippage paid, expressed in INR and as a percentage of gross profit.

---

## 8. Research Period Disclosure

In accordance with institutional research protocol:
- **Validation Period (2023-01-02 to 2024-12-23):** Used as the primary pre-holdout development benchmark.
- **Holdout Test Period (2025-01-01 to 2026-07-22):** Previously accessed once for classification evaluation in Sprint 5.0. It is evaluated here under frozen backtest rules **strictly as out-of-sample historical evidence**. No post-hoc tuning or optimization is permitted based on test performance.

This specification is frozen and signed off. Engine implementation may proceed.
