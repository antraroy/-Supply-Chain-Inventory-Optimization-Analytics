import streamlit as st
import pandas as pd
import numpy as np
import os

import analysis


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Supply Chain Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #f7f9fc;
}

[data-testid="stMetric"] {
    background-color: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}

h1 {
    color: #14213d;
}

h2, h3 {
    color: #1f2937;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_csv(file_path):

    try:

        df = pd.read_csv(file_path)

        return analysis.clean_data(df)

    except Exception as e:

        st.error(f"Unable to load CSV: {e}")

        return pd.DataFrame()


def load_uploaded_file(uploaded_file):

    try:

        df = pd.read_csv(uploaded_file)

        return analysis.clean_data(df)

    except Exception as e:

        st.error(f"Error reading uploaded file: {e}")

        return pd.DataFrame()


# =========================================================
# FIND DATASET
# =========================================================

def get_dataset():

    uploaded_file = st.sidebar.file_uploader(
        "Upload Inventory CSV",
        type=["csv"]
    )

    if uploaded_file is not None:

        df = load_uploaded_file(uploaded_file)

        return df

    possible_files = [
        "inventory.csv",
        "inventory_data.csv",
        "supply_chain.csv",
        "data.csv",
        "inventory_dataset.csv"
    ]

    for file_name in possible_files:

        if os.path.exists(file_name):

            return load_csv(file_name)

    # Search in data folder
    if os.path.exists("data"):

        for file_name in os.listdir("data"):

            if file_name.lower().endswith(".csv"):

                file_path = os.path.join(
                    "data",
                    file_name
                )

                return load_csv(file_path)

    return pd.DataFrame()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🔎 Dashboard Filters")

st.sidebar.markdown("---")

df_original = get_dataset()


# =========================================================
# DATA NOT FOUND
# =========================================================

if df_original.empty:

    st.title("📦 Supply Chain & Inventory Optimization Analytics")

    st.warning(
        "No inventory dataset found. "
        "Upload your CSV file using the sidebar."
    )

    st.markdown("""
    ### Expected dataset columns

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


# =========================================================
# FILTERS
# =========================================================

df = df_original.copy()


# Warehouse filter
warehouse_col = analysis.get_column(
    df,
    "warehouse"
)

if warehouse_col is not None:

    warehouse_options = sorted(
        df[warehouse_col]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_warehouses = st.sidebar.multiselect(
        "Warehouse",
        options=warehouse_options,
        default=warehouse_options
    )

    if selected_warehouses:

        df = df[
            df[warehouse_col]
            .astype(str)
            .isin(selected_warehouses)
        ]

    else:

        df = df.iloc[0:0]

else:

    st.sidebar.info(
        "Warehouse column not available."
    )


# Category filter
category_col = analysis.get_column(
    df,
    "category"
)

if category_col is not None:

    category_options = sorted(
        df[category_col]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_categories = st.sidebar.multiselect(
        "Category",
        options=category_options,
        default=category_options
    )

    if selected_categories:

        df = df[
            df[category_col]
            .astype(str)
            .isin(selected_categories)
        ]

    else:

        df = df.iloc[0:0]

else:

    st.sidebar.info(
        "Category column not available."
    )


# =========================================================
# HEADER
# =========================================================

st.title(
    "📦 Supply Chain & Inventory Optimization Analytics"
)

st.markdown("""
Reduce stockouts, overstocking and delivery delays through
forecasting, ABC analysis, supplier scorecards and
reorder-point optimization.
""")


st.markdown("---")


# =========================================================
# NO FILTERED DATA
# =========================================================

if df.empty:

    st.warning(
        "No data available for the selected filters."
    )

    st.stop()


# =========================================================
# KPI SECTION
# =========================================================

st.header("📊 Key Performance Indicators")


kpis = analysis.headline_kpis(df)


col1, col2, col3, col4 = st.columns(4)


col1.metric(
    "Total Products",
    f"{kpis['total_products']:,}"
)


col2.metric(
    "Total Stock",
    f"{kpis['total_stock']:,.0f}"
)


col3.metric(
    "Stockout Rate",
    f"{kpis['stockout_rate']:.2f}%"
)


col4.metric(
    "Fill Rate",
    f"{kpis['fill_rate']:.2f}%"
)


col5, col6, col7 = st.columns(3)


col5.metric(
    "Inventory Value",
    f"₹{kpis['inventory_value']:,.2f}"
)


col6.metric(
    "Low Stock Items",
    f"{kpis['low_stock_items']:,}"
)


col7.metric(
    "Average Lead Time",
    f"{kpis['average_lead_time']:.2f} days"
)


st.markdown("---")


# =========================================================
# INVENTORY ANALYSIS
# =========================================================

st.header("📦 Inventory Analytics")


left_col, right_col = st.columns(2)


# =========================================================
# INVENTORY DISTRIBUTION
# =========================================================

with left_col:

    st.subheader("Inventory Distribution")

    inventory_data = analysis.inventory_distribution(df)

    if not inventory_data.empty:

        st.bar_chart(
            inventory_data.set_index("Category")
        )

    else:

        st.info(
            "Category or stock column not found."
        )


# =========================================================
# STOCK STATUS
# =========================================================

with right_col:

    st.subheader("Stock Status")

    status_data = analysis.stock_status(df)

    if not status_data.empty:

        status_counts = (
            status_data["Stock Status"]
            .value_counts()
            .reset_index()
        )

        status_counts.columns = [
            "Status",
            "Count"
        ]

        st.bar_chart(
            status_counts.set_index("Status")
        )

    else:

        st.info(
            "Stock column not found."
        )


st.markdown("---")


# =========================================================
# LOW STOCK ALERTS
# =========================================================

st.header("⚠️ Low Stock Alerts")


low_stock_data = analysis.low_stock_alerts(df)


if not low_stock_data.empty:

    st.warning(
        f"{len(low_stock_data)} product(s) require attention."
    )

    st.dataframe(
        low_stock_data,
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "✅ No low-stock products found."
    )


st.markdown("---")


# =========================================================
# REORDER RECOMMENDATIONS
# =========================================================

st.header("🔄 Reorder Recommendations")


reorder_data = analysis.reorder_recommendations(df)


if not reorder_data.empty:

    st.info(
        f"{len(reorder_data)} product(s) need replenishment."
    )

    st.dataframe(
        reorder_data,
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "No reorder recommendations available."
    )


st.markdown("---")


# =========================================================
# ABC ANALYSIS
# =========================================================

st.header("📈 ABC Inventory Analysis")


abc_data = analysis.abc_analysis(df)


if not abc_data.empty:

    abc_col1, abc_col2 = st.columns(2)

    with abc_col1:

        abc_counts = (
            abc_data["ABC Class"]
            .value_counts()
            .reset_index()
        )

        abc_counts.columns = [
            "Class",
            "Products"
        ]

        st.subheader("Product Distribution")

        st.bar_chart(
            abc_counts.set_index("Class")
        )

    with abc_col2:

        st.subheader("ABC Classification")

        st.dataframe(
            abc_data,
            use_container_width=True,
            hide_index=True
        )

else:

    st.info(
        "ABC Analysis requires stock quantity and unit price columns."
    )


st.markdown("---")


# =========================================================
# SUPPLIER ANALYSIS
# =========================================================

st.header("🏭 Supplier Scorecard")


supplier_data = analysis.supplier_scorecard(df)


if not supplier_data.empty:

    st.dataframe(
        supplier_data,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "Supplier column not found in dataset."
    )


st.markdown("---")


# =========================================================
# WAREHOUSE ANALYSIS
# =========================================================

st.header("🏢 Warehouse Performance")


warehouse_data = analysis.warehouse_analysis(df)


if not warehouse_data.empty:

    st.dataframe(
        warehouse_data,
        use_container_width=True,
        hide_index=True
    )

    if "Total Stock" in warehouse_data.columns:

        st.bar_chart(
            warehouse_data.set_index("Warehouse")
        )

else:

    st.info(
        "Warehouse information is not available."
    )


st.markdown("---")


# =========================================================
# SALES TREND
# =========================================================

st.header("📅 Sales Trend")


trend_data = analysis.sales_trend(df)


if not trend_data.empty:

    st.line_chart(
        trend_data.set_index("Date")
    )

else:

    st.info(
        "Date or sales columns are not available "
        "for sales trend analysis."
    )


st.markdown("---")


# =========================================================
# DATASET INFORMATION
# =========================================================

with st.expander("📋 Dataset Information"):

    summary = analysis.dataset_summary(df)

    st.write(
        f"**Rows:** {summary.get('rows', 0)}"
    )

    st.write(
        f"**Columns:** {summary.get('columns', 0)}"
    )

    st.write(
        f"**Missing Values:** "
        f"{summary.get('missing_values', 0)}"
    )

    st.write(
        f"**Duplicate Rows:** "
        f"{summary.get('duplicate_rows', 0)}"
    )

    st.write("### Column Names")

    st.write(
        summary.get("column_names", [])
    )


# =========================================================
# RAW DATA
# =========================================================

with st.expander("👁️ View Raw Dataset"):

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "Supply Chain & Inventory Optimization Analytics Dashboard"
)
