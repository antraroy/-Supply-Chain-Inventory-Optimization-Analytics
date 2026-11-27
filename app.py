# =========================
# KEY PERFORMANCE INDICATORS
# =========================

st.header("📊 Key Performance Indicators")

# Safely convert values to numbers
def safe_number(value, default=0.0):
    try:
        if value is None:
            return default

        value = float(value)

        if pd.isna(value):
            return default

        return value

    except (ValueError, TypeError):
        return default


# Safely read KPI dictionary
stockout_rate = safe_number(k.get("stockout_rate", 0))
fill_rate = safe_number(k.get("fill_rate", 0))

total_sales = safe_number(k.get("total_sales", 0))
total_orders = safe_number(k.get("total_orders", 0))
inventory_value = safe_number(k.get("inventory_value", 0))
total_inventory = safe_number(k.get("total_inventory", 0))

# KPI columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Stockout Rate",
        value=f"{stockout_rate:.2%}"
    )

with col2:
    st.metric(
        label="Fill Rate",
        value=f"{fill_rate:.1%}"
    )

with col3:
    st.metric(
        label="Total Sales",
        value=f"₹{total_sales:,.2f}"
    )

with col4:
    st.metric(
        label="Inventory Value",
        value=f"₹{inventory_value:,.2f}"
    )

# Second KPI row
col5, col6 = st.columns(2)

with col5:
    st.metric(
        label="Total Orders",
        value=f"{total_orders:,.0f}"
    )

with col6:
    st.metric(
        label="Total Inventory Units",
        value=f"{total_inventory:,.0f}"
    )
