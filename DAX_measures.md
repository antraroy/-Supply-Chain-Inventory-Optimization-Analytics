# Power BI setup

Import the 5 CSVs from `data/`. Relationships (all 1 → *):
`products[sku]` → `sales[sku]`, `inventory_daily[sku]`, `purchase_orders[sku]` and `suppliers[supplier]` → `products[supplier]`.
Add a `Date` table and relate it to `sales[date]` and `inventory_daily[date]`.

```DAX
Stockout Rate = DIVIDE(CALCULATE(COUNTROWS(inventory_daily), inventory_daily[on_hand] = 0), COUNTROWS(inventory_daily))
Fill Rate = DIVIDE(SUM(sales[units_sold]), SUM(sales[demand_units]))
Return Rate = DIVIDE(SUM(sales[returned_units]), SUM(sales[units_sold]))
Revenue = SUMX(sales, sales[units_sold] * RELATED(products[unit_price]))
COGS = SUMX(sales, sales[units_sold] * RELATED(products[unit_cost]))
Lost Revenue = SUMX(sales, sales[lost_units] * RELATED(products[unit_price]))
Avg Inventory Value = AVERAGEX(VALUES('Date'[Date]), CALCULATE(SUMX(inventory_daily, inventory_daily[on_hand] * RELATED(products[unit_cost]))))
Inventory Turnover = DIVIDE([COGS], [Avg Inventory Value]) * (365 / DISTINCTCOUNT(sales[date]))
Days of Supply = DIVIDE([Avg Inventory Value], DIVIDE([COGS], DISTINCTCOUNT(sales[date])))
Delay Days = DATEDIFF(purchase_orders[promised_date], purchase_orders[delivered_date], DAY)   -- calculated column
On-Time % = DIVIDE(CALCULATE(COUNTROWS(purchase_orders), purchase_orders[Delay Days] <= 0), COUNTROWS(purchase_orders))
Defect % = DIVIDE(SUM(purchase_orders[defective_units]), SUM(purchase_orders[qty]))
```

**Pages:** 1 Executive KPIs (stockout rate, return rate, fill rate, turnover) · 2 Inventory carrying cost by warehouse + days of supply trend · 3 ABC analysis (Pareto) · 4 Supplier scorecard · 5 Delivery delays · 6 Reorder-point recommendations (import `reorder_recommendations.csv` exported from the app).
