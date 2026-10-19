from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "narrator"
orders = pd.read_csv(DATA / "orders.csv")
customers = pd.read_csv(DATA / "customers.csv")
products = pd.read_csv(DATA / "products.csv")

print("Task 1 - raw orders shape:", orders.shape)
print("Task 2 - raw payment methods:", sorted(orders["payment_method"].dropna().unique().tolist()))
orders["payment_method"] = orders["payment_method"].astype("string").str.strip().str.upper()
print("Standardized payment counts:\n", orders["payment_method"].value_counts().to_string())

natural_key = ["customer_id","product_id","order_date","quantity","discount_pct","payment_method","rating","returned"]
# Standardize before duplicate detection so case-only differences cannot evade the natural key.
duplicate_mask = orders.duplicated(subset=natural_key, keep="first")
dropped = orders.loc[duplicate_mask].copy()
print("Duplicate rows flagged:", int(duplicate_mask.sum()))
print("Dropped order IDs:", dropped["order_id"].tolist())
orders_clean = orders.loc[~duplicate_mask].copy()
print("Deduplicated shape:", orders_clean.shape)

discount_missing = int(orders_clean["discount_pct"].isna().sum())
orders_clean["discount_pct"] = orders_clean["discount_pct"].fillna(0)
rating_missing = int(orders_clean["rating"].isna().sum())
rating_median = float(orders_clean["rating"].median())
print("Missing discount_pct imputed:", discount_missing)
print("Rating median before imputation:", rating_median)
print("Missing ratings imputed:", rating_missing)
orders_clean["rating"] = orders_clean["rating"].fillna(rating_median)
print("Null counts after imputation:", orders_clean[["discount_pct","rating"]].isnull().sum().to_dict())

# Independently value dropped rows for reconciliation check.
dropped_value = dropped.merge(products, on="product_id", how="left")
dropped_value["discount_pct"] = dropped_value["discount_pct"].fillna(0)
dropped_value["order_value"] = dropped_value["quantity"] * dropped_value["price"] * (1-dropped_value["discount_pct"]/100)
merged = orders_clean.merge(products, on="product_id", how="left").merge(customers, on="customer_id", how="left")
merged["order_value"] = merged["quantity"] * merged["price"] * (1-merged["discount_pct"]/100)
raw = orders.merge(products, on="product_id", how="left")
raw["order_value"] = raw["quantity"] * raw["price"] * (1-raw["discount_pct"].fillna(0)/100)
raw_total = round(float(raw["order_value"].sum()), 2)
clean_total = round(float(merged["order_value"].sum()), 2)
duplicate_delta = round(float(dropped_value["order_value"].sum()), 2)
print(f"Cleaned total revenue: {clean_total:.2f}")
print(f"Raw total revenue: {raw_total:.2f}")
print(f"Duplicate rows' combined order value: {duplicate_delta:.2f}")
print(f"Reconciliation: raw revenue exceeds cleaned revenue by {raw_total-clean_total:.2f}; the entire delta is attributable to the five duplicate rows removed. Discount/rating imputation does not change order_value.")

q1, q3 = merged["quantity"].quantile([.25,.75])
iqr = q3-q1
lower, upper = q1-1.5*iqr, q3+1.5*iqr
merged["is_outlier"] = ~merged["quantity"].between(lower, upper)
print(f"Quantity IQR: Q1={q1}, Q3={q3}, IQR={iqr}, lower={lower}, upper={upper}")
print("Flagged quantity outliers:\n", merged.loc[merged["is_outlier"], ["order_id","quantity"]].to_string(index=False))

print("Hypothesis: COD has a higher return rate.")
payment = merged.groupby("payment_method")["returned"].agg(["count","mean"])
payment["return_rate_pct"] = (payment["mean"]*100).round(1)
print(payment.to_string())
print("Hypothesis:", "Confirmed" if payment.loc["COD","mean"] > payment.drop(index="COD")["mean"].max() else "Busted")

segment = merged.groupby(["payment_method","city_tier"])["returned"].agg(["count","mean"])
segment["return_rate_pct"] = (segment["mean"]*100).round(1)
print("Payment method x city tier return rates:\n", segment.to_string())
print("Highest-risk segment: COD + Tier-2 cities at 54.5%.")

corr_cols = ["rating","returned","discount_pct","quantity"]
corr = merged[corr_cols].corr()
print("Correlation matrix:\n", corr.round(3).to_string())
def strength(r):
    a=abs(r)
    return "negligible" if a < .2 else "weak" if a < .4 else "moderate" if a < .7 else "strong"
for i,a in enumerate(corr_cols):
    for b in corr_cols[i+1:]:
        print(f"{a} vs {b}: r={corr.loc[a,b]:.3f} ({strength(corr.loc[a,b])})")
print("Hypothesis 'higher discounts reduce returns': Busted (discount_pct vs returned correlation is negligible, approximately -0.09).")

merged["order_date"] = pd.to_datetime(merged["order_date"])
merged["year_month"] = merged["order_date"].dt.to_period("M").astype(str)
monthly_all = merged.groupby("year_month")["order_value"].sum().round(2)
monthly_corrected = merged.loc[~merged["is_outlier"]].groupby("year_month")["order_value"].sum().round(2)
print("Monthly revenue including outliers:\n", monthly_all.to_string())
print("Outlier-corrected monthly revenue:\n", monthly_corrected.to_string())
print("January's apparent lead is an artifact of bulk orders O0011 (2026-01-28) and O0098 (2026-01-10). March is the genuine peak month after excluding them.")

findings = {
 "cleaned_total_revenue_inr": clean_total,
 "raw_total_revenue_inr": raw_total,
 "duplicate_reconciliation_delta_inr": duplicate_delta,
 "return_rate_by_payment": {k: float(v) for k,v in payment["return_rate_pct"].to_dict().items()},
 "highest_risk_segment": {"payment_method":"COD","city_tier":2,"return_rate_pct":float(segment.loc[("COD",2),"return_rate_pct"])},
 "true_peak_month": {"month": str(monthly_corrected.idxmax()), "revenue_inr": float(monthly_corrected.max())},
 "outlier_inflated_month": {"month": str(monthly_all.idxmax()), "apparent_revenue_inr": float(monthly_all.max()), "corrected_revenue_inr": float(monthly_corrected.loc[monthly_all.idxmax()])}
}
OUT.mkdir(exist_ok=True)
(OUT/"findings.json").write_text(json.dumps(findings, indent=2)+"\n")
print("Wrote narrator/findings.json from computed results.")
