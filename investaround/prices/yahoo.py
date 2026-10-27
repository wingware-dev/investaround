"""YahooPriceSource: prices from Yahoo Finance's public chart/search JSON.

The endpoints are unofficial and need no key.  We send an honest
User-Agent (a browser-imitating one gets HTTP 429), space requests out a
little, and turn every failure into PriceSourceError / UnknownSymbol so
the app can degrade gracefully.  Wrap it in CachingPriceSource.
"""

from __future__ import annotations

import datetime as dt
import logging
import threading
import time
from urllib.parse import quote as urlquote

import httpx

from ..models import PriceBar, PriceSeries, Quote, SearchHit, normalize_symbol
from .base import PriceSourceError, UnknownSymbol

log = logging.getLogger(__name__)

BASE_URL = "https://query1.finance.yahoo.com"
USER_AGENT = "investaround/0.1 (personal paper-trading app)"
# Asking for "everything" sends this as period1
EARLIEST = dt.date(1970, 1, 2)


class RateLimited(PriceSourceError):
    def __init__(self, retry_after: float | None = None) -> None:
        msg = "Yahoo Finance is limiting requests; try again in a few minutes"
        super().__init__(msg)
        self.retry_after = retry_after


def _epoch(day: dt.date) -> int:
    return int(dt.datetime.combine(day, dt.time(), dt.UTC).timestamp())


def _bar_date(ts: int, gmtoffset: int) -> dt.date:
    return dt.datetime.fromtimestamp(ts + gmtoffset, dt.UTC).date()


