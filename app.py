import streamlit as st
import pandas as pd
import plotly.express as px
import os

import analysis as an


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Supply Chain Analytics",
    page_icon="📦",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #f7f9fc;
}

h1 {
    color: #17365D;
}

h2, h3 {
    color: #24476B;
}

[data-testid="metric-container"] {
    background-color: white;
    border: 1px solid #e6eaf0;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# DATA LOADING
# =========================================================

@st.cache_data
def load_csv_file(file_path):

    try:
        return pd.read_csv(file_path)

    except Exception:
        return pd.DataFrame()


def load_data():

    uploaded_file = st.sidebar.file_uploader(
        "Upload Inventory CSV",
        type=["csv"]
    )

    if uploaded_file is not None:

        try:
            df = pd.read_csv(uploaded_file)
            return df

        except Exception as e:
            st.error(f"Unable to read uploaded file: {e}")
            return pd.DataFrame()

    # Local dataset options
    possible_files = [
        "inventory_daily.csv",
        "products.csv",
        "sales.csv",
    ]

    for file_name in possible_files:

        if os.path.exists(file_name):

            df = load_csv_file(file_name)

            if not df.empty:
                return df

    return pd.DataFrame()


# =========================================================
# HEADER
# =========================================================

st.title("📦 Supply Chain & Inventory Optimization Analytics")

st.caption(
    "Reduce stockouts, overstocking and delivery delays "
    "through forecasting, ABC analysis, supplier analytics "
    "and inventory optimization."
)


# =========================================================
# LOAD DATA
# =========================================================

raw_df = load_data()

if raw_df.empty:

    st.warning(
        "No inventory dataset found. "
        "Upload a CSV file from the sidebar."
    )

    st.markdown("### Expected dataset columns")

    st.write("""
    Your dataset may contain these columns:

    - Product / Product Name
    - Warehouse / Location
    - Category
    - Stock / Quantity
    - Sales
    - Reorder Point
    - Supplier
    - Lead Time
    - Unit Price
    - Date

    Column names do not need to match exactly.
    """)

    st.stop()


df = an.standardize_data(raw_df)


# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.header("🔎 Dashboard Filters")


# Warehouse filter
warehouse_options = sorted(
    df["warehouse"].dropna().astype(str).unique().tolist()
)

selected_warehouses = st.sidebar.multiselect(
    "Warehouse",
    warehouse_options,
    default=warehouse_options
)


# Category filter
category_options = sorted(
    df["category"].dropna().astype(str).unique().tolist()
)

selected_categories = st.sidebar.multiselect(
    "Category",
    category_options,
    default=category_options
)


# Apply filters
filtered_df = df.copy()


if selected_warehouses:

    filtered_df = filtered_df[
        filtered_df["warehouse"].isin(selected_warehouses)
    ]


if selected_categories:

    filtered_df = filtered_df[
        filtered_df["category"].isin(selected_categories)
    ]


if filtered_df.empty:

    st.warning("No data available for the selected filters.")

    st.stop()


# =========================================================
# KPI SECTION
# =========================================================

st.header("📊 Key Performance Indicators")


kpis = an.headline_kpis(filtered_df)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Total Products",
        f"{kpis['total_products']:,}"
    )


with col2:

    st.metric(
        "Total Stock",
        f"{kpis['total_stock']:,.0f}"
    )


with col3:

    st.metric(
        "Stockout Rate",
        f"{kpis['stockout_rate']:.2f}%"
    )


with col4:

    st.metric(
        "Fill Rate",
        f"{kpis['fill_rate']:.2f}%"
    )


col5, col6, col7 = st.columns(3)


with col5:

    st.metric(
        "Total Sales",
        f"{kpis['total_sales']:,.0f}"
    )


with col6:

    st.metric(
        "Inventory Value",
        f"₹{kpis['inventory_value']:,.2f}"
    )


with col7:

    st.metric(
        "Low Stock Items",
        f"{kpis['low_stock_items']:,}"
    )


st.divider()


# =========================================================
# INVENTORY DISTRIBUTION
# =========================================================

st.header("📦 Inventory Distribution")


col1, col2 = st.columns(2)


category_data = an.inventory_by_category(filtered_df)


