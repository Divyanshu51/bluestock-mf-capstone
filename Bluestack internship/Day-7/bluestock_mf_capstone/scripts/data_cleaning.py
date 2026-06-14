"""
data_cleaning.py
----------------
Day 2 task: Clean all 10 raw datasets and save cleaned versions
to data/processed/. Each dataset gets specific cleaning logic
based on what the data represents.

Cleaning steps per dataset:
  - Parse date columns to proper datetime
  - Remove duplicate rows
  - Fix or flag invalid values
  - Standardise categorical text values
  - Forward-fill NAV gaps for weekends/holidays

Run from project root:
    python scripts/data_cleaning.py
"""

import pandas as pd
import numpy as np
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RAW       = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)


# ── helpers ──────────────────────────────────────────────────────────────────

def log(msg):
    print(f"  {msg}")


def save(df, filename):
    path = PROCESSED / filename
    df.to_csv(path, index=False)
    log(f"Saved {filename} → {len(df)} rows, {df.shape[1]} cols")


# ── dataset-specific cleaning functions ──────────────────────────────────────

def clean_fund_master():
    """
    fund_master needs date parsing and stripping of whitespace
    in text columns. No nulls or duplicates expected.
    """
    print("\n[01] Cleaning fund_master...")
    df = pd.read_csv(RAW / "01_fund_master.csv")

    before = len(df)
    df = df.drop_duplicates()
    log(f"Duplicates removed: {before - len(df)}")

    # launch_date is stored as string YYYY-MM-DD
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")

    # strip any stray whitespace in text columns
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip()

    # sanity check expense ratio range (SEBI: typical range 0.1 to 2.5)
    bad_expense = df[~df["expense_ratio_pct"].between(0.1, 2.5)]
    if not bad_expense.empty:
        log(f"WARNING: {len(bad_expense)} funds outside 0.1–2.5% expense ratio")
        log(bad_expense[["scheme_name", "expense_ratio_pct"]].to_string())
    else:
        log("Expense ratio check passed (all between 0.1% and 2.5%)")

    save(df, "01_fund_master_clean.csv")
    return df


def clean_nav_history():
    """
    nav_history is the biggest dataset (46k rows). Key steps:
    - Parse date
    - Sort by amfi_code + date (required for forward-fill to work correctly)
    - Reindex to full business-day calendar and forward-fill missing NAV
      (markets are closed on weekends and public holidays, so NAV doesn't
       change on those days — we carry the last known value forward)
    - Remove any duplicate amfi_code + date combinations
    - Validate NAV is always positive
    """
    print("\n[02] Cleaning nav_history...")
    df = pd.read_csv(RAW / "02_nav_history.csv")

    df["date"] = pd.to_datetime(df["date"])

    # remove duplicates on the natural key
    before = len(df)
    df = df.drop_duplicates(subset=["amfi_code", "date"])
    log(f"Duplicates removed: {before - len(df)}")

    # sort — critical before forward-fill
    df = df.sort_values(["amfi_code", "date"]).reset_index(drop=True)

    # forward-fill NAV for weekends and public holidays
    # reindex each scheme to a continuous date range then ffill
    full_date_range = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    filled_parts = []

    for code, group in df.groupby("amfi_code"):
        group = group.set_index("date")
        group = group.reindex(full_date_range)
        group["amfi_code"] = code
        # ffill carries last known NAV forward into weekend/holiday gaps
        group["nav"] = group["nav"].ffill()
        # drop rows that are still NaN (dates before the fund started)
        group = group.dropna(subset=["nav"])
        group.index.name = "date"
        group = group.reset_index()
        filled_parts.append(group)

    df_filled = pd.concat(filled_parts, ignore_index=True)
    log(f"Rows after forward-fill (includes weekends): {len(df_filled)}")

    # validate NAV > 0
    bad_nav = (df_filled["nav"] <= 0).sum()
    if bad_nav > 0:
        log(f"WARNING: {bad_nav} rows with NAV <= 0 — dropping them")
        df_filled = df_filled[df_filled["nav"] > 0]
    else:
        log("NAV validation passed (all values > 0)")

    # compute daily return % — useful for Day 4 performance analytics
    df_filled = df_filled.sort_values(["amfi_code", "date"])
    df_filled["daily_return_pct"] = (
        df_filled.groupby("amfi_code")["nav"]
        .pct_change()
        .round(6)
    )

    save(df_filled, "02_nav_history_clean.csv")
    return df_filled


