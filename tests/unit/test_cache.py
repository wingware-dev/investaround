import datetime as dt
import json
from pathlib import Path

import httpx
import pytest

from investaround.models import PriceBar, PriceSeries, Quote, SearchHit
from investaround.prices.base import PriceSourceError, UnknownSymbol
from investaround.prices.cache import EARLIEST, CachingPriceSource
from investaround.prices.yahoo import YahooPriceSource

D = dt.date
TODAY = D(2026, 10, 27)  # a Tuesday
NOON = dt.datetime(2026, 10, 27, 12, 0).timestamp()  # local time, as the cache's "today" is


class Stub:
    """Wrapped source with weekday bars 2020-01-01..today and call recording."""

    name = "stub"

    def __init__(self, today=TODAY):
        self.today = today
        self.adj_factor = 0.9
        self.fail = None
        self.calls = []
        self.dates = []
        day = D(2020, 1, 1)
        while day <= D(2030, 1, 1):
            if day.weekday() < 5:
                self.dates.append(day)
            day += dt.timedelta(days=1)

    def close_on(self, day):
        return 100 + (day - D(2020, 1, 1)).days

    def _check(self, sym):
        if self.fail:
            raise self.fail
        if sym == "NOPE":
            raise UnknownSymbol(sym)

    def history(self, sym, start, end):
        self.calls.append(("history", sym, start, end))
        self._check(sym)
        bars = [PriceBar(d, self.close_on(d), self.close_on(d) * self.adj_factor)
                for d in self.dates if start <= d <= end and d <= self.today]
        return PriceSeries(sym, bars)

    def quote(self, sym):
        self.calls.append(("quote", sym))
        self._check(sym)
        return Quote(sym, 123.0, 120.0, name=f"{sym} Inc", instrument_type="EQUITY",
                     as_of=dt.datetime(2026, 10, 27, 16, tzinfo=dt.UTC))

    def search(self, q, limit=10):
        self.calls.append(("search", q, limit))
        self._check(q)
        return [SearchHit("VOO", "Vanguard S&P 500 ETF", "ETF", "NYSEArca")][:limit]


class Clock:
    def __init__(self, t=NOON):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, seconds=0, days=0):
        self.t += seconds + days * 86400


@pytest.fixture
def stub():
    return Stub()


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def cache(stub, clock, tmp_path):
    return CachingPriceSource(stub, tmp_path / "prices.sqlite", quote_ttl=900, search_ttl=3600, clock=clock)


def history_calls(stub):
    return [c[2:] for c in stub.calls if c[0] == "history"]


