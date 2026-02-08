"""
Build stock_aliases.json from a local NASDAQ screener CSV, or from NASDAQ/NYSE URLs.
Run from project root: python scripts/update_stock_list.py
- If nasdaq_screener_*.csv exists in project root, use it (Symbol, Name columns).
- Optional: stock_aliases_override.json for extra aliases (e.g. "amazo" -> "AMZN").
"""
from __future__ import annotations

import csv
import json
import re
import urllib.request
from pathlib import Path

# URLs (official NASDAQ; updated daily) – used when no local CSV
NASDAQ_LISTED = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
OTHER_LISTED = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"

# Project root = parent of scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_JSON = PROJECT_ROOT / "stock_aliases.json"
OVERRIDE_JSON = PROJECT_ROOT / "stock_aliases_override.json"
# Local NASDAQ screener CSV (Symbol, Name, ...) – preferred when present
NASDAQ_SCREENER_GLOB = "nasdaq_screener_*.csv"


def normalize_name(s: str) -> str:
    """Lowercase, keep letters and spaces, collapse spaces."""
    if not s:
        return ""
    s = re.sub(r"[^a-z0-9\s]", "", s.lower().strip())
    return re.sub(r"\s+", " ", s).strip()


def add_aliases(alias_to_ticker: dict, symbol: str, security_name: str) -> None:
    """Add ticker and normalized company name(s) to alias map."""
    sym = (symbol or "").strip().upper()
    if not sym or len(sym) > 10:
        return
    # Ticker (lower) -> ticker
    alias_to_ticker[sym.lower()] = sym
    if not security_name:
        return
    norm = normalize_name(security_name)
    if norm:
        alias_to_ticker[norm] = sym
    # First word as alias (e.g. "Apple" from "Apple Inc.")
    first = norm.split()[0] if norm else ""
    if first and len(first) >= 2:
        alias_to_ticker[first] = sym


def fetch_tsv(url: str):
    """Download pipe-delimited file and return rows as list of columns."""
    with urllib.request.urlopen(url, timeout=30) as resp:
        text = resp.read().decode("utf-8", errors="ignore")
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        rows.append(parts)
    return rows


def parse_nasdaq_listed(rows):
    """nasdaqlisted.txt: Symbol=0, Security Name=1. Skip header and trailer."""
    out = {}
    for parts in rows:
        if len(parts) < 2:
            continue
        symbol, name = parts[0], parts[1]
        if symbol.upper() == "SYMBOL" or symbol.startswith("File Creation"):
            continue
        add_aliases(out, symbol, name)
    return out


def parse_other_listed(rows):
    """otherlisted.txt: ACT Symbol=0, Security Name=1. Skip header/trailer."""
    out = {}
    for parts in rows:
        if len(parts) < 2:
            continue
        symbol, name = parts[0], parts[1]
        if symbol.upper() == "ACT SYMBOL" or symbol.startswith("File Creation"):
            continue
        add_aliases(out, symbol, name)
    return out


def load_from_nasdaq_screener_csv(csv_path: Path) -> dict:
    """Load Symbol, Name from NASDAQ screener CSV (header: Symbol,Name,...)."""
    out = {}
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return out
        # Find Symbol and Name column indices (case-insensitive)
        col_map = {h.strip().lower(): i for i, h in enumerate(header)}
        sym_idx = col_map.get("symbol", 0)
        name_idx = col_map.get("name", 1)
        for row in reader:
            if len(row) <= max(sym_idx, name_idx):
                continue
            symbol = (row[sym_idx] or "").strip()
            name = (row[name_idx] or "").strip()
            if symbol.upper() == "SYMBOL":
                continue
            add_aliases(out, symbol, name)
    return out


def main() -> None:
    alias_to_ticker = {}

    # Prefer local NASDAQ screener CSV if present
    csv_files = sorted(PROJECT_ROOT.glob(NASDAQ_SCREENER_GLOB), key=lambda p: p.stat().st_mtime, reverse=True)
    if csv_files:
        csv_path = csv_files[0]
        print(f"Loading from {csv_path.name} ...")
        try:
            n = load_from_nasdaq_screener_csv(csv_path)
            alias_to_ticker.update(n)
            print(f"  -> {len(n)} symbols from CSV")
        except Exception as e:
            print(f"  -> Failed: {e}")
    else:
        print("No nasdaq_screener_*.csv found; trying NASDAQ/NYSE URLs ...")

    if not alias_to_ticker:
        print("Fetching nasdaqlisted.txt ...")
        try:
            nasdaq_rows = fetch_tsv(NASDAQ_LISTED)
            n = parse_nasdaq_listed(nasdaq_rows)
            alias_to_ticker.update(n)
            print(f"  -> {len(n)} symbols from NASDAQ")
        except Exception as e:
            print(f"  -> Failed: {e}")

        print("Fetching otherlisted.txt ...")
        try:
            other_rows = fetch_tsv(OTHER_LISTED)
            o = parse_other_listed(other_rows)
            alias_to_ticker.update(o)
            print(f"  -> {len(o)} symbols from NYSE/other")
        except Exception as e:
            print(f"  -> Failed: {e}")

    # Optional override (e.g. "amazo" -> "AMZN", "appl" -> "AAPL")
    if OVERRIDE_JSON.exists():
        print(f"Loading override from {OVERRIDE_JSON.name} ...")
        try:
            with open(OVERRIDE_JSON, "r", encoding="utf-8") as f:
                override = json.load(f)
            if isinstance(override, dict):
                for k, v in override.items():
                    if isinstance(v, str):
                        alias_to_ticker[k.strip().lower()] = v.strip().upper()
                    elif isinstance(v, list):
                        ticker = v[0] if v else ""
                        if isinstance(ticker, str):
                            alias_to_ticker[k.strip().lower()] = ticker.strip().upper()
            print(f"  -> applied {len(override)} overrides")
        except Exception as e:
            print(f"  -> Override failed: {e}")

    # If no data from URLs, use fallback so file always exists
    if not alias_to_ticker:
        alias_to_ticker = {
            "apple": "AAPL", "amazon": "AMZN", "nvidia": "NVDA", "tesla": "TSLA",
            "google": "GOOGL", "microsoft": "MSFT", "meta": "META", "palantir": "PLTR",
            "netflix": "NFLX", "amd": "AMD", "intel": "INTC", "sofi": "SOFI", "oklo": "OKLO",
        }
        print("Using fallback list (NASDAQ/NYSE fetch failed or no data).")

    # Dedupe: keep first seen (override wins if loaded after)
    seen = {}
    for k, v in alias_to_ticker.items():
        knorm = k.lower().strip()
        if knorm not in seen:
            seen[knorm] = v
    alias_to_ticker = seen

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(alias_to_ticker, f, indent=0, sort_keys=True)
    print(f"Wrote {len(alias_to_ticker)} aliases to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
