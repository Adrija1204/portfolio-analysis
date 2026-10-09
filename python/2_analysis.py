import pandas as pd
import numpy as np

prices = pd.read_csv("data/prices.csv", parse_dates=["Date"])
transactions = pd.read_csv("data/transactions.csv", parse_dates=["Buy_Date", "Sell_Date"])

# ---------- Returns ----------
close_wide = prices.pivot(index="Date", columns="Stock", values="Close")
returns = close_wide.pct_change().dropna()
cumulative = (1 + returns).cumprod()

# ---------- Risk metrics ----------
TRADING_DAYS = 252
RISK_FREE = 0.065

ann_return = (1 + returns.mean()) ** TRADING_DAYS - 1
ann_vol = returns.std() * np.sqrt(TRADING_DAYS)
sharpe = (ann_return - RISK_FREE) / ann_vol
max_dd = (cumulative / cumulative.cummax() - 1).min()

sector_map = prices.drop_duplicates("Stock").set_index("Stock")["Sector"]

risk_return = pd.DataFrame({
    "Sector": sector_map,
    "Ann_Return": ann_return,
    "Ann_Volatility": ann_vol,
    "Sharpe": sharpe,
    "Max_Drawdown": max_dd,
}).round(3)

print("\n=== RISK / RETURN ===")
print(risk_return.sort_values("Sharpe", ascending=False))

print("\n=== CORRELATION ===")
print(returns.corr().round(2))

# ---------- Portfolio P&L (closed trades) ----------
closed = transactions.dropna(subset=["Sell_Date"]).copy()
closed["PnL"] = (closed["Sell_Price"] - closed["Buy_Price"]) * closed["Quantity"]
print("\n=== REALIZED P&L BY PORTFOLIO ===")
print(closed.groupby("Portfolio_ID")["PnL"].sum().round(0))

# ---------- Export for Power BI ----------
risk_return.to_csv("data/risk_return.csv")
returns.to_csv("data/daily_returns.csv")
print("\nSaved: data/risk_return.csv, data/daily_returns.csv")

# ---------- Drawdown export for Power BI ----------
drawdown = cumulative / cumulative.cummax() - 1
dd_long = drawdown.reset_index().melt(id_vars="Date", var_name="Stock", value_name="Drawdown")
dd_long.to_csv("data/drawdown_long.csv", index=False)
print("Saved: data/drawdown_long.csv")