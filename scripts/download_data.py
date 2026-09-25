#!/usr/bin/env python3
"""Download Divvy trip data (Jun–Aug 2026) from the City of Chicago open data."""
import os, urllib.request

BASE = "https://divvy-tripdata.s3.amazonaws.com"
MONTHS = ["202606", "202607", "202608"]
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

os.makedirs(DATA, exist_ok=True)
for m in MONTHS:
    fname = f"{m}-divvy-tripdata.zip"
    dest = os.path.join(DATA, fname)
    if os.path.exists(dest):
        print(f"exists: {fname}")
        continue
    print(f"downloading {fname} ...")
    urllib.request.urlretrieve(f"{BASE}/{fname}", dest)
    d = os.path.join(DATA, f"{m}-divvy-tripdata")
    os.makedirs(d, exist_ok=True)
    import zipfile
    with zipfile.ZipFile(dest) as z:
        z.extractall(d)
    print(f"done: {fname}")
