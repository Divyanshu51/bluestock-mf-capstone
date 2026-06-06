"""
live_nav_fetch.py
-----------------
Day 1 task: Fetch historical NAV data from the mfapi.in public API
for 6 schemes (HDFC Top 100 + 5 bluechip funds), parse the JSON
response, and save each as a CSV in data/raw/.

API used: https://api.mfapi.in/mf/{scheme_code}
No authentication required - fully public.

NOTE: mfapi.in blocks requests from cloud/server IPs.
Run this on your LOCAL machine, not on a hosted server.

Run from project root:
    python scripts/live_nav_fetch.py
"""

import requests
import pandas as pd
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)


# schemes to fetch - code: (name, filename)
SCHEMES = {
    125497: ("HDFC Top 100 Direct Plan Growth",    "live_hdfc_top100.csv"),
    119551: ("SBI Bluechip Fund Regular Growth",   "live_sbi_bluechip.csv"),
    120503: ("ICICI Pru Bluechip Fund Growth",     "live_icici_bluechip.csv"),
    118632: ("Nippon India Large Cap Fund Growth", "live_nippon_largecap.csv"),
    119092: ("Axis Bluechip Fund Growth",          "live_axis_bluechip.csv"),
    120841: ("Kotak Bluechip Fund Growth",         "live_kotak_bluechip.csv"),
}

BASE_URL = "https://api.mfapi.in/mf/{code}"

# browser-like headers so mfapi.in doesn't block the request
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.mfapi.in/",
}


def fetch_nav(scheme_code, scheme_name):
    """
    Hit mfapi.in for a given scheme code, parse the JSON,
    and return a clean DataFrame with date and nav columns.
    Returns None if the request fails.
    """
    url = BASE_URL.format(code=scheme_code)
    print(f"  Fetching: {scheme_name} (code: {scheme_code})")
    print(f"  URL: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if "403" in str(e):
            print(f"  403 Forbidden - mfapi.in is blocking this IP.")
            print(f"  This is normal on cloud/server environments.")
            print(f"  Run this script on your LOCAL machine to fetch live data.")
        else:
            print(f"  HTTP error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  Request failed: {e}")
        return None

    data = response.json()

    # the API returns {"status": "SUCCESS", "meta": {...}, "data": [{"date": "...", "nav": "..."}, ...]}
    if data.get("status") != "SUCCESS":
        print(f"  API returned non-success status: {data.get('status')}")
        return None

    records = data.get("data", [])
    if not records:
        print(f"  No NAV data in response.")
        return None

    df = pd.DataFrame(records)

    # API returns date as DD-MM-YYYY string, nav as string - fix both
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")

    # add scheme info so the CSV is self-contained
    df["amfi_code"] = scheme_code
    df["scheme_name"] = scheme_name

    # sort oldest first
    df = df.sort_values("date").reset_index(drop=True)

    # reorder columns
    df = df[["amfi_code", "scheme_name", "date", "nav"]]

    print(f"  Got {len(df)} NAV records | {df['date'].min().date()} to {df['date'].max().date()}")
    return df


def fallback_from_existing(scheme_code, scheme_name, filename):
    """
    If the live API is not accessible (e.g. 403 from a server), pull the
    scheme's NAV from the already-provided nav_history dataset as a fallback.
    This still produces the same output file so the rest of the pipeline works.
    """
    nav_path = RAW / "02_nav_history.csv"
    if not nav_path.exists():
        print(f"  Fallback failed: 02_nav_history.csv not found in data/raw/")
        return None

    nav_history = pd.read_csv(nav_path)
    subset = nav_history[nav_history["amfi_code"] == scheme_code].copy()

    if subset.empty:
        print(f"  Fallback failed: amfi_code {scheme_code} not in nav_history")
        return None

    subset["date"] = pd.to_datetime(subset["date"])
    subset = subset.sort_values("date").reset_index(drop=True)
    subset["scheme_name"] = scheme_name
    subset = subset[["amfi_code", "scheme_name", "date", "nav"]]

    print(f"  Fallback used: pulled {len(subset)} rows from 02_nav_history.csv")
    return subset


def save_nav(df, filename):
    """Save the fetched NAV DataFrame to data/raw/."""
    path = RAW / filename
    df.to_csv(path, index=False)
    print(f"  Saved to: {path}")


def main():
    print("\nBluestock Fintech - Mutual Fund Analytics")
    print("Day 1: Live NAV Fetch from mfapi.in")
    print(f"Fetching {len(SCHEMES)} schemes...\n")

    success_count = 0
    fallback_count = 0
    failed = []

    for code, (name, filename) in SCHEMES.items():
        df = fetch_nav(code, name)

        if df is not None:
            save_nav(df, filename)
            success_count += 1
        else:
            # try pulling from existing nav_history as fallback
            print(f"  Trying fallback from 02_nav_history.csv...")
            df_fallback = fallback_from_existing(code, name, filename)
            if df_fallback is not None:
                save_nav(df_fallback, filename)
                fallback_count += 1
            else:
                failed.append((code, name))

        # small pause between API requests
        time.sleep(1)
        print()

    print("=" * 55)
    print(f"Live API fetches  : {success_count}/{len(SCHEMES)}")
    print(f"Fallback (nav_history): {fallback_count}/{len(SCHEMES)}")

    if failed:
        print(f"\nFailed completely ({len(failed)}):")
        for code, name in failed:
            print(f"  {code}: {name}")
    else:
        print("\nAll scheme files saved successfully.")

    print(f"\nRaw CSV files saved to: {RAW}")
    print("\nNote: To get real live NAV, run this script on your local machine.")
    print("mfapi.in blocks requests from cloud/server IPs (returns 403).")


if __name__ == "__main__":
    main()
