# ============================================================
# SUPPLY CHAIN & INVENTORY OPTIMIZATION ANALYTICS
# analysis.py
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

# Also check alternative dataset folders
DATA_FOLDERS = [
    BASE_DIR / "data",
    BASE_DIR / "datasets",
    BASE_DIR / "Data",
    BASE_DIR / "Dataset",
    BASE_DIR
]


# ============================================================
# HELPER: FIND CSV FILE
# ============================================================

def find_csv_file(possible_names):
    """
    Search for a CSV file in common project folders.
    """

    # First check expected folders
    for folder in DATA_FOLDERS:

        if not folder.exists():
            continue

        for filename in possible_names:

            file_path = folder / filename

            if file_path.exists():
                return file_path

    # Recursive fallback search
    for filename in possible_names:

        matches = list(
            BASE_DIR.rglob(filename)
        )

        # Ignore .git folders
        matches = [
            path for path in matches
            if ".git" not in path.parts
        ]

        if matches:
            return matches[0]

    return None


# ============================================================
# HELPER: LOAD CSV
# ============================================================

def read_csv_safely(file_path):
    """
    Read CSV while handling common encoding issues.
    """

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

            # Remove unnecessary spaces from column names
            df.columns = [
                str(column).strip()
                for column in df.columns
            ]

            return df

        except UnicodeDecodeError:
            continue

        except Exception as error:

            raise ValueError(
                f"Unable to read {file_path.name}: {error}"
            )

    raise ValueError(
        f"Could not read file: {file_path.name}"
    )


# ============================================================
# HELPER: FIND COLUMN
# ============================================================

def find_column(df, possible_names):
    """
    Identify a column using possible names.
    """

    if df.empty:
        return None

    column_mapping = {
        str(column).lower().strip(): column
        for column in df.columns
    }

    for name in possible_names:

        name = name.lower().strip()

        if name in column_mapping:
            return column_mapping[name]

    # Partial matching fallback
    for column in df.columns:

        column_lower = str(column).lower().strip()

        for name in possible_names:

            if name.lower() in column_lower:
                return column

    return None


# ============================================================
# HELPER: CLEAN DATA
# ============================================================

def clean_dataframe(df):
    """
    Basic cleaning of dataset.
    """

    if df.empty:
        return df

    # Remove duplicate records
    df = df.drop_duplicates()

    # Remove spaces from column names
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    # Clean string columns
    for column in df.select_dtypes(
        include=["object"]
    ).columns:

        df[column] = df[column].astype(str).str.strip()

        df[column] = df[column].replace(
            ["nan", "None", ""],
            np.nan
        )

    return df


# ============================================================
# LOAD PROJECT DATA
# ============================================================

