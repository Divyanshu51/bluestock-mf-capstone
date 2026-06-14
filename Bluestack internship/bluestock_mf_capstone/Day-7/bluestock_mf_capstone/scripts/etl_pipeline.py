"""
etl_pipeline.py
---------------
Master ETL script for the Bluestock MF Analytics pipeline.
Runs the full Extract → Transform → Load sequence in one shot.

This is the production-ready version of run_pipeline.py — it imports
and calls each module's functions directly rather than spawning subprocesses,
which is faster and gives better error messages.

Run from project root:
    python scripts/etl_pipeline.py

Optional:
    python scripts/etl_pipeline.py --skip-live   # skip mfapi.in API call
"""

import sys
import time
import argparse
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)


def step(name):
    """Context manager for timing and logging a pipeline step."""
    class _Step:
        def __enter__(self):
            log.info(f"START  {name}")
            self.t = time.time()
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed = time.time() - self.t
            if exc_type is None:
                log.info(f"DONE   {name} ({elapsed:.1f}s)")
            else:
                log.error(f"FAIL   {name} — {exc_val}")
            return False   # re-raise exceptions
    return _Step()


def run_extract(skip_live: bool):
    """
    EXTRACT — Load raw CSVs and optionally fetch live NAV from mfapi.in.
    Validates that all 10 CSVs exist in data/raw/ before proceeding.
    """
    raw = ROOT / "data" / "raw"
    required = [f"0{i}_" for i in range(1, 10)] + ["10_"]
    missing = [r for r in required if not any(f.name.startswith(r) for f in raw.glob("*.csv"))]
    if missing:
        raise FileNotFoundError(
            f"Missing raw CSV files starting with: {missing}\n"
            f"Place all 10 provided CSVs in {raw}"
        )
    log.info(f"  Raw CSVs found: {len(list(raw.glob('*.csv')))} files")

    if not skip_live:
        import live_nav_fetch
        live_nav_fetch.main()
    else:
        log.info("  Live NAV fetch skipped (--skip-live flag)")


def run_transform():
    """
    TRANSFORM — Clean all 10 datasets.
    Handles: date parsing, forward-fill, deduplication, type validation.
    Saves cleaned files to data/processed/.
    """
    import data_cleaning
    data_cleaning.main()

    processed = ROOT / "data" / "processed"
    count = len(list(processed.glob("*.csv")))
    log.info(f"  Cleaned files in data/processed/: {count}")


def run_load():
    """
    LOAD — Build SQLite star schema and load all cleaned data.
    Verifies row counts between CSVs and database after loading.
    """
    import database_setup
    database_setup.main()

    db_path = ROOT / "data" / "db" / "bluestock_mf.db"
    if db_path.exists():
        size_mb = db_path.stat().st_size / 1024 / 1024
        log.info(f"  Database: {db_path.name} ({size_mb:.1f} MB)")
    else:
        raise FileNotFoundError(f"Database not found at {db_path}")


def main():
    parser = argparse.ArgumentParser(description="Bluestock MF ETL Pipeline")
    parser.add_argument("--skip-live", action="store_true",
                        help="Skip live NAV fetch from mfapi.in (use when offline)")
    args = parser.parse_args()

    log.info("=" * 55)
    log.info("  BLUESTOCK FINTECH — ETL PIPELINE")
    log.info("=" * 55)

    t_total = time.time()

    with step("EXTRACT — Load raw CSVs + live NAV fetch"):
        run_extract(skip_live=args.skip_live)

    with step("TRANSFORM — Clean all 10 datasets"):
        run_transform()

    with step("LOAD — Build SQLite database"):
        run_load()

    elapsed = time.time() - t_total
    log.info("=" * 55)
    log.info(f"  Pipeline complete in {elapsed:.1f}s")
    log.info("  Next: open notebooks/ in Jupyter Lab")
    log.info("  Dashboard: dashboard/bluestock_mf_dashboard.html")
    log.info("=" * 55)


if __name__ == "__main__":
    main()