class TestHistory:
    def test_name_passes_through(self, cache):
        assert cache.name == "stub"

    def test_past_range_fetched_once(self, cache, stub, clock):
        a = cache.history("SPY", D(2021, 1, 1), D(2021, 12, 31))
        clock.advance(days=30)
        b = cache.history("spy", D(2021, 1, 1), D(2021, 12, 31))
        assert a.bars == b.bars and len(a) == 261
        assert history_calls(stub) == [(D(2021, 1, 1), D(2021, 12, 31))]

    def test_sub_range_served_from_cache(self, cache, stub):
        cache.history("SPY", D(2021, 1, 1), D(2021, 12, 31))
        s = cache.history("SPY", D(2021, 3, 1), D(2021, 3, 5))
        assert [b.date.day for b in s.bars] == [1, 2, 3, 4, 5]
        assert len(history_calls(stub)) == 1

    def test_start_none_means_everything(self, cache, stub):
        s = cache.history("SPY")
        assert history_calls(stub) == [(EARLIEST, TODAY)]
        assert s.first_date == D(2020, 1, 1) and s.last_date == TODAY
        cache.history("SPY", None, D(2022, 1, 1))
        assert len(history_calls(stub)) == 1

    def test_future_end_clamped_to_today(self, cache, stub):
        s = cache.history("SPY", D(2026, 10, 1), D(2027, 1, 1))
        assert history_calls(stub) == [(D(2026, 10, 1), TODAY)]
        assert s.last_date == TODAY

    def test_inverted_range(self, cache, stub):
        assert len(cache.history("SPY", D(2022, 1, 1), D(2021, 1, 1))) == 0
        assert stub.calls == []

    def test_today_refreshed_after_ttl_only(self, cache, stub, clock):
        cache.history("SPY", D(2026, 1, 1))
        clock.advance(seconds=600)
        cache.history("SPY", D(2026, 1, 1))
        assert len(history_calls(stub)) == 1
        clock.advance(seconds=600)
        cache.history("SPY", D(2026, 1, 1))
        # Re-fetches only from the last finished bar (Monday), not the whole range
        assert history_calls(stub)[1] == (D(2026, 10, 26), TODAY)

    def test_next_day_fetches_only_the_tail(self, cache, stub, clock):
        cache.history("SPY", D(2026, 1, 1))
        clock.advance(days=1)
        stub.today = TODAY + dt.timedelta(days=1)
        s = cache.history("SPY", D(2026, 1, 1))
        assert history_calls(stub)[1] == (D(2026, 10, 26), D(2026, 10, 28))
        assert s.last_date == D(2026, 10, 28)
        # The 27th has now been fetched after its day ended, so it is final
        clock.advance(days=1)
        stub.today = TODAY + dt.timedelta(days=2)
        cache.history("SPY", D(2026, 1, 1))
        assert history_calls(stub)[2] == (D(2026, 10, 27), D(2026, 10, 29))

    def test_partial_today_bar_replaced(self, cache, stub, clock):
        cache.history("SPY", D(2026, 10, 1))
        original = stub.close_on
        stub.close_on = lambda d: original(d) + (5 if d == TODAY else 0)
        clock.advance(seconds=1000)
        s = cache.history("SPY", D(2026, 10, 1))
        assert s.bars[-1].close == original(TODAY) + 5

    def test_extend_backwards_overlaps_first_bar(self, cache, stub):
        cache.history("SPY", D(2022, 1, 3), D(2022, 6, 30))
        s = cache.history("SPY", D(2021, 1, 1), D(2022, 6, 30))
        assert history_calls(stub)[1] == (D(2021, 1, 1), D(2022, 1, 3))
        assert s.first_date == D(2021, 1, 1)
        dates = [b.date for b in s.bars]
        assert len(dates) == len(set(dates))

    def test_later_disjoint_range_fills_gap(self, cache, stub):
        cache.history("SPY", D(2021, 1, 1), D(2021, 3, 31))
        s = cache.history("SPY", D(2023, 1, 1), D(2023, 1, 31))
        assert history_calls(stub)[1] == (D(2021, 3, 31), D(2023, 1, 31))
        assert s.first_date == D(2023, 1, 2)
        # Everything between is now cached
        cache.history("SPY", D(2022, 1, 1), D(2022, 12, 31))
        assert len(history_calls(stub)) == 2

    def test_adjclose_rescaled_after_dividend(self, cache, stub, clock):
        cache.history("SPY", D(2026, 1, 1), D(2026, 10, 26))
        stub.adj_factor = 0.8  # a dividend: Yahoo rescales every past adjclose
        s = cache.history("SPY", D(2026, 1, 1))
        for b in s.bars:
            assert b.adjclose == pytest.approx(b.close * 0.8), b.date

    def test_rescale_on_backward_extension(self, cache, stub):
        cache.history("SPY", D(2022, 1, 3), D(2022, 6, 30))
        stub.adj_factor = 0.7
        s = cache.history("SPY", D(2021, 1, 1), D(2022, 6, 30))
        assert all(b.adjclose == pytest.approx(b.close * 0.7) for b in s.bars)

    def test_symbol_listed_later(self, cache, stub):
        stub.dates = [d for d in stub.dates if d >= D(2024, 1, 1)]
        assert len(cache.history("NEW", D(2023, 1, 1), D(2023, 12, 31))) == 0
        s = cache.history("NEW", D(2023, 1, 1), D(2024, 1, 31))
        assert s.first_date == D(2024, 1, 1)

    def test_offline_serves_cached(self, cache, stub, clock, caplog):
        cache.history("SPY", D(2026, 1, 1))
        clock.advance(days=1)
        stub.fail = PriceSourceError("offline")
        s = cache.history("SPY", D(2026, 1, 1))
        assert s.last_date == TODAY
        assert "Using cached prices for SPY: offline" in caplog.text

    def test_offline_without_cache_raises(self, cache, stub):
        stub.fail = PriceSourceError("offline")
        with pytest.raises(PriceSourceError):
            cache.history("SPY", D(2026, 1, 1))

    def test_unknown_symbol_raises(self, cache):
        with pytest.raises(UnknownSymbol):
            cache.history("NOPE", D(2026, 1, 1))

    def test_persists_across_instances(self, cache, stub, clock, tmp_path):
        cache.history("SPY", D(2021, 1, 1), D(2021, 12, 31))
        again = CachingPriceSource(stub, tmp_path / "prices.sqlite", clock=clock)
        assert len(again.history("SPY", D(2021, 1, 1), D(2021, 12, 31))) == 261
        assert len(history_calls(stub)) == 1


