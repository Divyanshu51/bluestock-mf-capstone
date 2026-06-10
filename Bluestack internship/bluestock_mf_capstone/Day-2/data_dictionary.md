# Data Dictionary – Bluestock Mutual Fund Analytics
**Capstone Project I | Day 2 Deliverable**

---

## Overview

| File / Table | Rows (cleaned) | Grain | Source CSV |
|---|---|---|---|
| `dim_fund` / `01_fund_master_clean.csv` | 40 | One row per AMFI scheme code | `01_fund_master.csv` |
| `fact_nav` / `02_nav_history_clean.csv` | 64,320 | One row per fund per calendar day (forward-filled) | `02_nav_history.csv` |
| `fact_aum` / `03_aum_by_fund_house_clean.csv` | 90 | One row per fund house per quarter-end date | `03_aum_by_fund_house.csv` |
| `04_monthly_sip_inflows_clean.csv` | 48 | One row per month (industry-wide) | `04_monthly_sip_inflows.csv` |
| `05_category_inflows_clean.csv` | 144 | One row per category per month | `05_category_inflows.csv` |
| `06_industry_folio_count_clean.csv` | 21 | One row per month (industry-wide) | `06_industry_folio_count.csv` |
| `fact_performance` / `07_scheme_performance_clean.csv` | 40 | One row per AMFI scheme code | `07_scheme_performance.csv` |
| `fact_transactions` / `08_investor_transactions_clean.csv` | 32,778 | One row per investor transaction | `08_investor_transactions.csv` |
| `09_portfolio_holdings_clean.csv` | 322 | One row per fund × stock holding | `09_portfolio_holdings.csv` |
| `10_benchmark_indices_clean.csv` | 8,050 | One row per index per trading day | `10_benchmark_indices.csv` |

---

## Table: `dim_fund` (01_fund_master_clean.csv)

| Column | Data Type | Example | Business Definition |
|---|---|---|---|
| `amfi_code` | INTEGER | 119551 | **Primary key.** AMFI-assigned unique scheme identifier. Used across all fact tables as foreign key. |
| `fund_house` | TEXT | SBI Mutual Fund | Asset Management Company (AMC) name. |
| `scheme_name` | TEXT | SBI Bluechip Fund – Regular – Growth | Full SEBI-registered scheme name including plan and option. |
| `category` | TEXT | Equity | Broad SEBI category: Equity / Debt / Hybrid / Solution Oriented / Other. |
| `sub_category` | TEXT | Large Cap | SEBI sub-category (e.g., Large Cap, Short Duration, Balanced Advantage). |
| `plan` | TEXT | Regular | Regular (distributor) or Direct (no commission). |
| `launch_date` | DATE | 2013-01-01 | Scheme inception date (parsed to `datetime`). |
| `benchmark` | TEXT | NIFTY 100 TRI | Official benchmark index for performance comparison. |
| `expense_ratio_pct` | REAL | 1.58 | Annual total expense ratio as % of AUM. Valid range: 0.0–5.0. |
| `exit_load_pct` | REAL | 1.0 | Exit load charged on early redemption (%). |
| `min_sip_amount` | INTEGER | 500 | Minimum SIP instalment in INR. |
| `min_lumpsum_amount` | INTEGER | 5000 | Minimum one-time investment in INR. |
| `fund_manager` | TEXT | Sohini Andani | Name(s) of the managing fund manager(s). |
| `risk_category` | TEXT | Moderate | Risk label: Low / Moderate / High / Very High. |
| `sebi_category_code` | TEXT | EC01 | SEBI standardisation code for scheme classification. |

---

## Table: `fact_nav` (02_nav_history_clean.csv)

| Column | Data Type | Example | Business Definition |
|---|---|---|---|
| `amfi_code` | INTEGER | 119551 | FK → `dim_fund.amfi_code`. |
| `date_key` | TEXT (YYYY-MM-DD) | 2022-01-03 | Observation date. Non-trading days (weekends/holidays) are forward-filled from the last known NAV. |
| `nav` | REAL | 54.3856 | Net Asset Value per unit in INR. Must be > 0. |
| `nav_pct_change` | REAL | -0.07 | Day-on-day percentage change in NAV. NULL for first row of each fund. |
| `nav_anomaly` | BOOLEAN (0/1) | 0 | Flag = 1 if `|nav_pct_change| > 20%`, indicating a potential data quality issue. |

**Cleaning notes:** Raw file had 46,000 rows. After forward-filling all calendar days per fund (2022-01-01 → 2025-12-31), the cleaned file has 64,320 rows. Duplicates on `(amfi_code, date)` were removed.

---

## Table: `fact_aum` (03_aum_by_fund_house_clean.csv)

