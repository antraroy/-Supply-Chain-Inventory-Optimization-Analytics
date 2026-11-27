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
        "stock", "stock_quantity", "quantity",
        "inventory", "available_stock",
        "current_stock", "on_hand", "units_in_stock"
    ],

    "sales": [
        "sales", "daily_sales", "units_sold",
        "sales_quantity", "demand", "quantity_sold"
    ],

    "reorder": [
        "reorder_point", "reorder level",
        "minimum_stock", "min_stock",
        "safety_stock", "stock_threshold"
    ],

    "supplier": [
        "supplier", "supplier_name",
        "vendor", "vendor_name"
    ],

    "lead_time": [
        "lead_time", "lead time",
        "delivery_days", "shipping_days"
    ],

    "price": [
        "price", "unit_price", "cost",
        "purchase_price", "product_price"
    ],

    "date": [
        "date", "order_date", "sales_date",
        "transaction_date", "timestamp"
    ],

    "order_quantity": [
        "order_quantity", "quantity_ordered",
        "purchase_quantity", "ordered_quantity"
    ],

    "status": [
        "status", "stock_status", "inventory_status"
    ],

    "revenue": [
        "revenue", "sales_revenue", "total_sales"
    ],

    "fill_rate": [
        "fill_rate", "order_fill_rate",
        "fulfillment_rate"
    ]
}


