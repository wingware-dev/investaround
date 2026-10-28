"""Home dashboard helpers: sparklines, totals and the price-source status."""

import datetime as dt

import pytest

from investaround.models import Holding, Portfolio
from investaround.prices.fake import FakePriceSource
from investaround.web.home import SPARK_HEIGHT, SPARK_PAD, SPARK_WIDTH, source_status, sparkline, sparkline_points, totals
from investaround.web.portfolios import value_portfolio


@pytest.fixture(scope="module")
def prices():
    return FakePriceSource()


def _points(s):
    return [tuple(float(n) for n in pair.split(",")) for pair in s.split()]


def test_sparkline_points_fill_the_box_highest_at_top():
    pts = _points(sparkline_points([10, 30, 20]))
    assert [x for x, _ in pts] == [SPARK_PAD, SPARK_WIDTH / 2, SPARK_WIDTH - SPARK_PAD]
    assert [y for _, y in pts] == [SPARK_HEIGHT - SPARK_PAD, SPARK_PAD, SPARK_HEIGHT / 2]


def test_sparkline_points_flat_and_too_short():
    assert {y for _, y in _points(sparkline_points([5, 5, 5]))} == {SPARK_PAD}
    assert sparkline_points([5]) == ""
    assert sparkline_points([]) == ""


def test_sparkline_follows_the_holdings(prices):
    p = Portfolio("Mix", [Holding("SPY", weight=60), Holding("BND", weight=40)])
    s = sparkline(p, prices, prices.today)
    assert s is not None
    assert s.end <= prices.today
    assert (prices.today - s.start).days <= 91
    assert s.first == pytest.approx(10_000)
    assert len(s.points.split()) > 40  # about one point per trading day
    assert s.label.startswith(("+", "−"))


def test_sparkline_with_share_counts(prices):
    p = Portfolio("Shares", [Holding("AAPL", shares=3), Holding("MSFT", shares=2)])
    assert sparkline(p, prices, prices.today) is not None


def test_sparkline_none_when_prices_fail():
    failing = FakePriceSource(fail_symbols={"BND"})
    p = Portfolio("Mix", [Holding("SPY", weight=60), Holding("BND", weight=40)])
    assert sparkline(p, failing, failing.today) is None


def test_totals_add_up_portfolios(prices):
    a = value_portfolio(Portfolio("A", [Holding("SPY", weight=100)], created=dt.date(2026, 1, 5)), prices)
    b = value_portfolio(Portfolio("B", [Holding("BND", weight=100)], created=dt.date(2026, 1, 5)), prices)
    t = totals([a, b])
    assert t.value == pytest.approx(a.value + b.value)
    assert t.day_change == pytest.approx(a.day_change + b.day_change)
    assert t.day_change_pct == pytest.approx(t.day_change / (t.value - t.day_change) * 100)
    assert t.unpriced == 0


def test_totals_without_prices():
    failing = FakePriceSource(fail_symbols={"SPY"})
    t = totals([value_portfolio(Portfolio("A", [Holding("SPY", weight=100)]), failing)])
    assert (t.value, t.day_change, t.day_change_pct, t.unpriced) == (None, None, None, 1)
    assert totals([]).value is None


def test_source_status_fake_and_errors(prices):
    ok = value_portfolio(Portfolio("A", [Holding("SPY", weight=100)]), prices)
    st = source_status(prices, [ok])
    assert st.name == "fake"
    assert "Made-up sample prices" in st.description
    assert st.errors == []
    assert st.as_of == ok.prices_as_of

    failing = FakePriceSource(fail_symbols={"SPY"})
    bad = value_portfolio(Portfolio("B", [Holding("SPY", weight=100)]), failing)
    st = source_status(failing, [bad, bad])
    assert st.errors == ["Could not get prices right now: Simulated failure for SPY"]


def test_source_status_yahoo_says_it_is_unofficial(prices):
    class Yahooish:
        name = "yahoo"

    assert "unofficial" in source_status(Yahooish(), []).description