| Column | Data Type | Example | Business Definition |
|---|---|---|---|
| `date_key` | TEXT (YYYY-MM-DD) | 2022-03-31 | Quarter-end or month-end date of the AUM snapshot. FK → `dim_date.date_key`. |
| `fund_house` | TEXT | SBI Mutual Fund | AMC name. |
| `aum_lakh_crore` | REAL | 6.05 | AUM in INR Lakh Crore (= 100,000 Crore). |
| `aum_crore` | REAL | 605000 | AUM in INR Crore (primary analytical field). |
| `num_schemes` | INTEGER | 186 | Number of active schemes for this fund house at the snapshot date. |

---

## Table: `04_monthly_sip_inflows_clean.csv`

| Column | Data Type | Example | Business Definition |
|---|---|---|---|
| `month` | DATE | 2022-01-01 | First day of the reporting month (parsed from YYYY-MM). |
| `sip_inflow_crore` | INTEGER | 11517 | Gross SIP inflows across the industry for the month (INR Crore). |
| `active_sip_accounts_crore` | REAL | 5.01 | Number of live SIP mandates (in Crore units). |
| `new_sip_accounts_lakh` | REAL | 17.6 | New SIP registrations during the month (in Lakh units). |
| `sip_aum_lakh_crore` | REAL | 4.80 | Total AUM held under SIP mandates (INR Lakh Crore). |
| `yoy_growth_pct` | REAL | 15.2 | Year-on-year growth in SIP inflows. NULL for first 12 months (no prior year). |

---

## Table: `05_category_inflows_clean.csv`

| Column | Data Type | Example | Business Definition |
|---|---|---|---|
| `month` | DATE | 2024-04-01 | First day of the reporting month. |
| `category` | TEXT | Large Cap | SEBI fund category. |
| `net_inflow_crore` | REAL | 2413.0 | Net inflows (purchases minus redemptions) for the category in INR Crore. Negative = net outflow. |

---

## Table: `06_industry_folio_count_clean.csv`

| Column | Data Type | Example | Business Definition |
|---|---|---|---|
| `month` | DATE | 2022-01-01 | First day of the reporting month. |
| `total_folios_crore` | REAL | 13.26 | Total investor folios across all categories (in Crore units). |
| `equity_folios_crore` | REAL | 8.50 | Folios in equity schemes. |
| `debt_folios_crore` | REAL | 2.63 | Folios in debt schemes. |
| `hybrid_folios_crore` | REAL | 0.80 | Folios in hybrid schemes. |
| `others_folios_crore` | REAL | 1.33 | Folios in solution-oriented and other schemes. |

---

## Table: `fact_performance` (07_scheme_performance_clean.csv)

| Column | Data Type | Example | Business Definition |
|---|---|---|---|
| `amfi_code` | INTEGER | 119551 | FK → `dim_fund.amfi_code`. |
| `scheme_name` | TEXT | SBI Bluechip Fund | Scheme name (denormalised for convenience). |
| `fund_house` | TEXT | SBI Mutual Fund | AMC name. |
| `category` | TEXT | Equity | SEBI category. |
| `plan` | TEXT | Regular | Regular or Direct. |
| `return_1yr_pct` | REAL | 18.45 | Trailing 1-year absolute return (%). |
| `return_3yr_pct` | REAL | 19.82 | Trailing 3-year CAGR (%). |
| `return_5yr_pct` | REAL | 17.23 | Trailing 5-year CAGR (%). |
| `benchmark_3yr_pct` | REAL | 18.95 | Benchmark index 3-year CAGR for alpha calculation. |
| `alpha` | REAL | 0.87 | Jensen's Alpha: excess return over the benchmark (risk-adjusted). |
| `beta` | REAL | 0.95 | Market beta: sensitivity to benchmark movements (1.0 = market). |
| `sharpe_ratio` | REAL | 0.92 | (Return − Risk-free rate) / Standard deviation. Higher = better. |
| `sortino_ratio` | REAL | 1.12 | Like Sharpe but penalises only downside volatility. |
| `std_dev_ann_pct` | REAL | 14.30 | Annualised standard deviation of daily returns (%). |
| `max_drawdown_pct` | REAL | -22.10 | Maximum peak-to-trough portfolio decline (%). Negative value. |
| `aum_crore` | INTEGER | 32500 | Scheme AUM at snapshot date (INR Crore). |
| `expense_ratio_pct` | REAL | 1.58 | Annual TER at snapshot date. Anomaly-flagged if outside 0.1–2.5%. |
| `morningstar_rating` | INTEGER | 4 | 1–5 star rating from Morningstar India. |
| `risk_grade` | TEXT | Moderate | Risk label consistent with `dim_fund.risk_category`. |
| `return_1yr_pct_anomaly` | BOOLEAN | 0 | Flag = 1 if `|return_1yr_pct| > 100%`. |
| `return_3yr_pct_anomaly` | BOOLEAN | 0 | Flag = 1 if `|return_3yr_pct| > 100%`. |
| `return_5yr_pct_anomaly` | BOOLEAN | 0 | Flag = 1 if `|return_5yr_pct| > 100%`. |
| `expense_ratio_valid` | BOOLEAN | 1 | Flag = 1 if `expense_ratio_pct` is in the valid range 0.1–2.5%. |

