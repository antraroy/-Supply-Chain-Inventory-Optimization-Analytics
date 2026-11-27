import pandas as pd
import numpy as np


# =========================================================
# COLUMN DETECTION
# =========================================================

COLUMN_ALIASES = {
    "product": [
        "product", "product_name", "item", "item_name",
        "sku", "product_id", "item_id"
    ],
    "warehouse": [
        "warehouse", "warehouse_name", "warehouse_id",
        "location", "warehouse_location", "store", "branch"
    ],
    "category": [
        "category", "product_category", "category_name",
        "product_type", "type"
    ],
    "stock": [
        "stock", "stock_quantity", "quantity", "inventory",
        "available_stock", "inventory_level", "units_in_stock"
    ],
    "sales": [
        "sales", "sale", "units_sold", "sales_quantity",
        "demand", "quantity_sold"
    ],
    "reorder_point": [
        "reorder_point", "reorder level", "reorder_level",
        "minimum_stock", "min_stock"
    ],
    "supplier": [
        "supplier", "supplier_name", "vendor", "vendor_name"
    ],
    "lead_time": [
        "lead_time", "lead time", "delivery_time",
        "delivery_days", "supplier_lead_time"
    ],
    "unit_price": [
        "unit_price", "price", "cost", "product_price",
        "selling_price"
    ],
    "date": [
        "date", "order_date", "sales_date", "transaction_date",
        "timestamp"
    ],
}


