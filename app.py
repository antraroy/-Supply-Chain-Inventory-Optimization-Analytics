"""
Streamlit Dashboard:
Supply Chain & Inventory Optimization Analytics

Run:
streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analysis as A


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Supply Chain & Inventory Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def get_data():
    return A.load()


@st.cache_resource
def get_forecast_model(sales_data):
    return A.evaluate_forecasts(sales_data)


# ============================================================
# LOAD DATA SAFELY
# ============================================================

try:
    prod, sales, inv, po = get_data()

except Exception as e:
    st.error("❌ Unable to load project datasets.")
    st.exception(e)
    st.stop()


# ============================================================
# VALIDATE DATA
# ============================================================

required_datasets = {
    "Products": prod,
    "Sales": sales,
    "Inventory": inv,
    "Purchase Orders": po
}

for name, df in required_datasets.items():

    if not isinstance(df, pd.DataFrame):
        st.error(f"{name} dataset is not a valid DataFrame.")
        st.stop()

    if df.empty:
        st.warning(f"{name} dataset is empty.")


required_product_columns = [
    "sku",
    "warehouse",
    "category"
]

missing_columns = [
    col for col in required_product_columns
    if col not in prod.columns
]

if missing_columns:

    st.error(
        f"Missing columns in products dataset: {missing_columns}"
    )

    st.write("Available columns:", list(prod.columns))
    st.stop()


# ============================================================
# HEADER
# ============================================================

st.title(
    "📦 Supply Chain & Inventory Optimization Analytics"
)

st.caption(
    "Reduce stockouts, overstocking and delivery delays through "
    "forecasting, ABC analysis, supplier scorecards and "
    "reorder-point optimisation."
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🔎 Filters")


warehouses = sorted(
    prod["warehouse"].dropna().unique().tolist()
)

categories = sorted(
    prod["category"].dropna().unique().tolist()
)


wh = st.sidebar.multiselect(
    "Warehouse",
    warehouses,
    default=warehouses
)

cat = st.sidebar.multiselect(
    "Category",
    categories,
    default=categories
)


# ============================================================
# FILTER PRODUCTS
# ============================================================

sel = prod[
    prod["warehouse"].isin(wh)
    &
    prod["category"].isin(cat)
].copy()


if sel.empty:

    st.warning(
        "No SKUs match the selected filters. "
        "Please select another warehouse or category."
    )

    st.stop()


# ============================================================
# FILTER OTHER DATASETS
# ============================================================

skus = sel["sku"].unique()

f_sales = sales[
    sales["sku"].isin(skus)
].copy()

f_inv = inv[
    inv["sku"].isin(skus)
].copy()

f_po = po[
    po["sku"].isin(skus)
].copy()


# ============================================================
# KPI CALCULATIONS
# ============================================================

try:

    k = A.headline_kpis(
        sel,
        f_sales,
        f_inv,
        f_po
    )

except Exception as e:

    st.error("Unable to calculate KPI metrics.")
    st.exception(e)
    st.stop()


# ============================================================
# KPI DISPLAY
# ============================================================

st.subheader("📊 Key Performance Indicators")

c = st.columns(6)

c[0].metric(
    "Stockout Rate",
    f"{float(k.get('stockout_rate') or 0):.2%}"
)

c[1].metric(
    "Fill Rate",
    f"{k['fill_rate']:.1%}"
)

c[2].metric(
    "Return Rate",
    f"{k['return_rate']:.2%}"
)

c[3].metric(
    "Inventory Turnover",
    f"{k['inventory_turnover']:.1f}x"
)

c[4].metric(
    "Days of Supply",
    f"{k['days_of_supply']:.1f}"
)

c[5].metric(
    "On-Time Delivery",
    f"{k['on_time_delivery']:.1%}"
)


st.divider()


# ============================================================
# TABS
# ============================================================

t1, t2, t3, t4, t5, t6 = st.tabs([
    "📦 Inventory Health",
    "📊 ABC / XYZ",
    "🚚 Suppliers & Delays",
    "🔮 Demand Forecast",
    "📈 Reorder Points",
    "📂 Raw Data"
])


# ============================================================
# SKU SUMMARY
# ============================================================

try:

    sk = A.sku_summary(
        sel,
        f_sales,
        f_inv
    )

except Exception as e:

    st.error("Unable to calculate SKU summary.")
    st.exception(e)
    st.stop()


# ============================================================
# TAB 1: INVENTORY HEALTH
# ============================================================

with t1:

    st.subheader("📦 Inventory Health Analysis")

    if sk.empty:

        st.warning("SKU summary is empty.")

    else:

        # Carrying cost

        if all(
            col in sk.columns
            for col in [
                "avg_on_hand",
                "unit_cost",
                "holding_rate",
                "warehouse",
                "category"
            ]
        ):

            carry = sk.copy()

            carry["carrying_cost"] = (
                carry["avg_on_hand"]
                *
                carry["unit_cost"]
                *
                carry["holding_rate"]
            )

            carry = (
                carry.groupby(
                    ["warehouse", "category"],
                    as_index=False
                )["carrying_cost"]
                .sum()
            )

            fig = px.bar(
                carry,
                x="warehouse",
                y="carrying_cost",
                color="category",
                title="Annual Inventory Carrying Cost by Warehouse"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # Inventory value over time

        if (
            "date" in f_inv.columns
            and "on_hand" in f_inv.columns
            and "sku" in f_inv.columns
            and "sku" in sel.columns
            and "unit_cost" in sel.columns
        ):

            cost_map = (
                sel.drop_duplicates("sku")
                .set_index("sku")["unit_cost"]
            )

            daily = f_inv.copy()

            daily["unit_cost"] = daily["sku"].map(cost_map)

            daily["inventory_value"] = (
                daily["on_hand"]
                *
                daily["unit_cost"]
            )

            daily["date"] = pd.to_datetime(
                daily["date"],
                errors="coerce"
            )

            daily = daily.dropna(
                subset=["date"]
            )

            daily = (
                daily.groupby("date", as_index=False)
                ["inventory_value"]
                .sum()
            )

            fig = px.line(
                daily,
                x="date",
                y="inventory_value",
                title="Total Inventory Value Over Time"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # Lost revenue

        if (
            "lost_revenue" in sk.columns
            and "sku" in sk.columns
        ):

            so = (
                sk.sort_values(
                    "lost_revenue",
                    ascending=False
                )
                .head(10)
            )

            fig = px.bar(
                so,
                x="sku",
                y="lost_revenue",
                color="category",
                title="Top 10 SKUs by Revenue Lost to Stockouts"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # Overstock vs stockout

        required_scatter_columns = [
            "days_of_supply",
            "stockout_days_pct",
            "revenue",
            "category",
            "sku"
        ]

        if all(
            col in sk.columns
            for col in required_scatter_columns
        ):

            fig = px.scatter(
                sk,
                x="days_of_supply",
                y="stockout_days_pct",
                size="revenue",
                color="category",
                hover_name="sku",
                title=(
                    "Overstock vs Stockout: "
                    "Days of Supply vs Stockout Percentage"
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


# ============================================================
# TAB 2: ABC / XYZ ANALYSIS
# ============================================================

try:

    ab = A.abc_xyz(
        sk,
        f_sales
    )

except Exception as e:

    ab = pd.DataFrame()

    with t2:

        st.error("ABC-XYZ analysis could not be generated.")
        st.exception(e)


with t2:

    st.subheader("📊 ABC / XYZ Inventory Classification")

    if ab.empty:

        st.warning("ABC-XYZ analysis data is unavailable.")

    else:

        # Pareto chart

        if all(
            col in ab.columns
            for col in [
                "sku",
                "revenue",
                "cum_share"
            ]
        ):

            p = (
                ab.sort_values(
                    "revenue",
                    ascending=False
                )
                .reset_index(drop=True)
            )

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    x=p["sku"],
                    y=p["revenue"],
                    name="Revenue"
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=p["sku"],
                    y=p["cum_share"] * 100,
                    name="Cumulative %",
                    yaxis="y2"
                )
            )

            fig.update_layout(
                title="Pareto Analysis: SKU Revenue",
                yaxis_title="Revenue",
                yaxis2=dict(
                    title="Cumulative %",
                    overlaying="y",
                    side="right",
                    range=[0, 105]
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # ABC-XYZ matrix

        if all(
            col in ab.columns
            for col in [
                "abc",
                "xyz"
            ]
        ):

            mat = (
                ab.groupby(
                    ["abc", "xyz"]
                )
                .size()
                .reset_index(name="skus")
            )

            fig = px.density_heatmap(
                mat,
                x="xyz",
                y="abc",
                z="skus",
                text_auto=True,
                title="ABC-XYZ Matrix: SKU Count"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        st.caption(
            "A = approximately the top 80% of revenue; "
            "B = next 15%; C = last 5%. "
            "X/Y/Z represents stable, variable and erratic demand."
        )


        # Classification table

        display_columns = [
            "sku",
            "product_name",
            "category",
            "revenue",
            "cum_share",
            "abc",
            "demand_cv",
            "xyz",
            "class"
        ]

        available_columns = [
            col for col in display_columns
            if col in ab.columns
        ]

        st.dataframe(
            ab[available_columns],
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# TAB 3: SUPPLIERS & DELAYS
# ============================================================

with t3:

    st.subheader("🚚 Supplier Performance")

    try:

        sc = A.supplier_scorecard(f_po)

        if sc.empty:

            st.warning(
                "Supplier scorecard is empty."
            )

        else:

            l, r = st.columns(2)

            # Supplier score

            if "score" in sc.columns:

                l.plotly_chart(
                    px.bar(
                        sc,
                        x="supplier",
                        y="score",
                        color="tier",
                        title="Supplier Score (0-100)"
                    ),
                    use_container_width=True
                )


            # On-time delivery

            if "on_time_pct" in sc.columns:

                r.plotly_chart(
                    px.bar(
                        sc,
                        x="supplier",
                        y="on_time_pct",
                        title="On-Time Delivery Percentage"
                    ),
                    use_container_width=True
                )


            st.dataframe(
                sc,
                use_container_width=True,
                hide_index=True
            )


            # Delay distribution

            if all(
                col in f_po.columns
                for col in [
                    "supplier",
                    "delay_days"
                ]
            ):

                st.plotly_chart(
                    px.box(
                        f_po,
                        x="supplier",
                        y="delay_days",
                        title="Delivery Delay Distribution"
                    ),
                    use_container_width=True
                )


            # Monthly delay

            try:

                delay_month = A.delay_by_month(f_po)

                if not delay_month.empty:

                    st.plotly_chart(
                        px.line(
                            delay_month,
                            x="month",
                            y="avg_delay",
                            markers=True,
                            title="Average Delay by Order Month"
                        ),
                        use_container_width=True
                    )

            except Exception as e:

                st.warning(
                    f"Monthly delay chart unavailable: {e}"
                )


            st.caption(
                "Supplier score: 60% on-time delivery, "
                "25% quality and 15% lead-time consistency."
            )

    except Exception as e:

        st.error(
            "Supplier analysis failed."
        )

        st.exception(e)


# ============================================================
# TAB 4: DEMAND FORECAST
# ============================================================

with t4:

    st.subheader("🔮 Demand Forecasting")

    try:

        res, model, piv = get_forecast_model(sales)

        st.write(
            "### Model Comparison on a 12-Week Hold-Out"
        )

        if isinstance(res, pd.DataFrame):

            st.dataframe(
                res,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.write(res)


        if piv is not None and not piv.empty:

            available_skus = [
                sku for sku in skus
                if sku in piv.columns
            ]

            if available_skus:

                s_pick = st.selectbox(
                    "Select SKU",
                    available_skus
                )

                horizon = st.slider(
                    "Forecast Horizon (Weeks)",
                    min_value=4,
                    max_value=12,
                    value=8
                )


                # Generate forecast

                fc = A.forecast_sku(
                    model,
                    piv,
                    s_pick,
                    horizon
                )


                # Historical demand

                hist = (
                    piv[s_pick]
                    .tail(40)
                    .reset_index()
                )

                hist.columns = [
                    "week",
                    "actual"
                ]


                fig = go.Figure()

                fig.add_trace(
                    go.Scatter(
                        x=hist["week"],
                        y=hist["actual"],
                        name="Actual Weekly Demand"
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=fc["week"],
                        y=fc["forecast"],
                        name="Forecast",
                        line=dict(
                            dash="dash"
                        )
                    )
                )

                fig.update_layout(
                    title=f"Weekly Demand Forecast: {s_pick}",
                    xaxis_title="Week",
                    yaxis_title="Demand"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


                st.subheader("Forecast Data")

                st.dataframe(
                    fc,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.warning(
                    "No selected SKUs exist in the forecast dataset."
                )

        else:

            st.warning(
                "Forecast pivot data is empty."
            )

    except Exception as e:

        st.error(
            "Demand forecasting failed."
        )

        st.exception(e)


# ============================================================
# TAB 5: REORDER POINT OPTIMIZATION
# ============================================================

with t5:

    st.subheader("📈 Reorder Point Optimization")

    service_level = st.slider(
        "Target Service Level",
        min_value=0.80,
        max_value=0.995,
        value=0.95,
        step=0.005
    )


    try:

        rec = A.reorder_policy(
            sel,
            f_sales,
            f_po,
            service_level=service_level
        )


        if rec.empty:

            st.warning(
                "Reorder recommendations are unavailable."
            )

        else:

            # Status metrics

            if "status" in rec.columns:

                too_low = rec[
                    rec["status"].astype(str)
                    .str.startswith("Too low")
                ]

                too_high = rec[
                    rec["status"].astype(str)
                    .str.startswith("Too high")
                ]

                okay = rec[
                    rec["status"] == "OK"
                ]

                m = st.columns(3)

                m[0].metric(
                    "SKUs with ROP Too Low",
                    len(too_low)
                )

                m[1].metric(
                    "SKUs with ROP Too High",
                    len(too_high)
                )

                m[2].metric(
                    "SKUs OK",
                    len(okay)
                )


            # Recommendation table

            display_columns = [
                "sku",
                "category",
                "supplier",
                "d",
                "L",
                "safety_stock",
                "current_reorder_point",
                "recommended_rop",
                "eoq",
                "status"
            ]

            available_columns = [
                col for col in display_columns
                if col in rec.columns
            ]

            show = rec[
                available_columns
            ].copy()


            # Rename columns

            rename_mapping = {
                "d": "Average Daily Demand",
                "L": "Average Lead Time (Days)",
                "safety_stock": "Safety Stock",
                "current_reorder_point": "Current ROP",
                "recommended_rop": "Recommended ROP",
                "eoq": "EOQ"
            }

            show = show.rename(
                columns=rename_mapping
            )


            # Round numerical columns

            show = show.round(1)


            st.dataframe(
                show,
                use_container_width=True,
                hide_index=True
            )


            # Download

            st.download_button(
                label="📥 Download Recommendations CSV",
                data=show.to_csv(index=False),
                file_name="reorder_recommendations.csv",
                mime="text/csv"
            )


            st.caption(
                "ROP = Demand × Lead Time + Safety Stock. "
                "EOQ = Economic Order Quantity."
            )


            # Monte Carlo backtest

            if st.button(
                "🎲 Run Monte-Carlo Backtest"
            ):

                with st.spinner(
                    "Simulating demand and supplier lead times..."
                ):

                    bt = A.policy_backtest(
                        sel,
                        f_sales,
                        f_po,
                        rec
                    )


                if not bt.empty:

                    b = st.columns(3)


                    # Fill rate

                    b[0].metric(
                        "Fill Rate",
                        f"{bt.new_fill.mean():.1%}",
                        f"{(
                            bt.new_fill.mean()
                            -
                            bt.cur_fill.mean()
                        ) * 100:+.1f} pts"
                    )


                    # Inventory

                    current_inventory = bt.cur_inv.sum()

                    new_inventory = bt.new_inv.sum()

                    inventory_change = (
                        new_inventory / current_inventory - 1
                        if current_inventory != 0
                        else 0
                    )

                    b[1].metric(
                        "Average Inventory (Units)",
                        f"{new_inventory:,.0f}",
                        f"{inventory_change:+.1%}",
                        delta_color="inverse"
                    )


                    # Cost

                    current_cost = bt.cur_cost.sum()

                    new_cost = bt.new_cost.sum()

                    cost_change = (
                        new_cost / current_cost - 1
                        if current_cost != 0
                        else 0
                    )

                    b[2].metric(
                        "Total Cost",
                        f"{new_cost:,.0f}",
                        f"{cost_change:+.1%}",
                        delta_color="inverse"
                    )


                    st.success(
                        "Monte-Carlo backtest completed successfully."
                    )

                    st.dataframe(
                        bt,
                        use_container_width=True
                    )

                else:

                    st.warning(
                        "Backtest returned no results."
                    )


    except Exception as e:

        st.error(
            "Reorder point analysis failed."
        )

        st.exception(e)


# ============================================================
# TAB 6: RAW DATA
# ============================================================

with t6:

    st.subheader("📂 Explore Raw Datasets")


    dataset_name = st.selectbox(
        "Select Dataset",
        [
            "Products",
            "Sales",
            "Inventory Daily",
            "Purchase Orders"
        ]
    )


    dataset_mapping = {
        "Products": prod,
        "Sales": sales,
        "Inventory Daily": inv,
        "Purchase Orders": po
    }


    selected_dataset = dataset_mapping[
        dataset_name
    ]


    st.write(
        f"Rows: {len(selected_dataset):,}"
    )

    st.write(
        f"Columns: {len(selected_dataset.columns):,}"
    )


    st.dataframe(
        selected_dataset.head(1000),
        use_container_width=True,
        hide_index=True
    )


    # Download dataset

    st.download_button(
        label=f"📥 Download {dataset_name} CSV",
        data=selected_dataset.to_csv(index=False),
        file_name=f"{dataset_name.lower().replace(' ', '_')}.csv",
        mime="text/csv"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center">

    **Supply Chain & Inventory Optimization Analytics**

    Built with Python | Streamlit | Pandas | Plotly

    </div>
    """,
    unsafe_allow_html=True
)
