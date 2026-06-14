# 📊 Bluestock Fintech — Mutual Fund Analytics Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Wrangling-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebooks-F37626?style=for-the-badge&logo=jupyter&logoColor=white)

**End-to-end Mutual Fund Analytics Platform built as a Data Analyst Intern Capstone at Bluestock Fintech Pvt. Ltd.**

*7 Working Days | June 2026 | Data Source: AMFI India, mfapi.in, NSE/BSE*

| 40 | 87,393+ | 32,778 | 10 |
|:---:|:---:|:---:|:---:|
| Fund Schemes | Total Rows | Transactions | Fund Houses |

</div>

---

## 📸 Dashboard Screenshots

### Page 1 — Industry Overview
![Industry Overview](https://raw.githubusercontent.com/Divyanshu51/bluestock-mf-capstone/main/Bluestack%20internship/Day-5/Images/Industry%20Overview.png)

### Page 2 — Fund Performance
![Fund Performance](https://raw.githubusercontent.com/Divyanshu51/bluestock-mf-capstone/main/Bluestack%20internship/Day-5/Images/Fund%20Performance.png)

### Page 3 — Investor Analytics
![Investor Analytics](https://raw.githubusercontent.com/Divyanshu51/bluestock-mf-capstone/main/Bluestack%20internship/Day-5/Images/Investor%20Analytics.png)

### Page 4 — SIP & Market Trends
![SIP & Market Trends](https://raw.githubusercontent.com/Divyanshu51/bluestock-mf-capstone/main/Bluestack%20internship/Day-5/Images/SIP%20%26%20Market%20Trends.png)

---

## 🎯 Project Overview

The Indian mutual fund industry manages over ₹62.74 lakh crore in AUM, yet retail investors lack access to institutional-grade analytics. This platform solves that gap by building a complete data pipeline — from raw AMFI data to an interactive Power BI dashboard — covering risk metrics, investor behaviour, and fund performance across 40 schemes.

### Problems Solved

| # | Problem | Solution |
|---|---------|----------|
| P1 | NAV, AUM, SIP data fragmented across AMFI/NSE/BSE | Unified ETL pipeline into single SQLite DB |
| P2 | No easy way to compare 40+ funds on risk-adjusted metrics | Sharpe, Sortino, Alpha, Beta computed for all schemes |
| P3 | Retail investors can't track benchmark performance | Nifty 50 / Nifty 100 / CRISIL comparison built-in |
| P4 | Limited visibility into SIP demographic patterns | 32,778 transactions analysed by state, age, city tier |
| P5 | Monthly MF reports are static PDFs | 4-page live Power BI dashboard with slicers |

---

## 🏗️ Architecture

```
Raw Data (AMFI / mfapi.in / NSE)
        │
        ▼
┌─────────────────┐
│  ETL Pipeline   │  etl_pipeline.py — Extract → Clean → Validate → Load
│  (Python)       │  live_nav_fetch.py — Daily cron @ 8 PM IST
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQLite DB      │  bluestock_mf.db — 10-table star schema
│  (Star Schema)  │  Indexes on amfi_code + date
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Jupyter        │  EDA → Performance Metrics → Advanced Analytics
│  Notebooks (5)  │  Sharpe | VaR | Monte Carlo | Markowitz Frontier
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Power BI       │  4-page interactive dashboard
│  Dashboard      │  12 DAX measures | 5 table relationships
└─────────────────┘
```

---

## 📁 Project Structure

```
bluestock_mf_capstone/
├── data/
│   ├── raw/                        ← 10 original CSVs from AMFI/NSE
│   ├── processed/                  ← 13 cleaned + derived CSVs
│   └── db/
│       └── bluestock_mf.db         ← SQLite (NOT committed — see schema.sql)
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb
├── scripts/
│   ├── etl_pipeline.py             ← Main ETL — runs without manual steps
│   ├── live_nav_fetch.py           ← mfapi.in live NAV fetcher (cron-ready)
│   ├── compute_metrics.py          ← Recompute all metrics from latest NAV
│   └── recommender.py              ← CLI fund recommender by risk appetite
├── sql/
│   ├── schema.sql                  ← Full DB schema
│   └── queries.sql                 ← 12 key analytical SQL queries
├── dashboard/
│   └── bluestock_mf.pbix           ← Power BI 4-page dashboard
├── reports/
│   ├── Final_Report.pdf
│   └── Presentation.pptx
├── logs/
├── .gitignore
└── README.md
```

---

## 📦 Datasets

| # | File | Rows | Description |
|---|------|------|-------------|
| 01 | fund_master | 40 | Fund house, category, expense ratio, risk grade |
| 02 | nav_history | 46,000+ | Daily NAV — Jan 2022 to May 2026 (ffill applied) |
| 03 | aum_by_fund_house | 90 | Quarterly AUM (₹ Crore) for 10 fund houses |
| 04 | monthly_sip_inflows | 48 | SIP inflow, active accounts, new registrations |
| 05 | category_inflows | 144 | Net inflows by fund category |
| 06 | industry_folio_count | 21 | Total folios — equity, debt, hybrid segments |
| 07 | scheme_performance | 40 | 1yr/3yr returns, Sharpe, Sortino, Alpha, Beta |
| 08 | investor_transactions | 32,778 | SIP/Lumpsum/Redemption — 5,000 investors, 12 states |
| 09 | portfolio_holdings | 322 | Equity holdings with sector weights per fund |
| 10 | benchmark_indices | 8,050 | Daily Nifty 50, Nifty 100, CRISIL closing values |

> ⚠️ Raw data files are not committed. Place them in `data/raw/` before running the ETL.

---

## 🚀 Getting Started

### Prerequisites
```bash
pip install pandas numpy matplotlib scipy requests jupyter
```

### 1. Run the ETL Pipeline
```bash
python scripts/etl_pipeline.py
```

### 2. Run the Notebooks (in order)
```bash
jupyter lab notebooks/
```
Run `01` → `02` → `03` → `04` → `05` in sequence.

### 3. Use the Fund Recommender
```bash
# Interactive mode
python scripts/recommender.py

# CLI mode
python scripts/recommender.py --risk High --top 5
```

### 4. Schedule Live NAV Fetch
```bash
# Runs every weekday at 8 PM IST
0 20 * * 1-5 /usr/bin/python3 /path/to/scripts/live_nav_fetch.py
```

---

## 📊 Key Metrics & Findings

### Industry Overview
| Metric | Value |
|--------|-------|
| Industry AUM (Dec 2025) | ₹62.74 Lakh Crore |
| Monthly SIP Inflow | ₹31,002 Crore (all-time high) |
| SIP Growth (2022–2025) | 169% (₹11,517 Cr → ₹31,002 Cr) |
| Total Folios | 26.12 Crore |
| Active SIP Accounts | 9.35 Crore |

### Top Funds by Sharpe Ratio
| Rank | Fund | Category | 3Y CAGR | Sharpe |
|------|------|----------|---------|--------|
| 1 | ICICI Pru Liquid Fund | Liquid | — | 7.8+ |
| 2 | Kotak Liquid Fund | Liquid | — | 6.2 |
| 3 | Kotak Emerging Equity Fund | Mid Cap | 18.2% | 0.960 |
| 4 | ICICI Pru Midcap Fund | Mid Cap | 18.1% | 0.950 |
| 5 | SBI Small Cap Fund | Small Cap | 23.4% | 0.940 |

### VaR 95% Risk Metrics
| Fund | Daily VaR | Daily CVaR |
|------|-----------|------------|
| SBI Small Cap Fund | -2.69% | -3.24% |
| ABSL Small Cap Fund | -2.39% | -3.10% |
| ICICI Pru Liquid Fund | -0.02% | -0.03% |

---

## 🔬 Deliverables

| ID | Deliverable | Status |
|----|-------------|--------|
| D1 | `etl_pipeline.py` — automated ETL, no manual steps | ✅ Done |
| D2 | `bluestock_mf.db` — 10-table SQLite star schema | ✅ Done |
| D3 | `03_eda_analysis.ipynb` — 15+ charts | ✅ Done |
| D4 | `04_performance_analytics.ipynb` + CSVs | ✅ Done |
| D5 | `bluestock_mf.pbix` — 4-page Power BI dashboard | ✅ Done |
| D6 | `05_advanced_analytics.ipynb` | ✅ Done |
| D7 | `Final_Report.pdf` + `Presentation.pptx` | ✅ Done |
| B1 | Live NAV cron fetch from mfapi.in | ✅ Done |
| B3 | Monte Carlo 5-year NAV projection | ✅ Done |
| B4 | Markowitz Efficient Frontier | ✅ Done |

---

## 🛠️ Tech Stack

| Category | Tool | Purpose |
|----------|------|---------|
| Language | Python 3.10+ | ETL, analytics, automation |
| Data Wrangling | Pandas 2.0, NumPy | Cleaning, time-series |
| Visualisation | Matplotlib, Plotly | EDA charts |
| Statistics | SciPy | OLS regression for Alpha/Beta |
| Database | SQLite | 10-table star schema |
| Dashboard | Power BI Desktop | 4-page interactive report |
| Live Data | mfapi.in REST API | Daily NAV fetch |
| Notebooks | Jupyter Lab | Analysis & documentation |

---

## ⚠️ Limitations

- NAV data covers Jan 2022 – May 2026 (4.4 years) — 5-year CAGR not computable
- Portfolio holdings are a single snapshot (Dec 2025)
- VaR uses historical simulation — does not model black swan events
- `*.db` files excluded from git — use `schema.sql` to recreate

---

<div align="center">

**Divyanshu Rai** — Data Analyst Intern
Bluestock Fintech Pvt. Ltd. | June 2026

*"Making institutional-grade fund analytics accessible to every Indian investor."*

</div>
