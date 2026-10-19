from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/"data"
OUT = ROOT/"visualizations"
OUT.mkdir(exist_ok=True)
orders = pd.read_csv(DATA/"orders.csv")
products = pd.read_csv(DATA/"products.csv")
orders["payment_method"] = orders["payment_method"].astype("string").str.strip().str.upper()
key = ["customer_id","product_id","order_date","quantity","discount_pct","payment_method","rating","returned"]
orders = orders.drop_duplicates(subset=key, keep="first").copy()
orders["discount_pct"] = orders["discount_pct"].fillna(0)
orders["rating"] = orders["rating"].fillna(orders["rating"].median())
df = orders.merge(products,on="product_id")
df["order_value"] = df["quantity"]*df["price"]*(1-df["discount_pct"]/100)
rates = (df.groupby("payment_method")["returned"].mean()*100).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(8,5))
bars=ax.bar(rates.index, rates.values)
ax.set_ylabel("Return rate (%)")
ax.set_title(f"COD Returns at {rates.get('COD',0):.1f}% — about 3x Card")
ax.set_ylim(0, max(rates.values)*1.2)
for bar,val in zip(bars,rates.values):
    ax.text(bar.get_x()+bar.get_width()/2, val+0.6, f"{val:.1f}%", ha="center")
fig.tight_layout(); fig.savefig(OUT/"return_rate_by_payment.png", dpi=160); plt.close(fig)

df["order_date"]=pd.to_datetime(df["order_date"])
q1,q3=df["quantity"].quantile([.25,.75]); iqr=q3-q1
lo,hi=q1-1.5*iqr,q3+1.5*iqr
df=df[df["quantity"].between(lo,hi)].copy()
df["year_month"]=df["order_date"].dt.to_period("M").astype(str)
monthly=df.groupby("year_month")["order_value"].sum().sort_index()
fig,ax=plt.subplots(figsize=(9,5))
ax.plot(monthly.index,monthly.values,marker="o")
ax.set_xlabel("Month"); ax.set_ylabel("Revenue (INR)")
ax.set_title(f"Outlier-corrected monthly revenue — peak: {monthly.idxmax()}")
ax.tick_params(axis="x",rotation=35)
fig.tight_layout(); fig.savefig(OUT/"monthly_revenue_trend.png",dpi=160); plt.close(fig)
print("Saved both visualizations to visualizations/.")
