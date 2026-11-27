"""Streamlit dashboard: Supply Chain & Inventory Optimization Analytics.  Run: streamlit run app.py"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import analysis as A

st.set_page_config(page_title="Supply Chain & Inventory Analytics", page_icon="📦", layout="wide")


@st.cache_data
def get_data():
    return A.load()


@st.cache_resource
def get_forecast_model(_sales):
    return A.evaluate_forecasts(_sales)


prod, sales, inv, po = get_data()

st.sidebar.header("Filters")
wh = st.sidebar.multiselect("Warehouse", sorted(prod.warehouse.unique()), default=sorted(prod.warehouse.unique()))
cat = st.sidebar.multiselect("Category", sorted(prod.category.unique()), default=sorted(prod.category.unique()))
sel = prod[prod.warehouse.isin(wh) & prod.category.isin(cat)]
if sel.empty:
    st.warning("No SKUs match the selected filters."); st.stop()
skus = sel.sku
f_sales, f_inv, f_po = sales[sales.sku.isin(skus)], inv[inv.sku.isin(skus)], po[po.sku.isin(skus)]

st.title("📦 Supply Chain & Inventory Optimization Analytics")
st.caption("Reduce stockouts, overstocking and delivery delays: forecasting, ABC analysis, supplier scorecards and reorder-point optimisation.")

k = A.headline_kpis(sel, f_sales, f_inv, f_po)
c = st.columns(6)
c[0].metric("Stockout rate", f"{k['stockout_rate']:.2%}")
c[1].metric("Fill rate", f"{k['fill_rate']:.1%}")
c[2].metric("Return rate", f"{k['return_rate']:.2%}")
c[3].metric("Inventory turnover", f"{k['inventory_turnover']:.1f}x")
c[4].metric("Days of supply", f"{k['days_of_supply']:.1f}")
c[5].metric("On-time delivery", f"{k['on_time_delivery']:.1%}")

t1, t2, t3, t4, t5, t6 = st.tabs(["Inventory health", "ABC / XYZ", "Suppliers & delays",
                                  "Demand forecast", "Reorder points", "Raw data"])

sk = A.sku_summary(sel, f_sales, f_inv)

with t1:
    l, r = st.columns(2)
    carry = sk.assign(carrying_cost=sk.avg_on_hand * sk.unit_cost * sk.holding_rate).groupby(["warehouse", "category"]).carrying_cost.sum().reset_index()
    l.plotly_chart(px.bar(carry, x="warehouse", y="carrying_cost", color="category",
                          title="Annual inventory carrying cost by warehouse"), use_container_width=True)
    daily = f_inv.join(sel.set_index("sku").unit_cost, on="sku").assign(v=lambda d: d.on_hand * d.unit_cost).groupby("date").v.sum().reset_index()
    r.plotly_chart(px.line(daily, x="date", y="v", title="Total inventory value over time"), use_container_width=True)
    so = sk.sort_values("lost_revenue", ascending=False).head(10)
    st.plotly_chart(px.bar(so, x="sku", y="lost_revenue", color="category", title="Top 10 SKUs by revenue lost to stockouts"),
                    use_container_width=True)
    st.plotly_chart(px.scatter(sk, x="days_of_supply", y="stockout_days_pct", size="revenue", color="category", hover_name="sku",
                               title="Overstock vs stockout: days of supply against share of days out of stock"),
                    use_container_width=True)

ab = A.abc_xyz(sk, f_sales)
with t2:
    l, r = st.columns(2)
    p = ab.sort_values("revenue", ascending=False).reset_index(drop=True)
    fig = go.Figure([go.Bar(x=p.sku, y=p.revenue, name="Revenue"),
                     go.Scatter(x=p.sku, y=p.cum_share * 100, name="Cumulative %", yaxis="y2")])
    fig.update_layout(title="Pareto: SKU revenue", yaxis2=dict(overlaying="y", side="right", range=[0, 105]))
    l.plotly_chart(fig, use_container_width=True)
    mat = ab.groupby(["abc", "xyz"]).size().reset_index(name="skus")
    r.plotly_chart(px.density_heatmap(mat, x="xyz", y="abc", z="skus", text_auto=True, title="ABC-XYZ matrix (SKU count)"),
                   use_container_width=True)
    st.caption("A = top ~80% of revenue, B = next 15%, C = last 5%. X/Y/Z = stable / variable / erratic weekly demand (CV ≤0.25 / ≤0.5 / >0.5).")
    st.dataframe(ab[["sku", "product_name", "category", "revenue", "cum_share", "abc", "demand_cv", "xyz", "class"]],
                 use_container_width=True, hide_index=True)

with t3:
    sc = A.supplier_scorecard(f_po)
    l, r = st.columns(2)
    l.plotly_chart(px.bar(sc, x="supplier", y="score", color="tier", title="Supplier score (0-100)"), use_container_width=True)
    r.plotly_chart(px.bar(sc, x="supplier", y="on_time_pct", title="On-time delivery %"), use_container_width=True)
    st.dataframe(sc, use_container_width=True, hide_index=True)
    st.plotly_chart(px.box(f_po, x="supplier", y="delay_days", title="Delivery delay distribution (days vs promised date)"),
                    use_container_width=True)
    st.plotly_chart(px.line(A.delay_by_month(f_po), x="month", y="avg_delay", markers=True, title="Avg delay by order month (days)"),
                    use_container_width=True)
    st.caption("Score = 60% on-time + 25% quality (defects) + 15% lead-time consistency.")

with t4:
    res, model, piv = get_forecast_model(sales)
    st.subheader("Model comparison on a 12-week hold-out")
    st.dataframe(res, use_container_width=True, hide_index=True)
    s_pick = st.selectbox("SKU", list(skus))
    horizon = st.slider("Forecast horizon (weeks)", 4, 12, 8)
    fc = A.forecast_sku(model, piv, s_pick, horizon)
    hist = piv[s_pick].tail(40).reset_index(); hist.columns = ["week", "actual"]
    fig = go.Figure([go.Scatter(x=hist.week, y=hist.actual, name="Actual weekly demand"),
                     go.Scatter(x=fc.week, y=fc.forecast, name="Forecast", line=dict(dash="dash"))])
    fig.update_layout(title=f"Weekly demand forecast: {s_pick}")
    st.plotly_chart(fig, use_container_width=True)

with t5:
    sl = st.slider("Target service level", 0.80, 0.995, 0.95, 0.005)
    rec = A.reorder_policy(sel, f_sales, f_po, service_level=sl)
    m = st.columns(3)
    m[0].metric("SKUs with ROP too low", int((rec.status.str.startswith("Too low")).sum()))
    m[1].metric("SKUs with ROP too high", int((rec.status.str.startswith("Too high")).sum()))
    m[2].metric("SKUs OK", int((rec.status == "OK").sum()))
    show = rec[["sku", "category", "supplier", "d", "L", "safety_stock", "current_reorder_point", "recommended_rop", "eoq", "status"]].round(1)
    show.columns = ["sku", "category", "supplier", "avg daily demand", "avg lead time (d)", "safety stock",
                    "current ROP", "recommended ROP", "EOQ", "status"]
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.download_button("Download recommendations (CSV)", show.to_csv(index=False), "reorder_recommendations.csv")
    st.caption("ROP = demand × lead time + z × √(L·σd² + d²·σL²).  EOQ = √(2·D·S / H).")
    if st.button("Run Monte-Carlo backtest (current vs recommended ROP)"):
        with st.spinner("Simulating one year of demand and supplier lead times..."):
            bt = A.policy_backtest(sel, f_sales, f_po, rec)
        b = st.columns(3)
        b[0].metric("Fill rate", f"{bt.new_fill.mean():.1%}", f"{(bt.new_fill.mean() - bt.cur_fill.mean()) * 100:+.1f} pts")
        b[1].metric("Avg inventory (units)", f"{bt.new_inv.sum():,.0f}", f"{bt.new_inv.sum() / bt.cur_inv.sum() - 1:+.1%}", delta_color="inverse")
        b[2].metric("Total cost (holding+ordering+lost margin)", f"{bt.new_cost.sum():,.0f}", f"{bt.new_cost.sum() / bt.cur_cost.sum() - 1:+.1%}", delta_color="inverse")
        st.caption("Simulation bootstraps historical demand and lead times; both policies use the same order quantity (EOQ).")

with t6:
    name = st.selectbox("Table", ["products", "sales", "inventory_daily", "purchase_orders"])
    st.dataframe({"products": prod, "sales": sales, "inventory_daily": inv, "purchase_orders": po}[name].head(1000),
                 use_container_width=True)
