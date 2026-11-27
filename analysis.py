# ============================================================
# SUPPLY CHAIN & INVENTORY OPTIMIZATION ANALYTICS
# analysis.py
# ============================================================

from pathlib import Path

import pandas as pd
import numpy as np


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FOLDERS = [
    BASE_DIR,
    BASE_DIR / "data",
    BASE_DIR / "datasets",
    BASE_DIR / "Dataset",
    BASE_DIR / "Data",
]


# ============================================================
# FILE SEARCH
# ============================================================

def find_csv_file(possible_names):

    # Search expected folders first
    for folder in DATA_FOLDERS:

        if folder.exists():

            for filename in possible_names:

                file_path = folder / filename

                if file_path.exists():
                    return file_path

    # Recursive search
    for filename in possible_names:

        try:
            matches = list(BASE_DIR.rglob(filename))

            matches = [
                path for path in matches
                if ".git" not in path.parts
            ]

            if matches:
                return matches[0]

        except Exception:
            pass

    return None


# ============================================================
# CSV READER
# ============================================================

def read_csv_safely(file_path):

    if file_path is None:
        return pd.DataFrame()

    encodings = [
        "utf-8",
        "utf-8-sig",
        "latin1",
        "cp1252"
    ]

    for encoding in encodings:

        try:

            df = pd.read_csv(
                file_path,
                encoding=encoding
            )

            df.columns = [
                str(column).strip()
                for column in df.columns
            ]

            return df

        except UnicodeDecodeError:
            continue

        except Exception as error:

            raise ValueError(
                f"Could not read {file_path.name}: {error}"
            )

    raise ValueError(
        f"Could not decode file: {file_path.name}"
    )


# ============================================================
# DATA CLEANING
# ============================================================

def clean_dataframe(df):

    if df is None:
        return pd.DataFrame()

    if df.empty:
        return df

    df = df.copy()

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    df = df.drop_duplicates()

    # Clean text columns
    for column in df.select_dtypes(
        include=["object", "string"]
    ).columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

        df[column] = df[column].replace(
            ["", "nan", "None", "NULL"],
            pd.NA
        )

    return df


# ============================================================
# COLUMN DETECTION
# ============================================================

def find_column(df, possible_names):

    if df is None or df.empty:
        return None

    column_map = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    # Exact match
    for name in possible_names:

        name_lower = str(name).strip().lower()

        if name_lower in column_map:
            return column_map[name_lower]

    # Partial match
    for column in df.columns:

        column_lower = str(column).strip().lower()

        for name in possible_names:

            name_lower = str(name).strip().lower()

            if name_lower in column_lower:
                return column

    return None


# ============================================================
# SAFE NUMERIC CONVERSION
# ============================================================

def to_numeric_series(df, column):

    if df is None or df.empty or column is None:
        return pd.Series(dtype=float)

    return pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0)


# ============================================================
# LOAD DATASETS
# ============================================================

def load():

    # PRODUCTS
    product_file = find_csv_file([
        "products.csv",
        "product.csv",
        "product_data.csv",
        "products_data.csv"
    ])

    # SALES
    sales_file = find_csv_file([
        "sales.csv",
        "sales_data.csv",
        "sale.csv",
        "sales_dataset.csv"
    ])

    # INVENTORY
    # Your actual filename is inventory_daily.csv
    inventory_file = find_csv_file([
        "inventory_daily.csv",
        "inventory.csv",
        "inventory_data.csv",
        "stock.csv",
        "inventory_dataset.csv"
    ])

    # PURCHASE ORDERS
    purchase_order_file = find_csv_file([
        "purchase_orders.csv",
        "purchase_order.csv",
        "purchase_orders_data.csv",
        "po.csv",
        "orders.csv",
        "purchase_data.csv"
    ])

    missing_files = []

    if product_file is None:
        missing_files.append("products.csv")

    if sales_file is None:
        missing_files.append("sales.csv")

    if inventory_file is None:
        missing_files.append("inventory_daily.csv")

    if missing_files:

        raise FileNotFoundError(
            "Missing dataset files: "
            + ", ".join(missing_files)
            + "\n\nFiles searched inside:\n"
            + str(BASE_DIR)
        )

    # Read datasets
    products = read_csv_safely(product_file)

    sales = read_csv_safely(sales_file)

    inventory = read_csv_safely(inventory_file)

    if purchase_order_file is not None:

        purchase_orders = read_csv_safely(
            purchase_order_file
        )

    else:

        purchase_orders = pd.DataFrame()

    # Clean datasets
    products = clean_dataframe(products)

    sales = clean_dataframe(sales)

    inventory = clean_dataframe(inventory)

    purchase_orders = clean_dataframe(
        purchase_orders
    )

    # Convert date columns
    date_keywords = [
        "date",
        "sales_date",
        "order_date",
        "transaction_date",
        "purchase_date",
        "delivery_date",
        "ship_date"
    ]

    for df in [
        sales,
        inventory,
        purchase_orders
    ]:

        for column in df.columns:

            if str(column).lower().strip() in date_keywords:

                df[column] = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

    return (
        products,
        sales,
        inventory,
        purchase_orders
    )


