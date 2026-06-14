"""
Day 2 Pipeline: Data Cleaning + SQLite DB Design + Load + Queries
Bluestock Internship – Mutual Fund Analytics
"""

import pandas as pd
import numpy as np
import sqlite3
import os
from sqlalchemy import create_engine, text

RAW = "/home/claude/bluestock_mf/data/raw"
PROCESSED = "/home/claude/bluestock_mf/data/processed"
DB_PATH = "/home/claude/bluestock_mf/bluestock_mf.db"
SQL_DIR = "/home/claude/bluestock_mf/sql"

os.makedirs(PROCESSED, exist_ok=True)
os.makedirs(SQL_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# 1. CLEAN nav_history.csv  (02)
# ─────────────────────────────────────────────
print("=" * 60)
print("1. Cleaning nav_history.csv …")

nav = pd.read_csv(f"{RAW}/02_nav_history.csv")
print(f"   Raw rows : {len(nav):,}")

nav["date"] = pd.to_datetime(nav["date"], errors="coerce")
nav = nav.dropna(subset=["date"])
nav = nav.sort_values(["amfi_code", "date"]).reset_index(drop=True)

# Forward-fill missing NAV for weekends/holidays within each fund
def ffill_nav(g):
    code = g.name  # group key when using groupby
    nav_series = g.set_index("date")["nav"]
    nav_series = nav_series.reindex(
        pd.date_range(nav_series.index.min(), nav_series.index.max(), freq="D"),
        method="ffill"
    )
    return pd.DataFrame({
        "date": nav_series.index,
        "nav": nav_series.values,
        "amfi_code": code
    })

nav = nav.groupby("amfi_code")[["date","nav","amfi_code"]].apply(ffill_nav).reset_index(drop=True)

nav = nav.drop_duplicates(subset=["amfi_code", "date"])
nav = nav[nav["nav"] > 0]

# Add anomaly flag: NAV change > 20% day-on-day
nav = nav.sort_values(["amfi_code", "date"])
nav["nav_pct_change"] = nav.groupby("amfi_code")["nav"].pct_change() * 100
nav["nav_anomaly"] = nav["nav_pct_change"].abs() > 20

print(f"   Cleaned rows : {len(nav):,}")
print(f"   NAV anomalies flagged : {nav['nav_anomaly'].sum():,}")
nav.to_csv(f"{PROCESSED}/02_nav_history_clean.csv", index=False)
print("   ✓ Saved 02_nav_history_clean.csv")

# ─────────────────────────────────────────────
# 2. CLEAN investor_transactions.csv  (08)
# ─────────────────────────────────────────────
print("\n2. Cleaning investor_transactions.csv …")

txn = pd.read_csv(f"{RAW}/08_investor_transactions.csv")
print(f"   Raw rows : {len(txn):,}")

txn["transaction_date"] = pd.to_datetime(txn["transaction_date"], errors="coerce")
txn = txn.dropna(subset=["transaction_date"])

# Standardise transaction_type
type_map = {
    "sip": "SIP", "Sip": "SIP", "SIP": "SIP",
    "lumpsum": "Lumpsum", "Lumpsum": "Lumpsum", "LumpSum": "Lumpsum",
    "redemption": "Redemption", "Redemption": "Redemption", "REDEMPTION": "Redemption",
    "Switch": "Switch", "switch": "Switch",
    "SWP": "SWP", "swp": "SWP",
    "STP": "STP", "stp": "STP",
}
txn["transaction_type"] = txn["transaction_type"].map(type_map).fillna(txn["transaction_type"])
valid_types = {"SIP", "Lumpsum", "Redemption", "Switch", "SWP", "STP"}
before = len(txn)
txn = txn[txn["transaction_type"].isin(valid_types)]
print(f"   Rows removed (invalid transaction_type) : {before - len(txn):,}")

# Validate amount > 0
txn = txn[txn["amount_inr"] > 0]

# Validate KYC enum
valid_kyc = {"Verified", "Pending", "Rejected", "Not Submitted"}
txn["kyc_status"] = txn["kyc_status"].where(txn["kyc_status"].isin(valid_kyc), "Unknown")

txn = txn.drop_duplicates()
print(f"   Cleaned rows : {len(txn):,}")
txn.to_csv(f"{PROCESSED}/08_investor_transactions_clean.csv", index=False)
print("   ✓ Saved 08_investor_transactions_clean.csv")

# ─────────────────────────────────────────────
# 3. CLEAN scheme_performance.csv  (07)
# ─────────────────────────────────────────────
print("\n3. Cleaning scheme_performance.csv …")

perf = pd.read_csv(f"{RAW}/07_scheme_performance.csv")
print(f"   Raw rows : {len(perf):,}")

return_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
               "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
               "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct"]