def load():
    """
    Load products, sales, inventory and purchase orders.

    Returns:
        products, sales, inventory, purchase_orders
    """

    # --------------------------------------------------------
    # PRODUCT DATA
    # --------------------------------------------------------

    product_file = find_csv_file([
        "products.csv",
        "product.csv",
        "product_data.csv",
        "products_data.csv"
    ])

    # --------------------------------------------------------
    # SALES DATA
    # --------------------------------------------------------

    sales_file = find_csv_file([
        "sales.csv",
        "sales_data.csv",
        "sale.csv",
        "sales_dataset.csv"
    ])

    # --------------------------------------------------------
    # INVENTORY DATA
    # --------------------------------------------------------

    inventory_file = find_csv_file([
        "inventory.csv",
        "inventory_data.csv",
        "stock.csv",
        "inventory_dataset.csv"
    ])

    # --------------------------------------------------------
    # PURCHASE ORDER DATA
    # --------------------------------------------------------

    purchase_order_file = find_csv_file([
        "purchase_orders.csv",
        "purchase_order.csv",
        "purchase_orders_data.csv",
        "po.csv",
        "orders.csv",
        "purchase_data.csv"
    ])

    # --------------------------------------------------------
    # CHECK REQUIRED FILES
    # --------------------------------------------------------

    missing_files = []

    if product_file is None:
        missing_files.append("products.csv")

    if sales_file is None:
        missing_files.append("sales.csv")

    if inventory_file is None:
        missing_files.append("inventory.csv")

    if missing_files:

        searched_locations = "\n".join(
            str(folder)
            for folder in DATA_FOLDERS
        )

        raise FileNotFoundError(
            "Missing required dataset(s): "
            + ", ".join(missing_files)
            + "\n\nExpected files inside folders such as:\n"
            + str(BASE_DIR / "data")
            + "\n\nFolders searched:\n"
            + searched_locations
        )

    # --------------------------------------------------------
    # READ FILES
    # --------------------------------------------------------

    products = read_csv_safely(product_file)

    sales = read_csv_safely(sales_file)

    inventory = read_csv_safely(inventory_file)

    if purchase_order_file:

        purchase_orders = read_csv_safely(
            purchase_order_file
        )

    else:

        # Purchase orders are optional
        purchase_orders = pd.DataFrame()

    # --------------------------------------------------------
    # CLEAN DATA
    # --------------------------------------------------------

    products = clean_dataframe(products)

    sales = clean_dataframe(sales)

    inventory = clean_dataframe(inventory)

    purchase_orders = clean_dataframe(
        purchase_orders
    )

    # --------------------------------------------------------
    # CONVERT DATE COLUMNS
    # --------------------------------------------------------

    date_columns = [
        "date",
        "sales_date",
        "order_date",
        "transaction_date",
        "purchase_date",
        "delivery_date"
    ]

    for df in [
        sales,
        inventory,
        purchase_orders
    ]:

        for column in df.columns:

            if str(column).lower().strip() in date_columns:

                df[column] = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

    # --------------------------------------------------------
    # CONVERT NUMERIC COLUMNS
    # --------------------------------------------------------

    numeric_candidates = [
        "sales",
        "revenue",
        "sales_amount",
        "quantity",
        "qty",
        "units_sold",
        "stock",
        "inventory",
        "inventory_quantity",
        "available_stock",
        "price",
        "cost",
        "amount",
        "order_amount"
    ]

    for df in [
        products,
        sales,
        inventory,
        purchase_orders
    ]:

        for column in df.columns:

            if str(column).lower().strip() in numeric_candidates:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

    # --------------------------------------------------------
    # RETURN DATASETS
    # --------------------------------------------------------

    return (
        products,
        sales,
        inventory,
        purchase_orders
    )


# ============================================================
# SALES FORECASTING
# ============================================================

def evaluate_forecasts(sales):
    """
    Generate a simple sales forecast using historical data.

    Uses monthly or daily sales data and moving averages.

    Returns a DataFrame containing:
        Date
        Actual Sales
        Forecast
    """

    if sales is None or sales.empty:

        return pd.DataFrame()

    # --------------------------------------------------------
    # FIND DATE COLUMN
    # --------------------------------------------------------

    date_column = find_column(
        sales,
        [
            "date",
            "sales_date",
            "order_date",
            "transaction_date"
        ]
    )

    # --------------------------------------------------------
    # FIND SALES COLUMN
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if date_column is None:

        return pd.DataFrame({
            "Message": [
                "No date column found for forecasting."
            ]
        })

    if sales_column is None:

        return pd.DataFrame({
            "Message": [
                "No sales/revenue column found."
            ]
        })

    # --------------------------------------------------------
    # PREPARE DATA
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # AGGREGATE SALES BY DATE
    # --------------------------------------------------------

    daily_sales = (
        data.groupby(date_column)[sales_column]
        .sum()
        .reset_index()
    )

    daily_sales = daily_sales.sort_values(
        date_column
    )

    daily_sales.columns = [
        "Date",
        "Actual Sales"
    ]

    # --------------------------------------------------------
    # MOVING AVERAGE FORECAST
    # --------------------------------------------------------

    daily_sales["Forecast"] = (
        daily_sales["Actual Sales"]
        .rolling(
            window=3,
            min_periods=1
        )
        .mean()
    )

    # --------------------------------------------------------
    # FUTURE FORECAST
    # --------------------------------------------------------

    last_date = daily_sales["Date"].max()

    last_forecast = daily_sales["Actual Sales"].tail(
        3
    ).mean()

    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1),
        periods=7,
        freq="D"
    )

    future_data = pd.DataFrame({
        "Date": future_dates,
        "Actual Sales": [np.nan] * len(future_dates),
        "Forecast": [last_forecast] * len(future_dates)
    })

    # --------------------------------------------------------
    # COMBINE HISTORICAL + FUTURE
    # --------------------------------------------------------

    result = pd.concat(
        [
            daily_sales,
            future_data
        ],
        ignore_index=True
    )

    return result


