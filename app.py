# ============================================================
# SUPPLY CHAIN & INVENTORY OPTIMIZATION ANALYTICS
# app.py - Complete, error-resistant Streamlit dashboard
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Supply Chain Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIRS = [
    BASE_DIR,
    BASE_DIR / "data",
    BASE_DIR / "datasets",
    BASE_DIR / "Dataset",
    BASE_DIR / "Data",
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_column_name(column):
    """Normalize column names for easier matching."""
    return (
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def clean_dataframe(df):
    """Clean column names and remove completely empty rows."""

    if df is None:
        return pd.DataFrame()

    df = df.copy()

    df.columns = [
        normalize_column_name(col)
        for col in df.columns
    ]

    df = df.dropna(how="all")

    return df


def find_column(df, possible_names):
    """
    Find a column using multiple possible names.
    """

    if df is None or df.empty:
        return None

    columns = list(df.columns)

    normalized_columns = {
        normalize_column_name(col): col
        for col in columns
    }

    for name in possible_names:

        normalized_name = normalize_column_name(name)

        if normalized_name in normalized_columns:
            return normalized_columns[normalized_name]

    # Partial matching
    for name in possible_names:

        normalized_name = normalize_column_name(name)

        for col in columns:

            if normalized_name in normalize_column_name(col):
                return col

    return None


def safe_numeric(series):
    """Convert values to numeric safely."""

    if series is None:
        return pd.Series(dtype=float)

    return pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)


def safe_sum(df, column):
    """Safely calculate sum."""

    if df.empty or column is None:
        return 0

    return safe_numeric(df[column]).sum()


def safe_mean(df, column):
    """Safely calculate average."""

    if df.empty or column is None:
        return 0

    values = safe_numeric(df[column])

    if len(values) == 0:
        return 0

    return values.mean()


def safe_percentage(numerator, denominator):
    """Safely calculate percentage."""

    if denominator == 0:
        return 0

    return (numerator / denominator) * 100


def format_currency(value):
    """Format Indian currency."""

    try:
        return f"₹{value:,.2f}"
    except:
        return "₹0.00"


def format_number(value):
    """Format numbers."""

    try:
        return f"{value:,.0f}"
    except:
        return "0"


def load_csv_file(filename):
    """
    Search CSV in project root and common folders.
    """

    for folder in DATA_DIRS:

        file_path = folder / filename

        if file_path.exists():

            try:

                df = pd.read_csv(file_path)

                return clean_dataframe(df)

            except Exception as e:

                st.warning(
                    f"Could not read {filename}: {e}"
                )

    return pd.DataFrame()


def load_data():

    products = load_csv_file("products.csv")
    sales = load_csv_file("sales.csv")
    inventory = load_csv_file("inventory_daily.csv")
    purchase_orders = load_csv_file("purchase_orders.csv")
    suppliers = load_csv_file("suppliers.csv")

    return (
        products,
        sales,
        inventory,
        purchase_orders,
        suppliers
    )


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def cached_load_data():

    return load_data()


try:

    (
        products,
        sales,
        inventory,
        purchase_orders,
        suppliers
    ) = cached_load_data()

except Exception as e:

    st.error("Unable to load project datasets.")

    st.exception(e)

    st.stop()


# ============================================================
# CHECK DATASETS
# ============================================================

datasets = {
    "Products": products,
    "Sales": sales,
    "Inventory": inventory,
    "Purchase Orders": purchase_orders,
    "Suppliers": suppliers
}

available_datasets = {
    name: df
    for name, df in datasets.items()
    if not df.empty
}

if not available_datasets:

    st.error(
        "No datasets were found. "
        "Please upload CSV files or place them in the project folder."
    )

    st.info(
        "Expected files: products.csv, sales.csv, "
        "inventory_daily.csv, purchase_orders.csv, suppliers.csv"
    )

    st.stop()


# ============================================================
# COLUMN DETECTION
# ============================================================

# Products

product_id_col = find_column(
    products,
    [
        "product_id",
        "product",
        "sku",
        "item_id"
    ]
)

product_name_col = find_column(
    products,
    [
        "product_name",
        "name",
        "product",
        "item_name"
    ]
)

product_category_col = find_column(
    products,
    [
        "category",
        "product_category",
        "product_type"
    ]
)


# Sales

sales_product_col = find_column(
    sales,
    [
        "product_id",
        "product",
        "sku",
        "item_id"
    ]
)

sales_quantity_col = find_column(
    sales,
    [
        "quantity",
        "units_sold",
        "sales_quantity",
        "qty_sold",
        "sold"
    ]
)

sales_revenue_col = find_column(
    sales,
    [
        "revenue",
        "sales",
        "sales_amount",
        "total_sales",
        "amount"
    ]
)

sales_date_col = find_column(
    sales,
    [
        "date",
        "order_date",
        "sales_date",
        "transaction_date"
    ]
)

sales_category_col = find_column(
    sales,
    [
        "category",
        "product_category"
    ]
)

sales_warehouse_col = find_column(
    sales,
    [
        "warehouse",
        "warehouse_name",
        "location"
    ]
)


# Inventory

inventory_product_col = find_column(
    inventory,
    [
        "product_id",
        "product",
        "sku",
        "item_id"
    ]
)

inventory_quantity_col = find_column(
    inventory,
    [
        "stock_quantity",
        "quantity",
        "inventory_quantity",
        "stock",
        "current_stock",
        "available_quantity",
        "on_hand"
    ]
)

inventory_reorder_col = find_column(
    inventory,
    [
        "reorder_level",
        "reorder_point",
        "minimum_stock",
        "min_stock",
        "safety_stock"
    ]
)

inventory_category_col = find_column(
    inventory,
    [
        "category",
        "product_category"
    ]
)

inventory_warehouse_col = find_column(
    inventory,
    [
        "warehouse",
        "warehouse_name",
        "location"
    ]
)


# Purchase Orders

po_supplier_col = find_column(
    purchase_orders,
    [
        "supplier",
        "supplier_name",
        "supplier_id"
    ]
)

po_quantity_col = find_column(
    purchase_orders,
    [
        "quantity",
        "order_quantity",
        "quantity_ordered",
        "qty"
    ]
)

po_date_col = find_column(
    purchase_orders,
    [
        "order_date",
        "date",
        "purchase_date"
    ]
)

po_delivery_col = find_column(
    purchase_orders,
    [
        "delivery_date",
        "actual_delivery_date",
        "received_date"
    ]
)

po_status_col = find_column(
    purchase_orders,
    [
        "status",
        "order_status",
        "delivery_status"
    ]
)


# Suppliers

supplier_name_col = find_column(
    suppliers,
    [
        "supplier_name",
        "supplier",
        "name",
        "supplier_id"
    ]
)

supplier_lead_time_col = find_column(
    suppliers,
    [
        "lead_time",
        "lead_time_days",
        "delivery_days"
    ]
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🔎 Dashboard Filters")

# Warehouse filter

warehouse_options = []

for df, col in [
    (inventory, inventory_warehouse_col),
    (sales, sales_warehouse_col)
]:

    if col and not df.empty:

        warehouse_options.extend(
            df[col]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

warehouse_options = sorted(
    list(set(warehouse_options))
)

selected_warehouses = st.sidebar.multiselect(
    "Warehouse",
    warehouse_options,
    default=warehouse_options
)


# Category filter

category_options = []

for df, col in [
    (products, product_category_col),
    (inventory, inventory_category_col),
    (sales, sales_category_col)
]:

    if col and not df.empty:

        category_options.extend(
            df[col]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

category_options = sorted(
    list(set(category_options))
)

selected_categories = st.sidebar.multiselect(
    "Category",
    category_options,
    default=category_options
)


# ============================================================
# FILTER DATA
# ============================================================

filtered_inventory = inventory.copy()
filtered_sales = sales.copy()
filtered_products = products.copy()
filtered_purchase_orders = purchase_orders.copy()
filtered_suppliers = suppliers.copy()


# Warehouse filter

if selected_warehouses:

    if inventory_warehouse_col:

        filtered_inventory = filtered_inventory[
            filtered_inventory[
                inventory_warehouse_col
            ].astype(str).isin(selected_warehouses)
        ]

    if sales_warehouse_col:

        filtered_sales = filtered_sales[
            filtered_sales[
                sales_warehouse_col
            ].astype(str).isin(selected_warehouses)
        ]


# Category filter

if selected_categories:

    if inventory_category_col:

        filtered_inventory = filtered_inventory[
            filtered_inventory[
                inventory_category_col
            ].astype(str).isin(selected_categories)
        ]

    if sales_category_col:

        filtered_sales = filtered_sales[
            filtered_sales[
                sales_category_col
            ].astype(str).isin(selected_categories)
        ]

    if product_category_col:

        filtered_products = filtered_products[
            filtered_products[
                product_category_col
            ].astype(str).isin(selected_categories)
        ]


# ============================================================
# HEADER
# ============================================================

st.title(
    "📦 Supply Chain & Inventory Optimization Analytics"
)

st.caption(
    "Reduce stockouts, overstocking and delivery delays "
    "through forecasting, ABC analysis, supplier scorecards "
    "and reorder-point optimization."
)

st.divider()


# ============================================================
# KPI CALCULATIONS
# ============================================================

# Revenue

revenue = safe_sum(
    filtered_sales,
    sales_revenue_col
)


# Units sold

units_sold = safe_sum(
    filtered_sales,
    sales_quantity_col
)


# Products

if product_id_col and not filtered_products.empty:

    total_products = (
        filtered_products[
            product_id_col
        ].nunique()
    )

else:

    total_products = len(filtered_products)


# Inventory quantity

total_inventory = safe_sum(
    filtered_inventory,
    inventory_quantity_col
)


# Stockout products

stockout_count = 0

if inventory_quantity_col and not filtered_inventory.empty:

    stock_values = safe_numeric(
        filtered_inventory[
            inventory_quantity_col
        ]
    )

    stockout_count = (
        stock_values <= 0
    ).sum()


# Low stock products

low_stock_count = 0

if (
    inventory_quantity_col
    and inventory_reorder_col
    and not filtered_inventory.empty
):

    stock = safe_numeric(
        filtered_inventory[
            inventory_quantity_col
        ]
    )

    reorder = safe_numeric(
        filtered_inventory[
            inventory_reorder_col
        ]
    )

    low_stock_count = (
        stock <= reorder
    ).sum()


# Stockout rate

if len(filtered_inventory) > 0:

    stockout_rate = safe_percentage(
        stockout_count,
        len(filtered_inventory)
    )

else:

    stockout_rate = 0


# Inventory value

inventory_value_col = find_column(
    filtered_inventory,
    [
        "inventory_value",
        "inventory_cost",
        "stock_value",
        "total_inventory_value"
    ]
)

inventory_value = safe_sum(
    filtered_inventory,
    inventory_value_col
)


# Purchase orders

total_purchase_orders = len(
    filtered_purchase_orders
)


# Suppliers

if supplier_name_col and not filtered_suppliers.empty:

    total_suppliers = (
        filtered_suppliers[
            supplier_name_col
        ].nunique()
    )

else:

    total_suppliers = len(filtered_suppliers)


# Lead time

average_lead_time = safe_mean(
    filtered_suppliers,
    supplier_lead_time_col
)


# Fill rate

fill_rate = 0

demand_col = find_column(
    filtered_sales,
    [
        "demand",
        "customer_demand",
        "demand_quantity"
    ]
)

if demand_col and sales_quantity_col:

    total_demand = safe_sum(
        filtered_sales,
        demand_col
    )

    total_fulfilled = safe_sum(
        filtered_sales,
        sales_quantity_col
    )

    fill_rate = safe_percentage(
        total_fulfilled,
        total_demand
    )


# ============================================================
# KPI DISPLAY
# ============================================================

st.header("📊 Key Performance Indicators")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Total Revenue",
    format_currency(revenue)
)

kpi2.metric(
    "Units Sold",
    format_number(units_sold)
)

kpi3.metric(
    "Total Products",
    format_number(total_products)
)

kpi4.metric(
    "Inventory Value",
    format_currency(inventory_value)
)


kpi5, kpi6, kpi7, kpi8 = st.columns(4)

kpi5.metric(
    "Total Stock",
    format_number(total_inventory)
)

kpi6.metric(
    "Stockout Rate",
    f"{stockout_rate:.2f}%"
)

kpi7.metric(
    "Low Stock Items",
    format_number(low_stock_count)
)

kpi8.metric(
    "Total Suppliers",
    format_number(total_suppliers)
)


st.divider()


# ============================================================
# SALES ANALYSIS
# ============================================================

st.header("💰 Sales Analytics")

if filtered_sales.empty:

    st.info("Sales dataset is not available.")

else:

    sales_col1, sales_col2 = st.columns(2)

    # Revenue by category

    with sales_col1:

        st.subheader(
            "Revenue by Category"
        )

        category_col = sales_category_col

        if category_col and sales_revenue_col:

            category_sales = (
                filtered_sales
                .groupby(category_col)[
                    sales_revenue_col
                ]
                .apply(
                    lambda x: safe_numeric(x).sum()
                )
                .sort_values(ascending=False)
            )

            if not category_sales.empty:

                st.bar_chart(
                    category_sales
                )

            else:

                st.info(
                    "No category revenue data available."
                )

        else:

            st.info(
                "Category or revenue column not found."
            )


    # Monthly sales trend

    with sales_col2:

        st.subheader(
            "Monthly Sales Trend"
        )

        if sales_date_col and sales_revenue_col:

            sales_trend = filtered_sales.copy()

            sales_trend[sales_date_col] = pd.to_datetime(
                sales_trend[sales_date_col],
                errors="coerce"
            )

            sales_trend = sales_trend.dropna(
                subset=[sales_date_col]
            )

            sales_trend["month"] = (
                sales_trend[sales_date_col]
                .dt.to_period("M")
                .astype(str)
            )

            monthly_revenue = (
                sales_trend
                .groupby("month")[
                    sales_revenue_col
                ]
                .apply(
                    lambda x: safe_numeric(x).sum()
                )
            )

            if not monthly_revenue.empty:

                st.line_chart(
                    monthly_revenue
                )

            else:

                st.info(
                    "No monthly sales data available."
                )

        else:

            st.info(
                "Date or revenue column not found."
            )


# ============================================================
# TOP PRODUCTS
# ============================================================

st.subheader("🏆 Top Products")

if (
    sales_product_col
    and sales_quantity_col
    and not filtered_sales.empty
):

    top_products = (
        filtered_sales
        .groupby(sales_product_col)[
            sales_quantity_col
        ]
        .apply(
            lambda x: safe_numeric(x).sum()
        )
        .sort_values(ascending=False)
        .head(10)
    )

    st.bar_chart(
        top_products
    )

else:

    st.info(
        "Product or quantity column not found."
    )


# ============================================================
# INVENTORY ANALYSIS
# ============================================================

st.divider()

st.header("📦 Inventory Analytics")


if filtered_inventory.empty:

    st.warning(
        "Inventory data is unavailable."
    )

else:

    inventory_col1, inventory_col2 = st.columns(2)


    # Inventory distribution

    with inventory_col1:

        st.subheader(
            "Inventory Distribution"
        )

        if inventory_category_col and inventory_quantity_col:

            inventory_by_category = (
                filtered_inventory
                .groupby(inventory_category_col)[
                    inventory_quantity_col
                ]
                .apply(
                    lambda x: safe_numeric(x).sum()
                )
                .sort_values(ascending=False)
            )

            st.bar_chart(
                inventory_by_category
            )

        else:

            st.info(
                "Category or stock column not found."
            )


    # Stock status

    with inventory_col2:

        st.subheader(
            "Stock Status"
        )

        if inventory_quantity_col:

            stock_data = safe_numeric(
                filtered_inventory[
                    inventory_quantity_col
                ]
            )

            stock_status = pd.DataFrame(
                {
                    "Status": [
                        "Out of Stock",
                        "Low Stock",
                        "Healthy Stock"
                    ],
                    "Count": [
                        (stock_data <= 0).sum(),
                        low_stock_count,
                        max(
                            len(stock_data)
                            - stockout_count
                            - low_stock_count,
                            0
                        )
                    ]
                }
            )

            stock_status = stock_status.set_index(
                "Status"
            )

            st.bar_chart(
                stock_status
            )


# ============================================================
# LOW STOCK TABLE
# ============================================================

st.subheader("⚠️ Low Stock Alerts")

if (
    inventory_quantity_col
    and inventory_reorder_col
    and not filtered_inventory.empty
):

    low_stock_df = filtered_inventory.copy()

    low_stock_df["stock_numeric"] = safe_numeric(
        low_stock_df[
            inventory_quantity_col
        ]
    )

    low_stock_df["reorder_numeric"] = safe_numeric(
        low_stock_df[
            inventory_reorder_col
        ]
    )

    low_stock_df = low_stock_df[
        low_stock_df["stock_numeric"]
        <= low_stock_df["reorder_numeric"]
    ]

    display_columns = [
        col
        for col in [
            inventory_product_col,
            inventory_category_col,
            inventory_warehouse_col,
            inventory_quantity_col,
            inventory_reorder_col
        ]
        if col is not None
        and col in low_stock_df.columns
    ]

    if not low_stock_df.empty:

        st.dataframe(
            low_stock_df[
                display_columns
            ].head(100),
            use_container_width=True
        )

    else:

        st.success(
            "No low-stock products found."
        )

else:

    st.info(
        "Reorder point information is unavailable."
    )


# ============================================================
# PURCHASE ORDER ANALYSIS
# ============================================================

st.divider()

st.header("🚚 Purchase Order Analytics")


if filtered_purchase_orders.empty:

    st.info(
        "Purchase order dataset is unavailable."
    )

else:

    po_col1, po_col2 = st.columns(2)


    # Purchase quantity by supplier

    with po_col1:

        st.subheader(
            "Purchase Quantity by Supplier"
        )

        if po_supplier_col and po_quantity_col:

            supplier_purchases = (
                filtered_purchase_orders
                .groupby(po_supplier_col)[
                    po_quantity_col
                ]
                .apply(
                    lambda x: safe_numeric(x).sum()
                )
                .sort_values(ascending=False)
            )

            st.bar_chart(
                supplier_purchases
            )

        else:

            st.info(
                "Supplier or quantity column not found."
            )


    # Purchase order status

    with po_col2:

        st.subheader(
            "Purchase Order Status"
        )

        if po_status_col:

            status_counts = (
                filtered_purchase_orders[
                    po_status_col
                ]
                .astype(str)
                .value_counts()
            )

            st.bar_chart(
                status_counts
            )

        else:

            st.info(
                "Purchase order status column not found."
            )


# ============================================================
# SUPPLIER ANALYSIS
# ============================================================

st.divider()

st.header("🏭 Supplier Analytics")


if filtered_suppliers.empty:

    st.info(
        "Supplier dataset is unavailable."
    )

else:

    supplier_col1, supplier_col2 = st.columns(2)


    # Lead time

    with supplier_col1:

        st.subheader(
            "Average Supplier Lead Time"
        )

        if (
            supplier_name_col
            and supplier_lead_time_col
        ):

            lead_time_analysis = (
                filtered_suppliers
                .groupby(supplier_name_col)[
                    supplier_lead_time_col
                ]
                .apply(
                    lambda x: safe_numeric(x).mean()
                )
                .sort_values(ascending=False)
            )

            st.bar_chart(
                lead_time_analysis
            )

        else:

            st.info(
                "Supplier or lead time column not found."
            )


    # Supplier table

    with supplier_col2:

        st.subheader(
            "Supplier Details"
        )

        st.dataframe(
            filtered_suppliers.head(100),
            use_container_width=True
        )


# ============================================================
# DATA TABLES
# ============================================================

st.divider()

st.header("📋 Dataset Explorer")


dataset_choice = st.selectbox(
    "Select dataset",
    list(available_datasets.keys())
)


selected_dataset = available_datasets[
    dataset_choice
]


st.write(
    f"Total records: {len(selected_dataset):,}"
)


st.dataframe(
    selected_dataset.head(500),
    use_container_width=True
)


# ============================================================
# DOWNLOAD DATA
# ============================================================

st.subheader("⬇️ Download Filtered Data")

if not filtered_inventory.empty:

    inventory_csv = filtered_inventory.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Inventory CSV",
        data=inventory_csv,
        file_name="filtered_inventory.csv",
        mime="text/csv"
    )


if not filtered_sales.empty:

    sales_csv = filtered_sales.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Sales CSV",
        data=sales_csv,
        file_name="filtered_sales.csv",
        mime="text/csv"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Supply Chain & Inventory Optimization Analytics | "
    "Built with Python, Pandas and Streamlit"
)

st.caption(
    "Dashboard provides descriptive analytics based on "
    "the available project datasets."
)
