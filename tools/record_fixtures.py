"""Record real price data into tests/fixtures/prices (developer-only, LIVE).

Makes read-only GETs to Yahoo's public chart endpoint with an honest
User-Agent, one symbol at a time with a pause between, and writes:

  tests/fixtures/prices/<SYM>.csv   date,close,adjclose  (daily, START..today)
  tests/fixtures/prices/quotes.json latest quote per symbol + recording date

Tests never run this; they read the files it wrote through
FakePriceSource.  Run it by hand to refresh the fixtures:

  .venv/bin/python tools/record_fixtures.py [SYM ...]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "tests" / "fixtures" / "prices"
USER_AGENT = "investaround/0.1 (personal paper-trading app)"
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
START = dt.date(2005, 1, 1)
PAUSE_SECONDS = 1.5

DEFAULT_SYMBOLS = [
    "SPY", "VOO", "VTI", "VXUS", "BND", "QQQ", "VNQ", "GLD",
    "AAPL", "MSFT", "JNJ", "KO", "AMZN", "NVDA", "VTSAX",
]


def fetch_chart(client: httpx.Client, symbol: str, start: dt.date, end: dt.date) -> dict:
    period1 = int(dt.datetime.combine(start, dt.time(), dt.UTC).timestamp())
    period2 = int(dt.datetime.combine(end + dt.timedelta(days=1), dt.time(), dt.UTC).timestamp())
    resp = client.get(
        CHART_URL.format(symbol=symbol),
        params={"period1": period1, "period2": period2, "interval": "1d", "events": "div|split"},
    )
    resp.raise_for_status()
    body = resp.json()
    err = body.get("chart", {}).get("error")
    if err:
        raise RuntimeError(f"{symbol}: {err}")
    return body["chart"]["result"][0]


def parse_bars(result: dict) -> list[tuple[str, float, float]]:
    """(iso date, close, adjclose) per trading day, skipping null rows."""
    offset = result["meta"].get("gmtoffset", 0)
    stamps = result.get("timestamp") or []
    closes = result["indicators"]["quote"][0].get("close") or []
    adj = (result["indicators"].get("adjclose") or [{}])[0].get("adjclose") or closes
    rows: dict[str, tuple[str, float, float]] = {}
    for ts, c, a in zip(stamps, closes, adj):
        if c is None or a is None:
            continue
        day = dt.datetime.fromtimestamp(ts + offset, dt.UTC).date().isoformat()
        rows[day] = (day, round(c, 6), round(a, 6))
    return [rows[d] for d in sorted(rows)]


def quote_from_meta(meta: dict, bars: list[tuple[str, float, float]]) -> dict:
    price = meta.get("regularMarketPrice") or bars[-1][1]
    previous = bars[-2][1] if len(bars) >= 2 else meta.get("chartPreviousClose")
    as_of = meta.get("regularMarketTime")
    return {
        "symbol": meta["symbol"],
        "price": price,
        "previous_close": previous,
        "currency": meta.get("currency", "USD"),
        "name": meta.get("longName") or meta.get("shortName") or meta["symbol"],
        "instrument_type": meta.get("instrumentType", ""),
        "exchange": meta.get("fullExchangeName") or meta.get("exchangeName", ""),
        "as_of": dt.datetime.fromtimestamp(as_of, dt.UTC).isoformat() if as_of else None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbols", nargs="*", default=DEFAULT_SYMBOLS)
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    quotes_path = OUT_DIR / "quotes.json"
    existing = json.loads(quotes_path.read_text()) if quotes_path.exists() else {}
    quotes = existing.get("quotes", {})
    today = dt.date.today()
    failures = []

    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30) as client:
        for i, sym in enumerate(s.upper() for s in args.symbols):
            if i:
                time.sleep(PAUSE_SECONDS)
            try:
                result = fetch_chart(client, sym, START, today)
                bars = parse_bars(result)
                if not bars:
                    raise RuntimeError("no bars returned")
            except (httpx.HTTPError, RuntimeError, KeyError, IndexError) as exc:
                print(f"{sym}: FAILED {exc}", file=sys.stderr)
                failures.append(sym)
                continue
            with (OUT_DIR / f"{sym}.csv").open("w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["date", "close", "adjclose"])
                w.writerows(bars)
            quotes[sym] = quote_from_meta(result["meta"], bars)
            print(f"{sym}: {len(bars)} bars {bars[0][0]} .. {bars[-1][0]}")

    last_dates = [q["as_of"][:10] for q in quotes.values() if q.get("as_of")]
    payload = {
        "recorded": today.isoformat(),
        "as_of": max(last_dates) if last_dates else today.isoformat(),
        "source": "Yahoo Finance chart API (unofficial), via tools/record_fixtures.py",
        "quotes": dict(sorted(quotes.items())),
    }
    quotes_path.write_text(json.dumps(payload, indent=2) + "\n")
    if failures:
        print(f"Failed: {' '.join(failures)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
