-- 1. Data check: rows per stock
SELECT Stock, COUNT(*) AS days, MIN(Date) AS first_date, MAX(Date) AS last_date
FROM prices
GROUP BY Stock;

-- 2. Realized P&L by portfolio
SELECT
    Portfolio_ID,
    ROUND(SUM((Sell_Price - Buy_Price) * Quantity), 0) AS realized_pnl
FROM transactions
WHERE Sell_Date IS NOT NULL AND Sell_Date <> ''
GROUP BY Portfolio_ID;

-- 3. Daily returns
SELECT
    Date, Stock, Close,
    ROUND((Close / LAG(Close) OVER (PARTITION BY Stock ORDER BY Date) - 1) * 100, 3) AS daily_return_pct
FROM prices
ORDER BY Stock, Date
LIMIT 20;

-- 4. Best and worst stocks (total return over full period)
WITH first_last AS (
    SELECT Stock,
           FIRST_VALUE(Close) OVER (PARTITION BY Stock ORDER BY Date) AS first_close,
           FIRST_VALUE(Close) OVER (PARTITION BY Stock ORDER BY Date DESC) AS last_close
    FROM prices
)
SELECT Stock,
       ROUND((MAX(last_close) / MAX(first_close) - 1) * 100, 1) AS total_return_pct
FROM first_last
GROUP BY Stock
ORDER BY total_return_pct DESC;

-- 5. Sector performance (average total return per sector)
WITH first_last AS (
    SELECT Stock, Sector,
           FIRST_VALUE(Close) OVER (PARTITION BY Stock ORDER BY Date) AS first_close,
           FIRST_VALUE(Close) OVER (PARTITION BY Stock ORDER BY Date DESC) AS last_close
    FROM prices
),
per_stock AS (
    SELECT Stock, Sector,
           (MAX(last_close) / MAX(first_close) - 1) * 100 AS ret
    FROM first_last
    GROUP BY Stock, Sector
)
SELECT Sector, COUNT(*) AS stocks, ROUND(AVG(ret), 1) AS avg_return_pct
FROM per_stock
GROUP BY Sector
ORDER BY avg_return_pct DESC;

-- 6. Trading volume analysis (average daily volume by stock)
SELECT Stock, Sector,
       ROUND(AVG(Volume), 0) AS avg_daily_volume,
       MAX(Volume) AS peak_volume
FROM prices
GROUP BY Stock, Sector
ORDER BY avg_daily_volume DESC;

-- 7. Holding-period returns (closed trades)
SELECT Portfolio_ID, Stock, Buy_Date, Sell_Date,
       CAST(JULIANDAY(Sell_Date) - JULIANDAY(Buy_Date) AS INTEGER) AS holding_days,
       ROUND((Sell_Price / Buy_Price - 1) * 100, 2) AS return_pct,
       ROUND((Sell_Price - Buy_Price) * Quantity, 0) AS pnl
FROM transactions
WHERE Sell_Date IS NOT NULL AND Sell_Date <> ''
ORDER BY return_pct DESC;

-- 8. Portfolio P&L: realized vs unrealized (open positions at latest price)
WITH latest AS (
    SELECT Stock, Close AS last_close
    FROM prices
    WHERE Date = (SELECT MAX(Date) FROM prices)
)
SELECT t.Portfolio_ID,
       ROUND(SUM(CASE WHEN t.Sell_Date IS NOT NULL AND t.Sell_Date <> ''
                      THEN (t.Sell_Price - t.Buy_Price) * t.Quantity ELSE 0 END), 0) AS realized_pnl,
       ROUND(SUM(CASE WHEN t.Sell_Date IS NULL OR t.Sell_Date = ''
                      THEN (l.last_close - t.Buy_Price) * t.Quantity ELSE 0 END), 0) AS unrealized_pnl
FROM transactions t
JOIN latest l ON l.Stock = t.Stock
GROUP BY t.Portfolio_ID;