def normalize_name(name):
    return (
        str(name)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


def find_column(df, possible_names):
    """
    Detect a column using flexible case-insensitive matching.
    """

    if df is None or df.empty:
        return None

    columns = list(df.columns)

    normalized_columns = {
        normalize_name(col): col
        for col in columns
    }

    # Exact match
    for name in possible_names:

        normalized_name = normalize_name(name)

        if normalized_name in normalized_columns:
            return normalized_columns[normalized_name]

    # Partial match
    for name in possible_names:

        normalized_name = normalize_name(name)

        for normalized_col, original_col in normalized_columns.items():

            if normalized_name in normalized_col:
                return original_col

    return None


def get_column(df, key):

    aliases = COLUMN_ALIASES.get(key, [key])

    return find_column(df, aliases)


# =========================================================
# DATA CLEANING
# =========================================================

def clean_data(df):

    if df is None:
        return pd.DataFrame()

    df = df.copy()

    # Remove empty columns
    df = df.dropna(axis=1, how="all")

    # Clean column names
    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Convert numeric columns
    numeric_keys = [
        "stock",
        "sales",
        "reorder",
        "lead_time",
        "price",
        "order_quantity",
        "revenue",
        "fill_rate"
    ]

    for key in numeric_keys:

        col = get_column(df, key)

        if col is not None:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # Date conversion
    date_col = get_column(df, "date")

    if date_col is not None:

        df[date_col] = pd.to_datetime(
            df[date_col],
            errors="coerce"
        )

    return df


# =========================================================
# HEADLINE KPI METRICS
# =========================================================

def headline_kpis(df):

    df = clean_data(df)

    if df.empty:

        return {
            "total_products": 0,
            "total_stock": 0,
            "stockout_rate": 0,
            "fill_rate": 0,
            "inventory_value": 0,
            "low_stock_items": 0,
            "average_lead_time": 0
        }

    stock_col = get_column(df, "stock")

    reorder_col = get_column(df, "reorder")

    sales_col = get_column(df, "sales")

    price_col = get_column(df, "price")

    lead_col = get_column(df, "lead_time")

    total_products = len(df)

    total_stock = 0

    stockout_rate = 0

    fill_rate = 100

    inventory_value = 0

    low_stock_items = 0

    average_lead_time = 0

    # Total stock
    if stock_col is not None:

        stock = pd.to_numeric(
            df[stock_col],
            errors="coerce"
        ).fillna(0)

        total_stock = stock.sum()

        stockout_count = (stock <= 0).sum()

        stockout_rate = (
            stockout_count / total_products
        ) * 100

        # Low stock
        if reorder_col is not None:

            reorder = pd.to_numeric(
                df[reorder_col],
                errors="coerce"
            ).fillna(0)

            low_stock_items = (
                stock <= reorder
            ).sum()

        else:

            low_stock_items = stockout_count

    # Inventory value
    if stock_col is not None and price_col is not None:

        stock = pd.to_numeric(
            df[stock_col],
            errors="coerce"
        ).fillna(0)

        price = pd.to_numeric(
            df[price_col],
            errors="coerce"
        ).fillna(0)

        inventory_value = (
            stock * price
        ).sum()

    # Fill rate
    fill_rate_col = get_column(df, "fill_rate")

    if fill_rate_col is not None:

        fill_values = pd.to_numeric(
            df[fill_rate_col],
            errors="coerce"
        ).dropna()

        if not fill_values.empty:

            fill_rate = fill_values.mean()

            if fill_rate <= 1:
                fill_rate *= 100

    elif stock_col is not None and sales_col is not None:

        stock = pd.to_numeric(
            df[stock_col],
            errors="coerce"
        ).fillna(0)

        sales = pd.to_numeric(
            df[sales_col],
            errors="coerce"
        ).fillna(0)

        total_demand = sales.sum()

        if total_demand > 0:

            fulfilled = np.minimum(
                stock,
                sales
            ).sum()

            fill_rate = (
                fulfilled / total_demand
            ) * 100

    # Average lead time
    if lead_col is not None:

        lead_values = pd.to_numeric(
            df[lead_col],
            errors="coerce"
        ).dropna()

        if not lead_values.empty:

            average_lead_time = lead_values.mean()

    return {
        "total_products": int(total_products),
        "total_stock": float(total_stock),
        "stockout_rate": float(stockout_rate),
        "fill_rate": float(fill_rate),
        "inventory_value": float(inventory_value),
        "low_stock_items": int(low_stock_items),
        "average_lead_time": float(average_lead_time)
    }


# =========================================================
# INVENTORY DISTRIBUTION
# =========================================================

def inventory_distribution(df):

    df = clean_data(df)

    category_col = get_column(df, "category")

    stock_col = get_column(df, "stock")

    if category_col is None or stock_col is None:

        return pd.DataFrame()

    result = (
        df.groupby(category_col, dropna=False)[stock_col]
        .sum()
        .reset_index()
    )

    result.columns = [
        "Category",
        "Total Stock"
    ]

    return result


# =========================================================
# STOCK STATUS
# =========================================================

def stock_status(df):

    df = clean_data(df)

    stock_col = get_column(df, "stock")

    reorder_col = get_column(df, "reorder")

    if stock_col is None:

        return pd.DataFrame()

    df["Stock Status"] = "Normal"

    stock = pd.to_numeric(
        df[stock_col],
        errors="coerce"
    ).fillna(0)

    df.loc[
        stock <= 0,
        "Stock Status"
    ] = "Out of Stock"

    if reorder_col is not None:

        reorder = pd.to_numeric(
            df[reorder_col],
            errors="coerce"
        ).fillna(0)

        df.loc[
            (stock > 0) & (stock <= reorder),
            "Stock Status"
        ] = "Low Stock"

        df.loc[
            stock > reorder,
            "Stock Status"
        ] = "Healthy Stock"

    else:

        df.loc[
            stock > 0,
            "Stock Status"
        ] = "Healthy Stock"

    return df


# =========================================================
# LOW STOCK ALERTS
# =========================================================

def low_stock_alerts(df):

    df = clean_data(df)

    stock_col = get_column(df, "stock")

    reorder_col = get_column(df, "reorder")

    if stock_col is None:

        return pd.DataFrame()

    stock = pd.to_numeric(
        df[stock_col],
        errors="coerce"
    ).fillna(0)

    if reorder_col is not None:

        reorder = pd.to_numeric(
            df[reorder_col],
            errors="coerce"
        ).fillna(0)

        alerts = df[
            stock <= reorder
        ].copy()

    else:

        alerts = df[
            stock <= 0
        ].copy()

    return alerts


# =========================================================
# ABC ANALYSIS
# =========================================================

def abc_analysis(df):

    df = clean_data(df)

    stock_col = get_column(df, "stock")

    price_col = get_column(df, "price")

    product_col = get_column(df, "product")

    category_col = get_column(df, "category")

    if stock_col is None or price_col is None:

        return pd.DataFrame()

    df["Inventory Value"] = (
        pd.to_numeric(
            df[stock_col],
            errors="coerce"
        ).fillna(0)
        *
        pd.to_numeric(
            df[price_col],
            errors="coerce"
        ).fillna(0)
    )

    df = df.sort_values(
        "Inventory Value",
        ascending=False
    )

    total_value = df["Inventory Value"].sum()

    if total_value == 0:

        df["Cumulative Percentage"] = 0

        df["ABC Class"] = "C"

        return df

    df["Cumulative Value"] = (
        df["Inventory Value"].cumsum()
    )

    df["Cumulative Percentage"] = (
        df["Cumulative Value"] / total_value
    ) * 100

    df["ABC Class"] = np.where(
        df["Cumulative Percentage"] <= 80,
        "A",
        np.where(
            df["Cumulative Percentage"] <= 95,
            "B",
            "C"
        )
    )

    return df


# =========================================================
# REORDER RECOMMENDATIONS
# =========================================================

def reorder_recommendations(df):

    df = clean_data(df)

    stock_col = get_column(df, "stock")

    reorder_col = get_column(df, "reorder")

    sales_col = get_column(df, "sales")

    if stock_col is None:

        return pd.DataFrame()

    stock = pd.to_numeric(
        df[stock_col],
        errors="coerce"
    ).fillna(0)

    if reorder_col is not None:

        reorder = pd.to_numeric(
            df[reorder_col],
            errors="coerce"
        ).fillna(0)

    else:

        reorder = pd.Series(
            0,
            index=df.index
        )

    if sales_col is not None:

        sales = pd.to_numeric(
            df[sales_col],
            errors="coerce"
        ).fillna(0)

        recommended_order = np.maximum(
            reorder - stock,
            sales
        )

    else:

        recommended_order = np.maximum(
            reorder - stock,
            0
        )

    df["Recommended Order Quantity"] = (
        recommended_order
    )

    df["Action"] = np.where(
        stock <= reorder,
        "Reorder",
        "No Action"
    )

    result = df[
        df["Action"] == "Reorder"
    ].copy()

    return result


# =========================================================
# SUPPLIER SCORECARD
# =========================================================

def supplier_scorecard(df):

    df = clean_data(df)

    supplier_col = get_column(df, "supplier")

    lead_col = get_column(df, "lead_time")

    stock_col = get_column(df, "stock")

    if supplier_col is None:

        return pd.DataFrame()

    aggregations = {}

    if lead_col is not None:

        aggregations[lead_col] = "mean"

    if stock_col is not None:

        aggregations[stock_col] = "sum"

    if not aggregations:

        return (
            df[supplier_col]
            .value_counts()
            .reset_index()
        )

    result = (
        df.groupby(supplier_col)
        .agg(aggregations)
        .reset_index()
    )

    return result


# =========================================================
# SALES TREND
# =========================================================

def sales_trend(df):

    df = clean_data(df)

    date_col = get_column(df, "date")

    sales_col = get_column(df, "sales")

    if date_col is None or sales_col is None:

        return pd.DataFrame()

    df = df.dropna(
        subset=[date_col]
    )

    result = (
        df.groupby(date_col)[sales_col]
        .sum()
        .reset_index()
    )

    result.columns = [
        "Date",
        "Sales"
    ]

    return result.sort_values("Date")


# =========================================================
# WAREHOUSE ANALYSIS
# =========================================================

def warehouse_analysis(df):

    df = clean_data(df)

    warehouse_col = get_column(df, "warehouse")

    stock_col = get_column(df, "stock")

    if warehouse_col is None:

        return pd.DataFrame()

    if stock_col is None:

        result = (
            df.groupby(warehouse_col)
            .size()
            .reset_index(name="Product Count")
        )

        return result

    result = (
        df.groupby(warehouse_col)[stock_col]
        .sum()
        .reset_index()
    )

    result.columns = [
        "Warehouse",
        "Total Stock"
    ]

    return result


# =========================================================
# DATASET SUMMARY
# =========================================================

def dataset_summary(df):

    df = clean_data(df)

    if df.empty:

        return {}

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum())
    }
