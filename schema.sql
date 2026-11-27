CREATE TABLE products (
    sku VARCHAR(10) PRIMARY KEY, product_name VARCHAR(60), category VARCHAR(30), warehouse VARCHAR(20),
    supplier VARCHAR(40), unit_cost DECIMAL(10,2), unit_price DECIMAL(10,2),
    order_cost DECIMAL(10,2), holding_rate DECIMAL(5,2), current_reorder_point INT
);
CREATE TABLE suppliers (supplier VARCHAR(40) PRIMARY KEY, promised_lead_days INT, defect_rate DECIMAL(5,3));
CREATE TABLE sales (date DATE, sku VARCHAR(10), demand_units INT, units_sold INT, lost_units INT, returned_units INT);
CREATE TABLE inventory_daily (date DATE, sku VARCHAR(10), on_hand INT, on_order INT);
CREATE TABLE purchase_orders (
    po_id VARCHAR(10) PRIMARY KEY, sku VARCHAR(10), supplier VARCHAR(40), order_date DATE,
    promised_date DATE, delivered_date DATE, qty INT, defective_units INT
);
