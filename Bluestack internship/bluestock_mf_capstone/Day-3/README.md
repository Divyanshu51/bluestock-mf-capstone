# Day 3 – Exploratory Data Analysis

This folder has all the EDA work I did for Day 3 of the Bluestock internship. The goal was to explore the mutual fund datasets visually and pull out meaningful patterns before moving to modelling.

## What's inside

```
Day-3/
├── EDA_Analysis.ipynb   ← main notebook with all charts + findings
├── charts/              ← exported PNGs (15 charts)
│   ├── chart01_nav_trend.png
│   ├── chart02_aum_bar.png
│   ├── chart03_sip_timeseries.png
│   ├── chart04_category_heatmap.png
│   ├── chart05_demographics.png
│   ├── chart06_geographic.png
│   ├── chart07_folio_growth.png
│   ├── chart08_corr_matrix.png
│   ├── chart09_sector_donut.png
│   ├── chart10_risk_return.png
│   ├── chart11_sharpe_ratio.png
│   ├── chart12_txn_type.png
│   ├── chart13_state_month_heatmap.png
│   ├── chart14_expense_vs_return.png
│   └── chart15_sip_yoy.png
└── eda_charts.py        ← script that generates all the charts
```

## Charts covered

1. NAV trend for all 40 schemes (2022–2026) with bull run and correction highlighted
2. AUM grouped bar chart by fund house per year
3. Monthly SIP inflow time-series with ATH annotation
4. Category inflow heatmap (months × categories)
5. Investor demographics – age pie, SIP box plot, gender split
6. Geographic distribution – state-wise SIP bar + city tier pie
7. Folio count growth from 13.26 Cr to 26.12 Cr with milestones
8. NAV return correlation matrix for 10 funds
9. Sector allocation donut for equity funds
10. Risk vs Return scatter (3yr CAGR vs Std Dev)
11. Sharpe ratio ranking
12. Transaction type distribution
13. State × month heatmap
14. Expense ratio vs 1-year return
15. Annual SIP YoY growth

## Key things I noticed

- SBI MF is way ahead of everyone else on AUM at ₹12.5 lakh crore
- SIP inflows hit ₹31,002 Cr in Dec 2025 which is an all-time high
- Folios literally doubled in 4 years which shows how fast retail participation is growing
- Financial services takes up ~30% of equity fund holdings — quite concentrated
- Small/mid cap funds clearly show the high risk–high return pattern

## How to run

```bash
pip install pandas matplotlib seaborn plotly nbformat
python eda_charts.py        # generates all PNGs
jupyter notebook EDA_Analysis.ipynb
```
