"""Record raw Yahoo responses into tests/fixtures/yahoo (developer-only, LIVE).

The unit tests for YahooPriceSource replay these through a fake HTTP
transport, so they check the parser against the real response shapes.
Each file is {"request": {...}, "status": int, "headers": {...}, "body": ...}.
A few error cases Yahoo won't produce on demand (429) are written by hand
and are not touched here.

  .venv/bin/python tools/record_yahoo_fixtures.py
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "tests" / "fixtures" / "yahoo"
USER_AGENT = "investaround/0.1 (personal paper-trading app)"
BASE = "https://query1.finance.yahoo.com"


def _epoch(day: str) -> int:
    return int(dt.datetime.combine(dt.date.fromisoformat(day), dt.time(), dt.UTC).timestamp())


def _chart_range(sym: str, start: str, end: str) -> tuple[str, dict]:
    return f"/v8/finance/chart/{sym}", {
        "period1": _epoch(start), "period2": _epoch(end), "interval": "1d", "events": "div|split",
    }


CAPTURES = {
    "quote_SPY": ("/v8/finance/chart/SPY", {"range": "5d", "interval": "1d"}),
    "quote_VTSAX": ("/v8/finance/chart/VTSAX", {"range": "5d", "interval": "1d"}),
    "quote_unknown": ("/v8/finance/chart/NOSUCHSYMBOLX", {"range": "5d", "interval": "1d"}),
    # Covid crash with Good Friday (2020-04-10) closed
    "history_SPY_2020": _chart_range("SPY", "2020-03-02", "2020-04-15"),
    # AAPL 4:1 split on 2020-08-31 and a dividend on 2020-08-07
    "history_AAPL_split": _chart_range("AAPL", "2020-08-03", "2020-09-05"),
    # VOO did not trade yet in 2008
    "history_VOO_prelisting": _chart_range("VOO", "2008-01-01", "2008-12-31"),
    "search_vanguard_total": ("/v1/finance/search", {"q": "vanguard total", "quotesCount": 10, "newsCount": 0}),
    "search_nothing": ("/v1/finance/search", {"q": "zzqqxxnotathing", "quotesCount": 10, "newsCount": 0}),
}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with httpx.Client(base_url=BASE, headers={"User-Agent": USER_AGENT}, timeout=30) as client:
        for i, (name, (path, params)) in enumerate(CAPTURES.items()):
            if i:
                time.sleep(1.5)
            resp = client.get(path, params=params)
            try:
                body = resp.json()
            except ValueError:
                body = resp.text
            record = {
                "request": {"path": path, "params": params},
                "status": resp.status_code,
                "headers": {"content-type": resp.headers.get("content-type", "")},
                "body": body,
            }
            (OUT_DIR / f"{name}.json").write_text(json.dumps(record, indent=1) + "\n")
            print(f"{name}: HTTP {resp.status_code}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
