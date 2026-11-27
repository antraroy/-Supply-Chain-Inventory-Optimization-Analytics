-- 1. Stockout rate and fill rate
SELECT ROUND(100.0 * SUM(CASE WHEN on_hand = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS stockout_rate_pct
FROM inventory_daily;

SELECT ROUND(100.0 * SUM(units_sold) / SUM(demand_units), 2) AS fill_rate_pct,
       ROUND(100.0 * SUM(returned_units) / SUM(units_sold), 2) AS return_rate_pct
FROM sales;

-- 2. Stockout days and lost revenue per SKU
SELECT s.sku, p.category,
       SUM(s.lost_units) AS lost_units,
       SUM(s.lost_units * p.unit_price) AS lost_revenue,
       SUM(CASE WHEN i.on_hand = 0 THEN 1 ELSE 0 END) AS stockout_days
FROM sales s
JOIN products p ON p.sku = s.sku
JOIN inventory_daily i ON i.sku = s.sku AND i.date = s.date
GROUP BY s.sku, p.category
ORDER BY lost_revenue DESC
LIMIT 10;

-- 3. ABC classification (cumulative revenue share, window function)
WITH rev AS (
    SELECT s.sku, SUM(s.units_sold * p.unit_price) AS revenue
    FROM sales s JOIN products p ON p.sku = s.sku GROUP BY s.sku
), ranked AS (
    SELECT sku, revenue,
           SUM(revenue) OVER (ORDER BY revenue DESC) * 1.0 / SUM(revenue) OVER () AS cum_share
    FROM rev
)
SELECT sku, revenue, ROUND(cum_share, 3) AS cum_share,
       CASE WHEN cum_share <= 0.80 THEN 'A' WHEN cum_share <= 0.95 THEN 'B' ELSE 'C' END AS abc_class
FROM ranked ORDER BY revenue DESC;

-- 4. Supplier scorecard: on-time %, avg lead time, defects
SELECT supplier,
       COUNT(*) AS orders,
       ROUND(100.0 * SUM(CASE WHEN delivered_date <= promised_date THEN 1 ELSE 0 END) / COUNT(*), 1) AS on_time_pct,
       ROUND(100.0 * SUM(defective_units) / SUM(qty), 2) AS defect_pct
FROM purchase_orders
GROUP BY supplier
ORDER BY on_time_pct DESC;

-- 5. Monthly demand with month-over-month change (CTE + LAG)
WITH m AS (
    SELECT SUBSTR(CAST(date AS VARCHAR(10)), 1, 7) AS month, SUM(demand_units) AS demand
    FROM sales GROUP BY SUBSTR(CAST(date AS VARCHAR(10)), 1, 7)
)
SELECT month, demand,
       ROUND(100.0 * (demand - LAG(demand) OVER (ORDER BY month)) / LAG(demand) OVER (ORDER BY month), 1) AS mom_pct
FROM m ORDER BY month;

-- 6. Average inventory and days of supply per SKU
SELECT i.sku, ROUND(AVG(i.on_hand), 1) AS avg_on_hand,
       ROUND(AVG(i.on_hand) / NULLIF(AVG(s.demand_units), 0), 1) AS days_of_supply
FROM inventory_daily i JOIN sales s ON s.sku = i.sku AND s.date = i.date
GROUP BY i.sku
ORDER BY days_of_supply DESC;

-- 7. Reorder-point check: SKUs that hit zero stock while on order
SELECT sku, COUNT(*) AS days_out_of_stock_with_open_order
FROM inventory_daily
WHERE on_hand = 0 AND on_order > 0
GROUP BY sku
ORDER BY 2 DESC;
