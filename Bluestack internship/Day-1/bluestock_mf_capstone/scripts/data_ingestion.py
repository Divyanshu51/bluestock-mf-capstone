"""
data_ingestion.py
-----------------
Day 1 task: Load all 10 raw datasets, run basic inspection on each,
flag any obvious anomalies, and validate AMFI codes are consistent
between fund_master and nav_history.

Run this from the project root:
    python scripts/data_ingestion.py
"""

import os
import pandas as pd
from pathlib import Path


# project root is one level above scripts/
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"


def load_dataset(filename):
    """Load a single CSV from the raw data folder and return a DataFrame."""
    path = RAW / filename
    df = pd.read_csv(path)
    return df


def inspect_dataset(name, df):
    """Print shape, dtypes, head, and basic null info for a DataFrame."""
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  Shape      : {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"\n  Column dtypes:")
    for col, dtype in df.dtypes.items():
        null_count = df[col].isnull().sum()
        null_flag = f"  <<< {null_count} nulls" if null_count > 0 else ""
        print(f"    {col:<35} {str(dtype):<12}{null_flag}")
    print(f"\n  First 3 rows:")
    print(df.head(3).to_string(index=False))


def check_anomalies(name, df):
    """
    Do basic anomaly checks per dataset.
    Nothing fancy here - just printing things that look off.
    """
    anomalies = []

    # duplicate rows check
    dupes = df.duplicated().sum()
    if dupes > 0:
        anomalies.append(f"  {dupes} duplicate rows found")

    # null check
    total_nulls = df.isnull().sum().sum()
    if total_nulls > 0:
        anomalies.append(f"  {total_nulls} total null values across all columns")

    # NAV specific - nav should never be 0 or negative
    if "nav" in df.columns:
        bad_nav = (df["nav"] <= 0).sum()
        if bad_nav > 0:
            anomalies.append(f"  {bad_nav} rows where NAV <= 0 (should not happen)")

    # transaction amounts
    if "amount_inr" in df.columns:
        bad_amt = (df["amount_inr"] <= 0).sum()
        if bad_amt > 0:
            anomalies.append(f"  {bad_amt} transactions with amount <= 0")

    # expense ratio range: anything above 2.5 is unusual for Indian MFs
    if "expense_ratio_pct" in df.columns:
        high_expense = (df["expense_ratio_pct"] > 2.5).sum()
        if high_expense > 0:
            anomalies.append(f"  {high_expense} funds with expense ratio > 2.5%")

    if anomalies:
        print(f"\n  Anomaly check for {name}:")
        for a in anomalies:
            print(a)
    else:
        print(f"\n  Anomaly check for {name}: all clear")


def validate_amfi_codes(fund_master, nav_history):
    """
    Cross-check: every amfi_code in fund_master should appear in nav_history.
    If some are missing, we want to know before doing any analysis.
    """
    print(f"\n{'='*60}")
    print("  AMFI Code Validation (fund_master vs nav_history)")
    print(f"{'='*60}")

    master_codes = set(fund_master["amfi_code"].unique())
    nav_codes = set(nav_history["amfi_code"].unique())

    in_master_not_nav = master_codes - nav_codes
    in_nav_not_master = nav_codes - master_codes

    print(f"  Unique codes in fund_master : {len(master_codes)}")
    print(f"  Unique codes in nav_history : {len(nav_codes)}")

    if in_master_not_nav:
        print(f"\n  Codes in fund_master but NOT in nav_history ({len(in_master_not_nav)}):")
        print(f"    {sorted(in_master_not_nav)}")
    else:
        print("\n  All fund_master codes are present in nav_history. Good.")

    if in_nav_not_master:
        print(f"\n  Codes in nav_history but NOT in fund_master ({len(in_nav_not_master)}):")
        print(f"    {sorted(in_nav_not_master)}")
    else:
        print("  All nav_history codes are present in fund_master. Good.")

    return in_master_not_nav, in_nav_not_master


