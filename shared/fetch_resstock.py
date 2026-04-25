"""Fetch NREL ResStock End-Use Load Profiles for the four state case studies.

Source: NREL ResStock 2022 release, AMY2018, residential building stock.
   https://data.openei.org/s3_viewer?bucket=oedi-data-lake&prefix=nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2022/resstock_amy2018_release_1/

State-level: 5 building-type CSVs per state (single-family detached, attached, MF 2-4, MF 5+, mobile home).
County-level (CA only): per-county GEOID files for PG&E / SCE / SDG&E proxy counties.

Files are public, no API key required. Cached under each state's load profile data folder.

Usage:
    python shared/fetch_resstock.py --state {CA|MA|NC|TX}
    python shared/fetch_resstock.py --state ALL
"""

import argparse
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
OEDI_BASE = "https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2022/resstock_amy2018_release_1/timeseries_aggregates"

BUILDING_TYPES = [
    "single-family_detached",
    "single-family_attached",
    "multi-family_with_2_-_4_units",
    "multi-family_with_5plus_units",
    "mobile_home",
]

# State-level downloads (per ResStock URL convention)
STATE_LEVEL = {
    "MA": {"label": "ma", "geoid": "ma"},
    "NC": {"label": "nc", "geoid": "nc"},
    "TX": {"label": "tx", "geoid": "tx"},
}

# CA uses three county proxies in the case study.
# FIPS codes: Sacramento=06067 (G0600670), Riverside=06065 (G0600650), San Diego=06073 (G0600730).
CA_COUNTIES = [
    ("g0600670", "PGE Sacramento County"),
    ("g0600650", "SCE Riverside County"),
    ("g0600730", "SDGE San Diego County"),
]


def state_target_dir(state: str) -> Path:
    if state == "CA":
        return REPO_ROOT / "case_studies" / "CA" / "CA county proxy load profiles"
    return REPO_ROOT / "case_studies" / state / f"{state} load profile" / "data"


def fetch_one(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 100_000:
        print(f"[cached] {dest.relative_to(REPO_ROOT)}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"[fetch]  {url.rsplit('/', 1)[-1]}")
    resp = requests.get(url, stream=True, timeout=300)
    if resp.status_code == 404:
        print(f"  [skip] 404 not found: {url}")
        return
    resp.raise_for_status()
    with dest.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=64 * 1024):
            f.write(chunk)
    print(f"[done]   {dest.relative_to(REPO_ROOT)} ({dest.stat().st_size // (1024 * 1024)} MB)")


def fetch_state_level(state: str) -> None:
    info = STATE_LEVEL[state]
    target = state_target_dir(state)
    geoid = info["geoid"]
    for bt in BUILDING_TYPES:
        url = f"{OEDI_BASE}/by_state/state={geoid}/upgrade=0/up00-{geoid}-{bt}.csv"
        dest = target / f"up00-{geoid}-{bt}.csv"
        fetch_one(url, dest)


def fetch_ca_counties() -> None:
    base = state_target_dir("CA")
    for geoid, county_label in CA_COUNTIES:
        target = base / county_label / "data"
        target.mkdir(parents=True, exist_ok=True)
        for bt in BUILDING_TYPES:
            url = f"{OEDI_BASE}/by_county/state=ca/upgrade=0/{geoid}-{bt}.csv"
            dest = target / f"{geoid}-{bt}.csv"
            fetch_one(url, dest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", choices=["CA", "MA", "NC", "TX", "ALL"], required=True)
    args = parser.parse_args()

    states = ["CA", "MA", "NC", "TX"] if args.state == "ALL" else [args.state]

    for st in states:
        if st == "CA":
            fetch_ca_counties()
        else:
            fetch_state_level(st)

    print("\nNext step: run the per-state load-profile analysis script to derive representative profiles:")
    for st in states:
        if st == "CA":
            print(f"  (CA: representative profiles already committed under CA county proxy load profiles/*/outputs/)")
        else:
            script = REPO_ROOT / "case_studies" / st / f"{st} load profile" / f"analyze_{st.lower()}_representative_profile.py"
            if script.exists():
                print(f"  python \"{script.relative_to(REPO_ROOT)}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
