# Mutual Fund Analytics Platform
### Bluestock Fintech Capstone Project

This is my capstone project built during my internship at Bluestock Fintech. The goal was to build an end-to-end data platform for mutual fund analytics — covering everything from raw data ingestion to an interactive dashboard.

---

## What this project does

The Indian MF industry manages over ₹81 lakh crore across 1,900+ schemes. But for a retail investor trying to compare funds, the data is all over the place — AMFI, NSE, BSE, all in different formats. This project pulls it together into one place.

- Ingests NAV, AUM, SIP, and transaction data from AMFI India public sources
- Cleans and stores everything in a normalised SQLite database
- Computes risk-adjusted performance metrics (Sharpe, Sortino, Alpha, Beta, VaR)
- Compares fund returns against Nifty 50, Nifty 100, and BSE SmallCap benchmarks
- Presents everything through a 4-page interactive Power BI dashboard

---

## Tech stack

| Area | Tools |
|---|---|
| Language | Python 3.10+ |
| Data processing | Pandas, NumPy |
| Visualisation | Matplotlib, Seaborn, Plotly |
| Database | SQLite + SQLAlchemy |
| Statistics | SciPy |
| Dashboard | Power BI Desktop |
| Notebooks | Jupyter Lab |
| API | mfapi.in (public, no auth) |

---

## Data sources

All data is from publicly available sources:
- **AMFI India** — NAV, AUM, SIP inflow, folio counts
- **mfapi.in** — Historical NAV via REST API
- **NSE/BSE** — Benchmark index closing values

The project covers 40 fund schemes across 10 fund houses, with NAV history from Jan 2022 to May 2026.

---

## Project structure

```
bluestock_mf_capstone/
├── data/
│   ├── raw/           # original CSVs and API downloads
│   ├── processed/     # cleaned datasets ready for analysis
│   └── db/            # SQLite database file
├── notebooks/         # Jupyter notebooks for EDA and analytics
├── scripts/           # Python scripts for ETL and metrics
├── sql/               # schema and analytical queries
├── dashboard/         # Power BI .pbix file
├── reports/           # final report PDF and presentation
└── README.md
```

---

## How to run

**1. Clone the repo and install dependencies**
```bash
git clone https://github.com/yourusername/bluestock_mf_capstone.git
cd bluestock_mf_capstone
pip install -r requirements.txt
```

**2. Place the 10 raw CSV datasets in `data/raw/`**

**3. Run Day 1 - data ingestion**
```bash
python scripts/data_ingestion.py
```

**4. Fetch live NAV from mfapi.in**
```bash
python scripts/live_nav_fetch.py
```

**5. Run the full ETL pipeline (after Day 2)**
```bash
python scripts/etl_pipeline.py
```

---

## Dataset overview

| File | Rows | Description |
|---|---|---|
| 01_fund_master.csv | 40 | Master list of 40 schemes with fund house, category, expense ratio |
| 02_nav_history.csv | ~46,000 | Daily NAV for all 40 schemes, Jan 2022–May 2026 |
| 03_aum_by_fund_house.csv | 90 | Quarterly AUM for 10 fund houses |
| 04_monthly_sip_inflows.csv | 48 | Monthly SIP inflow, accounts, and AUM |
| 05_category_inflows.csv | 144 | Net inflows by category (Large Cap, Mid Cap, etc.) |
| 06_industry_folio_count.csv | 21 | Total folios broken by Equity, Debt, Hybrid |
| 07_scheme_performance.csv | 40 | Sharpe, Sortino, Alpha, Beta, CAGR per scheme |
| 08_investor_transactions.csv | ~32,000 | SIP/Lumpsum/Redemption transactions with demographics |
| 09_portfolio_holdings.csv | 322 | Top equity holdings per fund, with sector weights |
| 10_benchmark_indices.csv | ~8,000 | Daily closing for Nifty 50, Nifty 100, BSE SmallCap etc. |

---

## Day-wise progress

- [x] Day 1 — Project setup, data ingestion, live API fetch
- [ ] Day 2 — Data cleaning, SQLite schema, SQL queries
- [ ] Day 3 — Exploratory Data Analysis (15+ charts)
- [ ] Day 4 — Performance metrics (Sharpe, Alpha, Beta, CAGR)
- [ ] Day 5 — Power BI dashboard (4 pages)
- [ ] Day 6 — Advanced analytics (VaR, cohort analysis, recommender)
- [ ] Day 7 — Final report and presentation

---

## Important note

All data is sourced from publicly available information published by AMFI India, NSE, BSE, and open APIs. This project is for educational purposes only and does not constitute financial advice.
