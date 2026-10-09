import yfinance as yf
import pandas as pd
import numpy as np
import os

os.makedirs("data", exist_ok=True)

# ---------- 1. Prices table ----------
sectors = {
    "RELIANCE.NS": "Energy",
    "TCS.NS": "IT",
    "INFY.NS": "IT",
    "HDFCBANK.NS": "Banking",
    "ICICIBANK.NS": "Banking",
    "ITC.NS": "FMCG",
    "HINDUNILVR.NS": "FMCG",
    "SUNPHARMA.NS": "Pharma",
    "MARUTI.NS": "Auto",
    "LT.NS": "Infrastructure",
}

yf.set_tz_cache_location("tz_cache")

raw = yf.download(
    list(sectors), start="2021-01-01", end="2026-10-01",
    auto_adjust=True, group_by="ticker", progress=False,
    threads=False,
)

frames = []
for ticker, sector in sectors.items():
    df = raw[ticker].dropna().reset_index()
    df["Stock"] = ticker.replace(".NS", "")
    df["Sector"] = sector
    frames.append(df)

prices = pd.concat(frames, ignore_index=True)
prices = prices[["Date", "Stock", "Open", "High", "Low", "Close", "Volume", "Sector"]]
prices[["Open", "High", "Low", "Close"]] = prices[["Open", "High", "Low", "Close"]].round(2)
prices = prices.sort_values(["Stock", "Date"]).reset_index(drop=True)

prices.to_csv("data/prices.csv", index=False)
print(prices.shape, prices["Stock"].nunique(), "stocks")

# ---------- 2. Transactions table ----------
rng = np.random.default_rng(42)
close = prices.set_index(["Stock", "Date"])["Close"]
stocks = prices["Stock"].unique()

rows = []
for pid in ["P1", "P2", "P3"]:
    for _ in range(12):
        stock = rng.choice(stocks)
        days = prices.loc[prices["Stock"] == stock, "Date"].reset_index(drop=True)
        i = int(rng.integers(0, len(days) - 260))
        j = i + int(rng.integers(20, 250))
        still_open = rng.random() < 0.2

        buy_date, sell_date = days[i], days[j]
        rows.append({
            "Portfolio_ID": pid,
            "Stock": stock,
            "Buy_Date": buy_date.date(),
            "Sell_Date": None if still_open else sell_date.date(),
            "Quantity": int(rng.integers(10, 200)),
            "Buy_Price": round(float(close[(stock, buy_date)]), 2),
            "Sell_Price": None if still_open else round(float(close[(stock, sell_date)]), 2),
        })

transactions = pd.DataFrame(rows).sort_values(["Portfolio_ID", "Buy_Date"])
transactions.to_csv("data/transactions.csv", index=False)
print(transactions.head(10))