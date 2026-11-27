# 📦 Supply Chain & Inventory Optimization Analytics

An end-to-end analytics project that helps a company **reduce stockouts, overstocking and delivery delays**. It covers demand forecasting, inventory turnover, supplier performance, delivery-delay analysis, ABC/XYZ classification, and a reorder-point optimiser that is validated with a Monte-Carlo simulation.

**Tech stack:** Python (pandas, NumPy, SciPy, scikit-learn) · SQL · Power BI · Streamlit · Plotly

## 🎯 Business questions answered
- Which SKUs run out of stock, and how much revenue does that cost?
- Where are we overstocked (high days of supply, low turnover)?
- Which products matter most (ABC) and which are hard to forecast (XYZ)?
- Which suppliers deliver late or ship defective goods?
- How much stock should we hold, and when should we reorder?

## 📊 Key results (synthetic dataset: 48 SKUs · 4 warehouses · 6 suppliers · 2 years)
| Metric | Value |
|---|---|
| Stockout rate (SKU-days at zero stock) | ~4.5% |
| Fill rate | ~96% |
| Return rate | ~2.1% |
| Inventory turnover | ~20x per year (about 18 days of supply) |
| On-time supplier delivery | ~78% |
| ABC split | 24 A-items drive ~79% of revenue; 13 C-items drive ~6% |
| Demand forecast accuracy (12-week hold-out) | Gradient boosting 90.4% vs 4-week moving average 89.5% vs seasonal naive 86.7% |
| Reorder points reviewed | 25 SKUs too low, 14 too high, 9 OK |
| Backtest of recommended reorder points | Fill rate 94.1% → 99.7%, with ~15% more average stock; total cost (holding + ordering + lost margin) down by about 60% |

**Insights**
- Electronics has the highest stockout share and the largest lost revenue.
- EverGreen Imports and CoreMart Wholesale score "Review" on the supplier scorecard (about 62% and 68% on-time, with the highest defect rates).
- The gradient-boosting forecast only slightly beats a moving average on this data, so the project reports both and does not oversell the model.
- Fixing reorder points gives the biggest gain: 25 SKUs reorder too late and 14 hold too much.

*The backtest replays one year using bootstrapped demand and supplier lead times, with the same order quantity (EOQ) for both policies, so it isolates the effect of the reorder point. It is a simulation on synthetic data, not a real-world guarantee.*

## 🗂️ Structure
```
supply-chain-inventory-analytics/
├── app.py                   # Streamlit dashboard (6 tabs)
├── src/
│   ├── generate_data.py     # simulates demand, replenishment, supplier delays, stockouts, returns
│   └── analysis.py          # KPIs, ABC/XYZ, scorecards, forecasting, reorder points, backtest
├── sql/                     # schema + 7 KPI queries (CTEs, window functions)
├── powerbi/DAX_measures.md  # data model, DAX measures, 6-page dashboard layout
├── data/                    # generated CSVs
└── requirements.txt
```

## 🚀 Run it
```bash
git clone https://github.com/<your-username>/supply-chain-inventory-analytics.git
cd supply-chain-inventory-analytics
pip install -r requirements.txt
python src/generate_data.py     # regenerate the dataset
python src/analysis.py          # KPIs, forecast accuracy and backtest in the terminal
streamlit run app.py            # open the interactive dashboard
```

## 🧠 Methods
- **Demand forecasting:** weekly demand per SKU (true demand, not censored by stockouts). Gradient boosting with lags, rolling means, last-year demand and seasonality, compared with moving-average and seasonal-naive baselines using WAPE.
- **Inventory turnover:** annualised COGS ÷ average inventory value; days of supply = average stock ÷ average daily demand.
- **ABC/XYZ:** ABC from cumulative revenue (80/15/5); XYZ from the coefficient of variation of weekly demand.
- **Supplier scorecard:** 60% on-time rate + 25% quality (defects) + 15% lead-time consistency.
- **Optimal reorder point:** `ROP = d·L + z·√(L·σd² + d²·σL²)`, where z comes from the target service level. Order quantity uses **EOQ = √(2·D·S / H)**. The dashboard lets you move the service-level slider and download the recommendations.

## 🔮 Future improvements
- Multi-echelon inventory (warehouse transfers)
- Prophet / LightGBM forecasts with promotions and holidays
- Supplier risk prediction from delay history
- Deploy the dashboard on Streamlit Community Cloud

> Data is synthetic and generated for demonstration; no real company data is used.
