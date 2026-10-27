"""YahooPriceSource against recorded responses (tests/fixtures/yahoo), never live."""

import copy
import datetime as dt
import json
from pathlib import Path

import httpx
import pytest

from investaround.prices.base import PriceSource, PriceSourceError, UnknownSymbol
from investaround.prices.yahoo import USER_AGENT, RateLimited, YahooPriceSource

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "yahoo"


def load(name):
    return json.loads((FIXTURES / f"{name}.json").read_text())


def response(record):
    body = record["body"]
    if isinstance(body, str):
        return httpx.Response(record["status"], text=body, headers=record["headers"])
    return httpx.Response(record["status"], json=body)


class Replay:
    """Fake transport: answers each request with the next queued fixture."""

    def __init__(self, *records):
        self.queue = list(records)
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        item = self.queue.pop(0)
        if isinstance(item, Exception):
            raise item
        if isinstance(item, httpx.Response):
            return item
        return response(item)


def source(*records):
    replay = Replay(*records)
    return YahooPriceSource(transport=httpx.MockTransport(replay), min_interval=0), replay


def test_is_a_price_source():
    src, _ = source()
    assert isinstance(src, PriceSource)
    assert src.name == "yahoo"


class TestQuote:
    def test_etf_quote(self):
        src, replay = source(load("quote_SPY"))
        q = src.quote("spy")
        assert q.symbol == "SPY"
        assert q.price == pytest.approx(624.76)
        # previous trading day's close, not chartPreviousClose (the close before the 5-day window)
        assert q.previous_close == pytest.approx(608.27, abs=1e-3)
        assert q.name == "State Street SPDR S&P 500 ETF Trust"
        assert q.instrument_type == "ETF"
        assert q.currency == "USD"
        assert q.as_of == dt.datetime.fromtimestamp(1793129511, dt.UTC)

    def test_request_is_honest_and_correct(self):
        src, replay = source(load("quote_SPY"))
        src.quote("SPY")
        [req] = replay.requests
        assert req.headers["user-agent"] == USER_AGENT
        assert req.url.path == "/v8/finance/chart/SPY"
        assert req.url.params["range"] == "5d"
        assert req.url.host == "query1.finance.yahoo.com"

    def test_mutual_fund_with_unpriced_today(self):
        # Today's row has a null close: the fund's NAV isn't out yet
        src, _ = source(load("quote_VTSAX"))
        q = src.quote("VTSAX")
        assert q.price == pytest.approx(146.41)
        assert q.previous_close == pytest.approx(147.1, abs=1e-3)
        assert q.instrument_type == "MUTUALFUND"

    def test_index_symbol_is_url_quoted(self):
        rec = load("quote_SPY")
        src, replay = source(rec)
        src.quote("^GSPC")
        assert replay.requests[0].url.raw_path.startswith(b"/v8/finance/chart/%5EGSPC")

    def test_unknown_symbol(self):
        src, _ = source(load("quote_unknown"))
        with pytest.raises(UnknownSymbol) as info:
            src.quote("NOSUCHSYMBOLX")
        assert info.value.symbol == "NOSUCHSYMBOLX"

    def test_rate_limited(self):
        src, _ = source(load("rate_limited"))
        with pytest.raises(RateLimited, match="limiting"):
            src.quote("SPY")

    def test_rate_limited_retry_after(self):
        src, _ = source(httpx.Response(429, headers={"Retry-After": "30"}, text="slow down"))
        with pytest.raises(RateLimited) as info:
            src.quote("SPY")
        assert info.value.retry_after == 30
        assert isinstance(info.value, PriceSourceError)

    def test_network_down(self):
        src, _ = source(httpx.ConnectError("no route"))
        with pytest.raises(PriceSourceError, match="Could not reach"):
            src.quote("SPY")

    def test_server_error(self):
        src, _ = source(httpx.Response(503, text="oops"))
        with pytest.raises(PriceSourceError, match="503"):
            src.quote("SPY")

    def test_non_json_reply(self):
        src, _ = source(httpx.Response(200, text="<html>consent page</html>"))
        with pytest.raises(PriceSourceError, match="Unexpected"):
            src.quote("SPY")

    def test_unauthorized_is_not_unknown_symbol(self):
        body = {"finance": {"result": None, "error": {"code": "Unauthorized", "description": "Invalid Crumb"}}}
        src, _ = source(httpx.Response(401, json=body))
        with pytest.raises(PriceSourceError) as info:
            src.quote("SPY")
        assert not isinstance(info.value, UnknownSymbol)

    def test_missing_market_price_falls_back_to_last_bar(self):
        rec = copy.deepcopy(load("quote_SPY"))
        del rec["body"]["chart"]["result"][0]["meta"]["regularMarketPrice"]
        src, _ = source(rec)
        q = src.quote("SPY")
        assert q.price == pytest.approx(624.76)
        assert q.previous_close == pytest.approx(608.27, abs=1e-3)

    def test_price_moved_past_last_bar(self):
        # After hours the price can differ from the day's bar; the bar is then the previous close
        rec = copy.deepcopy(load("quote_SPY"))
        rec["body"]["chart"]["result"][0]["meta"]["regularMarketPrice"] = 640.0
        src, _ = source(rec)
        q = src.quote("SPY")
        assert q.previous_close == pytest.approx(624.76)

    def test_quotes_skips_unknown(self):
        src, _ = source(load("quote_SPY"), load("quote_unknown"), load("quote_VTSAX"))
        got = src.quotes(["SPY", "NOSUCHSYMBOLX", "VTSAX"])
        assert sorted(got) == ["SPY", "VTSAX"]

    def test_polite_spacing(self):
        sleeps = []
        clock = iter([0.0, 0.1, 0.1, 0.4])
        replay = Replay(load("quote_SPY"), load("quote_SPY"))
        src = YahooPriceSource(transport=httpx.MockTransport(replay), min_interval=0.25,
                               sleep=sleeps.append, monotonic=lambda: next(clock))
        src.quote("SPY")
        src.quote("SPY")
        assert sleeps == [pytest.approx(0.15)]