def normalize_column_name(column):
    return (
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def find_column(df, column_type):
    """
    Finds a column using predefined aliases.
    Returns None if column is not found.
    """

    if df is None or df.empty:
        return None

    normalized_columns = {
        normalize_column_name(col): col
        for col in df.columns
    }

    aliases = COLUMN_ALIASES.get(column_type, [])

    for alias in aliases:
        alias = normalize_column_name(alias)

        if alias in normalized_columns:
            return normalized_columns[alias]

    # Partial matching
    for normalized, original in normalized_columns.items():
        for alias in aliases:
            alias = normalize_column_name(alias)

            if alias in normalized:
                return original

    return None


# =========================================================
# DATA CLEANING
# =========================================================

def clean_data(df):
    if df is None:
        return pd.DataFrame()

    df = df.copy()

    df.columns = [
        normalize_column_name(col)
        for col in df.columns
    ]

    df = df.drop_duplicates()

    # Numeric conversion
    numeric_candidates = [
        "stock",
        "stock_quantity",
        "quantity",
        "inventory",
        "available_stock",
        "sales",
        "units_sold",
        "sales_quantity",
        "demand",
        "reorder_point",
        "minimum_stock",
        "min_stock",
        "lead_time",
        "lead_time_days",
        "delivery_time",
        "unit_price",
        "price",
        "cost"
    ]

    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # Date conversion
    date_col = find_column(df, "date")

    if date_col:
        df[date_col] = pd.to_datetime(
            df[date_col],
            errors="coerce"
        )

    return df


# =========================================================
# STANDARDIZE DATASET
# =========================================================

def standardize_data(df):
    df = clean_data(df)

    if df.empty:
        return df

    # Standard columns
    mappings = {
        "product": find_column(df, "product"),
        "warehouse": find_column(df, "warehouse"),
        "category": find_column(df, "category"),
        "stock": find_column(df, "stock"),
        "sales": find_column(df, "sales"),
        "reorder_point": find_column(df, "reorder_point"),
        "supplier": find_column(df, "supplier"),
        "lead_time": find_column(df, "lead_time"),
        "unit_price": find_column(df, "unit_price"),
        "date": find_column(df, "date"),
    }

    for standard_name, original_name in mappings.items():

        if original_name and original_name != standard_name:
            df[standard_name] = df[original_name]

    # Missing default columns
    defaults = {
        "product": "Unknown Product",
        "warehouse": "Unknown Warehouse",
        "category": "Unknown Category",
        "stock": 0,
        "sales": 0,
        "reorder_point": 0,
        "supplier": "Unknown Supplier",
        "lead_time": 0,
        "unit_price": 0,
    }

    for col, default_value in defaults.items():

        if col not in df.columns:
            df[col] = default_value

        df[col] = df[col].fillna(default_value)

    # Convert numeric values safely
    numeric_columns = [
        "stock",
        "sales",
        "reorder_point",
        "lead_time",
        "unit_price"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        ).fillna(0)

    return df


# =========================================================
# KPI CALCULATIONS
# =========================================================

def headline_kpis(df):

    df = standardize_data(df)

    if df.empty:
        return {
            "total_products": 0,
            "total_stock": 0,
            "total_sales": 0,
            "stockout_rate": 0,
            "fill_rate": 0,
            "inventory_value": 0,
            "low_stock_items": 0,
        }

    total_products = df["product"].nunique()

    total_stock = df["stock"].sum()

    total_sales = df["sales"].sum()

    stockout_items = (df["stock"] <= 0).sum()

    stockout_rate = (
        stockout_items / len(df) * 100
        if len(df) > 0
        else 0
    )

    total_demand = df["sales"].sum()

    fill_rate = (
        min(total_stock / total_demand * 100, 100)
        if total_demand > 0
        else 100
    )

    inventory_value = (
        df["stock"] * df["unit_price"]
    ).sum()

    low_stock_items = (
        df["stock"] <= df["reorder_point"]
    ).sum()

    return {
        "total_products": int(total_products),
        "total_stock": float(total_stock),
        "total_sales": float(total_sales),
        "stockout_rate": float(stockout_rate),
        "fill_rate": float(fill_rate),
        "inventory_value": float(inventory_value),
        "low_stock_items": int(low_stock_items),
    }


# =========================================================
# INVENTORY DISTRIBUTION
# =========================================================

def inventory_by_category(df):

    df = standardize_data(df)

    if df.empty:
        return pd.DataFrame()

    result = (
        df.groupby("category", as_index=False)
        .agg(
            total_stock=("stock", "sum"),
            total_sales=("sales", "sum"),
            product_count=("product", "nunique")
        )
    )

    return result.sort_values(
        "total_stock",
        ascending=False
    )


def inventory_by_warehouse(df):

    df = standardize_data(df)

    if df.empty:
        return pd.DataFrame()

    result = (
        df.groupby("warehouse", as_index=False)
        .agg(
            total_stock=("stock", "sum"),
            total_sales=("sales", "sum"),
            product_count=("product", "nunique")
        )
    )

    return result.sort_values(
        "total_stock",
        ascending=False
    )


# =========================================================
# STOCK STATUS
# =========================================================

def stock_status(df):

    df = standardize_data(df)

    if df.empty:
        return pd.DataFrame()

    df["stock_status"] = np.select(
        [
            df["stock"] <= 0,
            df["stock"] <= df["reorder_point"],
        ],
        [
            "Out of Stock",
            "Low Stock",
        ],
        default="Healthy Stock"
    )

    return df


# =========================================================
# LOW STOCK ALERTS
# =========================================================

def low_stock_alerts(df):

    df = standardize_data(df)

    if df.empty:
        return pd.DataFrame()

    alerts = df[
        df["stock"] <= df["reorder_point"]
    ].copy()

    alerts["shortage"] = (
        alerts["reorder_point"] - alerts["stock"]
    ).clip(lower=0)

    return alerts.sort_values(
        "shortage",
        ascending=False
    )


# =========================================================
# ABC ANALYSIS
# =========================================================

def abc_analysis(df):

    df = standardize_data(df)

    if df.empty:
        return pd.DataFrame()

    df["revenue"] = (
        df["sales"] * df["unit_price"]
    )

    if df["revenue"].sum() == 0:

        df["revenue"] = df["stock"] * df["unit_price"]

    result = (
        df.groupby("product", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            stock=("stock", "sum"),
            category=("category", "first")
        )
    )

    result = result.sort_values(
        "revenue",
        ascending=False
    )

    total_revenue = result["revenue"].sum()

    if total_revenue == 0:
        result["cumulative_percentage"] = 0
        result["abc_class"] = "C"
        return result

    result["percentage"] = (
        result["revenue"] / total_revenue * 100
    )

    result["cumulative_percentage"] = (
        result["percentage"].cumsum()
    )

    result["abc_class"] = np.select(
        [
            result["cumulative_percentage"] <= 80,
            result["cumulative_percentage"] <= 95,
        ],
        [
            "A",
            "B",
        ],
        default="C"
    )

    return result


# =========================================================
# SUPPLIER ANALYSIS
# =========================================================

def supplier_analysis(df):

    df = standardize_data(df)

    if df.empty:
        return pd.DataFrame()

    result = (
        df.groupby("supplier", as_index=False)
        .agg(
            total_stock=("stock", "sum"),
            total_sales=("sales", "sum"),
            average_lead_time=("lead_time", "mean"),
            product_count=("product", "nunique")
        )
    )

    return result.sort_values(
        "total_sales",
        ascending=False
    )


# =========================================================
# INVENTORY FORECAST
# =========================================================

def inventory_forecast(df):

    df = standardize_data(df)

    if df.empty:
        return pd.DataFrame()

    result = (
        df.groupby("product", as_index=False)
        .agg(
            current_stock=("stock", "sum"),
            average_sales=("sales", "mean"),
            reorder_point=("reorder_point", "mean")
        )
    )

    result["forecast_demand"] = (
        result["average_sales"] * 1.1
    )

    result["recommended_order"] = (
        result["forecast_demand"]
        + result["reorder_point"]
        - result["current_stock"]
    ).clip(lower=0)

    return result.sort_values(
        "recommended_order",
        ascending=False
    )


# =========================================================
# DAILY / MONTHLY TREND
# =========================================================

def sales_trend(df):

    df = standardize_data(df)

    date_col = find_column(df, "date")

    if date_col is None or df.empty:
        return pd.DataFrame()

    df = df.dropna(subset=[date_col])

    if df.empty:
        return pd.DataFrame()

    result = (
        df.groupby(date_col, as_index=False)
        .agg(
            sales=("sales", "sum"),
            stock=("stock", "sum")
        )
    )

    return result.sort_values(date_col)


# =========================================================
# GENERAL SUMMARY
# =========================================================

def generate_summary(df):

    kpis = headline_kpis(df)

    summary = {
        "Total Products": kpis["total_products"],
        "Total Stock": kpis["total_stock"],
        "Total Sales": kpis["total_sales"],
        "Stockout Rate": kpis["stockout_rate"],
        "Fill Rate": kpis["fill_rate"],
        "Inventory Value": kpis["inventory_value"],
        "Low Stock Items": kpis["low_stock_items"],
    }

    return summary
