"""Generate the sample prices in tests/fixtures/prices (no network).

The fake price source, the tests and the screenshots all read these
files.  They are made up: each symbol is a seeded random walk around a
shared market path with the 2008, 2020 and 2022 crashes, its own trend
and quarterly dividends.  They behave like a real market but are no real
security's prices, so the repository ships nobody's market data.  The
same seed always writes the same files.

  tests/fixtures/prices/<SYM>.csv   date,close,adjclose  (daily trading days)
  tests/fixtures/prices/quotes.json latest quote per symbol

  .venv/bin/python tools/generate_fixtures.py
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import math
import random
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "tests" / "fixtures" / "prices"
START = dt.date(2005, 1, 3)
TODAY = dt.date(2026, 10, 27)
SEED = 20261027

# The shared market path: (date, level) anchors that the random walk
# passes through, with the daily volatility used on the way to each one
MARKET = [
    (dt.date(2005, 1, 3), 100.0, 0.009),
    (dt.date(2007, 10, 9), 135.0, 0.008),
    (dt.date(2009, 3, 9), 62.0, 0.025),     # 2008 crash
    (dt.date(2011, 4, 29), 115.0, 0.012),
    (dt.date(2011, 10, 3), 95.0, 0.020),
    (dt.date(2018, 9, 20), 260.0, 0.008),
    (dt.date(2018, 12, 24), 212.0, 0.016),
    (dt.date(2020, 2, 19), 300.0, 0.009),
    (dt.date(2020, 3, 23), 198.0, 0.040),   # COVID crash
    (dt.date(2022, 1, 3), 420.0, 0.010),
    (dt.date(2022, 10, 12), 315.0, 0.016),  # 2022 bear market
    (dt.date(2026, 10, 27), 610.0, 0.009),
]

# Bond prices: rising while rates fall, then the 2022 drop
BONDS = [
    (dt.date(2005, 1, 3), 100.0, 0.003),
    (dt.date(2008, 12, 18), 118.0, 0.005),
    (dt.date(2013, 5, 1), 128.0, 0.003),
    (dt.date(2013, 9, 5), 120.0, 0.004),
    (dt.date(2020, 8, 4), 150.0, 0.003),
    (dt.date(2022, 10, 24), 112.0, 0.006),
    (dt.date(2026, 10, 27), 121.0, 0.004),
]

GOLD = [
    (dt.date(2005, 1, 3), 100.0, 0.010),
    (dt.date(2011, 9, 5), 290.0, 0.013),
    (dt.date(2015, 12, 17), 160.0, 0.010),
    (dt.date(2020, 8, 6), 315.0, 0.010),
    (dt.date(2022, 9, 26), 245.0, 0.009),
    (dt.date(2026, 10, 27), 560.0, 0.011),
]

COMMODITIES = [
    (dt.date(2006, 2, 6), 100.0, 0.012),
    (dt.date(2008, 7, 2), 165.0, 0.014),
    (dt.date(2009, 2, 18), 75.0, 0.025),
    (dt.date(2011, 4, 29), 120.0, 0.013),
    (dt.date(2020, 4, 21), 42.0, 0.013),
    (dt.date(2022, 6, 8), 105.0, 0.016),
    (dt.date(2026, 10, 27), 88.0, 0.011),
]

# 13-week T-bill yield, in percent
TBILL = [
    (dt.date(2005, 1, 3), 2.2), (dt.date(2006, 7, 3), 5.0),
    (dt.date(2007, 8, 1), 4.8), (dt.date(2008, 12, 1), 0.05),
    (dt.date(2015, 11, 30), 0.15), (dt.date(2019, 4, 1), 2.4),
    (dt.date(2020, 3, 2), 1.2), (dt.date(2020, 4, 1), 0.05),
    (dt.date(2021, 12, 31), 0.05), (dt.date(2022, 3, 1), 0.4),
    (dt.date(2022, 12, 30), 4.4), (dt.date(2023, 7, 31), 5.2),
    (dt.date(2024, 8, 30), 5.1), (dt.date(2024, 12, 31), 4.3),
    (dt.date(2026, 10, 27), 3.9),
]

# symbol: (name, instrument type, exchange, first trading day, base path,
#          beta to the base path, daily idiosyncratic volatility, extra
#          trend per year, dividend yield per year, last close)
SYMBOLS = {
    "AAPL": ("Apple Inc.", "EQUITY", "NasdaqGS", None, "market", 1.2, 0.017, 0.16, 0.006, 340.0),
    "AMZN": ("Amazon.com, Inc.", "EQUITY", "NasdaqGS", None, "market", 1.3, 0.020, 0.08, 0.0, 250.0),
    "BND": ("Vanguard Total Bond Market Index Fund ETF Shares", "ETF", "NasdaqGM", dt.date(2007, 4, 10), "bonds", 0.7, 0.001, 0.015, 0.032, 72.0),
    "DBC": ("Invesco DB Commodity Index Tracking Fund", "ETF", "NYSEArca", dt.date(2006, 2, 6), "commodities", 1.0, 0.002, 0.0, 0.02, 24.0),
    "GLD": ("SPDR Gold Shares", "ETF", "NYSEArca", None, "gold", 1.0, 0.001, 0.0, 0.0, 370.0),
    "HD": ("The Home Depot, Inc.", "EQUITY", "NYSE", None, "market", 1.0, 0.012, 0.04, 0.022, 390.0),
    "IEF": ("iShares 7-10 Year Treasury Bond ETF", "ETF", "NasdaqGM", None, "bonds", 1.0, 0.0015, 0.015, 0.028, 96.0),
    "JNJ": ("Johnson & Johnson", "EQUITY", "NYSE", None, "market", 0.6, 0.009, -0.01, 0.028, 165.0),
    "JPM": ("JPMorgan Chase & Co.", "EQUITY", "NYSE", None, "market", 1.3, 0.014, 0.02, 0.025, 300.0),
    "KO": ("The Coca-Cola Company", "EQUITY", "NYSE", None, "market", 0.6, 0.008, -0.01, 0.03, 70.0),
    "MSFT": ("Microsoft Corporation", "EQUITY", "NasdaqGS", None, "market", 1.1, 0.013, 0.02, 0.009, 520.0),
    "NVDA": ("NVIDIA Corporation", "EQUITY", "NasdaqGS", None, "market", 1.6, 0.025, 0.12, 0.001, 190.0),
    "PG": ("The Procter & Gamble Company", "EQUITY", "NYSE", None, "market", 0.55, 0.008, -0.01, 0.026, 155.0),
    "QQQ": ("Invesco QQQ Trust", "ETF", "NasdaqGM", None, "market", 1.15, 0.003, 0.04, 0.006, 610.0),
    "SCHD": ("Schwab U.S. Dividend Equity ETF", "ETF", "NYSEArca", dt.date(2011, 10, 20), "market", 0.85, 0.003, -0.01, 0.035, 27.0),
    "SPY": ("State Street SPDR S&P 500 ETF Trust", "ETF", "NYSEArca", None, "market", 1.0, 0.0004, 0.0, 0.015, 680.0),
    "TLT": ("iShares 20+ Year Treasury Bond ETF", "ETF", "NasdaqGM", None, "bonds", 1.8, 0.002, 0.02, 0.035, 90.0),
    "VNQ": ("Vanguard Real Estate Index Fund ETF Shares", "ETF", "NYSEArca", None, "market", 1.25, 0.006, -0.04, 0.038, 90.0),
    "VOO": ("Vanguard S&P 500 ETF", "ETF", "NYSEArca", dt.date(2010, 9, 9), "market", 1.0, 0.0004, 0.0, 0.015, 625.0),
    "VTI": ("Vanguard Morningstar Total Stock Market ETF", "ETF", "NYSEArca", None, "market", 1.02, 0.0006, 0.0, 0.015, 330.0),
    "VTSAX": ("Vanguard MStar Total Stk Mkt Idx Admiral", "MUTUALFUND", "Nasdaq", None, "market", 1.02, 0.0006, 0.0, 0.015, 180.0),
    "VXUS": ("Vanguard Total International Stock Index Fund ETF Shares", "ETF", "NasdaqGS", dt.date(2011, 1, 28), "market", 0.85, 0.005, -0.06, 0.03, 72.0),
    "VYM": ("Vanguard High Dividend Yield Index Fund ETF Shares", "ETF", "NYSEArca", dt.date(2006, 11, 16), "market", 0.85, 0.003, -0.02, 0.03, 140.0),
    "WMT": ("Walmart Inc.", "EQUITY", "NasdaqGS", None, "market", 0.55, 0.010, 0.03, 0.015, 100.0),
    "XOM": ("ExxonMobil Holdings Corporation", "EQUITY", "NYSE", None, "market", 0.8, 0.014, -0.03, 0.035, 115.0),
}

# Mutual funds price once a day after the close, so their last bar is
# the previous trading day
MUTUAL_FUND_LAG = {"VTSAX"}


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> dt.date:
    d = dt.date(year, month, 1)
    d += dt.timedelta((weekday - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def _last_weekday(year: int, month: int, weekday: int) -> dt.date:
    d = dt.date(year, month + 1, 1) - dt.timedelta(1)
    return d - dt.timedelta((d.weekday() - weekday) % 7)


def _easter(year: int) -> dt.date:
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return dt.date(year, month, day)


def _observed(d: dt.date) -> dt.date:
    if d.weekday() == 5:
        return d - dt.timedelta(1)
    if d.weekday() == 6:
        return d + dt.timedelta(1)
    return d


def holidays(year: int) -> set[dt.date]:
    """US stock market holidays (the regular ones, not one-off closures)."""
    days = {
        _observed(dt.date(year, 1, 1)),
        _nth_weekday(year, 1, 0, 3),        # Martin Luther King Jr. Day
        _nth_weekday(year, 2, 0, 3),        # Presidents' Day
        _easter(year) - dt.timedelta(2),    # Good Friday
        _last_weekday(year, 5, 0),          # Memorial Day
        _observed(dt.date(year, 7, 4)),
        _nth_weekday(year, 9, 0, 1),        # Labor Day
        _nth_weekday(year, 11, 3, 4),       # Thanksgiving
        _observed(dt.date(year, 12, 25)),
    }
    if year >= 2022:
        days.add(_observed(dt.date(year, 6, 19)))
    # New Year's Day on a Saturday is not observed on the Friday before
    return {d for d in days if d.year == year}


# One-off closures: national days of mourning and Hurricane Sandy
SPECIAL_CLOSURES = {
    dt.date(2007, 1, 2), dt.date(2012, 10, 29), dt.date(2012, 10, 30),
    dt.date(2018, 12, 5), dt.date(2025, 1, 9),
}


def trading_days(start: dt.date, end: dt.date) -> list[dt.date]:
    closed = set(SPECIAL_CLOSURES)
    for year in range(start.year, end.year + 1):
        closed |= holidays(year)
    days, d = [], start
    while d <= end:
        if d.weekday() < 5 and d not in closed:
            days.append(d)
        d += dt.timedelta(1)
    return days


def bridge(days: list[dt.date], anchors, rng: random.Random) -> list[float]:
    """Log levels on *days* that pass through each anchor's level, as a
    random walk tied down at the anchors (a Brownian bridge per span)."""
    index = {d: i for i, d in enumerate(days)}
    out = [0.0] * len(days)
    points = [(index[_on_or_after(days, d)], math.log(level), vol) for d, level, vol in anchors]
    for (i0, y0, _), (i1, y1, vol) in zip(points, points[1:]):
        walk = [0.0]
        for _ in range(i1 - i0):
            walk.append(walk[-1] + rng.gauss(0.0, vol))
        n = i1 - i0
        for j in range(n + 1):
            t = j / n
            out[i0 + j] = y0 + (y1 - y0) * t + walk[j] - walk[-1] * t
    first = points[0][0]
    for i in range(first):
        out[i] = out[first]
    return out


def _on_or_after(days: list[dt.date], d: dt.date) -> dt.date:
    for day in days:
        if day >= d:
            return day
    return days[-1]


def dividend_days(days: list[dt.date]) -> set[dt.date]:
    """Quarterly ex-dividend days: the third Friday of each quarter's
    last month, or the next trading day."""
    out = set()
    for year in range(days[0].year, days[-1].year + 1):
        for month in (3, 6, 9, 12):
            day = _nth_weekday(year, month, 4, 3)
            if days[0] <= day <= days[-1]:
                out.add(_on_or_after(days, day))
    return out


def symbol_rows(sym: str, days: list[dt.date], bases: dict[str, list[float]]) -> list[tuple[dt.date, float, float]]:
    _, _, _, first, base, beta, vol, trend, yield_, last = SYMBOLS[sym]
    rng = random.Random(SEED ^ zlib.crc32(sym.encode()))
    end = days[-2] if sym in MUTUAL_FUND_LAG else days[-1]
    idx = [i for i, d in enumerate(days) if (first is None or d >= first) and d <= end]
    path = bases[base]
    logs, idio = [], 0.0
    for i in idx:
        idio += rng.gauss(0.0, vol)
        logs.append(beta * (path[i] - path[idx[0]]) + trend * (i - idx[0]) / 252 + idio)
    total = [math.exp(v - logs[-1]) * last for v in logs]   # total return, ends at *last*
    ex_days = dividend_days(days) if yield_ else set()
    factor, rows = 1.0, []
    for k in range(len(idx) - 1, -1, -1):
        d = days[idx[k]]
        close = total[k] / factor
        rows.append((d, close, total[k]))
        if d in ex_days:
            factor *= 1 - yield_ / 4
    rows.reverse()
    return rows


def tbill_rows(days: list[dt.date], rng: random.Random) -> list[tuple[dt.date, float, float]]:
    index = {d: i for i, d in enumerate(days)}
    points = [(index[_on_or_after(days, d)], y) for d, y in TBILL]
    rows, noise = [], 0.0
    for (i0, y0), (i1, y1) in zip(points, points[1:]):
        for i in range(i0, i1):
            noise = 0.9 * noise + rng.gauss(0.0, 0.003)
            y = (y0 + (y1 - y0) * (i - i0) / (i1 - i0)) * math.exp(noise)
            rows.append((days[i], y, y))
    rows.append((days[-1], TBILL[-1][1], TBILL[-1][1]))
    return rows


def main() -> None:
    days = trading_days(START, TODAY)
    rng = random.Random(SEED)
    bases = {
        "market": bridge(days, MARKET, rng),
        "bonds": bridge(days, BONDS, rng),
        "gold": bridge(days, GOLD, rng),
        "commodities": bridge(days, COMMODITIES, rng),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    series = {sym: symbol_rows(sym, days, bases) for sym in SYMBOLS}
    series["^IRX"] = tbill_rows(days, rng)
    for sym, rows in series.items():
        with (OUT_DIR / f"{sym}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["date", "close", "adjclose"])
            for d, close, adj in rows:
                w.writerow([d.isoformat(), f"{close:.6f}", f"{adj:.6f}"])

    meta = dict(SYMBOLS)
    meta["^IRX"] = ("13 WEEK TREASURY BILL", "INDEX", "Cboe Indices")
    quotes = {}
    for sym, rows in sorted(series.items()):
        name, kind, exchange = meta[sym][:3]
        when = dt.datetime.combine(rows[-1][0], dt.time(19, 30), dt.UTC)
        quotes[sym] = {
            "symbol": sym,
            "price": round(rows[-1][1], 4),
            "previous_close": round(rows[-2][1], 6),
            "currency": "USD",
            "name": name,
            "instrument_type": kind,
            "exchange": exchange,
            "as_of": when.isoformat(),
        }
    payload = {
        "generated": TODAY.isoformat(),
        "as_of": TODAY.isoformat(),
        "source": "Made-up sample prices from tools/generate_fixtures.py, not real market data",
        "quotes": quotes,
    }
    (OUT_DIR / "quotes.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(series)} series to {OUT_DIR}")


if __name__ == "__main__":
    main()
