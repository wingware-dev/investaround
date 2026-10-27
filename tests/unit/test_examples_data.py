"""The example portfolios data and the gallery's buy-and-hold growth."""

import datetime as dt
import json
import re

import pytest

from investaround.models import PriceBar, PriceSeries
from investaround.prices.fake import DEFAULT_FIXTURES, FakePriceSource
from investaround.web.examples import (
    BENCHMARK, CHART_YEARS, EXAMPLES_PATH, NoCommonHistory, buy_and_hold, chart_window, get_example,
    load_examples,
)

EXAMPLES = load_examples()
FIXTURE_SYMBOLS = set(json.loads((DEFAULT_FIXTURES / "quotes.json").read_text())["quotes"])


def test_about_eight_examples_with_unique_ids():
    assert 6 <= len(EXAMPLES) <= 12
    ids = [ex.id for ex in EXAMPLES]
    assert len(set(ids)) == len(ids)
    assert all(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", i) for i in ids)
    assert len({ex.name for ex in EXAMPLES}) == len(EXAMPLES)


@pytest.mark.parametrize("ex", EXAMPLES, ids=lambda ex: ex.id)
def test_every_symbol_has_fixtures(ex):
    for sym in ex.symbols:
        assert sym in FIXTURE_SYMBOLS, f"{ex.id}: {sym} has no quote fixture"
        assert (DEFAULT_FIXTURES / f"{sym}.csv").exists(), f"{ex.id}: {sym} has no price history fixture"


@pytest.mark.parametrize("ex", EXAMPLES, ids=lambda ex: ex.id)
def test_weights_sum_to_100(ex):
    assert sum(h.weight for h in ex.holdings) == pytest.approx(100)


@pytest.mark.parametrize("ex", EXAMPLES, ids=lambda ex: ex.id)
def test_explained_in_words(ex):
    for text in (ex.tagline, ex.idea, ex.risks):
        assert len(text.split()) >= 8
    assert all(h.what for h in ex.holdings)


@pytest.mark.parametrize("ex", EXAMPLES, ids=lambda ex: ex.id)
def test_copies_to_a_valid_portfolio(ex):
    p = ex.to_portfolio()
    p.validate()
    assert p.name == ex.name
    assert p.source_example == ex.id
    assert [h.to_dict() for h in p.holdings] == [{"symbol": h.symbol, "weight": h.weight} for h in ex.holdings]


def test_copy_name_avoids_existing_names():
    ex = get_example("three-fund")
    assert ex.to_portfolio({ex.name}).name == f"{ex.name} (2)"
    assert ex.to_portfolio({ex.name, f"{ex.name} (2)"}).name == f"{ex.name} (3)"


def test_get_example_unknown():
    with pytest.raises(KeyError):
        get_example("no-such-example")


def test_examples_file_has_version():
    assert json.loads(EXAMPLES_PATH.read_text())["version"] == 1


def test_every_example_and_benchmark_charts_over_the_window():
    src = FakePriceSource()
    start, end = chart_window(src)
    assert (start, end) == (src.today.replace(year=src.today.year - CHART_YEARS), src.today)
    for weights in [{BENCHMARK: 100}] + [{h.symbol: h.weight for h in ex.holdings} for ex in EXAMPLES]:
        g = buy_and_hold(src, weights, start, end)
        assert (g.start - start).days < 7 and (end - g.end).days < 7
        assert len(g.months) == len(g.values) >= CHART_YEARS * 12
        assert g.max_drawdown_pct < 0


class _Series:
    """A tiny price source over hand-made adjusted closes."""

    name = "test"

    def __init__(self, data: dict[str, dict[str, float]]) -> None:
        self.data = data

    def history(self, symbol, start=None, end=None):
        bars = [PriceBar(dt.date.fromisoformat(d), c, c) for d, c in self.data[symbol].items()]
        return PriceSeries(symbol, bars).between(start, end)


def test_buy_and_hold_by_hand():
    src = _Series({
        # B has no bar on 01-02, so the first common day is 01-03.
        "A": {"2020-01-02": 5.0, "2020-01-03": 10.0, "2020-01-31": 5.0, "2020-02-03": 20.0},
        "B": {"2020-01-03": 50.0, "2020-01-31": 50.0, "2020-02-03": 100.0},
    })
    g = buy_and_hold(src, {"A": 60, "B": 40}, dt.date(2020, 1, 1), dt.date(2020, 12, 31), start_cash=1000)
    # 600 buys 60 A at 10; 400 buys 8 B at 50.
    assert g.start == dt.date(2020, 1, 3)
    assert g.end == dt.date(2020, 2, 3)
    assert g.months == ["2020-01", "2020-02"]
    assert g.values == [60 * 5 + 8 * 50, 60 * 20 + 8 * 100]   # month-end values: 700, 2000
    assert g.final == 2000
    assert g.max_drawdown_pct == pytest.approx(-30)            # 1000 -> 700


def test_buy_and_hold_no_overlap():
    src = _Series({"A": {"2020-01-02": 1.0}, "B": {"2021-01-04": 1.0}})
    with pytest.raises(NoCommonHistory):
        buy_and_hold(src, {"A": 50, "B": 50}, dt.date(2020, 1, 1), dt.date(2021, 12, 31))