# ============================================================
# HEADLINE KPIs
# ============================================================

def headline_kpis(
    products,
    sales,
    inventory,
    purchase_orders=None
):

    kpis = {}

    # --------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------

    kpis["total_products"] = (
        len(products)
        if products is not None
        else 0
    )

    # --------------------------------------------------------
    # SALES
    # --------------------------------------------------------

    kpis["total_sales"] = 0

    kpis["average_sales"] = 0

    kpis["total_units_sold"] = 0

    if sales is not None and not sales.empty:

        sales_column = find_column(
            sales,
            [
                "sales",
                "sales_amount",
                "revenue",
                "total_sales",
                "amount"
            ]
        )

        quantity_column = find_column(
            sales,
            [
                "quantity",
                "qty",
                "units_sold"
            ]
        )

        if sales_column:

            sales_values = to_numeric_series(
                sales,
                sales_column
            )

            kpis["total_sales"] = float(
                sales_values.sum()
            )

            kpis["average_sales"] = float(
                sales_values.mean()
            )

        if quantity_column:

            quantity_values = to_numeric_series(
                sales,
                quantity_column
            )

            kpis["total_units_sold"] = float(
                quantity_values.sum()
            )

    # --------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------

    kpis["total_inventory"] = 0

    kpis["average_inventory"] = 0

    kpis["low_stock_items"] = 0

    if inventory is not None and not inventory.empty:

        inventory_column = find_column(
            inventory,
            [
                "stock",
                "inventory",
                "stock_quantity",
                "quantity",
                "available_stock",
                "inventory_quantity"
            ]
        )

        if inventory_column:

            stock_values = to_numeric_series(
                inventory,
                inventory_column
            )

            kpis["total_inventory"] = float(
                stock_values.sum()
            )

            kpis["average_inventory"] = float(
                stock_values.mean()
            )

            kpis["low_stock_items"] = int(
                (stock_values <= 10).sum()
            )

    # --------------------------------------------------------
    # PURCHASE ORDERS
    # --------------------------------------------------------

    kpis["total_purchase_orders"] = 0

    kpis["purchase_value"] = 0

    if (
        purchase_orders is not None
        and not purchase_orders.empty
    ):

        kpis["total_purchase_orders"] = len(
            purchase_orders
        )

        amount_column = find_column(
            purchase_orders,
            [
                "amount",
                "order_amount",
                "purchase_amount",
                "total_cost",
                "cost",
                "price"
            ]
        )

        if amount_column:

            amount_values = to_numeric_series(
                purchase_orders,
                amount_column
            )

            kpis["purchase_value"] = float(
                amount_values.sum()
            )

    return kpis


# ============================================================
# SALES FORECASTING
# ============================================================