---

## Table: `fact_transactions` (08_investor_transactions_clean.csv)

| Column | Data Type | Example | Business Definition |
|---|---|---|---|
| `investor_id` | TEXT | INV003054 | Anonymised investor identifier. |
| `transaction_date` | DATE | 2024-01-01 | Date the transaction was processed (parsed to `datetime`). |
| `amfi_code` | INTEGER | 119551 | FK → `dim_fund.amfi_code`. |
| `transaction_type` | TEXT | SIP | Standardised to one of: SIP / Lumpsum / Redemption / Switch / SWP / STP. |
| `amount_inr` | REAL | 5000 | Transaction amount in INR. Must be > 0. |
| `state` | TEXT | Maharashtra | Indian state of the investor. |
| `city` | TEXT | Mumbai | City of the investor. |
| `city_tier` | TEXT | Tier 1 | City classification: Tier 1 / Tier 2 / Tier 3. |
| `age_group` | TEXT | 35-44 | Investor age bracket. |
| `gender` | TEXT | Male | Investor gender. |
| `annual_income_lakh` | REAL | 12.5 | Self-declared annual income in INR Lakh. |
| `payment_mode` | TEXT | UPI | Payment channel: UPI / NetBanking / Cheque / NACH / Debit Card. |
| `kyc_status` | TEXT | Verified | KYC compliance status: Verified / Pending / Rejected / Not Submitted / Unknown. |

**Cleaning notes:** `transaction_type` values were standardised using a case-insensitive mapping. Rows with `amount_inr ≤ 0` were removed. `kyc_status` values outside the valid enum were set to "Unknown".

---

## Table: `09_portfolio_holdings_clean.csv`

| Column | Data Type | Example | Business Definition |
|---|---|---|---|
| `amfi_code` | INTEGER | 119551 | FK → `dim_fund.amfi_code`. |
| `stock_symbol` | TEXT | HDFCBANK | NSE ticker symbol. |
| `stock_name` | TEXT | HDFC Bank Ltd | Full company name. |
| `sector` | TEXT | Financials | GICS/SEBI sector classification. |
| `weight_pct` | REAL | 8.45 | Stock's weight in the fund portfolio (%). Sum should be ~100% per fund. |
| `market_value_cr` | REAL | 2735.20 | Market value of holding in INR Crore at `portfolio_date`. |
| `current_price_inr` | REAL | 1074.65 | Stock closing price in INR at `portfolio_date`. |
| `portfolio_date` | DATE | 2025-12-31 | Snapshot date of the portfolio disclosure. |

---

## Table: `10_benchmark_indices_clean.csv`

| Column | Data Type | Example | Business Definition |
|---|---|---|---|
| `date` | DATE | 2022-01-03 | Trading day (parsed to `datetime`). |
| `index_name` | TEXT | NIFTY50 | Index identifier: NIFTY50 / NIFTY_MIDCAP150 / NIFTY_SMALLCAP250 / SENSEX / etc. |
| `close_value` | REAL | 17492.79 | Index closing value on the given date. |

---

## Dimension: `dim_date`

| Column | Data Type | Example | Business Definition |
|---|---|---|---|
| `date_key` | TEXT (PK) | 2022-01-03 | ISO 8601 date string. Primary key and FK target for all fact tables. |
| `year` | INTEGER | 2022 | Calendar year. |
| `quarter` | INTEGER | 1 | Calendar quarter (1–4). |
| `month` | INTEGER | 1 | Calendar month (1–12). |
| `week` | INTEGER | 1 | ISO week number. |
| `day` | INTEGER | 3 | Day of month. |
| `day_of_week` | INTEGER | 0 | 0 = Monday, 6 = Sunday. |
| `is_weekend` | INTEGER | 0 | 1 if Saturday or Sunday, 0 otherwise. |

---

## Data Quality Rules

| Rule | Applies To | Threshold | Action |
|---|---|---|---|
| NAV > 0 | `fact_nav.nav` | 0 | Row removed |
| Date parseable | All date columns | — | Row removed if unparseable |
| transaction_type in allowed enum | `fact_transactions` | See enum | Row removed |
| amount_inr > 0 | `fact_transactions` | 0 | Row removed |
| kyc_status in allowed enum | `fact_transactions` | See enum | Set to "Unknown" |
| expense_ratio in 0.1–2.5% | `fact_performance`, `dim_fund` | 0.1–2.5 | Flagged via `expense_ratio_valid` column |
| Return anomaly flag | `fact_performance` | ±100% | Flagged via `*_anomaly` columns |
| NAV day-on-day change > 20% | `fact_nav` | 20% | Flagged via `nav_anomaly` column |

---

*Generated: Day 2 – Bluestock Capstone Project I – Mutual Fund Analytics*