class TestHistory:
    def test_range_with_holiday(self):
        src, replay = source(load("history_SPY_2020"))
        s = src.history("SPY", dt.date(2020, 3, 2), dt.date(2020, 4, 14))
        dates = [b.date for b in s.bars]
        assert dates[0] == dt.date(2020, 3, 2)
        assert dates[-1] == dt.date(2020, 4, 14)
        assert dt.date(2020, 4, 10) not in dates  # Good Friday
        assert dt.date(2020, 4, 9) in dates and dt.date(2020, 4, 13) in dates
        assert all(d.weekday() < 5 for d in dates)
        assert all(b.adjclose < b.close for b in s.bars)  # dividends since then
        params = replay.requests[0].url.params
        assert params["events"] == "div|split" and params["interval"] == "1d"
        assert int(params["period1"]) == int(dt.datetime(2020, 3, 2, tzinfo=dt.UTC).timestamp())
        assert int(params["period2"]) == int(dt.datetime(2020, 4, 15, tzinfo=dt.UTC).timestamp())

    def test_trims_to_requested_range(self):
        src, _ = source(load("history_SPY_2020"))
        s = src.history("SPY", dt.date(2020, 3, 10), dt.date(2020, 3, 12))
        assert [b.date.day for b in s.bars] == [10, 11, 12]

    def test_split_is_already_adjusted(self):
        # Yahoo's close is split-adjusted (only adjclose adds dividends), so
        # AAPL's 4:1 split on 2020-08-31 needs no handling of our own
        src, _ = source(load("history_AAPL_split"))
        s = src.history("AAPL", dt.date(2020, 8, 3), dt.date(2020, 9, 4))
        before = next(b for b in s.bars if b.date == dt.date(2020, 8, 28))
        after = next(b for b in s.bars if b.date == dt.date(2020, 8, 31))
        assert 0.9 < after.close / before.close < 1.1
        assert 0.9 < after.adjclose / before.adjclose < 1.1

    def test_gaps_skipped(self):
        rec = copy.deepcopy(load("history_SPY_2020"))
        result = rec["body"]["chart"]["result"][0]
        result["indicators"]["quote"][0]["close"][3] = None
        result["indicators"]["adjclose"][0]["adjclose"][5] = None
        src, _ = source(rec)
        s = src.history("SPY", dt.date(2020, 3, 2), dt.date(2020, 4, 14))
        assert len(s) == len(result["timestamp"]) - 1  # null close dropped
        bar5 = s.bars[4]
        assert bar5.adjclose == bar5.close  # null adjclose falls back to close

    def test_no_adjclose_block(self):
        rec = copy.deepcopy(load("history_SPY_2020"))
        del rec["body"]["chart"]["result"][0]["indicators"]["adjclose"]
        src, _ = source(rec)
        s = src.history("SPY", dt.date(2020, 3, 2), dt.date(2020, 4, 14))
        assert all(b.adjclose == b.close for b in s.bars)

    def test_before_listing_is_empty(self):
        src, _ = source(load("history_VOO_prelisting"))
        s = src.history("VOO", dt.date(2008, 1, 1), dt.date(2008, 12, 31))
        assert s.symbol == "VOO" and len(s) == 0

    def test_empty_result_without_timestamps(self):
        rec = copy.deepcopy(load("history_SPY_2020"))
        result = rec["body"]["chart"]["result"][0]
        del result["timestamp"]
        result["indicators"] = {"quote": [{}]}
        src, _ = source(rec)
        assert len(src.history("SPY", dt.date(2020, 3, 2), dt.date(2020, 4, 14))) == 0

    def test_unknown_symbol(self):
        src, _ = source(load("quote_unknown"))
        with pytest.raises(UnknownSymbol):
            src.history("NOSUCHSYMBOLX", dt.date(2020, 1, 1), dt.date(2020, 2, 1))

    def test_inverted_range_makes_no_request(self):
        src, replay = source()
        assert len(src.history("SPY", dt.date(2020, 2, 1), dt.date(2020, 1, 1))) == 0
        assert replay.requests == []

    def test_other_chart_error(self):
        body = {"chart": {"result": None, "error": {"code": "Bad Request", "description": "Invalid interval"}}}
        src, _ = source(httpx.Response(400, json=body))
        with pytest.raises(PriceSourceError, match="Invalid interval"):
            src.history("SPY", dt.date(2020, 1, 1), dt.date(2020, 2, 1))


