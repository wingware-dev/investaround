"""FakePriceSource: made-up sample prices from tests/fixtures, no network.

Used by every test and by ``INVESTAROUND_PRICE_SOURCE=fake``.  "Today" is
frozen at the date the fixtures end, so results never drift.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

from ..models import PriceBar, PriceSeries, Quote, SearchHit, normalize_symbol
from .base import PriceSourceError, UnknownSymbol

DEFAULT_FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "prices"


class FakePriceSource:
    name = "fake"

    def __init__(self, fixtures_dir: str | Path = DEFAULT_FIXTURES, fail_symbols: set[str] | None = None) -> None:
        """``fail_symbols``: symbols that raise PriceSourceError, to test error paths."""
        self.fixtures_dir = Path(fixtures_dir)
        quotes_path = self.fixtures_dir / "quotes.json"
        if not quotes_path.exists():
            raise FileNotFoundError(f"No price fixtures at {self.fixtures_dir}; run tools/generate_fixtures.py")
        payload = json.loads(quotes_path.read_text(encoding="utf-8"))
        self.today = dt.date.fromisoformat(payload["as_of"])
        self._quote_data: dict[str, dict] = payload["quotes"]
        self._series: dict[str, PriceSeries] = {}
        self.fail_symbols = {s.upper() for s in (fail_symbols or ())}

    @property
    def symbols(self) -> list[str]:
        return sorted(self._quote_data)

    def _check(self, symbol: str) -> str:
        sym = normalize_symbol(symbol)
        if sym in self.fail_symbols:
            raise PriceSourceError(f"Simulated failure for {sym}")
        if sym not in self._quote_data:
            raise UnknownSymbol(sym)
        return sym

    def quote(self, symbol: str) -> Quote:
        sym = self._check(symbol)
        d = self._quote_data[sym]
        return Quote(
            symbol=sym,
            price=float(d["price"]),
            previous_close=None if d.get("previous_close") is None else float(d["previous_close"]),
            currency=d.get("currency", "USD"),
            name=d.get("name", sym),
            instrument_type=d.get("instrument_type", ""),
            as_of=dt.datetime.fromisoformat(d["as_of"]) if d.get("as_of") else None,
        )

    def quotes(self, symbols: list[str]) -> dict[str, Quote]:
        out = {}
        for s in symbols:
            try:
                q = self.quote(s)
            except UnknownSymbol:
                continue
            out[q.symbol] = q
        return out

    def _load_series(self, sym: str) -> PriceSeries:
        if sym not in self._series:
            bars = []
            with (self.fixtures_dir / f"{sym}.csv").open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    bars.append(PriceBar(dt.date.fromisoformat(row["date"]), float(row["close"]), float(row["adjclose"])))
            self._series[sym] = PriceSeries(sym, bars)
        return self._series[sym]

    def history(self, symbol: str, start: dt.date | None = None, end: dt.date | None = None) -> PriceSeries:
        sym = self._check(symbol)
        return self._load_series(sym).between(start, end)

    def search(self, query: str, limit: int = 10) -> list[SearchHit]:
        q = (query or "").strip().lower()
        if not q:
            return []
        ranked = []
        for sym, d in self._quote_data.items():
            name = d.get("name", "")
            if sym.lower() == q:
                rank = 0
            elif sym.lower().startswith(q):
                rank = 1
            elif q in name.lower():
                rank = 2
            else:
                continue
            ranked.append((rank, sym, SearchHit(sym, name, d.get("instrument_type", ""), d.get("exchange", ""))))
        ranked.sort(key=lambda t: (t[0], t[1]))
        return [hit for _, _, hit in ranked[:limit]]