def evaluate_forecasts(sales):

    if sales is None or sales.empty:
        return pd.DataFrame()

    date_column = find_column(
        sales,
        [
            "date",
            "sales_date",
            "order_date",
            "transaction_date"
        ]
    )

    sales_column = find_column(
        sales,
        [
            "sales",
            "sales_amount",
            "revenue",
            "total_sales",
            "amount"
        ]
    )

    if date_column is None:
        return pd.DataFrame()

    if sales_column is None:
        return pd.DataFrame()

    data = sales.copy()

    data[date_column] = pd.to_datetime(
        data[date_column],
        errors="coerce"
    )

    data[sales_column] = pd.to_numeric(
        data[sales_column],
        errors="coerce"
    )

    data = data.dropna(
        subset=[
            date_column,
            sales_column
        ]
    )

    if data.empty:
        return pd.DataFrame()

    # Aggregate sales by date
    daily_sales = (
        data.groupby(date_column)[sales_column]
        .sum()
        .reset_index()
        .sort_values(date_column)
    )

    daily_sales.columns = [
        "Date",
        "Actual Sales"
    ]

    # Moving average forecast
    daily_sales["Forecast"] = (
        daily_sales["Actual Sales"]
        .rolling(
            window=3,
            min_periods=1
        )
        .mean()
    )

    # Generate 7-day forecast
    last_date = daily_sales["Date"].max()

    last_forecast = (
        daily_sales["Actual Sales"]
        .tail(3)
        .mean()
    )

    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1),
        periods=7,
        freq="D"
    )

    future_data = pd.DataFrame({
        "Date": future_dates,
        "Actual Sales": [np.nan] * 7,
        "Forecast": [last_forecast] * 7
    })

    result = pd.concat(
        [
            daily_sales,
            future_data
        ],
        ignore_index=True
    )

    return result


# ============================================================
# FORECAST PERFORMANCE METRICS
# ============================================================

def calculate_forecast_metrics(
    actual,
    predicted
):

    actual = np.asarray(
        actual,
        dtype=float
    )

    predicted = np.asarray(
        predicted,
        dtype=float
    )

    mask = (
        ~np.isnan(actual)
        &
        ~np.isnan(predicted)
    )

    actual = actual[mask]

    predicted = predicted[mask]

    if len(actual) == 0:

        return {
            "MAE": 0,
            "RMSE": 0,
            "MAPE": 0
        }

    mae = np.mean(
        np.abs(actual - predicted)
    )

    rmse = np.sqrt(
        np.mean(
            (actual - predicted) ** 2
        )
    )

    non_zero = actual != 0

    if np.any(non_zero):

        mape = np.mean(
            np.abs(
                (
                    actual[non_zero]
                    -
                    predicted[non_zero]
                )
                /
                actual[non_zero]
            )
        ) * 100

    else:

        mape = 0

    return {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "MAPE": float(mape)
    }


# ============================================================
# INVENTORY SUMMARY
# ============================================================

def inventory_summary(inventory):

    if inventory is None or inventory.empty:
        return {}

    stock_column = find_column(
        inventory,
        [
            "stock",
            "inventory",
            "stock_quantity",
            "quantity",
            "available_stock",
            "inventory_quantity"
        ]
    )

    if stock_column is None:
        return {}

    stock = to_numeric_series(
        inventory,
        stock_column
    )

    return {
        "Total Inventory": float(stock.sum()),
        "Average Inventory": float(stock.mean()),
        "Minimum Inventory": float(stock.min()),
        "Maximum Inventory": float(stock.max()),
        "Low Stock Items": int((stock <= 10).sum())
    }


# ============================================================
# SALES SUMMARY
# ============================================================

def sales_summary(sales):

    if sales is None or sales.empty:
        return {}

    sales_column = find_column(
        sales,
        [
            "sales",
            "sales_amount",
            "revenue",
            "total_sales",
            "amount"
        ]
    )

    quantity_column = find_column(
        sales,
        [
            "quantity",
            "qty",
            "units_sold"
        ]
    )

    summary = {}

    if sales_column:

        values = to_numeric_series(
            sales,
            sales_column
        )

        summary["Total Sales"] = float(
            values.sum()
        )

        summary["Average Sales"] = float(
            values.mean()
        )

    if quantity_column:

        quantity = to_numeric_series(
            sales,
            quantity_column
        )

        summary["Total Quantity Sold"] = float(
            quantity.sum()
        )

    return summary


# ============================================================
# PRODUCT SUMMARY
# ============================================================