for col in return_cols:
    perf[col] = pd.to_numeric(perf[col], errors="coerce")

# Flag return anomalies (beyond ±100 %)
for col in ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct"]:
    perf[f"{col}_anomaly"] = perf[col].abs() > 100

# Validate expense_ratio range 0.1 – 2.5 %
perf["expense_ratio_valid"] = perf["expense_ratio_pct"].between(0.1, 2.5)
invalid_er = (~perf["expense_ratio_valid"]).sum()
print(f"   Expense ratio out-of-range : {invalid_er}")

perf.to_csv(f"{PROCESSED}/07_scheme_performance_clean.csv", index=False)
print(f"   Cleaned rows : {len(perf):,}")
print("   ✓ Saved 07_scheme_performance_clean.csv")

# ─────────────────────────────────────────────
# 4. CLEAN remaining CSVs (pass-through with type fixes)
# ─────────────────────────────────────────────
print("\n4. Cleaning remaining CSVs …")

# 01_fund_master
fm = pd.read_csv(f"{RAW}/01_fund_master.csv")
fm["launch_date"] = pd.to_datetime(fm["launch_date"], errors="coerce")
fm["expense_ratio_pct"] = pd.to_numeric(fm["expense_ratio_pct"], errors="coerce")
fm["exit_load_pct"] = pd.to_numeric(fm["exit_load_pct"], errors="coerce")
fm.to_csv(f"{PROCESSED}/01_fund_master_clean.csv", index=False)
print(f"   ✓ 01_fund_master_clean.csv  ({len(fm):,} rows)")

# 03_aum_by_fund_house
aum = pd.read_csv(f"{RAW}/03_aum_by_fund_house.csv")
aum["date"] = pd.to_datetime(aum["date"], errors="coerce")
aum.to_csv(f"{PROCESSED}/03_aum_by_fund_house_clean.csv", index=False)
print(f"   ✓ 03_aum_by_fund_house_clean.csv  ({len(aum):,} rows)")

# 04_monthly_sip_inflows
sip = pd.read_csv(f"{RAW}/04_monthly_sip_inflows.csv")
sip["month"] = pd.to_datetime(sip["month"], errors="coerce")
sip.to_csv(f"{PROCESSED}/04_monthly_sip_inflows_clean.csv", index=False)
print(f"   ✓ 04_monthly_sip_inflows_clean.csv  ({len(sip):,} rows)")

# 05_category_inflows
cat_inf = pd.read_csv(f"{RAW}/05_category_inflows.csv")
cat_inf["month"] = pd.to_datetime(cat_inf["month"], errors="coerce")
cat_inf.to_csv(f"{PROCESSED}/05_category_inflows_clean.csv", index=False)
print(f"   ✓ 05_category_inflows_clean.csv  ({len(cat_inf):,} rows)")

# 06_industry_folio_count
folio = pd.read_csv(f"{RAW}/06_industry_folio_count.csv")
folio["month"] = pd.to_datetime(folio["month"], errors="coerce")
folio.to_csv(f"{PROCESSED}/06_industry_folio_count_clean.csv", index=False)
print(f"   ✓ 06_industry_folio_count_clean.csv  ({len(folio):,} rows)")

# 09_portfolio_holdings
ph = pd.read_csv(f"{RAW}/09_portfolio_holdings.csv")
ph["portfolio_date"] = pd.to_datetime(ph["portfolio_date"], errors="coerce")
ph.to_csv(f"{PROCESSED}/09_portfolio_holdings_clean.csv", index=False)
print(f"   ✓ 09_portfolio_holdings_clean.csv  ({len(ph):,} rows)")

# 10_benchmark_indices
bi = pd.read_csv(f"{RAW}/10_benchmark_indices.csv")
bi["date"] = pd.to_datetime(bi["date"], errors="coerce")
bi.to_csv(f"{PROCESSED}/10_benchmark_indices_clean.csv", index=False)
print(f"   ✓ 10_benchmark_indices_clean.csv  ({len(bi):,} rows)")

# ─────────────────────────────────────────────
# 5. SQLITE – CREATE SCHEMA + LOAD
# ─────────────────────────────────────────────
print("\n5. Creating SQLite DB + loading tables …")

engine = create_engine(f"sqlite:///{DB_PATH}")

