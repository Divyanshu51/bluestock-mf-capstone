"""
database_setup.py
-----------------
Day 2 task: Load all cleaned datasets into a SQLite database
using the star schema defined in sql/schema.sql.

Also generates dim_date from the NAV date range automatically
so we don't need a separate date dimension CSV.

Run from project root (after data_cleaning.py):
    python scripts/database_setup.py
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine, text


ROOT      = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
DB_PATH   = ROOT / "data" / "db" / "bluestock_mf.db"
SCHEMA    = ROOT / "sql" / "schema.sql"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_engine():
    """Create SQLAlchemy engine pointing to our SQLite database."""
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    return engine


def run_schema(engine):
    """Execute schema.sql to create all tables and indexes."""
    print("\n[1] Creating tables from schema.sql...")
    sql = SCHEMA.read_text()

    # SQLite doesn't support multiple statements in one execute —
    # split on semicolon and run each statement separately
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    with engine.connect() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
        conn.commit()
    print(f"  Schema applied from {SCHEMA.name}")


def build_dim_date(engine):
    """
    Build dim_date by generating every date between the min and max
    NAV date. This gives us a proper date dimension with year, month,
    quarter etc. pre-computed.
    """
    print("\n[2] Building dim_date...")
    nav = pd.read_csv(PROCESSED / "02_nav_history_clean.csv", usecols=["date"])
    nav["date"] = pd.to_datetime(nav["date"])

    all_dates = pd.date_range(nav["date"].min(), nav["date"].max(), freq="D")
    dim = pd.DataFrame({"date_id": all_dates})
    dim["date_id"]     = dim["date_id"].dt.strftime("%Y-%m-%d")
    dim["year"]        = all_dates.year
    dim["month"]       = all_dates.month
    dim["quarter"]     = all_dates.quarter
    dim["month_name"]  = all_dates.strftime("%B")
    dim["day_of_week"] = all_dates.dayofweek   # 0=Monday
    dim["is_weekday"]  = (all_dates.dayofweek < 5).astype(int)

    dim.to_sql("dim_date", engine, if_exists="replace", index=False)
    print(f"  dim_date loaded: {len(dim)} rows")


def load_dim_fund(engine):
    print("\n[3] Loading dim_fund...")
    df = pd.read_csv(PROCESSED / "01_fund_master_clean.csv")
    df["launch_date"] = pd.to_datetime(df["launch_date"]).dt.strftime("%Y-%m-%d")
    df.to_sql("dim_fund", engine, if_exists="replace", index=False)
    print(f"  dim_fund loaded: {len(df)} rows")


def load_fact_nav(engine):
    print("\n[4] Loading fact_nav...")
    df = pd.read_csv(PROCESSED / "02_nav_history_clean.csv")
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    # replace NaN in daily_return_pct with None so SQLite stores NULL
    df["daily_return_pct"] = df["daily_return_pct"].replace({np.nan: None})

    df.to_sql("fact_nav", engine, if_exists="replace", index=False)
    print(f"  fact_nav loaded: {len(df)} rows")


def load_fact_aum(engine):
    print("\n[5] Loading fact_aum...")
    df = pd.read_csv(PROCESSED / "03_aum_by_fund_house_clean.csv")
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df.to_sql("fact_aum", engine, if_exists="replace", index=False)
    print(f"  fact_aum loaded: {len(df)} rows")


def load_fact_sip_industry(engine):
    print("\n[6] Loading fact_sip_industry...")
    df = pd.read_csv(PROCESSED / "04_monthly_sip_inflows_clean.csv")
    df["month"] = pd.to_datetime(df["month"]).dt.strftime("%Y-%m-%d")
    df["yoy_growth_pct"] = df["yoy_growth_pct"].replace({np.nan: None})
    df.to_sql("fact_sip_industry", engine, if_exists="replace", index=False)
    print(f"  fact_sip_industry loaded: {len(df)} rows")


def load_fact_performance(engine):
    print("\n[7] Loading fact_performance...")
    df = pd.read_csv(PROCESSED / "07_scheme_performance_clean.csv")
    df.to_sql("fact_performance", engine, if_exists="replace", index=False)
    print(f"  fact_performance loaded: {len(df)} rows")


def load_fact_transactions(engine):
    print("\n[8] Loading fact_transactions...")
    df = pd.read_csv(PROCESSED / "08_investor_transactions_clean.csv")
    df["transaction_date"] = pd.to_datetime(df["transaction_date"]).dt.strftime("%Y-%m-%d")
    df.to_sql("fact_transactions", engine, if_exists="replace", index=False)
    print(f"  fact_transactions loaded: {len(df)} rows")


def load_fact_portfolio(engine):
    print("\n[9] Loading fact_portfolio...")
    df = pd.read_csv(PROCESSED / "09_portfolio_holdings_clean.csv")
    df["portfolio_date"] = pd.to_datetime(df["portfolio_date"]).dt.strftime("%Y-%m-%d")
    df.to_sql("fact_portfolio", engine, if_exists="replace", index=False)
    print(f"  fact_portfolio loaded: {len(df)} rows")


def verify_row_counts(engine):
    """
    Cross-check row counts between processed CSVs and database tables.
    If they don't match something went wrong in loading.
    """
    print("\n[10] Verifying row counts (CSV vs DB)...")

    checks = {
        "dim_fund"          : "01_fund_master_clean.csv",
        "fact_nav"          : "02_nav_history_clean.csv",
        "fact_aum"          : "03_aum_by_fund_house_clean.csv",
        "fact_sip_industry" : "04_monthly_sip_inflows_clean.csv",
        "fact_performance"  : "07_scheme_performance_clean.csv",
        "fact_transactions" : "08_investor_transactions_clean.csv",
        "fact_portfolio"    : "09_portfolio_holdings_clean.csv",
    }

    all_good = True
    with engine.connect() as conn:
        for table, csvfile in checks.items():
            csv_rows = len(pd.read_csv(PROCESSED / csvfile))
            db_rows  = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            status   = "✓" if csv_rows == db_rows else "✗ MISMATCH"
            if csv_rows != db_rows:
                all_good = False
            print(f"  {table:<25} CSV: {csv_rows:>7}   DB: {db_rows:>7}   {status}")

    if all_good:
        print("\n  All row counts match.")
    else:
        print("\n  WARNING: Some row counts don't match — check loading logic.")


def main():
    print("\nBluestock Fintech - Mutual Fund Analytics")
    print("Day 2: Loading cleaned data into SQLite database")

    engine = get_engine()

    run_schema(engine)
    build_dim_date(engine)
    load_dim_fund(engine)
    load_fact_nav(engine)
    load_fact_aum(engine)
    load_fact_sip_industry(engine)
    load_fact_performance(engine)
    load_fact_transactions(engine)
    load_fact_portfolio(engine)
    verify_row_counts(engine)

    print(f"\nDatabase created at: {DB_PATH}")
    print("Next: run python scripts/run_queries.py to test analytical queries")


if __name__ == "__main__":
    main()
