"""
bonus_b1_scheduler.py
---------------------
BONUS B1: Schedule the ETL pipeline to auto-fetch NAV from mfapi.in
every weekday at 8 PM IST and append to the existing database.

Two ways to use this:
    1. Run directly (loops forever, checks time every minute):
           python scripts/bonus_b1_scheduler.py

    2. Set up as a cron job (recommended):
           # Open crontab:  crontab -e
           # Add this line (runs at 8 PM Mon-Fri):
           0 20 * * 1-5 /usr/bin/python3 /path/to/scripts/bonus_b1_scheduler.py --once

           # Or with venv:
           0 20 * * 1-5 /path/to/venv/bin/python /path/to/scripts/bonus_b1_scheduler.py --once

Usage:
    python scripts/bonus_b1_scheduler.py          # runs forever
    python scripts/bonus_b1_scheduler.py --once   # fetch once and exit
    python scripts/bonus_b1_scheduler.py --test   # dry run, no actual fetch
"""

import sys
import time
import logging
import argparse
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
RAW  = ROOT / "data" / "raw"
DB   = ROOT / "data" / "db" / "bluestock_mf.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    handlers=[
        logging.FileHandler(ROOT / "reports" / "scheduler.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Accept": "application/json",
}

TARGET_HOUR_IST = 20   # 8 PM IST
IST_OFFSET      = 5.5  # hours ahead of UTC


def is_weekday():
    """Return True if today is Monday through Friday."""
    return datetime.now().weekday() < 5


def fetch_live_nav_all():
    """
    Fetch latest NAV for all schemes in fund_master using mfapi.in.
    Returns a DataFrame with amfi_code, date, nav columns.
    """
    fund_master = pd.read_csv(ROOT / "data" / "raw" / "01_fund_master.csv")
    codes = fund_master["amfi_code"].tolist()

    all_records = []
    today = datetime.now().strftime("%Y-%m-%d")

    for code in codes:
        url = f"https://api.mfapi.in/mf/{code}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "SUCCESS" or not data.get("data"):
                continue

            # take only the most recent NAV record
            latest = data["data"][0]
            nav_date = pd.to_datetime(latest["date"], format="%d-%m-%Y").strftime("%Y-%m-%d")
            nav_val  = float(latest["nav"])

            all_records.append({
                "amfi_code": code,
                "date": nav_date,
                "nav": nav_val,
            })
            time.sleep(0.3)   # polite delay between API calls

        except Exception as e:
            log.warning(f"Failed to fetch code {code}: {e}")
            continue

    if not all_records:
        return pd.DataFrame()

    return pd.DataFrame(all_records)


def append_to_database(df):
    """Append new NAV records to the SQLite database, skipping duplicates."""
    if df.empty:
        log.warning("No records to append.")
        return 0

    engine = create_engine(f"sqlite:///{DB}")

    # filter to only new records not already in fact_nav
    with engine.connect() as conn:
        existing = pd.read_sql(
            "SELECT amfi_code, date FROM fact_nav WHERE date = :d",
            conn, params={"d": df["date"].iloc[0]}
        )

    new_records = df[~df.set_index(["amfi_code","date"]).index.isin(
        existing.set_index(["amfi_code","date"]).index
    )]

    if new_records.empty:
        log.info("No new records to insert — already up to date.")
        return 0

    new_records.to_sql("fact_nav", engine, if_exists="append", index=False)
    log.info(f"Inserted {len(new_records)} new NAV records into fact_nav.")
    return len(new_records)


def save_raw_csv(df):
    """Save fetched NAV to a dated CSV in data/raw/ as a backup."""
    if df.empty:
        return
    date_str = datetime.now().strftime("%Y%m%d")
    path = RAW / f"live_nav_daily_{date_str}.csv"
    df.to_csv(path, index=False)
    log.info(f"Raw NAV saved to {path}")


def run_once(dry_run=False):
    """Fetch today's NAV and update the database."""
    log.info("=" * 50)
    log.info("Daily NAV fetch started")

    if not is_weekday():
        log.info("Today is a weekend — skipping fetch.")
        return

    if dry_run:
        log.info("DRY RUN — no actual API calls or DB writes.")
        return

    df = fetch_live_nav_all()
    log.info(f"Fetched {len(df)} NAV records from mfapi.in")

    save_raw_csv(df)

    if DB.exists():
        inserted = append_to_database(df)
        log.info(f"Database updated: {inserted} new records inserted")
    else:
        log.warning(f"Database not found at {DB} — run etl_pipeline.py first.")

    log.info("Daily NAV fetch complete")
    log.info("=" * 50)


def scheduler_loop():
    """Loop forever, running the fetch once per weekday at 8 PM IST."""
    log.info("Scheduler started — waiting for 8 PM IST on weekdays...")
    log.info("Press Ctrl+C to stop.")

    while True:
        now_utc = datetime.utcnow()
        now_ist_hour   = (now_utc.hour + int(IST_OFFSET)) % 24
        now_ist_minute = now_utc.minute

        if now_ist_hour == TARGET_HOUR_IST and now_ist_minute == 0 and is_weekday():
            run_once()
            time.sleep(61)   # wait a minute to avoid double-firing
        else:
            time.sleep(30)   # check every 30 seconds


def main():
    parser = argparse.ArgumentParser(description="Bluestock NAV Scheduler")
    parser.add_argument("--once", action="store_true", help="Fetch once and exit")
    parser.add_argument("--test", action="store_true", help="Dry run — no API calls")
    args = parser.parse_args()

    if args.once or args.test:
        run_once(dry_run=args.test)
    else:
        scheduler_loop()


if __name__ == "__main__":
    main()