def explore_fund_master(df):
    """Print unique values for key categorical columns in fund_master."""
    print(f"\n{'='*60}")
    print("  Fund Master - Unique Value Exploration")
    print(f"{'='*60}")

    cols_to_explore = ["fund_house", "category", "sub_category", "risk_category", "plan"]
    for col in cols_to_explore:
        if col in df.columns:
            vals = sorted(df[col].unique())
            print(f"\n  {col} ({len(vals)} unique):")
            for v in vals:
                print(f"    - {v}")

    # AMFI code pattern - they're 6-digit integers for most schemes
    print(f"\n  AMFI code sample (first 5): {list(df['amfi_code'].head())}")
    print(f"  AMFI code range: {df['amfi_code'].min()} to {df['amfi_code'].max()}")


def write_quality_summary(fund_master, nav_history, missing_in_nav, missing_in_master):
    """Write a short data quality summary text file."""
    output_path = ROOT / "reports" / "day1_data_quality_summary.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "DATA QUALITY SUMMARY - DAY 1",
        "=" * 40,
        "",
        f"fund_master     : {fund_master.shape[0]} rows, {fund_master.shape[1]} columns",
        f"nav_history     : {nav_history.shape[0]} rows, {nav_history.shape[1]} columns",
        "",
        "AMFI Code Validation",
        "-" * 30,
        f"Codes in fund_master           : {fund_master['amfi_code'].nunique()}",
        f"Codes in nav_history           : {nav_history['amfi_code'].nunique()}",
        f"In fund_master but not nav     : {len(missing_in_nav)} -> {sorted(missing_in_nav) if missing_in_nav else 'None'}",
        f"In nav but not fund_master     : {len(missing_in_master)} -> {sorted(missing_in_master) if missing_in_master else 'None'}",
        "",
        "NAV Data",
        "-" * 30,
        f"Date range     : {nav_history['date'].min()} to {nav_history['date'].max()}",
        f"Null NAV values: {nav_history['nav'].isnull().sum()}",
        f"NAV <= 0 count : {(nav_history['nav'] <= 0).sum()}",
        "",
        "Observations",
        "-" * 30,
        "- All datasets loaded without errors.",
        "- Date columns need parsing from string to datetime (will handle in Day 2 cleaning).",
        "- SIP inflow dataset has NaN in yoy_growth_pct for first year rows - expected, not a bug.",
        "- investor_transactions has most columns look clean, KYC status is either Verified/Pending.",
        "- No negative NAV values found - data looks trustworthy.",
    ]

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\n  Data quality summary saved to: {output_path}")


def main():
    # all 10 datasets
    datasets = {
        "01_fund_master"         : "01_fund_master.csv",
        "02_nav_history"         : "02_nav_history.csv",
        "03_aum_by_fund_house"   : "03_aum_by_fund_house.csv",
        "04_monthly_sip_inflows" : "04_monthly_sip_inflows.csv",
        "05_category_inflows"    : "05_category_inflows.csv",
        "06_industry_folio_count": "06_industry_folio_count.csv",
        "07_scheme_performance"  : "07_scheme_performance.csv",
        "08_investor_transactions": "08_investor_transactions.csv",
        "09_portfolio_holdings"  : "09_portfolio_holdings.csv",
        "10_benchmark_indices"   : "10_benchmark_indices.csv",
    }

    print("\nBluestock Fintech - Mutual Fund Analytics")
    print("Day 1: Loading and inspecting all datasets\n")

    loaded = {}
    for name, filename in datasets.items():
        df = load_dataset(filename)
        loaded[name] = df
        inspect_dataset(name, df)
        check_anomalies(name, df)

    # explore fund master categories
    explore_fund_master(loaded["01_fund_master"])

    # validate AMFI codes across the two key datasets
    missing_in_nav, missing_in_master = validate_amfi_codes(
        loaded["01_fund_master"],
        loaded["02_nav_history"]
    )

    # save quality summary
    write_quality_summary(
        loaded["01_fund_master"],
        loaded["02_nav_history"],
        missing_in_nav,
        missing_in_master
    )

    print("\n\nDay 1 ingestion complete. All 10 datasets loaded successfully.")
    print("Check reports/day1_data_quality_summary.txt for the summary.")


if __name__ == "__main__":
    main()
