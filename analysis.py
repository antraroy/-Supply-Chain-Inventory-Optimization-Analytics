# ============================================================
# HEADLINE KPI METRICS
# ============================================================

def headline_kpis(products, sales, inventory, purchase_orders=None):

    kpis = {}

    # ---------------- PRODUCTS ----------------
    kpis["total_products"] = (
        len(products) if products is not None else 0
    )

    # ---------------- SALES ----------------
    if sales is not None and not sales.empty:

        sales_col = find_column(
            sales,
            ["sales", "sales_amount", "revenue", "total_sales", "amount"]
        )

        quantity_col = find_column(
            sales,
            ["quantity", "qty", "units_sold"]
        )

        if sales_col:
            sales_values = pd.to_numeric(
                sales[sales_col],
                errors="coerce"
            ).fillna(0)

            kpis["total_sales"] = sales_values.sum()
            kpis["average_sales"] = sales_values.mean()

        else:
            kpis["total_sales"] = 0
            kpis["average_sales"] = 0

        if quantity_col:
            quantity_values = pd.to_numeric(
                sales[quantity_col],
                errors="coerce"
            ).fillna(0)

            kpis["total_units_sold"] = quantity_values.sum()

        else:
            kpis["total_units_sold"] = 0

    else:

        kpis["total_sales"] = 0
        kpis["average_sales"] = 0
        kpis["total_units_sold"] = 0

    # ---------------- INVENTORY ----------------
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

        if inventory_col:

            stock_values = pd.to_numeric(
                inventory[inventory_col],
                errors="coerce"
            ).fillna(0)

            kpis["total_inventory"] = stock_values.sum()

            kpis["average_inventory"] = stock_values.mean()

            kpis["low_stock_items"] = (
                stock_values <= 10
            ).sum()

        else:

            kpis["total_inventory"] = 0
            kpis["average_inventory"] = 0
            kpis["low_stock_items"] = 0

    else:

        kpis["total_inventory"] = 0
        kpis["average_inventory"] = 0
        kpis["low_stock_items"] = 0

    # ---------------- PURCHASE ORDERS ----------------
    if purchase_orders is not None and not purchase_orders.empty:

        kpis["total_purchase_orders"] = len(
            purchase_orders
        )

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

        if amount_col:

            amount_values = pd.to_numeric(
                purchase_orders[amount_col],
                errors="coerce"
            ).fillna(0)

            kpis["purchase_value"] = amount_values.sum()

        else:

            kpis["purchase_value"] = 0

    else:

        kpis["total_purchase_orders"] = 0
        kpis["purchase_value"] = 0

    # ---------------- RETURN ----------------
    return kpis