class YahooPriceSource:
    name = "yahoo"

    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        base_url: str = BASE_URL,
        timeout: float = 15.0,
        min_interval: float = 0.25,
        sleep=time.sleep,
        monotonic=time.monotonic,
    ) -> None:
        """``transport`` lets tests replay recorded responses; ``min_interval``
        is the polite gap in seconds between requests."""
        self._client = client or httpx.Client(
            base_url=base_url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=timeout,
            transport=transport,
            follow_redirects=True,
        )
        self._min_interval = min_interval
        self._sleep = sleep
        self._monotonic = monotonic
        self._last_request = None
        self._lock = threading.Lock()

    def close(self) -> None:
        self._client.close()

    # -- HTTP -------------------------------------------------------------

    def _get(self, path: str, params: dict) -> tuple[int, dict | None]:
        """GET and decode JSON; returns (status, body) for 2xx/4xx JSON replies,
        raises PriceSourceError for anything else."""
        with self._lock:
            if self._last_request is not None and self._min_interval:
                wait = self._min_interval - (self._monotonic() - self._last_request)
                if wait > 0:
                    self._sleep(wait)
            try:
                resp = self._client.get(path, params=params)
            except httpx.HTTPError as exc:
                raise PriceSourceError(f"Could not reach Yahoo Finance ({exc.__class__.__name__})") from exc
            finally:
                self._last_request = self._monotonic()

        if resp.status_code == 429:
            retry = resp.headers.get("retry-after")
            raise RateLimited(float(retry) if retry and retry.isdigit() else None)
        if resp.status_code >= 500:
            raise PriceSourceError(f"Yahoo Finance had a server error (HTTP {resp.status_code})")
        try:
            body = resp.json()
        except ValueError:
            raise PriceSourceError(f"Unexpected reply from Yahoo Finance (HTTP {resp.status_code})") from None
        if resp.status_code >= 400 and not isinstance(body, dict):
            raise PriceSourceError(f"Yahoo Finance refused the request (HTTP {resp.status_code})")
        return resp.status_code, body

    def _chart(self, symbol: str, params: dict) -> dict | None:
        """The chart result for symbol, or None when Yahoo says the range has
        no data (as for dates before a fund existed)."""
        status, body = self._get(f"/v8/finance/chart/{urlquote(symbol, safe='')}", params)
        chart = (body or {}).get("chart") or {}
        err = chart.get("error")
        if err:
            code = err.get("code", "")
            desc = err.get("description", "")
            if code == "Not Found" or status == 404:
                raise UnknownSymbol(symbol)
            if desc.startswith("Data doesn't exist"):
                return None
            raise PriceSourceError(f"Yahoo Finance error for {symbol}: {desc or code}")
        if status >= 400:
            raise PriceSourceError(f"Yahoo Finance refused the request for {symbol} (HTTP {status})")
        results = chart.get("result") or []
        if not results:
            raise UnknownSymbol(symbol)
        return results[0]

    # -- parsing ----------------------------------------------------------

    @staticmethod
    def _parse_bars(result: dict) -> list[PriceBar]:
        """Daily bars, skipping rows with no close (holidays Yahoo pads in,
        today's not-yet-priced mutual fund row, data gaps)."""
        offset = result.get("meta", {}).get("gmtoffset", 0) or 0
        stamps = result.get("timestamp") or []
        indicators = result.get("indicators") or {}
        closes = ((indicators.get("quote") or [{}])[0]).get("close") or []
        adj = ((indicators.get("adjclose") or [{}])[0]).get("adjclose") or closes
        by_date: dict[dt.date, PriceBar] = {}
        for ts, c, a in zip(stamps, closes, adj):
            if c is None or c <= 0:
                continue
            day = _bar_date(ts, offset)
            by_date[day] = PriceBar(day, float(c), float(a if a is not None and a > 0 else c))
        return [by_date[d] for d in sorted(by_date)]

    # -- PriceSource ------------------------------------------------------

    def quote(self, symbol: str) -> Quote:
        sym = normalize_symbol(symbol)
        result = self._chart(sym, {"range": "5d", "interval": "1d"})
        if result is None:
            raise UnknownSymbol(sym)
        meta = result.get("meta") or {}
        bars = self._parse_bars(result)
        price = meta.get("regularMarketPrice")
        if price is None:
            if not bars:
                raise PriceSourceError(f"Yahoo Finance has no current price for {sym}")
            price = bars[-1].close
        price = float(price)
        # The latest bar is usually the one the price belongs to (today, or
        # the last NAV for a fund); the day before is then the previous close.
        previous = None
        if bars:
            if abs(bars[-1].close - price) <= 1e-4 * price:
                previous = bars[-2].close if len(bars) >= 2 else None
            else:
                previous = bars[-1].close
        if previous is None and meta.get("chartPreviousClose"):
            previous = float(meta["chartPreviousClose"])
        when = meta.get("regularMarketTime")
        return Quote(
            symbol=sym,
            price=price,
            previous_close=previous,
            currency=meta.get("currency") or "USD",
            name=meta.get("longName") or meta.get("shortName") or sym,
            instrument_type=meta.get("instrumentType", ""),
            as_of=dt.datetime.fromtimestamp(when, dt.UTC) if when else None,
        )

    def quotes(self, symbols: list[str]) -> dict[str, Quote]:
        out = {}
        for s in symbols:
            try:
                q = self.quote(s)
            except UnknownSymbol:
                log.info("Skipping unknown symbol %s", s)
                continue
            out[q.symbol] = q
        return out

    def history(self, symbol: str, start: dt.date | None = None, end: dt.date | None = None) -> PriceSeries:
        sym = normalize_symbol(symbol)
        first = start or EARLIEST
        last = end or dt.date.today()
        if last < first:
            return PriceSeries(sym, [])
        result = self._chart(sym, {
            "period1": _epoch(first),
            "period2": _epoch(last + dt.timedelta(days=1)),
            "interval": "1d",
            "events": "div|split",
        })
        if result is None:
            return PriceSeries(sym, [])
        return PriceSeries(sym, self._parse_bars(result)).between(start, end)

    def search(self, query: str, limit: int = 10) -> list[SearchHit]:
        q = (query or "").strip()
        if not q:
            return []
        status, body = self._get("/v1/finance/search", {"q": q, "quotesCount": limit, "newsCount": 0})
        if status >= 400:
            raise PriceSourceError(f"Yahoo Finance search failed (HTTP {status})")
        hits = []
        for item in (body or {}).get("quotes") or []:
            sym = item.get("symbol")
            if not sym or item.get("isYahooFinance") is False:
                continue
            hits.append(SearchHit(
                symbol=sym,
                name=item.get("longname") or item.get("shortname") or sym,
                instrument_type=item.get("quoteType", ""),
                exchange=item.get("exchDisp") or item.get("exchange", ""),
            ))
        return hits[:limit]