class TestSearch:
    def test_hits(self):
        src, replay = source(load("search_vanguard_total"))
        hits = src.search("vanguard total", limit=10)
        syms = [h.symbol for h in hits]
        assert syms[:2] == ["VXUS", "VT"]
        assert "BND" in syms
        assert hits[0].name == "Vanguard Total International Stock Index Fund ETF Shares"
        assert hits[0].instrument_type == "ETF"
        assert hits[0].exchange == "NASDAQ"
        params = replay.requests[0].url.params
        assert params["q"] == "vanguard total" and params["newsCount"] == "0"

    def test_limit(self):
        src, _ = source(load("search_vanguard_total"))
        assert len(src.search("vanguard total", limit=2)) == 2

    def test_nothing_found(self):
        src, _ = source(load("search_nothing"))
        assert src.search("zzqqxxnotathing") == []

    def test_blank_query_makes_no_request(self):
        src, replay = source()
        assert src.search("   ") == []
        assert replay.requests == []

    def test_skips_entries_without_symbol(self):
        body = {"quotes": [{"shortname": "News thing"}, {"symbol": "VOO", "shortname": "Vanguard S&P"}]}
        src, _ = source(httpx.Response(200, json=body))
        assert [h.symbol for h in src.search("voo")] == ["VOO"]

    def test_rate_limited(self):
        src, _ = source(load("rate_limited"))
        with pytest.raises(RateLimited):
            src.search("voo")
