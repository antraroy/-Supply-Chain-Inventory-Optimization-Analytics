"""Supply-chain analytics: KPIs, ABC/XYZ, supplier scorecard, demand forecasting, reorder-point optimisation."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import GradientBoostingRegressor

DATA = Path(__file__).resolve().parent.parent / "data"


# ------------------------------------------------------------------ loading
def load():
    prod = pd.read_csv(DATA / "products.csv")
    sales = pd.read_csv(DATA / "sales.csv", parse_dates=["date"])
    inv = pd.read_csv(DATA / "inventory_daily.csv", parse_dates=["date"])
    po = pd.read_csv(DATA / "purchase_orders.csv", parse_dates=["order_date", "promised_date", "delivered_date"])
    po["delay_days"] = (po.delivered_date - po.promised_date).dt.days
    po["lead_days"] = (po.delivered_date - po.order_date).dt.days
    po["on_time"] = po.delay_days <= 0
    return prod, sales, inv, po


# ------------------------------------------------------------------ KPIs
def headline_kpis(prod, sales, inv, po):
    p = prod.set_index("sku")
    s = sales.join(p[["unit_cost", "unit_price"]], on="sku")
    i = inv.join(p[["unit_cost"]], on="sku")
    days = sales.date.nunique()
    cogs = (s.units_sold * s.unit_cost).sum()
    avg_inv_value = (i.on_hand * i.unit_cost).groupby(i.date).sum().mean()
    return {
        "stockout_rate": (inv.on_hand == 0).mean(),                       # share of SKU-days with zero stock
        "fill_rate": sales.units_sold.sum() / sales.demand_units.sum(),
        "return_rate": sales.returned_units.sum() / sales.units_sold.sum(),
        "inventory_turnover": cogs / avg_inv_value * (365 / days),         # annualised
        "days_of_supply": avg_inv_value / (cogs / days),
        "avg_inventory_value": avg_inv_value,
        "revenue": (s.units_sold * s.unit_price).sum(),
        "lost_sales_value": (s.lost_units * s.unit_price).sum(),
        "on_time_delivery": po.on_time.mean(),
        "avg_delay_days": po.loc[~po.on_time, "delay_days"].mean(),
    }


def sku_summary(prod, sales, inv):
    p = prod.set_index("sku")
    g = sales.groupby("sku").agg(units=("units_sold", "sum"), demand=("demand_units", "sum"),
                                 lost=("lost_units", "sum"), returns=("returned_units", "sum"),
                                 avg_daily_demand=("demand_units", "mean"), sd_daily_demand=("demand_units", "std"))
    gi = inv.groupby("sku").agg(avg_on_hand=("on_hand", "mean"), stockout_days_pct=("on_hand", lambda x: (x == 0).mean()))
    d = p.join(g).join(gi)
    days = sales.date.nunique()
    d["revenue"] = d.units * d.unit_price
    d["cogs"] = d.units * d.unit_cost
    d["lost_revenue"] = d.lost * d.unit_price
    d["turnover"] = d.cogs / (d.avg_on_hand * d.unit_cost) * (365 / days)
    d["days_of_supply"] = d.avg_on_hand / d.avg_daily_demand
    d["fill_rate"] = d.units / d.demand
    return d.reset_index()


def abc_xyz(sku_df, sales):
    d = sku_df.sort_values("revenue", ascending=False).copy()
    d["cum_share"] = d.revenue.cumsum() / d.revenue.sum()
    d["abc"] = np.where(d.cum_share <= 0.80, "A", np.where(d.cum_share <= 0.95, "B", "C"))
    wk = sales.set_index("date").groupby("sku").demand_units.resample("W").sum().reset_index()
    cv = wk.groupby("sku").demand_units.agg(lambda x: x.std() / x.mean()).rename("demand_cv")
    d = d.join(cv, on="sku")
    d["xyz"] = np.where(d.demand_cv <= 0.25, "X", np.where(d.demand_cv <= 0.50, "Y", "Z"))
    d["class"] = d.abc + d.xyz
    return d


# ------------------------------------------------------------------ suppliers
def supplier_scorecard(po):
    g = po.groupby("supplier").agg(
        orders=("po_id", "count"), on_time_pct=("on_time", "mean"),
        avg_delay_when_late=("delay_days", lambda x: x[x > 0].mean()),
        avg_lead_days=("lead_days", "mean"), lead_sd=("lead_days", "std"),
        defect_rate=("defective_units", "sum"), units=("qty", "sum"))
    g["defect_rate"] = g.defect_rate / g.units
    # Composite 0-100: 60% on-time, 25% quality (0% defects = full marks, 4%+ = zero), 15% lead-time consistency
    g["score"] = (60 * g.on_time_pct + 25 * (1 - (g.defect_rate / 0.04).clip(0, 1)) + 15 * (1 - (g.lead_sd / 6).clip(0, 1))).round(1)
    g["tier"] = pd.cut(g.score, [0, 70, 85, 101], labels=["Review", "Good", "Preferred"])
    return g.sort_values("score", ascending=False).reset_index()


def delay_by_month(po):
    d = po.assign(month=po.order_date.dt.to_period("M").astype(str)).groupby("month").agg(
        on_time_pct=("on_time", "mean"), avg_delay=("delay_days", lambda x: x.clip(lower=0).mean())).reset_index()
    return d


# ------------------------------------------------------------------ forecasting
def weekly_demand(sales):
    w = sales.set_index("date").groupby("sku").demand_units.resample("W").sum().reset_index()
    # drop the partial first/last weeks so weekly totals are comparable
    return w.pivot(index="date", columns="sku", values="demand_units").iloc[1:-1]


def _feat(hist, week_idx_dates):
    """Feature row for predicting the next point after `hist` (normalised units)."""
    nxt = week_idx_dates
    woy = nxt.isocalendar().week
    return [hist[-1], hist[-2], hist[-3], hist[-4], np.mean(hist[-4:]), np.mean(hist[-8:]), hist[-52],
            np.sin(2 * np.pi * woy / 52), np.cos(2 * np.pi * woy / 52)]


def _build(piv, upto):
    X, y = [], []
    for sku in piv.columns:
        s = piv[sku].iloc[:upto].values; scale = s.mean()
        z = s / scale
        for t in range(52, len(z)):
            X.append(_feat(z[:t], piv.index[t])); y.append(z[t])
    return np.array(X), np.array(y)


def _predict(model, piv, sku, upto, horizon):
    s = piv[sku].iloc[:upto].values; scale = s.mean(); z = list(s / scale)
    dates = pd.date_range(piv.index[upto - 1] + pd.Timedelta(weeks=1), periods=horizon, freq="W")
    out = []
    for dt in dates:
        v = float(model.predict([_feat(np.array(z), dt)])[0]); z.append(max(v, 0)); out.append(max(v, 0) * scale)
    return dates, np.array(out)


def evaluate_forecasts(sales, holdout=12):
    """Compare naive baselines vs gradient boosting on the last `holdout` weeks (WAPE = sum|err| / sum actual)."""
    piv = weekly_demand(sales); n = len(piv); cut = n - holdout
    model = GradientBoostingRegressor(n_estimators=250, max_depth=3, learning_rate=0.05, random_state=1)
    model.fit(*_build(piv, cut))
    rows, actual_tot = [], 0
    err = {"Moving average (4w)": 0, "Seasonal naive (52w)": 0, "Gradient boosting": 0}
    for sku in piv.columns:
        act = piv[sku].iloc[cut:].values; actual_tot += act.sum()
        hist = piv[sku].iloc[:cut].values
        err["Moving average (4w)"] += np.abs(act - hist[-4:].mean()).sum()
        err["Seasonal naive (52w)"] += np.abs(act - piv[sku].iloc[cut - 52:cut - 52 + holdout].values).sum()
        _, pred = _predict(model, piv, sku, cut, holdout)
        err["Gradient boosting"] += np.abs(act - pred).sum()
    res = pd.DataFrame({"model": list(err), "WAPE": [round(v / actual_tot, 4) for v in err.values()]})
    res["accuracy"] = (1 - res.WAPE).round(4)
    return res.sort_values("WAPE"), model, piv


def forecast_sku(model, piv, sku, horizon=8):
    dates, pred = _predict(model, piv, sku, len(piv), horizon)
    return pd.DataFrame({"week": dates, "forecast": pred.round(0)})


# ------------------------------------------------------------------ reorder points
def reorder_policy(prod, sales, po, service_level=0.95, lookback_days=180):
    """ROP = d*L + z*sqrt(L*sd_d^2 + d^2*sd_L^2);  EOQ = sqrt(2*D*S/H)."""
    z = norm.ppf(service_level)
    recent = sales[sales.date > sales.date.max() - pd.Timedelta(days=lookback_days)]
    dem = recent.groupby("sku").demand_units.agg(d="mean", sd_d="std")
    lt = po.groupby("sku").lead_days.agg(L="mean", sd_L="std").fillna(0)
    r = prod.set_index("sku").join(dem).join(lt)
    r["safety_stock"] = z * np.sqrt(r.L * r.sd_d ** 2 + (r.d ** 2) * (r.sd_L ** 2))
    r["recommended_rop"] = np.ceil(r.d * r.L + r.safety_stock)
    r["annual_demand"] = r.d * 365
    r["eoq"] = np.ceil(np.sqrt(2 * r.annual_demand * r.order_cost / (r.holding_rate * r.unit_cost)))
    r["rop_gap_pct"] = (r.current_reorder_point - r.recommended_rop) / r.recommended_rop
    r["status"] = np.where(r.rop_gap_pct < -0.25, "Too low - stockout risk",
                  np.where(r.rop_gap_pct > 0.25, "Too high - overstock", "OK"))
    return r.reset_index()


def simulate_policy(demand_hist, lead_hist, rop, qty, unit_cost, price, order_cost, holding_rate,
                    days=365, seed=0, runs=5):
    """Monte-Carlo replay: bootstrap demand and lead times, return fill rate, avg inventory and total cost."""
    rng = np.random.default_rng(seed); out = []
    for _ in range(runs):
        dem = rng.choice(demand_hist, days); on_hand, pipe = rop + qty, []
        sold_t = dem_t = inv_sum = n_orders = 0
        for t in range(days):
            for a in [x for x in pipe if x[0] <= t]:
                on_hand += a[1]; pipe.remove(a)
            s = min(on_hand, dem[t]); on_hand -= s; sold_t += s; dem_t += dem[t]; inv_sum += on_hand
            if on_hand + sum(x[1] for x in pipe) <= rop:
                pipe.append((t + int(rng.choice(lead_hist)), qty)); n_orders += 1
        avg_inv = inv_sum / days
        cost = avg_inv * unit_cost * holding_rate + n_orders * order_cost + (dem_t - sold_t) * (price - unit_cost)
        out.append((sold_t / dem_t, avg_inv, cost))
    return np.mean(out, axis=0)


def policy_backtest(prod, sales, po, rec):
    rows = []
    for r in rec.itertuples():
        dh = sales.loc[sales.sku == r.sku, "demand_units"].values
        lh = po.loc[po.sku == r.sku, "lead_days"].values
        if len(lh) == 0: continue
        args = (dh, lh)
        kw = dict(unit_cost=r.unit_cost, price=r.unit_price, order_cost=r.order_cost, holding_rate=r.holding_rate)
        cur = simulate_policy(*args, rop=r.current_reorder_point, qty=int(r.eoq), **kw)
        new = simulate_policy(*args, rop=int(r.recommended_rop), qty=int(r.eoq), **kw)
        rows.append({"sku": r.sku, "cur_fill": cur[0], "new_fill": new[0], "cur_inv": cur[1], "new_inv": new[1],
                     "cur_cost": cur[2], "new_cost": new[2]})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    prod, sales, inv, po = load()
    k = headline_kpis(prod, sales, inv, po)
    print("== KPIs =="); [print(f"{a}: {b:,.3f}") for a, b in k.items()]
    sk = sku_summary(prod, sales, inv); ab = abc_xyz(sk, sales)
    print("\n== ABC counts =="); print(ab.abc.value_counts().to_dict(), "| A share of revenue:", round(ab[ab.abc == 'A'].revenue.sum() / ab.revenue.sum(), 3))
    print("\n== Suppliers =="); print(supplier_scorecard(po)[["supplier", "on_time_pct", "defect_rate", "score", "tier"]])
    res, model, piv = evaluate_forecasts(sales); print("\n== Forecast accuracy =="); print(res)
    rec = reorder_policy(prod, sales, po); print("\n== ROP status =="); print(rec.status.value_counts())
    bt = policy_backtest(prod, sales, po, rec)
    print(f"\nBacktest  fill: {bt.cur_fill.mean():.3f} -> {bt.new_fill.mean():.3f} | avg inv units: {bt.cur_inv.sum():,.0f} -> {bt.new_inv.sum():,.0f} | cost: {bt.cur_cost.sum():,.0f} -> {bt.new_cost.sum():,.0f}")
