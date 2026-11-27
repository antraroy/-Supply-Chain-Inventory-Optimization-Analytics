# ============================================================
# HELPER: FIND COLUMN
# ============================================================

def find_column(df, possible_names):

    if df is None or df.empty:
        return None

    column_map = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for name in possible_names:

        name = str(name).strip().lower()

        if name in column_map:
            return column_map[name]

    for col in df.columns:

        col_lower = str(col).strip().lower()

        for name in possible_names:

            if str(name).strip().lower() in col_lower:
                return col

    return None


# ============================================================
# HEADLINE KPI METRICS
# ============================================================

def headline_kpis(products, sales, inventory, purchase_orders=None):

    kpis = {}

    # Products
    kpis["total_products"] = (
        len(products) if products is not None else 0
    )

    # Sales
    kpis["total_sales"] = 0
    kpis["average_sales"] = 0
    kpis["total_units_sold"] = 0

    if sales is not None and not sales.empty:

        sales_col = find_column(
            sales,
            ["sales", "sales_amount", "revenue", "total_sales", "amount"]
        )

        quantity_col = find_column(
            sales,
            ["quantity", "qty", "units_sold"]
        )

        if sales_col is not None:

            sales_values = pd.to_numeric(
                sales[sales_col],
                errors="coerce"
            ).fillna(0)

            kpis["total_sales"] = float(sales_values.sum())

            kpis["average_sales"] = float(sales_values.mean())

        if quantity_col is not None:

            quantity_values = pd.to_numeric(
                sales[quantity_col],
                errors="coerce"
            ).fillna(0)

            kpis["total_units_sold"] = float(
                quantity_values.sum()
            )

    # Inventory
    kpis["total_inventory"] = 0
    kpis["average_inventory"] = 0
    kpis["low_stock_items"] = 0

    if inventory is not None and not inventory.empty:

        inventory_col = find_column(
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

        if inventory_col is not None:

            stock = pd.to_numeric(
                inventory[inventory_col],
                errors="coerce"
            ).fillna(0)

            kpis["total_inventory"] = float(stock.sum())

            kpis["average_inventory"] = float(stock.mean())

            kpis["low_stock_items"] = int(
                (stock <= 10).sum()
            )

    # Purchase Orders
    kpis["total_purchase_orders"] = 0
    kpis["purchase_value"] = 0

    if purchase_orders is not None and not purchase_orders.empty:

        kpis["total_purchase_orders"] = len(purchase_orders)

        amount_col = find_column(
            purchase_orders,
            [
                "amount",
                "order_amount",
                "purchase_amount",
                "total_cost",
                "cost"
            ]
        )

        if amount_col is not None:

            amounts = pd.to_numeric(
                purchase_orders[amount_col],
                errors="coerce"
            ).fillna(0)

            kpis["purchase_value"] = float(amounts.sum())

    return kpis
