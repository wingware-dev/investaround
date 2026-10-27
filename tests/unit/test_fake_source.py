import datetime as dt

import pytest

from investaround.prices.base import PriceSource, PriceSourceError, UnknownSymbol
from investaround.prices.fake import FakePriceSource

RECORDED = ["AAPL", "AMZN", "BND", "DBC", "GLD", "HD", "IEF", "JNJ", "JPM", "KO",
            "MSFT", "NVDA", "PG", "QQQ", "SCHD", "SPY", "TLT", "VNQ", "VOO", "VTI",
            "VTSAX", "VXUS", "VYM", "WMT", "XOM"]


@pytest.fixture(scope="module")
def src():
    return FakePriceSource()


def test_is_a_price_source(src):
    assert isinstance(src, PriceSource)
    assert src.name == "fake"


def test_has_all_recorded_symbols(src):
    assert src.symbols == RECORDED


def test_quote(src):
    q = src.quote("spy")
    assert q.symbol == "SPY"
    assert q.price > 0 and q.previous_close > 0
    assert q.currency == "USD"
    assert "S&P 500" in q.name
    assert q.instrument_type == "ETF"


def test_quote_matches_last_bar(src):
    for sym in RECORDED:
        q = src.quote(sym)
        s = src.history(sym)
        # Yahoo rounds the live quote a little differently from the bar
        assert q.price == pytest.approx(s.bars[-1].close, rel=1e-5), sym
        assert q.previous_close == pytest.approx(s.bars[-2].close, rel=1e-6), sym


def test_quotes_skips_unknown(src):
    got = src.quotes(["VOO", "NOPE", "bnd"])
    assert sorted(got) == ["BND", "VOO"]


def test_unknown_symbol(src):
    with pytest.raises(UnknownSymbol):
        src.quote("NOPE")
    with pytest.raises(UnknownSymbol):
        src.history("NOPE")


def test_history_is_long_and_sorted(src):
    s = src.history("SPY")
    assert s.first_date <= dt.date(2005, 1, 5)
    assert s.last_date == src.today
    dates = [b.date for b in s.bars]
    assert dates == sorted(dates) and len(set(dates)) == len(dates)
    assert all(b.close > 0 and b.adjclose > 0 for b in s.bars)


def test_history_range(src):
    s = src.history("VOO", dt.date(2020, 3, 1), dt.date(2020, 3, 31))
    assert s.first_date >= dt.date(2020, 3, 1) and s.last_date <= dt.date(2020, 3, 31)
    assert 18 <= len(s) <= 23


def test_history_before_listing_is_empty(src):
    # VOO started trading in September 2010
    assert len(src.history("VOO", dt.date(2008, 1, 1), dt.date(2008, 12, 31))) == 0
    assert src.history("VOO").first_date.year == 2010


def test_search(src):
    assert [h.symbol for h in src.search("VO")][:1] == ["VOO"]
    assert src.search("voo")[0].symbol == "VOO"
    names = {h.symbol for h in src.search("vanguard")}
    assert {"VOO", "VTI", "BND", "VXUS"} <= names
    assert src.search("") == []
    assert src.search("zzzz") == []
    assert len(src.search("v", limit=2)) == 2


def test_fail_symbols(tmp_path):
    src = FakePriceSource(fail_symbols={"spy"})
    with pytest.raises(PriceSourceError):
        src.quote("SPY")
    assert src.quote("VOO").symbol == "VOO"


def test_missing_fixtures(tmp_path):
    with pytest.raises(FileNotFoundError):
        FakePriceSource(tmp_path)