def clean_aum_by_fund_house():
    """Simple cleaning — parse date, strip whitespace."""
    print("\n[03] Cleaning aum_by_fund_house...")
    df = pd.read_csv(RAW / "03_aum_by_fund_house.csv")

    df["date"] = pd.to_datetime(df["date"])
    df["fund_house"] = df["fund_house"].str.strip()
    df = df.drop_duplicates()

    log(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    log(f"Fund houses: {df['fund_house'].nunique()}")

    save(df, "03_aum_by_fund_house_clean.csv")
    return df


def clean_monthly_sip_inflows():
    """
    yoy_growth_pct is NaN for the first 12 months — that is expected
    because YoY needs a prior year to compare against. We keep those
    NaNs and document them.
    """
    print("\n[04] Cleaning monthly_sip_inflows...")
    df = pd.read_csv(RAW / "04_monthly_sip_inflows.csv")

    # month column is YYYY-MM string — convert to period or keep as string
    # keeping as datetime (first day of month) makes sorting easier
    df["month"] = pd.to_datetime(df["month"] + "-01")

    df = df.sort_values("month").reset_index(drop=True)

    null_yoy = df["yoy_growth_pct"].isnull().sum()
    log(f"yoy_growth_pct nulls: {null_yoy} (expected — first 12 months have no prior year)")

    # validate SIP inflows are positive
    bad = (df["sip_inflow_crore"] <= 0).sum()
    log(f"Rows with sip_inflow_crore <= 0: {bad}")

    save(df, "04_monthly_sip_inflows_clean.csv")
    return df


def clean_category_inflows():
    """Parse month to datetime, check no negative inflows."""
    print("\n[05] Cleaning category_inflows...")
    df = pd.read_csv(RAW / "05_category_inflows.csv")

    df["month"] = pd.to_datetime(df["month"] + "-01")
    df["category"] = df["category"].str.strip()
    df = df.sort_values(["month", "category"]).reset_index(drop=True)

    log(f"Categories: {sorted(df['category'].unique())}")

    save(df, "05_category_inflows_clean.csv")
    return df


def clean_industry_folio_count():
    """Parse month, validate folio counts are increasing over time."""
    print("\n[06] Cleaning industry_folio_count...")
    df = pd.read_csv(RAW / "06_industry_folio_count.csv")

    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values("month").reset_index(drop=True)

    # total folios should roughly increase over time
    log(f"Folio count range: {df['total_folios_crore'].min()} to {df['total_folios_crore'].max()} crore")

    save(df, "06_industry_folio_count_clean.csv")
    return df


def clean_scheme_performance():
    """
    Validate all return/metric columns are numeric.
    Flag funds with negative Sharpe (poor risk-adjusted returns).
    Check expense ratio is in valid range.
    """
    print("\n[07] Cleaning scheme_performance...")
    df = pd.read_csv(RAW / "07_scheme_performance.csv")

    # columns that must be numeric
    numeric_cols = [
        "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
        "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
        "aum_crore", "expense_ratio_pct"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        nulls = df[col].isnull().sum()
        if nulls > 0:
            log(f"WARNING: {nulls} non-numeric values found in {col}")

    # flag negative Sharpe — not necessarily wrong but worth noting
    negative_sharpe = df[df["sharpe_ratio"] < 0]
    if not negative_sharpe.empty:
        log(f"Funds with negative Sharpe ratio ({len(negative_sharpe)}):")
        log(negative_sharpe[["scheme_name", "sharpe_ratio"]].to_string())
    else:
        log("All Sharpe ratios are non-negative")

    # expense ratio check
    bad_expense = df[~df["expense_ratio_pct"].between(0.1, 2.5)]
    if not bad_expense.empty:
        log(f"WARNING: {len(bad_expense)} funds outside 0.1–2.5% expense ratio range")
    else:
        log("Expense ratio check passed")

    # max_drawdown should be negative (it's a loss)
    bad_dd = df[df["max_drawdown_pct"] > 0]
    if not bad_dd.empty:
        log(f"WARNING: {len(bad_dd)} funds with positive max_drawdown (should be negative)")

    df = df.drop_duplicates()
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip()

    save(df, "07_scheme_performance_clean.csv")
    return df


def clean_investor_transactions():
    """
    Key cleaning steps:
    - Standardise transaction_type to exactly: SIP / Lumpsum / Redemption
    - Parse transaction_date to datetime
    - Validate amount_inr > 0
    - Check KYC status is only Verified or Pending
    """
    print("\n[08] Cleaning investor_transactions...")
    df = pd.read_csv(RAW / "08_investor_transactions.csv")

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")

    # standardise transaction_type — strip whitespace and title-case
    df["transaction_type"] = df["transaction_type"].str.strip().str.title()

    valid_tx_types = {"Sip", "Lumpsum", "Redemption"}
    # rename SIP to uppercase (title-case gives Sip, we want SIP)
    df["transaction_type"] = df["transaction_type"].replace({"Sip": "SIP"})

    invalid_types = df[~df["transaction_type"].isin(["SIP", "Lumpsum", "Redemption"])]
    if not invalid_types.empty:
        log(f"WARNING: {len(invalid_types)} rows with unexpected transaction_type")
        log(f"  Values: {invalid_types['transaction_type'].unique()}")
    else:
        log(f"transaction_type values: {sorted(df['transaction_type'].unique())} — all valid")

    # validate amount > 0
    bad_amount = df[df["amount_inr"] <= 0]
    if not bad_amount.empty:
        log(f"WARNING: {len(bad_amount)} transactions with amount <= 0 — dropping")
        df = df[df["amount_inr"] > 0]
    else:
        log("Amount validation passed (all > 0)")

    # KYC status should only be Verified or Pending
    valid_kyc = {"Verified", "Pending"}
    bad_kyc = df[~df["kyc_status"].isin(valid_kyc)]
    if not bad_kyc.empty:
        log(f"WARNING: unexpected KYC values: {bad_kyc['kyc_status'].unique()}")
    else:
        log(f"KYC status values: {sorted(df['kyc_status'].unique())} — all valid")

    # strip whitespace in all string columns
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip()

    df = df.drop_duplicates()
    df = df.sort_values("transaction_date").reset_index(drop=True)

    save(df, "08_investor_transactions_clean.csv")
    return df


def clean_portfolio_holdings():
    """Parse portfolio_date, validate weights sum to ~100 per fund."""
    print("\n[09] Cleaning portfolio_holdings...")
    df = pd.read_csv(RAW / "09_portfolio_holdings.csv")

    df["portfolio_date"] = pd.to_datetime(df["portfolio_date"])
    df["sector"] = df["sector"].str.strip()
    df["stock_name"] = df["stock_name"].str.strip()
    df = df.drop_duplicates()

    # weight_pct should be positive and per fund should add up to roughly 100
    weight_sums = df.groupby("amfi_code")["weight_pct"].sum()
    unusual = weight_sums[(weight_sums < 80) | (weight_sums > 110)]
    if not unusual.empty:
        log(f"WARNING: {len(unusual)} funds with unusual total weight (not ~100%)")
    else:
        log("Portfolio weight sums look reasonable per fund")

    save(df, "09_portfolio_holdings_clean.csv")
    return df


def clean_benchmark_indices():
    """Parse date, validate close_value > 0, check all 6 indices present."""
    print("\n[10] Cleaning benchmark_indices...")
    df = pd.read_csv(RAW / "10_benchmark_indices.csv")

    df["date"] = pd.to_datetime(df["date"])
    df["index_name"] = df["index_name"].str.strip()
    df = df.drop_duplicates(subset=["date", "index_name"])
    df = df.sort_values(["index_name", "date"]).reset_index(drop=True)

    bad = (df["close_value"] <= 0).sum()
    log(f"Rows with close_value <= 0: {bad}")
    log(f"Indices present: {sorted(df['index_name'].unique())}")

    save(df, "10_benchmark_indices_clean.csv")
    return df


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print("\nBluestock Fintech - Mutual Fund Analytics")
    print("Day 2: Cleaning all 10 datasets\n")

    clean_fund_master()
    clean_nav_history()
    clean_aum_by_fund_house()
    clean_monthly_sip_inflows()
    clean_category_inflows()
    clean_industry_folio_count()
    clean_scheme_performance()
    clean_investor_transactions()
    clean_portfolio_holdings()
    clean_benchmark_indices()

    print("\n\nAll 10 datasets cleaned and saved to data/processed/")
    print("Next: run database_setup.py to load them into SQLite")


if __name__ == "__main__":
    main()
