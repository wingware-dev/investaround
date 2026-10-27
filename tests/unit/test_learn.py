"""Strategy lab logic and views, on small synthetic prices and the fake source."""

import datetime as dt
import re

import pytest

from investaround.app import create_app
from investaround.models import Holding, Portfolio, PriceBar, PriceSeries
from investaround.prices.fake import FakePriceSource
from investaround.web.learn import chart_data, explain, final_mix, range_dates, run_lab


def series(symbol, start, closes):
    bars = []
    d = start
    for c in closes:
        while d.weekday() >= 5:
            d += dt.timedelta(days=1)
        bars.append(PriceBar(date=d, close=c, adjclose=c))
        d += dt.timedelta(days=1)
    return PriceSeries(symbol, bars)


def monthly(symbol, start, closes):
    """One bar on the first weekday of each month."""
    bars = []
    for i, c in enumerate(closes):
        y, m = divmod(start.month - 1 + i, 12)
        d = dt.date(start.year + y, m + 1, 1)
        while d.weekday() >= 5:
            d += dt.timedelta(days=1)
        bars.append(PriceBar(date=d, close=c, adjclose=c))
    return PriceSeries(symbol, bars)


START = dt.date(2020, 1, 1)


def test_rising_market_lump_sum_wins_and_explanation_says_why():
    prices = {"A": monthly("A", START, [100 + 10 * i for i in range(13)])}
    r = run_lab(prices, {"A": 100}, START, dt.date(2021, 12, 31), months=12)
    assert [s.key for s in r.strategies] == ["lump_sum", "dca", "rebalance_yearly"]
    assert r.winner == "lump"
    assert r.lump.metrics.final_value == pytest.approx(22_000)
    assert r.difference > 0
    text = " ".join(explain(r))
    assert "at once ended $" in text and "ahead of spreading it over 12 months" in text
    assert "earns nothing (0%)" in text and "toward putting it all in at once" in text
    assert "only one holding there is nothing to rebalance" in text


def test_falling_then_rising_market_spreading_out_wins():
    closes = [100, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 100]
    r = run_lab({"A": monthly("A", START, closes)}, {"A": 100}, START, dt.date(2021, 12, 31), months=12)
    assert r.winner == "dca"
    assert "ahead of putting it all in at once" in explain(r)[0]


def test_rebalancing_two_holdings_reports_the_drift():
    a = monthly("A", START, [100 * 1.05 ** i for i in range(25)])
    b = monthly("B", START, [100] * 25)
    r = run_lab({"A": a, "B": b}, {"A": 50, "B": 50}, START, dt.date(2022, 1, 31), period="yearly")
    drift = final_mix(r.lump)
    assert drift["A"] > 0.7 and drift["A"] + drift["B"] == pytest.approx(1)
    text = " ".join(explain(r))
    assert "Rebalancing yearly ended $" in text and "behind leaving the mix alone" in text
    assert "drifted from 50% A / 50% B at the start to 76% A / 24% B" in text


def test_chart_data_is_month_end_values_for_each_strategy():
    prices = {"A": series("A", START, [100 + i for i in range(60)])}
    r = run_lab(prices, {"A": 100}, START, dt.date(2020, 12, 31), months=3)
    d = chart_data(r)
    assert d["months"] == ["2020-01", "2020-02", "2020-03"]
    assert [s["key"] for s in d["series"]] == ["lump_sum", "dca", "rebalance_yearly"]
    assert d["series"][0]["values"][-1] == pytest.approx(r.lump.metrics.final_value, abs=0.01)
    # The spread-out strategy has invested a third more each month.
    assert d["invested"] == pytest.approx([10_000 / 3, 20_000 / 3, 10_000], abs=0.01)


def test_range_dates():
    today = dt.date(2026, 10, 27)
    assert range_dates("10y", today) == (dt.date(2016, 10, 27), today)
    assert range_dates("5y", dt.date(2028, 2, 29)) == (dt.date(2023, 2, 28), dt.date(2028, 2, 29))
    assert range_dates("2008", today) == (dt.date(2007, 10, 9), dt.date(2012, 12, 31))


@pytest.fixture
def app(tmp_path):
    return create_app({"DATA_DIR": str(tmp_path / "data"), "PRICE_SOURCE": "fake", "TESTING": True})


def test_lab_runs_a_saved_share_count_portfolio(app):
    p = Portfolio(name="My shares", holdings=[Holding("SPY", shares=10), Holding("BND", shares=30)])
    app.extensions["investaround.store"].add(p)
    html = app.test_client().get(f"/learn/lab?portfolio=portfolio:{p.id}&range=5y").get_data(as_text=True)
    assert '<optgroup label="My portfolios">' in html
    assert f'value="portfolio:{p.id}" selected' in html
    assert "My shares: $10,000 from" in html
    assert "What this shows" in html


def test_lab_bad_choices_fall_back_to_defaults(app):
    html = app.test_client().get("/learn/lab?portfolio=nope&range=99y&months=7&period=daily").get_data(as_text=True)
    assert 'value="example:sixty-forty" selected' in html
    assert re.search(r'value="10y"[^>]*selected', html)
    assert 'value="12" selected' in html
    assert 'value="yearly" selected' in html
    assert "What this shows" in html


def test_lab_without_prices_says_so(tmp_path):
    app = create_app({"DATA_DIR": str(tmp_path / "data"), "TESTING": True,
                      "PRICE_SOURCE_OBJ": FakePriceSource(fail_symbols={"BND"})})
    resp = app.test_client().get("/learn/lab")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'id="lab-error"' in html and "Could not get prices right now" in html
    assert "What this shows" not in html
