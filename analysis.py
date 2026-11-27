# ============================================================
# SUPPLY CHAIN & INVENTORY OPTIMIZATION ANALYTICS
# analysis.py
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PROJECT DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

DATA_FOLDERS = [
    BASE_DIR,                 # CSV files in root
    BASE_DIR / "data",
    BASE_DIR / "datasets",
    BASE_DIR / "Dataset",
    BASE_DIR / "Data"
]


# ============================================================
# FIND CSV FILE
# ============================================================

def find_csv_file(possible_names):

    for folder in DATA_FOLDERS:

        if folder.exists():

            for filename in possible_names:

                file_path = folder / filename

                if file_path.exists():
                    return file_path

    # Search recursively
    for filename in possible_names:

        matches = list(BASE_DIR.rglob(filename))

        matches = [
            path for path in matches
            if ".git" not in path.parts
        ]

        if matches:
            return matches[0]

    return None


# ============================================================
# READ CSV SAFELY
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
                str(col).strip()
                for col in df.columns
            ]

            return df

        except UnicodeDecodeError:
            continue

        except Exception as error:

            raise ValueError(
                f"Error reading {file_path.name}: {error}"
            )

    raise ValueError(
        f"Unable to read CSV file: {file_path.name}"
    )


# ============================================================
# CLEAN DATAFRAME
# ============================================================

def clean_dataframe(df):

    if df.empty:
        return df

    df = df.drop_duplicates()

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

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
# FIND COLUMN
# ============================================================

def find_column(df, possible_names):

    if df.empty:
        return None

    column_mapping = {
        str(col).lower().strip(): col
        for col in df.columns
    }

    # Exact matching
    for name in possible_names:

        name_lower = name.lower().strip()

        if name_lower in column_mapping:
            return column_mapping[name_lower]

    # Partial matching
    for column in df.columns:

        column_lower = str(column).lower().strip()

        for name in possible_names:

            if name.lower() in column_lower:
                return column

    return None


# ============================================================
# LOAD DATA
# ============================================================

def load():

    # --------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------

    product_file = find_csv_file([
        "products.csv",
        "product.csv",
        "product_data.csv",
        "products_data.csv"
    ])

    # --------------------------------------------------------
    # SALES
    # --------------------------------------------------------

    sales_file = find_csv_file([
        "sales.csv",
        "sales_data.csv",
        "sale.csv",
        "sales_dataset.csv"
    ])

    # --------------------------------------------------------
    # INVENTORY
    # IMPORTANT: YOUR ACTUAL FILE IS inventory_daily.csv
    # --------------------------------------------------------

    inventory_file = find_csv_file([
        "inventory_daily.csv",
        "inventory.csv",
        "inventory_data.csv",
        "stock.csv",
        "inventory_dataset.csv"
    ])

    # --------------------------------------------------------
    # PURCHASE ORDERS
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
    # CHECK REQUIRED DATASETS
    # --------------------------------------------------------

    missing_files = []

    if product_file is None:
        missing_files.append("products.csv")

    if sales_file is None:
        missing_files.append("sales.csv")

    if inventory_file is None:
        missing_files.append("inventory_daily.csv")

    if missing_files:

        raise FileNotFoundError(
            "Missing required dataset files: "
            + ", ".join(missing_files)
            + "\n\nYour CSV files should be located in:\n"
            + str(BASE_DIR)
        )

    # --------------------------------------------------------
    # LOAD CSV FILES
    # --------------------------------------------------------

    products = read_csv_safely(product_file)

    sales = read_csv_safely(sales_file)

    inventory = read_csv_safely(inventory_file)

    # Purchase orders are optional
    if purchase_order_file is not None:

        purchase_orders = read_csv_safely(
            purchase_order_file
        )

    else:

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

    date_keywords = [
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

            if str(column).lower().strip() in date_keywords:

                df[column] = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

    # --------------------------------------------------------
    # CONVERT NUMERIC COLUMNS
    # --------------------------------------------------------

    numeric_keywords = [
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

            if str(column).lower().strip() in numeric_keywords:

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

    if sales is None or sales.empty:
        return pd.DataFrame()

    # Find date column
    date_column = find_column(
        sales,
        [
            "date",
            "sales_date",
            "order_date",
            "transaction_date"
        ]
    )

    # Find sales column
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

        return pd.DataFrame({
            "Message": [
                "Date column not found in sales dataset."
            ]
        })

    if sales_column is None:

        return pd.DataFrame({
            "Message": [
                "Sales column not found in sales dataset."
            ]
        })

    # Prepare data
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
    )

    daily_sales = daily_sales.sort_values(
        date_column
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

    # Future forecast
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

    # Combine actual and forecast data
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

def calculate_forecast_metrics(actual, predicted):

    actual = np.array(
        actual,
        dtype=float
    )

    predicted = np.array(
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
            "MAE": np.nan,
            "RMSE": np.nan,
            "MAPE": np.nan
        }

    # Mean Absolute Error
    mae = np.mean(
        np.abs(actual - predicted)
    )

    # Root Mean Squared Error
    rmse = np.sqrt(
        np.mean(
            (actual - predicted) ** 2
        )
    )

    # Mean Absolute Percentage Error
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
# INVENTORY SUMMARY
# ============================================================

def inventory_summary(inventory):

    if inventory.empty:
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

    suppliers = clean_dataframe(
        suppliers
    )

    return suppliers


# ============================================================
# END OF FILE
# ============================================================
