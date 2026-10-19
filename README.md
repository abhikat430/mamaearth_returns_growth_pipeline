# Mamaearth Returns & Growth Intelligence Pipeline

A reproducible capstone project with a SQLite relational layer, an independent pandas cleaning/EDA pipeline, two Matplotlib visualizations, and a Gemini-powered SCR narrative with an offline fallback. Raw CSVs in `data/` are preserved as provided.

## Repository layout
- `sql/`: SQLite schema, re-runnable seed inserts, and report queries.
- `data/`: original customers, products, and orders CSV files.
- `analysis/clean_and_eda.py`: independent pandas cleaning, reconciliation, EDA, and computed `narrator/findings.json`.
- `analysis/visualize.py`: regenerates both PNG charts.
- `visualizations/`: generated charts.
- `narrator/`: computed findings, SCR generator, and saved sample output.

## Requirements
Python 3.10+; install dependencies:
```bash
python -m pip install pandas matplotlib google-genai
```
SQLite is available through the `sqlite3` command or Python standard library.

## Run in order

### 1. SQL relational layer
From the repository root, create a database and apply the schema and seed data:
```bash
sqlite3 mamaearth.db < sql/schema.sql
sqlite3 mamaearth.db < sql/seed_data.sql
sqlite3 mamaearth.db < sql/reports.sql
```
`seed_data.sql` is generated from the untouched CSV seed rows and is re-runnable. The report script includes the requested report queries; note that the `ALTER TABLE` statement in report (i) is intended to run once per fresh database.

### 2. Python cleaning and analysis
```bash
python analysis/clean_and_eda.py
python analysis/visualize.py
```
The cleaning script reads the raw CSVs directly, standardizes payment methods, removes duplicate natural-key orders, imputes missing values, computes revenue/reconciliation, flags quantity outliers, tests return-rate hypotheses, and writes `narrator/findings.json` from computed values. The visualization script regenerates `visualizations/return_rate_by_payment.png` and `visualizations/monthly_revenue_trend.png`.

### 3. SCR narrative
For Gemini, set a free-tier Google AI Studio key as an environment variable:
```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
python narrator/generate_narrative.py
```
Do not commit your API key. Without a key, run the same command and the fully deterministic offline narrative is used automatically; if the online call errors, it also falls back offline. The script saves the produced text to `narrator/sample_output.txt` and checks the required numeric figures.

## Data flow
The SQL layer reports against raw loaded rows. The independent pandas layer reads the same raw CSVs, performs cleaning, and computes its own verified figures. It exports those figures to `narrator/findings.json`; the narrative layer reads that JSON rather than hardcoding values into the prompt or template.

## Key findings to validate
The expected benchmark figures are cleaned revenue ₹97,358.30; raw revenue ₹99,860.20; duplicate delta ₹2,501.90; COD return rate 44.4%; COD + Tier-2 return rate 54.5%; and corrected peak month March 2026 at ₹20,318.90. Always run the scripts to generate results rather than manually editing generated values.