with col1:

    st.subheader("Inventory by Category")

    if not category_data.empty:

        fig = px.bar(
            category_data,
            x="category",
            y="total_stock",
            color="category",
            title="Stock by Product Category",
            labels={
                "category": "Category",
                "total_stock": "Stock Quantity"
            }
        )

        fig.update_layout(
            showlegend=False,
            template="plotly_white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info("Category data unavailable.")


warehouse_data = an.inventory_by_warehouse(filtered_df)


with col2:

    st.subheader("Inventory by Warehouse")

    if not warehouse_data.empty:

        fig = px.bar(
            warehouse_data,
            x="warehouse",
            y="total_stock",
            color="warehouse",
            title="Stock Distribution Across Warehouses",
            labels={
                "warehouse": "Warehouse",
                "total_stock": "Stock Quantity"
            }
        )

        fig.update_layout(
            showlegend=False,
            template="plotly_white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info("Warehouse data unavailable.")


# =========================================================
# STOCK STATUS
# =========================================================

st.header("📈 Stock Status")


status_df = an.stock_status(filtered_df)


if not status_df.empty:

    status_counts = (
        status_df["stock_status"]
        .value_counts()
        .reset_index()
    )

    status_counts.columns = [
        "stock_status",
        "count"
    ]

    fig = px.pie(
        status_counts,
        names="stock_status",
        values="count",
        hole=0.45,
        title="Inventory Stock Status"
    )

    fig.update_layout(
        template="plotly_white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =========================================================
# LOW STOCK ALERTS
# =========================================================

st.header("⚠️ Low Stock Alerts")


alerts = an.low_stock_alerts(filtered_df)


if alerts.empty:

    st.success("All products have sufficient inventory.")

else:

    st.warning(
        f"{len(alerts)} products require inventory attention."
    )

    display_columns = [
        "product",
        "warehouse",
        "category",
        "stock",
        "reorder_point",
        "shortage",
        "supplier"
    ]

    display_columns = [
        col for col in display_columns
        if col in alerts.columns
    ]

    st.dataframe(
        alerts[display_columns],
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# ABC ANALYSIS
# =========================================================

st.header("📊 ABC Inventory Analysis")


abc_df = an.abc_analysis(filtered_df)


if not abc_df.empty:

    col1, col2 = st.columns(2)


    with col1:

        abc_counts = (
            abc_df["abc_class"]
            .value_counts()
            .reset_index()
        )

        abc_counts.columns = [
            "ABC Class",
            "Products"
        ]

        fig = px.pie(
            abc_counts,
            names="ABC Class",
            values="Products",
            title="Products by ABC Class"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    with col2:

        fig = px.bar(
            abc_df.head(15),
            x="product",
            y="revenue",
            color="abc_class",
            title="Top Products by Revenue",
            labels={
                "product": "Product",
                "revenue": "Revenue"
            }
        )

        fig.update_layout(
            template="plotly_white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    st.subheader("ABC Product Details")

    st.dataframe(
        abc_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# SUPPLIER ANALYSIS
# =========================================================

st.header("🚚 Supplier Performance Analysis")


supplier_df = an.supplier_analysis(filtered_df)


if not supplier_df.empty:

    col1, col2 = st.columns(2)


    with col1:

        fig = px.bar(
            supplier_df,
            x="supplier",
            y="total_sales",
            color="supplier",
            title="Sales by Supplier"
        )

        fig.update_layout(
            showlegend=False,
            template="plotly_white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    with col2:

        fig = px.bar(
            supplier_df,
            x="supplier",
            y="average_lead_time",
            color="supplier",
            title="Average Supplier Lead Time"
        )

        fig.update_layout(
            showlegend=False,
            template="plotly_white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


    st.subheader("Supplier Details")

    st.dataframe(
        supplier_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# FORECASTING
# =========================================================

st.header("🔮 Inventory Forecast & Reorder Recommendation")


forecast_df = an.inventory_forecast(filtered_df)


if not forecast_df.empty:

    st.dataframe(
        forecast_df,
        use_container_width=True,
        hide_index=True
    )


    fig = px.bar(
        forecast_df.head(15),
        x="product",
        y="recommended_order",
        color="recommended_order",
        title="Recommended Order Quantity"
    )

    fig.update_layout(
        template="plotly_white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =========================================================
# SALES TREND
# =========================================================

st.header("📅 Sales Trend Analysis")


trend_df = an.sales_trend(filtered_df)


if not trend_df.empty:

    fig = px.line(
        trend_df,
        x="date",
        y="sales",
        markers=True,
        title="Sales Over Time"
    )

    fig.update_layout(
        template="plotly_white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.info(
        "Date-based sales trend is unavailable. "
        "Your dataset needs a Date column."
    )


# =========================================================
# RAW DATA
# =========================================================

with st.expander("📋 View Dataset"):

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# DOWNLOAD DATA
# =========================================================

st.header("📥 Download Reports")


csv_data = filtered_df.to_csv(index=False).encode("utf-8")


st.download_button(
    label="Download Filtered Inventory CSV",
    data=csv_data,
    file_name="filtered_inventory_report.csv",
    mime="text/csv"
)


st.success("Dashboard loaded successfully!")