DDL = """
-- Dimension: Fund
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code           INTEGER PRIMARY KEY,
    fund_house          TEXT    NOT NULL,
    scheme_name         TEXT    NOT NULL,
    category            TEXT,
    sub_category        TEXT,
    plan                TEXT,
    launch_date         TEXT,
    benchmark           TEXT,
    expense_ratio_pct   REAL    CHECK (expense_ratio_pct BETWEEN 0.0 AND 5.0),
    exit_load_pct       REAL,
    min_sip_amount      INTEGER,
    min_lumpsum_amount  INTEGER,
    fund_manager        TEXT,
    risk_category       TEXT,
    sebi_category_code  TEXT
);

-- Dimension: Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_key    TEXT PRIMARY KEY,   -- YYYY-MM-DD
    year        INTEGER,
    quarter     INTEGER,
    month       INTEGER,
    week        INTEGER,
    day         INTEGER,
    day_of_week INTEGER,
    is_weekend  INTEGER
);

-- Fact: NAV History
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    date_key        TEXT    NOT NULL REFERENCES dim_date(date_key),
    nav             REAL    NOT NULL CHECK (nav > 0),
    nav_pct_change  REAL,
    nav_anomaly     INTEGER DEFAULT 0
);

-- Fact: Investor Transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    txn_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT    NOT NULL,
    transaction_date    TEXT    NOT NULL,
    amfi_code           INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    transaction_type    TEXT    NOT NULL CHECK (transaction_type IN ('SIP','Lumpsum','Redemption','Switch','SWP','STP')),
    amount_inr          REAL    NOT NULL CHECK (amount_inr > 0),
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT
);

-- Fact: Scheme Performance
CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER,
    risk_grade          TEXT
);

-- Fact: AUM
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date_key        TEXT    NOT NULL REFERENCES dim_date(date_key),
    fund_house      TEXT    NOT NULL,
    aum_crore       REAL,
    aum_lakh_crore  REAL,
    num_schemes     INTEGER
);
"""

with engine.connect() as conn:
    for stmt in DDL.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(text(stmt))
    conn.commit()

print("   ✓ Schema created")

# Build dim_date from nav date range
all_dates = pd.date_range("2022-01-01", "2025-12-31", freq="D")
dim_date_df = pd.DataFrame({
    "date_key":    all_dates.strftime("%Y-%m-%d"),
    "year":        all_dates.year,
    "quarter":     all_dates.quarter,
    "month":       all_dates.month,
    "week":        all_dates.isocalendar().week.values,
    "day":         all_dates.day,
    "day_of_week": all_dates.dayofweek,
    "is_weekend":  (all_dates.dayofweek >= 5).astype(int),
})

table_map = [
    ("dim_fund",         fm,     "replace"),
    ("dim_date",         dim_date_df, "replace"),
    ("fact_nav",         nav[["amfi_code","date","nav","nav_pct_change","nav_anomaly"]].rename(columns={"date":"date_key"}).assign(date_key=lambda df: df["date_key"].dt.strftime("%Y-%m-%d")), "replace"),
    ("fact_transactions",txn.rename(columns={"transaction_date":"transaction_date"}), "replace"),
    ("fact_performance", perf[["amfi_code","return_1yr_pct","return_3yr_pct","return_5yr_pct",
                                "benchmark_3yr_pct","alpha","beta","sharpe_ratio","sortino_ratio",
                                "std_dev_ann_pct","max_drawdown_pct","expense_ratio_pct",
                                "morningstar_rating","risk_grade"]], "replace"),
    ("fact_aum",         aum.rename(columns={"date":"date_key"}), "replace"),
]

row_counts = {}
for tbl, df, mode in table_map:
    df.to_sql(tbl, engine, if_exists=mode, index=False)
    row_counts[tbl] = len(df)
    print(f"   ✓ {tbl:<25} {len(df):>8,} rows loaded")

# ─────────────────────────────────────────────
# 6. 10 ANALYTICAL SQL QUERIES
# ─────────────────────────────────────────────
print("\n6. Running 10 analytical SQL queries …")

