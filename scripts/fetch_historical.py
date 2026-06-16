"""Fetch historical international match results into data/raw/.

Primary source: martj42/international_results — every men's international since
1872 (date, home, away, scores, tournament, neutral flag). Public, widely cited.

Writes the CSV plus a provenance sidecar (source, url, retrieved_at, license)
so we can populate the Data Availability statement later.

Usage:  uv run python scripts/fetch_historical.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

SOURCES = {
    "international_results.csv": {
        "url": "https://raw.githubusercontent.com/martj42/international_results/master/results.csv",
        "license": "Public dataset (martj42/international_results); cite repository.",
        "desc": "All men's international football results, 1872-present.",
    },
    # shootouts.csv and goalscorers.csv exist in the same repo if we want them later.
}


def fetch(name: str, meta: dict) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    dest = RAW / name
    print(f"[fetch] {meta['url']}")
    resp = requests.get(meta["url"], timeout=60)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    prov = {
        "source": meta["url"],
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "license": meta["license"],
        "description": meta["desc"],
        "bytes": len(resp.content),
    }
    (RAW / f"{name}.provenance.json").write_text(json.dumps(prov, indent=2))
    print(f"[ok]    {dest}  ({len(resp.content):,} bytes)")
    return dest


def main() -> int:
    for name, meta in SOURCES.items():
        try:
            fetch(name, meta)
        except Exception as exc:  # noqa: BLE001
            print(f"[err]   {name}: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
