"""CachingPriceSource: a SQLite cache in front of any PriceSource.

- Daily bars are kept for good.  For each symbol we remember the date range
  fetched so far and only ask the wrapped source for what is missing.  Bars
  for today (and any fetched on their own day) may still change, so they
  are re-fetched once they are older than ``quote_ttl``.
- Adjusted closes are rescaled by Yahoo after each dividend or split.  Each
  fetch overlaps the cached bars by a day; if the overlap's adjclose moved,
  every cached adjclose for the symbol is scaled to match, so a series
  stitched from several fetches stays consistent.
- Quotes are reused for ``quote_ttl`` seconds, searches for ``search_ttl``.
- When the wrapped source fails (offline, rate limited) and there is cached
  data, the stale data is served and the failure logged.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import sqlite3
import time
from contextlib import closing, contextmanager
from pathlib import Path

from ..models import PriceBar, PriceSeries, Quote, SearchHit, normalize_symbol
from .base import PriceSource, PriceSourceError, UnknownSymbol

log = logging.getLogger(__name__)

EARLIEST = dt.date(1970, 1, 2)

SCHEMA = """
CREATE TABLE IF NOT EXISTS bars (
    symbol TEXT NOT NULL, date TEXT NOT NULL, close REAL NOT NULL, adjclose REAL NOT NULL,
    PRIMARY KEY (symbol, date));
CREATE TABLE IF NOT EXISTS coverage (
    symbol TEXT PRIMARY KEY,
    lo TEXT NOT NULL,        -- every bar in [lo, hi] has been fetched
    hi TEXT NOT NULL,
    final_hi TEXT NOT NULL,  -- bars up to here were fetched after their day ended
    fetched REAL NOT NULL);  -- when the range ending at hi was fetched