queries = {
    "Q1_top5_funds_by_aum": """
        SELECT f.fund_house, f.scheme_name, p.return_1yr_pct,
               p.morningstar_rating,
               a.total_aum_crore
        FROM   fact_performance p
        JOIN   dim_fund f ON f.amfi_code = p.amfi_code
        LEFT JOIN (
            SELECT fund_house, SUM(aum_crore) AS total_aum_crore
            FROM   fact_aum
            WHERE  date_key = (SELECT MAX(date_key) FROM fact_aum)
            GROUP  BY fund_house
        ) a ON a.fund_house = f.fund_house
        ORDER  BY a.total_aum_crore DESC
        LIMIT  5
    """,
    "Q2_avg_nav_per_month": """
        SELECT substr(n.date_key,1,4) AS year,
               CAST(substr(n.date_key,6,2) AS INTEGER) AS month,
               ROUND(AVG(n.nav), 4) AS avg_nav,
               COUNT(*)              AS records
        FROM   fact_nav n
        GROUP  BY year, month
        ORDER  BY year, month
    """,
    "Q3_sip_transactions_per_year": """
        SELECT strftime('%Y', transaction_date) AS yr,
               COUNT(*)                          AS sip_count,
               ROUND(SUM(amount_inr)/1e7, 2)    AS total_inr_crore
        FROM   fact_transactions
        WHERE  transaction_type = 'SIP'
        GROUP  BY yr
        ORDER  BY yr
    """,
    "Q4_transactions_by_state": """
        SELECT state,
               COUNT(*)                       AS txn_count,
               ROUND(SUM(amount_inr)/1e7, 2) AS total_crore
        FROM   fact_transactions
        GROUP  BY state
        ORDER  BY txn_count DESC
        LIMIT  15
    """,
    "Q5_low_expense_ratio_funds": """
        SELECT f.scheme_name, f.fund_house, f.category,
               f.expense_ratio_pct
        FROM   dim_fund f
        WHERE  f.expense_ratio_pct < 1.0
        ORDER  BY f.expense_ratio_pct ASC
    """,
    "Q6_top_performers_3yr": """
        SELECT f.scheme_name, f.category,
               p.return_3yr_pct, p.alpha, p.sharpe_ratio
        FROM   fact_performance p
        JOIN   dim_fund f ON f.amfi_code = p.amfi_code
        WHERE  p.return_3yr_pct IS NOT NULL
        ORDER  BY p.return_3yr_pct DESC
        LIMIT  10
    """,
    "Q7_kyc_status_distribution": """
        SELECT kyc_status,
               COUNT(*)                       AS txn_count,
               ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (), 2) AS pct
        FROM   fact_transactions
        GROUP  BY kyc_status
        ORDER  BY txn_count DESC
    """,
    "Q8_nav_52week_high_low": """
        SELECT f.scheme_name,
               ROUND(MAX(n.nav), 4) AS high_52w,
               ROUND(MIN(n.nav), 4) AS low_52w,
               ROUND((MAX(n.nav)-MIN(n.nav))/MIN(n.nav)*100, 2) AS range_pct
        FROM   fact_nav n
        JOIN   dim_fund f ON f.amfi_code = n.amfi_code
        WHERE  substr(n.date_key,1,4) = '2025'
        GROUP  BY n.amfi_code
        ORDER  BY range_pct DESC
        LIMIT  10
    """,
    "Q9_aum_by_fund_house_latest": """
        SELECT fund_house,
               ROUND(SUM(aum_crore),0) AS total_aum_crore
        FROM   fact_aum
        WHERE  date_key = (SELECT MAX(date_key) FROM fact_aum)
        GROUP  BY fund_house
        ORDER  BY total_aum_crore DESC
    """,
    "Q10_redemption_vs_purchase_ratio": """
        SELECT f.category,
               SUM(CASE WHEN t.transaction_type = 'Redemption' THEN t.amount_inr ELSE 0 END) AS redemptions,
               SUM(CASE WHEN t.transaction_type IN ('SIP','Lumpsum') THEN t.amount_inr ELSE 0 END) AS purchases,
               ROUND(
                 SUM(CASE WHEN t.transaction_type = 'Redemption' THEN t.amount_inr ELSE 0 END) * 1.0 /
                 NULLIF(SUM(CASE WHEN t.transaction_type IN ('SIP','Lumpsum') THEN t.amount_inr ELSE 0 END),0)
               ,4) AS redemption_ratio
        FROM   fact_transactions t
        JOIN   dim_fund f ON f.amfi_code = t.amfi_code
        GROUP  BY f.category
        ORDER  BY redemption_ratio DESC
    """,
}

query_results = {}
with engine.connect() as conn:
    for qname, sql in queries.items():
        df_result = pd.read_sql(text(sql), conn)
        query_results[qname] = df_result
        print(f"\n   {qname}")
        print(df_result.to_string(index=False, max_rows=5))

print("\n✅  Day 2 pipeline complete.")
print(f"   DB  : {DB_PATH}")
print(f"   Rows: {row_counts}")