def product_summary(products):

    if products is None or products.empty:
        return {}

    category_column = find_column(
        products,
        [
            "category",
            "product_category"
        ]
    )

    product_column = find_column(
        products,
        [
            "product_id",
            "product",
            "product_name",
            "sku"
        ]
    )

    summary = {
        "Total Products": int(len(products))
    }

    if product_column:

        summary["Unique Products"] = int(
            products[product_column].nunique()
        )

    if category_column:

        summary["Categories"] = int(
            products[category_column].nunique()
        )

    return summary


# ============================================================
# PURCHASE ORDER SUMMARY
# ============================================================

def purchase_order_summary(purchase_orders):

    if (
        purchase_orders is None
        or purchase_orders.empty
    ):
        return {}

    order_column = find_column(
        purchase_orders,
        [
            "order_id",
            "purchase_order_id",
            "po_id"
        ]
    )

    status_column = find_column(
        purchase_orders,
        [
            "status",
            "order_status",
            "purchase_status"
        ]
    )

    amount_column = find_column(
        purchase_orders,
        [
            "amount",
            "order_amount",
            "purchase_amount",
            "total_cost",
            "cost"
        ]
    )

    summary = {}

    if order_column:

        summary["Total Purchase Orders"] = int(
            purchase_orders[order_column].nunique()
        )

    else:

        summary["Total Purchase Orders"] = int(
            len(purchase_orders)
        )

    if status_column:

        summary["Order Statuses"] = (
            purchase_orders[status_column]
            .value_counts()
            .to_dict()
        )

    if amount_column:

        amounts = to_numeric_series(
            purchase_orders,
            amount_column
        )

        summary["Total Purchase Value"] = float(
            amounts.sum()
        )

    return summary


# ============================================================
# SUPPLIER DATA
# ============================================================

def load_suppliers():

    supplier_file = find_csv_file([
        "suppliers.csv",
        "supplier.csv",
        "supplier_data.csv"
    ])

    if supplier_file is None:
        return pd.DataFrame()

    suppliers = read_csv_safely(
        supplier_file
    )

    return clean_dataframe(
        suppliers
    )


# ============================================================
# ABC ANALYSIS
# ============================================================

def abc_analysis(products, sales):

    if (
        products is None
        or products.empty
        or sales is None
        or sales.empty
    ):
        return pd.DataFrame()

    product_column = find_column(
        products,
        [
            "product_id",
            "product",
            "product_name",
            "sku"
        ]
    )

    sales_product_column = find_column(
        sales,
        [
            "product_id",
            "product",
            "product_name",
            "sku"
        ]
    )

    sales_column = find_column(
        sales,
        [
            "sales",
            "sales_amount",
            "revenue",
            "amount"
        ]
    )

    if (
        product_column is None
        or sales_product_column is None
        or sales_column is None
    ):
        return pd.DataFrame()

    sales_data = sales.copy()

    sales_data[sales_column] = pd.to_numeric(
        sales_data[sales_column],
        errors="coerce"
    ).fillna(0)

    grouped = (
        sales_data.groupby(sales_product_column)[sales_column]
        .sum()
        .reset_index()
    )

    grouped.columns = [
        "Product",
        "Sales"
    ]

    grouped = grouped.sort_values(
        "Sales",
        ascending=False
    )

    total_sales = grouped["Sales"].sum()

    if total_sales == 0:
        return grouped

    grouped["Percentage"] = (
        grouped["Sales"] / total_sales * 100
    )

    grouped["Cumulative Percentage"] = (
        grouped["Percentage"].cumsum()
    )

    grouped["ABC Category"] = np.where(
        grouped["Cumulative Percentage"] <= 80,
        "A",
        np.where(
            grouped["Cumulative Percentage"] <= 95,
            "B",
            "C"
        )
    )

    return grouped


# ============================================================
# REORDER POINT CALCULATION
# ============================================================

def calculate_reorder_point(
    average_daily_demand,
    lead_time,
    safety_stock=0
):

    average_daily_demand = max(
        float(average_daily_demand),
        0
    )

    lead_time = max(
        float(lead_time),
        0
    )

    safety_stock = max(
        float(safety_stock),
        0
    )

    return (
        average_daily_demand * lead_time
        +
        safety_stock
    )


# ============================================================
# END OF ANALYSIS.PY
# ============================================================