CREATE TABLE IF NOT EXISTS quotes (symbol TEXT PRIMARY KEY, data TEXT NOT NULL, fetched REAL NOT NULL);
CREATE TABLE IF NOT EXISTS searches (query TEXT PRIMARY KEY, data TEXT NOT NULL, fetched REAL NOT NULL);
"""


def _quote_to_json(q: Quote) -> str:
    return json.dumps({
        "symbol": q.symbol, "price": q.price, "previous_close": q.previous_close, "currency": q.currency,
        "name": q.name, "instrument_type": q.instrument_type,
        "as_of": q.as_of.isoformat() if q.as_of else None,
    })


def _quote_from_json(s: str) -> Quote:
    d = json.loads(s)
    d["as_of"] = dt.datetime.fromisoformat(d["as_of"]) if d.get("as_of") else None
    return Quote(**d)


class CachingPriceSource:
    def __init__(
        self,
        wrapped: PriceSource,
        db_path: str | Path,
        *,
        quote_ttl: float = 15 * 60,
        search_ttl: float = 24 * 3600,
        clock=time.time,
    ) -> None:
        self.wrapped = wrapped
        self.name = wrapped.name
        self.db_path = Path(db_path)
        self.quote_ttl = quote_ttl
        self.search_ttl = search_ttl
        self._clock = clock
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as con:
            con.executescript(SCHEMA)

    @contextmanager
    def _db(self):
        with closing(sqlite3.connect(self.db_path, timeout=30)) as con:
            with con:
                yield con

    def _today(self) -> dt.date:
        return dt.datetime.fromtimestamp(self._clock()).date()

    # -- quotes -----------------------------------------------------------

    def quote(self, symbol: str) -> Quote:
        sym = normalize_symbol(symbol)
        now = self._clock()
        with self._db() as con:
            row = con.execute("SELECT data, fetched FROM quotes WHERE symbol=?", (sym,)).fetchone()
        if row and now - row[1] < self.quote_ttl:
            return _quote_from_json(row[0])
        try:
            q = self.wrapped.quote(sym)
        except UnknownSymbol:
            raise
        except PriceSourceError as exc:
            if row:
                log.warning("Using cached quote for %s: %s", sym, exc)
                return _quote_from_json(row[0])
            raise
        with self._db() as con:
            con.execute("INSERT OR REPLACE INTO quotes VALUES (?, ?, ?)", (sym, _quote_to_json(q), now))
        return q

    def quotes(self, symbols: list[str]) -> dict[str, Quote]:
        out = {}
        for s in symbols:
            try:
                q = self.quote(s)
            except UnknownSymbol:
                continue
            out[q.symbol] = q
        return out

    # -- history ----------------------------------------------------------

    def history(self, symbol: str, start: dt.date | None = None, end: dt.date | None = None) -> PriceSeries:
        sym = normalize_symbol(symbol)
        today = self._today()
        lo = start or EARLIEST
        hi = min(end or today, today)
        if hi < lo:
            return PriceSeries(sym, [])

        with self._db() as con:
            cov = con.execute("SELECT lo, hi, final_hi, fetched FROM coverage WHERE symbol=?", (sym,)).fetchone()
            first_bar, last_final_bar = None, None
            if cov:
                first_bar = con.execute("SELECT MIN(date) FROM bars WHERE symbol=?", (sym,)).fetchone()[0]
                last_final_bar = con.execute("SELECT MAX(date) FROM bars WHERE symbol=? AND date<=?",
                                             (sym, cov[2])).fetchone()[0]

        fetches: list[tuple[dt.date, dt.date]] = []
        if cov is None:
            fetches.append((lo, hi))
        else:
            c_lo, c_hi, c_final = (dt.date.fromisoformat(v) for v in cov[:3])
            if lo < c_lo:
                # Overlap the first cached bar so adjclose can be matched up
                back_end = dt.date.fromisoformat(first_bar) if first_bar else c_lo
                fetches.append((lo, max(back_end, c_lo)))
            if hi > c_final:
                fresh = hi <= c_hi and self._clock() - cov[3] < self.quote_ttl
                if not fresh:
                    fwd_start = dt.date.fromisoformat(last_final_bar) if last_final_bar else c_final
                    fetches.append((min(fwd_start, c_final), hi))

        for f_lo, f_hi in fetches:
            try:
                series = self.wrapped.history(sym, f_lo, f_hi)
            except UnknownSymbol:
                raise
            except PriceSourceError as exc:
                if cov is None:
                    raise
                log.warning("Using cached prices for %s: %s", sym, exc)
                break
            self._store(sym, f_lo, f_hi, series.bars, today)

        with self._db() as con:
            rows = con.execute(
                "SELECT date, close, adjclose FROM bars WHERE symbol=? AND date BETWEEN ? AND ? ORDER BY date",
                (sym, lo.isoformat(), hi.isoformat()),
            ).fetchall()
        return PriceSeries(sym, [PriceBar(dt.date.fromisoformat(d), c, a) for d, c, a in rows])

    def _store(self, sym: str, f_lo: dt.date, f_hi: dt.date, bars: list[PriceBar], today: dt.date) -> None:
        now = self._clock()
        with self._db() as con:
            if bars:
                new_by_date = {b.date.isoformat(): b for b in bars}
                cached = con.execute(
                    "SELECT date, adjclose FROM bars WHERE symbol=? AND date BETWEEN ? AND ? ORDER BY date DESC",
                    (sym, bars[0].date.isoformat(), bars[-1].date.isoformat()),
                )
                common = next((row for row in cached if row[0] in new_by_date), None)
                if common and common[1] > 0:
                    ratio = new_by_date[common[0]].adjclose / common[1]
                    if abs(ratio - 1) > 1e-9:
                        log.info("Rescaling cached adjusted closes for %s by %.6f", sym, ratio)
                        con.execute("UPDATE bars SET adjclose = adjclose * ? WHERE symbol=?", (ratio, sym))
                con.executemany(
                    "INSERT OR REPLACE INTO bars VALUES (?, ?, ?, ?)",
                    [(sym, b.date.isoformat(), b.close, b.adjclose) for b in bars],
                )
            final = min(f_hi, today - dt.timedelta(days=1))
            cov = con.execute("SELECT lo, hi, final_hi, fetched FROM coverage WHERE symbol=?", (sym,)).fetchone()
            if cov is None:
                lo, hi, final_hi, fetched = f_lo, f_hi, max(final, f_lo - dt.timedelta(days=1)), now
            else:
                c_lo, c_hi, c_final = (dt.date.fromisoformat(v) for v in cov[:3])
                lo, hi = min(c_lo, f_lo), max(c_hi, f_hi)
                final_hi = max(c_final, final)
                fetched = now if f_hi >= c_hi else cov[3]
            con.execute(
                "INSERT OR REPLACE INTO coverage VALUES (?, ?, ?, ?, ?)",
                (sym, lo.isoformat(), hi.isoformat(), final_hi.isoformat(), fetched),
            )

    # -- search -----------------------------------------------------------

    def search(self, query: str, limit: int = 10) -> list[SearchHit]:
        q = (query or "").strip()
        if not q:
            return []
        key = f"{limit}:{q.lower()}"
        now = self._clock()
        with self._db() as con:
            row = con.execute("SELECT data, fetched FROM searches WHERE query=?", (key,)).fetchone()
        if row and now - row[1] < self.search_ttl:
            return [SearchHit(**d) for d in json.loads(row[0])]
        try:
            hits = self.wrapped.search(q, limit)
        except PriceSourceError as exc:
            if row:
                log.warning("Using cached search for %r: %s", q, exc)
                return [SearchHit(**d) for d in json.loads(row[0])]
            raise
        data = json.dumps([{"symbol": h.symbol, "name": h.name, "instrument_type": h.instrument_type,
                            "exchange": h.exchange} for h in hits])
        with self._db() as con:
            con.execute("INSERT OR REPLACE INTO searches VALUES (?, ?, ?)", (key, data, now))
        return hits