class TestQuotes:
    def test_ttl(self, cache, stub, clock):
        q = cache.quote("aapl")
        assert q.symbol == "AAPL" and q.change_pct == pytest.approx(2.5)
        clock.advance(seconds=899)
        assert cache.quote("AAPL") == q
        clock.advance(seconds=2)
        cache.quote("AAPL")
        assert stub.calls == [("quote", "AAPL"), ("quote", "AAPL")]

    def test_round_trips_all_fields(self, cache, stub):
        q = cache.quote("AAPL")
        assert cache.quote("AAPL") == q
        assert q.as_of == dt.datetime(2026, 10, 27, 16, tzinfo=dt.UTC)

    def test_stale_on_error(self, cache, stub, clock, caplog):
        q = cache.quote("AAPL")
        clock.advance(days=1)
        stub.fail = PriceSourceError("rate limited")
        assert cache.quote("AAPL") == q
        assert "Using cached quote for AAPL" in caplog.text

    def test_error_without_cache(self, cache, stub):
        stub.fail = PriceSourceError("rate limited")
        with pytest.raises(PriceSourceError):
            cache.quote("AAPL")

    def test_unknown(self, cache):
        with pytest.raises(UnknownSymbol):
            cache.quote("NOPE")

    def test_quotes_skips_unknown(self, cache):
        assert sorted(cache.quotes(["AAPL", "NOPE", "msft"])) == ["AAPL", "MSFT"]


class TestSearch:
    def test_cached(self, cache, stub, clock):
        hits = cache.search("Vanguard")
        assert cache.search("vanguard ") == hits
        assert len([c for c in stub.calls if c[0] == "search"]) == 1
        clock.advance(seconds=3601)
        cache.search("vanguard")
        assert len([c for c in stub.calls if c[0] == "search"]) == 2

    def test_limit_is_part_of_key(self, cache, stub):
        cache.search("vanguard", limit=5)
        cache.search("vanguard", limit=10)
        assert len(stub.calls) == 2

    def test_stale_on_error(self, cache, stub, clock):
        hits = cache.search("vanguard")
        clock.advance(days=2)
        stub.fail = PriceSourceError("offline")
        assert cache.search("vanguard") == hits

    def test_blank(self, cache, stub):
        assert cache.search("  ") == []
        assert stub.calls == []


def test_with_yahoo_source(tmp_path, clock):
    """End to end over a recorded Yahoo reply: the second read makes no request."""
    record = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "yahoo" / "history_SPY_2020.json").read_text())
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(record["status"], json=record["body"])

    yahoo = YahooPriceSource(transport=httpx.MockTransport(handler), min_interval=0)
    cache = CachingPriceSource(yahoo, tmp_path / "p.sqlite", clock=clock)
    a = cache.history("SPY", D(2020, 3, 2), D(2020, 4, 14))
    b = cache.history("SPY", D(2020, 3, 16), D(2020, 3, 20))
    assert len(a) == 31 and len(b) == 5
    assert b.bars == [x for x in a.bars if D(2020, 3, 16) <= x.date <= D(2020, 3, 20)]
    assert len(requests) == 1
    assert cache.name == "yahoo"
