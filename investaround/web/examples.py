"""Example portfolios gallery.

The examples live in ``investaround/examples/examples.json``.  Each card
shows the idea, its risks, the holdings and a mini chart of what $10,000
would have grown to over the last ``CHART_YEARS`` years (buy and hold, with
dividends reinvested via adjusted closes), against the S&P 500.

Other features can use ``load_examples()`` and ``get_example(id)``; the
"See how it would have done" button links to ``history.index`` with
``?example=<id>``.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from flask import Blueprint, abort, redirect, render_template, request, url_for

from ..app import get_prices, get_store
from ..models import DEFAULT_START_CASH, Holding, Portfolio
from ..prices.base import PriceSource, PriceSourceError

log = logging.getLogger(__name__)

bp = Blueprint("examples", __name__, url_prefix="/examples")

EXAMPLES_PATH = Path(__file__).resolve().parent.parent / "examples" / "examples.json"
CHART_YEARS = 10
BENCHMARK = "SPY"
BENCHMARK_NAME = "S&P 500"


@dataclass(frozen=True)
class ExampleHolding:
    symbol: str
    weight: float
    what: str


@dataclass(frozen=True)
class Example:
    id: str
    name: str
    tagline: str
    idea: str
    risks: str
    holdings: tuple[ExampleHolding, ...]

    @property
    def symbols(self) -> list[str]:
        return [h.symbol for h in self.holdings]

    def to_portfolio(self, taken_names: set[str] = frozenset()) -> Portfolio:
        """A new paper portfolio copied from this example, named so it doesn't clash."""
        name, n = self.name, 2
        while name in taken_names:
            name, n = f"{self.name} ({n})", n + 1
        return Portfolio(
            name=name,
            holdings=[Holding(h.symbol, weight=h.weight) for h in self.holdings],
            notes=f"Copied from the “{self.name}” example.",
            source_example=self.id,
        )


@lru_cache(maxsize=4)
def load_examples(path: Path = EXAMPLES_PATH) -> tuple[Example, ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return tuple(
        Example(
            id=d["id"], name=d["name"], tagline=d["tagline"], idea=d["idea"], risks=d["risks"],
            holdings=tuple(ExampleHolding(h["symbol"], float(h["weight"]), h["what"]) for h in d["holdings"]),
        )
        for d in raw["examples"]
    )


def get_example(example_id: str) -> Example:
    for ex in load_examples():
        if ex.id == example_id:
            return ex
    raise KeyError(example_id)


# ------------------------------------------------------------ growth charts

class NoCommonHistory(Exception):
    """The holdings have no trading days in common in the window."""


@dataclass
class Growth:
    """Buy-and-hold value of ``start_cash``, sampled at each month's last trading day."""

    months: list[str]          # "YYYY-MM"
    values: list[float]
    start: dt.date
    end: dt.date
    final: float
    max_drawdown_pct: float    # worst fall from a previous high, as a negative percent


def buy_and_hold(prices: PriceSource, weights: dict[str, float], start: dt.date, end: dt.date,
                 start_cash: float = DEFAULT_START_CASH) -> Growth:
    """Value of ``start_cash`` split by ``weights`` (percent) on the first common day, then left alone."""
    closes: dict[str, dict[dt.date, float]] = {}
    for sym in weights:
        closes[sym] = {b.date: b.adjclose for b in prices.history(sym, start, end).bars}
    days = sorted(set.intersection(*(set(c) for c in closes.values())))
    if not days:
        raise NoCommonHistory(", ".join(weights))
    first = days[0]
    shares = {s: start_cash * w / 100 / closes[s][first] for s, w in weights.items()}

    months: list[str] = []
    values: list[float] = []
    peak, worst = 0.0, 0.0
    for day in days:
        value = sum(n * closes[s][day] for s, n in shares.items())
        peak = max(peak, value)
        worst = min(worst, value / peak - 1)
        month = day.strftime("%Y-%m")
        if months and months[-1] == month:
            values[-1] = value
        else:
            months.append(month)
            values.append(value)
    return Growth(months, [round(v, 2) for v in values], first, days[-1], values[-1], worst * 100)


def chart_window(prices: PriceSource) -> tuple[dt.date, dt.date]:
    # The fake source has a frozen "today"; real sources use the real one.
    end = getattr(prices, "today", None) or dt.date.today()
    return end.replace(year=end.year - CHART_YEARS), end


def _growth_or_none(prices: PriceSource, weights: dict[str, float], start: dt.date, end: dt.date) -> Growth | None:
    try:
        return buy_and_hold(prices, weights, start, end)
    except (PriceSourceError, NoCommonHistory) as exc:
        log.warning("No growth chart for %s: %s", ", ".join(weights), exc)
        return None


# ------------------------------------------------------------ views

@bp.get("/")
def index():
    prices = get_prices()
    start, end = chart_window(prices)
    benchmark = _growth_or_none(prices, {BENCHMARK: 100}, start, end)
    cards = []
    for ex in load_examples():
        growth = _growth_or_none(prices, {h.symbol: h.weight for h in ex.holdings}, start, end)
        cards.append({"example": ex, "growth": growth})

    chart_data = {}
    bench_by_month = dict(zip(benchmark.months, benchmark.values)) if benchmark else {}
    for card in cards:
        g = card["growth"]
        if g is not None:
            chart_data[card["example"].id] = {
                "months": g.months,
                "values": g.values,
                "benchmark": [bench_by_month.get(m) for m in g.months],
            }

    added = None
    added_id = request.args.get("added")
    if added_id:
        added = next((p for p in get_store().list() if p.id == added_id), None)

    return render_template(
        "examples/index.html",
        cards=cards, benchmark=benchmark, benchmark_name=BENCHMARK_NAME, chart_years=CHART_YEARS,
        start_cash=DEFAULT_START_CASH, chart_data=chart_data, added=added,
    )


@bp.post("/<example_id>/try")
def try_example(example_id: str):
    try:
        ex = get_example(example_id)
    except KeyError:
        abort(404)
    store = get_store()
    portfolio = ex.to_portfolio({p.name for p in store.list()})
    store.add(portfolio)
    return redirect(url_for("examples.index", added=portfolio.id) + f"#example-{ex.id}", code=303)