# ============================================================
# FORECAST METRICS
# ============================================================

def calculate_forecast_metrics(
    actual,
    predicted
):
    """
    Calculate forecast performance metrics.
    """

    actual = np.array(actual, dtype=float)

    predicted = np.array(
        predicted,
        dtype=float
    )

    # Remove missing values
    mask = (
        ~np.isnan(actual)
        &
        ~np.isnan(predicted)
    )

    actual = actual[mask]

    predicted = predicted[mask]

    if len(actual) == 0:

        return {
            "MAE": np.nan,
            "RMSE": np.nan,
            "MAPE": np.nan
        }

    # MAE
    mae = np.mean(
        np.abs(actual - predicted)
    )

    # RMSE
    rmse = np.sqrt(
        np.mean(
            (actual - predicted) ** 2
        )
    )

    # MAPE
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

        mape = np.nan

    return {
        "MAE": mae,
        "RMSE": rmse,
        "MAPE": mape
    }


# ============================================================
# INVENTORY ANALYSIS
# ============================================================

def inventory_summary(inventory):
    """
    Calculate inventory summary.
    """

    if inventory.empty:

        return {}

    stock_column = find_column(
        inventory,
        [
            "stock",
            "inventory",
            "stock_quantity",
            "quantity",
            "available_stock"
        ]
    )

    if stock_column is None:

        return {}

    stock = pd.to_numeric(
        inventory[stock_column],
        errors="coerce"
    ).fillna(0)

    return {
        "Total Inventory": stock.sum(),
        "Average Inventory": stock.mean(),
        "Minimum Inventory": stock.min(),
        "Maximum Inventory": stock.max()
    }


# ============================================================
# SALES SUMMARY
# ============================================================

def sales_summary(sales):
    """
    Calculate sales summary statistics.
    """

    if sales.empty:

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

        values = pd.to_numeric(
            sales[sales_column],
            errors="coerce"
        ).fillna(0)

        summary["Total Sales"] = values.sum()

        summary["Average Sales"] = values.mean()

    if quantity_column:

        quantity = pd.to_numeric(
            sales[quantity_column],
            errors="coerce"
        ).fillna(0)

        summary["Total Quantity Sold"] = quantity.sum()

    return summary


# ============================================================
# PRODUCT SUMMARY
# ============================================================

def product_summary(products):
    """
    Calculate product summary statistics.
    """

    if products.empty:

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
        "Total Products": len(products)
    }

    if product_column:

        summary["Unique Products"] = (
            products[product_column].nunique()
        )

    if category_column:

        summary["Categories"] = (
            products[category_column].nunique()
        )

    return summary


# ============================================================
# PURCHASE ORDER SUMMARY
# ============================================================

def purchase_order_summary(purchase_orders):
    """
    Calculate purchase order summary statistics.
    """

    if purchase_orders.empty:

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

        summary["Total Purchase Orders"] = (
            purchase_orders[order_column].nunique()
        )

    else:

        summary["Total Purchase Orders"] = (
            len(purchase_orders)
        )

    if status_column:

        summary["Order Statuses"] = (
            purchase_orders[status_column]
            .value_counts()
            .to_dict()
        )

    if amount_column:

        amounts = pd.to_numeric(
            purchase_orders[amount_column],
            errors="coerce"
        ).fillna(0)

        summary["Total Purchase Value"] = (
            amounts.sum()
        )

    return summary


# ============================================================
# END OF ANALYSIS.PY
# ============================================================
