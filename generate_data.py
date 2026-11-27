"""Simulate 2 years of supply-chain activity: demand, (s,Q) replenishment, supplier delays, stockouts, returns."""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
OUT = Path(__file__).resolve().parent.parent / "data"
OUT.mkdir(exist_ok=True)

START, DAYS = pd.Timestamp("2024-11-01"), 730
CATEGORIES = {  # category: (unit cost range, margin, seasonality amplitude, base daily demand range)
    "Electronics": ((800, 6000), 0.22, 0.25, (2, 9)),
    "Home & Kitchen": ((150, 1500), 0.35, 0.15, (5, 25)),
    "Apparel": ((200, 1800), 0.50, 0.30, (6, 30)),
    "Grocery": ((20, 250), 0.18, 0.08, (25, 90)),
    "Health & Beauty": ((80, 900), 0.40, 0.10, (8, 35)),
}
WAREHOUSES = ["Delhi", "Mumbai", "Kolkata", "Bengaluru"]
SUPPLIERS = {  # name: (avg promised lead time, P(late), mean delay when late, defect rate)
    "Apex Supplies": (5, 0.10, 1.5, 0.010), "BlueLine Traders": (7, 0.18, 2.5, 0.015),
    "CoreMart Wholesale": (9, 0.30, 3.5, 0.025), "Delta Logistics": (6, 0.12, 2.0, 0.012),
    "EverGreen Imports": (14, 0.40, 5.0, 0.030), "FastTrack Distributors": (4, 0.08, 1.0, 0.008),
}


def main(n_skus=48):
    sup_names = list(SUPPLIERS)
    sup_df = pd.DataFrame([{"supplier": k, "promised_lead_days": v[0], "defect_rate": v[3]} for k, v in SUPPLIERS.items()])

    prods = []
    for i in range(n_skus):
        cat = list(CATEGORIES)[i % len(CATEGORIES)]
        (clo, chi), margin, amp, (dlo, dhi) = CATEGORIES[cat]
        cost = round(float(rng.uniform(clo, chi)), 0)
        prods.append({
            "sku": f"SKU{i+1:03d}", "product_name": f"{cat} Item {i+1:03d}", "category": cat,
            "warehouse": WAREHOUSES[i % 4], "supplier": rng.choice(sup_names),
            "unit_cost": cost, "unit_price": round(cost * (1 + margin), 0),
            "base_demand": round(float(rng.uniform(dlo, dhi)), 1), "season_amp": amp,
            "order_cost": float(rng.choice([800, 1200, 1500])),
            "holding_rate": 0.22,          # annual holding cost as % of unit cost
            # current policy quality: <1 = too lean (stockouts), >1 = too heavy (overstock)
            "policy_factor": float(rng.choice([0.45, 0.7, 1.0, 1.0, 1.6, 2.4])),
        })
    prods = pd.DataFrame(prods)

    dates = pd.date_range(START, periods=DAYS)
    t = np.arange(DAYS)
    sales_rows, inv_rows, po_rows, po_id = [], [], [], 0

    for p in prods.itertuples():
        promised, p_late, mean_delay, defect = SUPPLIERS[p.supplier]
        season = 1 + p.season_amp * np.sin(2 * np.pi * (t - 60) / 365) + 0.0004 * t      # yearly cycle + mild growth
        festive = np.where(pd.Series(dates).dt.month.isin([10, 11]), 1.25, 1.0)           # festive-season lift
        weekend = np.where(pd.Series(dates).dt.dayofweek >= 5, 1.12, 1.0)
        lam = p.base_demand * season * festive * weekend
        demand = rng.poisson(lam)

        avg_d = p.base_demand
        rop = int(p.policy_factor * avg_d * (promised + 2))           # current (deliberately imperfect) reorder point
        order_qty = int(max(avg_d * 30, 60) * (1.0 if p.policy_factor <= 1.6 else 1.8))
        on_hand, pipeline = int(rop + order_qty), []                  # pipeline: (arrival_idx, qty, po_id)

        for d in range(DAYS):
            for arr in [x for x in pipeline if x[0] <= d]:
                on_hand += arr[1]; pipeline.remove(arr)
            sold = min(on_hand, int(demand[d])); lost = int(demand[d]) - sold
            on_hand -= sold
            returned = int(rng.binomial(sold, 0.021)) if sold else 0
            on_hand += returned
            sales_rows.append((dates[d], p.sku, int(demand[d]), sold, lost, returned))
            on_order = sum(x[1] for x in pipeline)
            if on_hand + on_order <= rop:
                late = rng.random() < p_late
                delay = int(max(1, round(rng.exponential(mean_delay)))) if late else 0
                lead = int(max(2, rng.normal(promised, 0.8))) + delay
                po_id += 1
                qty = order_qty
                pipeline.append((d + lead, qty, po_id))
                po_rows.append({
                    "po_id": f"PO{po_id:05d}", "sku": p.sku, "supplier": p.supplier, "order_date": dates[d],
                    "promised_date": dates[d] + pd.Timedelta(days=int(round(promised))),
                    "delivered_date": dates[d] + pd.Timedelta(days=lead), "qty": qty,
                    "defective_units": int(rng.binomial(qty, defect)),
                })
            inv_rows.append((dates[d], p.sku, on_hand, on_order))

    pd.DataFrame(sales_rows, columns=["date", "sku", "demand_units", "units_sold", "lost_units", "returned_units"]).to_csv(OUT / "sales.csv", index=False)
    pd.DataFrame(inv_rows, columns=["date", "sku", "on_hand", "on_order"]).to_csv(OUT / "inventory_daily.csv", index=False)
    pd.DataFrame(po_rows).to_csv(OUT / "purchase_orders.csv", index=False)
    prods.drop(columns=["policy_factor", "base_demand", "season_amp"]).assign(
        current_reorder_point=[int(r.policy_factor * r.base_demand * (SUPPLIERS[r.supplier][0] + 2)) for r in prods.itertuples()]
    ).to_csv(OUT / "products.csv", index=False)
    sup_df.to_csv(OUT / "suppliers.csv", index=False)
    print(f"Saved: {len(sales_rows):,} sales rows, {len(inv_rows):,} inventory rows, {len(po_rows):,} purchase orders -> {OUT}")


if __name__ == "__main__":
    main()
