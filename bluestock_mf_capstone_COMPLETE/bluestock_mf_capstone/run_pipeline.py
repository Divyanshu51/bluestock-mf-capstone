"""
run_pipeline.py
---------------
Master execution script for the Bluestock MF Analytics pipeline.
Runs all Day 1-2 steps in sequence — ingestion, live fetch, cleaning,
and database loading.

Run from project root:
    python run_pipeline.py

Optional flags:
    python run_pipeline.py --skip-live   # skip mfapi.in fetch (offline mode)
"""

import sys
import time
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

STEPS = [
    ("Data Ingestion",     "scripts/data_ingestion.py"),
    ("Live NAV Fetch",     "scripts/live_nav_fetch.py"),
    ("Data Cleaning",      "scripts/data_cleaning.py"),
    ("Database Setup",     "scripts/database_setup.py"),
]

def run_step(name, script, skip=False):
    """Run a single pipeline step and report outcome."""
    path = ROOT / script
    if not path.exists():
        print(f"  [SKIP] {name} — script not found: {script}")
        return True

    if skip:
        print(f"  [SKIP] {name} — skipped by flag")
        return True

    print(f"  [RUN]  {name}...")
    start = time.time()
    result = subprocess.run([sys.executable, str(path)], capture_output=False)
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"  [OK]   {name} completed in {elapsed:.1f}s")
        return True
    else:
        print(f"  [FAIL] {name} failed (exit code {result.returncode})")
        return False


def main():
    skip_live = "--skip-live" in sys.argv

    print()
    print("=" * 60)
    print("  BLUESTOCK FINTECH — MUTUAL FUND ANALYTICS PIPELINE")
    print("=" * 60)
    print(f"  Project root: {ROOT}")
    print(f"  Python      : {sys.executable}")
    print()

    results = []
    for name, script in STEPS:
        skip = skip_live and "live_nav" in script
        ok = run_step(name, script, skip=skip)
        results.append((name, ok))
        print()

    print("=" * 60)
    print("  PIPELINE SUMMARY")
    print("=" * 60)
    for name, ok in results:
        status = "OK  " if ok else "FAIL"
        print(f"  [{status}] {name}")

    all_ok = all(ok for _, ok in results)
    print()
    if all_ok:
        print("  Pipeline completed successfully.")
        print("  Next steps:")
        print("    1. Open notebooks/ in Jupyter Lab for EDA and analytics")
        print("    2. Open dashboard/bluestock_mf_dashboard.html in Chrome")
        print("    3. Import data/processed/ CSVs into Power BI")
    else:
        print("  Some steps failed. Check output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
