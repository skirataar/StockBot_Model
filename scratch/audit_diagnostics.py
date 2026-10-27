import json
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix, brier_score_loss
from sklearn.calibration import calibration_curve
from src.ml.dataset_builder import APPROVED_FEATURES
from src.backtest.event_driven_engine import EventDrivenBacktestEngine

def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

# Load ground-truth source artifacts
model = joblib.load("models/lightgbm.joblib")
df_test = pd.read_parquet("data/processed/test_dataset.parquet")
trades = pd.read_csv("data/reports/trade_ledger.csv")
port = pd.read_csv("data/reports/portfolio_ledger.csv")

# Load existing Sprint 6.1 artifacts
with open("data/reports/sprint_6_1_strategy_diagnostics.json") as f:
    json_data = json.load(f)

with open("data/reports/sprint_6_1_strategy_diagnostics_report.md") as f:
    md_text = f.read()

print("Loaded all artifacts successfully.")

# Run model predictions
X = df_test[APPROVED_FEATURES]
y_true = df_test["signal"].values
preds = model.predict(X)
probs = model.predict_proba(X)
classes = list(model.classes_)
buy_idx = classes.index(1)
p_buy = probs[:, buy_idx]

df_test["p_buy"] = p_buy
df_test["pred_signal"] = preds

# Let's inspect calibration curve deciles
y_buy_binary = (y_true == 1).astype(int)
prob_true, prob_pred = calibration_curve(y_buy_binary, p_buy, n_bins=10, strategy='quantile')
print("=== CALIBRATION DECILES ===")
for i in range(10):
    print(f"Decile {i+1}: Pred={prob_pred[i]:.4f}, True={prob_true[i]:.4f}, Diff={prob_true[i]-prob_pred[i]:.4f}")

# Let's inspect trades std
print("\n=== TRADE PNL STD ===")
print("Gross std ddof=1:", trades["gross_pnl"].std(ddof=1))
print("Net std ddof=1:", trades["net_pnl"].std(ddof=1))
print("Costs mean:", trades["total_costs"].mean(), "median:", trades["total_costs"].median())

# Let's inspect annual and quarterly
port["date"] = pd.to_datetime(port["date"])
trades["entry_date"] = pd.to_datetime(trades["entry_date"])
trades["exit_date"] = pd.to_datetime(trades["exit_date"])
trades["signal_date"] = pd.to_datetime(trades["signal_date"])
port["year"] = port["date"].dt.year
port["quarter"] = port["date"].dt.to_period("Q")

print("\n=== PORTFOLIO LEDGER SESSIONS BY YEAR ===")
for yr, grp in port.groupby("year"):
    print(f"Year {yr}: sessions={len(grp)}, start_dt={grp['date'].iloc[0].strftime('%Y-%m-%d')}, end_dt={grp['date'].iloc[-1].strftime('%Y-%m-%d')}")
    print(f"  start_eq={grp['portfolio_equity'].iloc[0]:.2f}, end_eq={grp['portfolio_equity'].iloc[-1]:.2f}, avg_exp={grp['gross_exposure_pct'].mean():.2f}%")

print("\n=== PORTFOLIO LEDGER SESSIONS BY QUARTER ===")
for qtr, grp in port.groupby("quarter"):
    print(f"Quarter {qtr}: sessions={len(grp)}, start_dt={grp['date'].iloc[0].strftime('%Y-%m-%d')}, end_dt={grp['date'].iloc[-1].strftime('%Y-%m-%d')}")
    print(f"  start_eq={grp['portfolio_equity'].iloc[0]:.2f}, end_eq={grp['portfolio_equity'].iloc[-1]:.2f}, avg_exp={grp['gross_exposure_pct'].mean():.2f}%")

print("\n=== TRADES BY ENTRY_DATE YEAR ===")
trades["entry_year"] = trades["entry_date"].dt.year
trades["entry_quarter"] = trades["entry_date"].dt.to_period("Q")
for yr, grp in trades.groupby("entry_year"):
    print(f"Year {yr}: trades={len(grp)}, gross={grp['gross_pnl'].sum():.2f}, costs={grp['total_costs'].sum():.2f}, net={grp['net_pnl'].sum():.2f}")

print("\n=== TRADES BY ENTRY_DATE QUARTER ===")
for qtr, grp in trades.groupby("entry_quarter"):
    print(f"Quarter {qtr}: trades={len(grp)}, gross={grp['gross_pnl'].sum():.2f}, costs={grp['total_costs'].sum():.2f}, net={grp['net_pnl'].sum():.2f}")

print("\n=== TRADES BY EXIT_DATE QUARTER ===")
trades["exit_quarter"] = trades["exit_date"].dt.to_period("Q")
for qtr, grp in trades.groupby("exit_quarter"):
    print(f"Quarter {qtr}: trades={len(grp)}, gross={grp['gross_pnl'].sum():.2f}, costs={grp['total_costs'].sum():.2f}, net={grp['net_pnl'].sum():.2f}")
