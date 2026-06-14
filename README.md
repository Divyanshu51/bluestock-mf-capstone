# Mutual Fund Analytics Platform
### Bluestock Fintech Capstone Project — June 2026

Built this during my internship at Bluestock Fintech. The goal was to put together a full data platform for mutual fund analytics — something that actually makes sense of the fragmented public data AMFI puts out, and turns it into insights a fund manager or retail investor can use.

---

## What this does

India's MF industry manages over ₹81 lakh crore across 1,900+ schemes. The data is all over the place — AMFI, NSE, BSE, all in different formats. This platform:

- Pulls NAV, AUM, SIP, and transaction data from AMFI India and mfapi.in
- Cleans and stores everything in a normalised SQLite database (7-table star schema)
- Computes Sharpe, Sortino, Alpha, Beta, VaR, CVaR, Max Drawdown, and HHI for all 40 schemes
- Benchmarks fund performance against Nifty 50, Nifty 100, and BSE SmallCap
- Presents everything in a 4-page interactive Power BI dashboard

---

## Quick start

```bash
git clone https://github.com/Divyanshu51/bluestock-mf-capstone.git
cd bluestock-mf-capstone

pip install -r requirements.txt

# run the full pipeline (ingestion → cleaning → database)
python run_pipeline.py

# or skip live API fetch if you're offline
python run_pipeline.py --skip-live
```

Then open `notebooks/` in Jupyter Lab and run each notebook in order.

---

## Project structure

```
bluestock_mf_capstone/
├── data/
│   ├── raw/              original CSVs + live NAV files from mfapi.in
│   ├── processed/        cleaned datasets ready for analysis
│   └── db/               SQLite database (not pushed to GitHub — see note)
├── notebooks/
│   ├── 04_Performance_Analytics.ipynb
│   └── 06_Advanced_Analytics.ipynb
├── scripts/
│   ├── data_ingestion.py    loads all 10 raw CSVs, validates AMFI codes
│   ├── live_nav_fetch.py    fetches live NAV from mfapi.in REST API
│   ├── data_cleaning.py     cleans all 10 datasets, saves to processed/
│   ├── database_setup.py    loads cleaned data into SQLite star schema
│   └── recommender.py       fund recommender by risk appetite
├── sql/
│   ├── schema.sql           CREATE TABLE statements
│   └── queries.sql          10 analytical SQL queries
├── dashboard/
│   └── bluestock_mf_dashboard.pbix   Power BI report (4 pages, slicers, cross-filtering)
├── reports/
│   ├── fund_scorecard.csv
│   ├── alpha_beta.csv
│   ├── var_cvar_report.csv
│   ├── benchmark_comparison.png
│   └── Final_Report.pdf
├── run_pipeline.py          master script — runs entire ETL in sequence
├── requirements.txt
└── README.md
```

---

## Datasets

| File | Rows | What it contains |
|---|---|---|
| 01_fund_master.csv | 40 | Scheme master — fund house, category, expense ratio, risk grade |
| 02_nav_history.csv | 46,000 | Daily NAV Jan 2022 to May 2026 |
| 03_aum_by_fund_house.csv | 90 | Quarterly AUM for 10 fund houses |
| 04_monthly_sip_inflows.csv | 48 | Monthly SIP inflow, accounts, AUM — AMFI Monthly Notes |
| 05_category_inflows.csv | 144 | Net inflows by category FY 2024-25 |
| 06_industry_folio_count.csv | 21 | Total folios by equity, debt, hybrid |
| 07_scheme_performance.csv | 40 | Sharpe, Sortino, Alpha, Beta, CAGR, Drawdown per scheme |
| 08_investor_transactions.csv | 32,778 | SIP/Lumpsum/Redemption for 5,000 investors across 12 states |
| 09_portfolio_holdings.csv | 322 | Top equity holdings with sector weights |
| 10_benchmark_indices.csv | 8,050 | Nifty 50, Nifty 100, BSE SmallCap, CRISIL daily values |

Place all 10 files in `data/raw/` before running the pipeline.

---

## How to open the dashboard

**Power BI Dashboard:**
- Open `dashboard/bluestock_mf_dashboard.pbix` in Power BI Desktop
  ([View on GitHub](https://github.com/Divyanshu51/bluestock-mf-capstone/tree/main/Bluestack%20internship/bluestock_mf_capstone/Day-5/dashboard))
- The report connects to the processed CSVs in `data/processed/` — update the data source path if needed via **Transform Data → Data Source Settings**
- All 4 pages, slicers, tooltips, and cross-filtering are ready to use out of the box

---

## Running individual scripts

```bash
# just load and inspect all 10 datasets
python scripts/data_ingestion.py

# fetch live NAV from mfapi.in (run on local machine — API blocks cloud IPs)
python scripts/live_nav_fetch.py

# clean all datasets
python scripts/data_cleaning.py

# load into SQLite
python scripts/database_setup.py

# fund recommender
python scripts/recommender.py
```

---

## Note on database file

The `.db` file is in `.gitignore` because SQLite binaries don't belong in Git. To recreate it:
```bash
python scripts/data_cleaning.py
python scripts/database_setup.py
```
This rebuilds `data/db/bluestock_mf.db` from the CSVs in about 30 seconds.

---

## Tech stack

Python 3.10 | Pandas | NumPy | Matplotlib | Seaborn | SciPy | SQLite | SQLAlchemy | Power BI | Jupyter Lab | mfapi.in

---

## Data sources

All data is from publicly available sources — AMFI India, mfapi.in (public REST API), NSE, and BSE.
This project is for educational purposes only and does not constitute financial advice.
