"""Fetch NSRDB hourly weather data for the four state case studies.

Reads NSRDB_API_KEY and NSRDB_EMAIL from environment (or .env if python-dotenv
is installed). Caches downloads under weather_cache/ so re-runs are free.

Usage:
    python shared/fetch_nsrdb.py --state {CA|MA|NC|TX}
    python shared/fetch_nsrdb.py --state ALL
    python shared/fetch_nsrdb.py --lat 35.78 --lon -78.64 --label NC_raleigh

Register a free NSRDB API key at https://developer.nrel.gov/signup/
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass  # python-dotenv optional; env vars must be set externally

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "weather_cache"

# State -> list of (label, lat, lon) sites used by the case studies.
# Coordinates match the per-state Workflow_Replicable.md docs.
SITES = {
    "CA": [
        ("CA_sacramento", 38.58, -121.49),
        ("CA_riverside", 33.95, -117.40),
        ("CA_san_diego", 32.72, -117.16),
    ],
    "MA": [
        ("MA_boston", 42.37, -71.06),
    ],
    "NC": [
        ("NC_raleigh", 35.78, -78.64),
    ],
    "TX": [
        ("TX_houston", 29.76, -95.37),
    ],
}

ENDPOINT = "https://developer.nrel.gov/api/nsrdb/v2/solar/nsrdb-GOES-aggregated-v4-0-0-download.csv"
ATTRIBUTES = "ghi,dni,dhi,air_temperature,wind_speed,surface_albedo"
YEAR = "2023"
INTERVAL = "60"


def fetch_one(api_key: str, email: str, label: str, lat: float, lon: float) -> Path:
    out_path = CACHE_DIR / f"{label}_{YEAR}_hourly.csv"
    if out_path.exists() and out_path.stat().st_size > 1000:
        print(f"[cached] {out_path.relative_to(REPO_ROOT)}")
        return out_path

    out_path.parent.mkdir(parents=True, exist_ok=True)
    url = (
        f"{ENDPOINT}"
        f"?api_key={api_key}"
        f"&wkt=POINT({lon}+{lat})"
        f"&attributes={ATTRIBUTES}"
        f"&names={YEAR}"
        f"&utc=false"
        f"&leap_day=false"
        f"&interval={INTERVAL}"
        f"&email={email}"
    )
    print(f"[fetch] {label} ({lat}, {lon})")
    resp = requests.get(url, timeout=180)
    if resp.status_code == 429:
        sys.exit("NSRDB rate-limited (429). Free tier is 1,000 requests/day. Retry tomorrow or use a different key.")
    resp.raise_for_status()
    if not resp.text or len(resp.text) < 1000:
        sys.exit(f"Empty / short response from NSRDB for {label}: status={resp.status_code}, body={resp.text[:200]}")
    out_path.write_text(resp.text)
    print(f"[done]  {out_path.relative_to(REPO_ROOT)} ({out_path.stat().st_size // 1024} KB)")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", choices=[*SITES.keys(), "ALL"], help="State code or ALL")
    parser.add_argument("--lat", type=float, help="Custom latitude (with --lon and --label)")
    parser.add_argument("--lon", type=float, help="Custom longitude")
    parser.add_argument("--label", help="Custom site label for output filename")
    args = parser.parse_args()

    api_key = os.environ.get("NSRDB_API_KEY")
    email = os.environ.get("NSRDB_EMAIL")
    if not api_key or api_key == "your_free_key_here":
        sys.exit("Set NSRDB_API_KEY in .env (register free at https://developer.nrel.gov/signup/)")
    if not email:
        sys.exit("Set NSRDB_EMAIL in .env (the email tied to your registered NSRDB key)")

    if args.lat is not None and args.lon is not None and args.label:
        fetch_one(api_key, email, args.label, args.lat, args.lon)
        return 0

    if args.state == "ALL":
        states = list(SITES)
    elif args.state in SITES:
        states = [args.state]
    else:
        parser.error("Provide --state {CA|MA|NC|TX|ALL} or --lat/--lon/--label")
        return 2

    for st in states:
        for label, lat, lon in SITES[st]:
            fetch_one(api_key, email, label, lat, lon)
    return 0


if __name__ == "__main__":
    sys.exit(main())
