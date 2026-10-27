"""Lessons, glossary and the strategy lab.

``/learn/`` is static teaching text (lessons and a glossary).  ``/learn/lab``
runs the same pot of money three ways over a chosen range, using
analytics.strategies:

- all at once (buy & hold),
- spread over some months (dollar-cost averaging, the rest waiting as cash),
- all at once, rebalanced back to the target weights every period,

and shows them side by side with a plain "what this shows" explanation built
from the results.  The lab is pure GET: the form's choices are in the URL, so
a result can be bookmarked or linked to; the Examples gallery links each card
to ``/learn/lab?portfolio=example:<id>``.
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass

from flask import Blueprint, render_template, request

from ..analytics.performance import REBALANCE_PERIODS, AnalyticsError
from ..analytics.strategies import StrategyResult, lump_sum_vs_dca, rebalanced
from ..app import get_prices, get_store
from ..models import DEFAULT_START_CASH, PriceSeries
from ..prices.base import PriceSource, PriceSourceError
from .examples import load_examples

log = logging.getLogger(__name__)

bp = Blueprint("learn", __name__, url_prefix="/learn")

LAB_AMOUNT = DEFAULT_START_CASH
DCA_MONTHS = (3, 6, 12, 24)
DEFAULT_DCA_MONTHS = 12
DEFAULT_PERIOD = "yearly"


# The picker offers the example portfolios (web/examples.py), then the user's own.
EXAMPLE_PREFIX = "example:"
PORTFOLIO_PREFIX = "portfolio:"
DEFAULT_CHOICE = EXAMPLE_PREFIX + "sixty-forty"


@dataclass(frozen=True)
class Range:
    id: str
    label: str
    why: str  # one line on what makes the range interesting


RANGES = (
    Range("5y", "Last 5 years", "A recent stretch."),
    Range("10y", "Last 10 years", "A long, mostly rising decade."),
    Range("15y", "Last 15 years", "Long enough to include several scares."),
    Range("2008", "2008 crash (Oct 2007 – 2012)", "Started right at a market top, then the worst crash in decades."),
    Range("2020", "2020 crash (Feb 2020 – 2021)", "A fast, deep fall and a fast recovery."),
    Range("2022", "2022 bear market (2022 – 2024)", "Stocks and bonds fell together, then recovered."),
)
DEFAULT_RANGE = "10y"

_FIXED_RANGES = {
    "2008": (dt.date(2007, 10, 9), dt.date(2012, 12, 31)),
    "2020": (dt.date(2020, 2, 19), dt.date(2021, 12, 31)),
    "2022": (dt.date(2022, 1, 3), dt.date(2024, 12, 31)),
}


def range_dates(range_id: str, today: dt.date) -> tuple[dt.date, dt.date]:
    if range_id in _FIXED_RANGES:
        return _FIXED_RANGES[range_id]
    years = int(range_id.rstrip("y"))
    try:
        start = today.replace(year=today.year - years)
    except ValueError:  # 29 February
        start = today.replace(year=today.year - years, day=28)
    return start, today


def _today(prices: PriceSource) -> dt.date:
    # The fake source has a frozen "today"; real sources use the real one.
    return getattr(prices, "today", None) or dt.date.today()


# ------------------------------------------------------------ lab results

@dataclass
class LabResult:
    strategies: list[StrategyResult]  # all at once, spread out, rebalanced
    difference: float  # all at once final value minus spread-out final value
    winner: str  # "lump", "dca" or "tie"
    months: int
    period: str
    start: dt.date
    end: dt.date
    weights: dict[str, float]
    late_starts: dict[str, dt.date]
    no_data: list[str]

    @property
    def lump(self) -> StrategyResult:
        return self.strategies[0]

    @property
    def dca(self) -> StrategyResult:
        return self.strategies[1]

    @property
    def rebalanced(self) -> StrategyResult:
        return self.strategies[2]


def run_lab(prices: dict[str, PriceSeries], weights: dict[str, float], start: dt.date, end: dt.date,
            months: int = DEFAULT_DCA_MONTHS, period: str = DEFAULT_PERIOD,
            amount: float = LAB_AMOUNT) -> LabResult:
    """The three strategies for one pot of money; raises AnalyticsError."""
    vs = lump_sum_vs_dca(prices, weights, total=amount, months=months, start=start, end=end)
    reb = rebalanced(prices, weights, period, amount=amount, start=start, end=end)
    s = vs.lump.series
    return LabResult(
        strategies=[vs.lump, vs.dca, reb], difference=vs.difference, winner=vs.winner,
        months=months, period=period, start=s.start, end=s.end, weights=dict(weights),
        late_starts=dict(s.late_starts), no_data=list(s.no_data))


def explain(r: LabResult) -> list[str]:
    """Plain-English paragraphs on what the results show."""
    lump, dca, reb = r.lump.metrics, r.dca.metrics, r.rebalanced.metrics
    out = []
    spread = f"spreading it over {r.months} month{'s' if r.months != 1 else ''}"
    if r.winner == "tie":
        out.append(f"Putting all the money in at once and {spread} ended up the same.")
    elif r.winner == "lump":
        out.append(f"Putting all the money in at once ended {_money(r.difference)} ahead of {spread}. "
                   "That is the usual result: markets rise more often than they fall, so money that "
                   "waits on the side usually misses some growth.")
    else:
        out.append(f"{spread.capitalize()} ended {_money(-r.difference)} ahead of putting it all in at once. "
                   "That happens when prices fall soon after the start: the money that waited bought "
                   "in cheaper.")
    if lump.max_drawdown and dca.max_drawdown:
        out.append(f"The worst drop was {_pct(lump.max_drawdown.depth)} all at once and "
                   f"{_pct(dca.max_drawdown.depth)} spread out. Spreading out mostly buys peace of mind: "
                   "if a crash comes right after you start, less of your money is in it.")
    out.append("In this lab, money waiting to be invested earns nothing (0%). That tilts the comparison "
               "slightly toward putting it all in at once; in real life the waiting money could earn a "
               "little interest in a savings account.")

    if len(r.weights) == 1:
        out.append("With only one holding there is nothing to rebalance, so the rebalanced result is the "
                   "same as all at once. Pick a mix of two or more to see what rebalancing does.")
    else:
        diff = reb.final_value - lump.final_value
        ahead = "ahead of" if diff > 0 else "behind"
        line = (f"Rebalancing {r.period} ended {_money(abs(diff))} {ahead} leaving the mix alone"
                if abs(diff) >= 1 else f"Rebalancing {r.period} ended about level with leaving the mix alone")
        if reb.volatility is not None and lump.volatility is not None:
            calmer = "a little calmer" if reb.volatility < lump.volatility else "a little bumpier"
            line += (f", and the ride was {calmer} (ups and downs of {_pct(reb.volatility, signed=False)} "
                     f"a year versus {_pct(lump.volatility, signed=False)})")
        out.append(line + ". Rebalancing sells some of whatever has grown and buys what has lagged, to keep "
                   "the mix you chose. Its job is to stop one holding from quietly taking over and making "
                   "the portfolio riskier than you meant, not to raise returns.")
        drift = final_mix(r.lump)
        target = {s: w / sum(r.weights.values()) for s, w in r.weights.items()}
        out.append("Left alone, the mix drifted from " + _mix(target) + " at the start to "
                   + _mix(drift) + " by the end.")
    out.append("This is one stretch of history. A different start date can flip any of these results, "
               "so try a few ranges before drawing conclusions.")
    return out


def final_mix(s: StrategyResult) -> dict[str, float]:
    """Each holding's share of the invested value on the last day, as fractions."""
    last = {sym: vals[-1] for sym, vals in s.series.holdings.items()}
    total = sum(last.values())
    return {sym: v / total for sym, v in last.items()} if total else {}


def _mix(fractions: dict[str, float]) -> str:
    return " / ".join(f"{w * 100:.0f}% {sym}" for sym, w in fractions.items())


def _money(x: float) -> str:
    return f"${x:,.0f}"


def _pct(x: float, signed: bool = True) -> str:
    return f"{x * 100:+.1f}%" if signed else f"{x * 100:.1f}%"


def chart_data(r: LabResult) -> dict:
    """Month-end values of each strategy, for learn.js."""
    months: list[str] = []
    idx: list[int] = []
    for i, d in enumerate(r.lump.series.dates):
        m = d.strftime("%Y-%m")
        if months and months[-1] == m:
            idx[-1] = i
        else:
            months.append(m)
            idx.append(i)
    return {
        "months": months,
        "series": [{"key": s.key, "label": s.label,
                    "values": [round(s.series.values[i], 2) for i in idx]} for s in r.strategies],
        "invested": [round(sum(r.dca.series.buys[:i + 1]), 2) for i in idx],
    }


# ------------------------------------------------------------ choices

@dataclass(frozen=True)
class Choice:
    value: str  # "example:<id>" or "portfolio:<id>"
    name: str
    weights: dict[str, float] | None  # None for share-count portfolios: priced at the start
    shares: dict[str, float] | None = None


def lab_choices() -> list[Choice]:
    out = [Choice(EXAMPLE_PREFIX + ex.id, ex.name, {h.symbol: h.weight for h in ex.holdings})
           for ex in load_examples()]
    for p in get_store().list():
        if p.holdings and all(h.weight is not None for h in p.holdings):
            out.append(Choice(PORTFOLIO_PREFIX + p.id, p.name, {h.symbol: h.weight for h in p.holdings}))
        elif p.holdings and all(h.shares is not None for h in p.holdings):
            out.append(Choice(PORTFOLIO_PREFIX + p.id, p.name, None, {h.symbol: h.shares for h in p.holdings}))
    return out


def _weights_from_shares(shares: dict[str, float], prices: dict[str, PriceSeries]) -> dict[str, float]:
    """Each holding's value at its first price in the range."""
    out = {}
    for sym, n in shares.items():
        bars = prices[sym].bars
        if bars and n > 0:
            out[sym] = n * bars[0].close
    if not out:
        raise AnalyticsError("No prices in that date range")
    return out


def _arg(name: str, allowed, default):
    value = request.args.get(name, default)
    return value if value in allowed else default


# ------------------------------------------------------------ views

@bp.get("/")
def index():
    return render_template("learn/index.html")


@bp.get("/lab")
def lab():
    choices = lab_choices()
    by_value = {c.value: c for c in choices}
    choice = by_value[_arg("portfolio", by_value, DEFAULT_CHOICE)]
    range_id = _arg("range", {r.id for r in RANGES}, DEFAULT_RANGE)
    try:
        months = int(request.args.get("months", DEFAULT_DCA_MONTHS))
    except ValueError:
        months = DEFAULT_DCA_MONTHS
    if months not in DCA_MONTHS:
        months = DEFAULT_DCA_MONTHS
    period = _arg("period", REBALANCE_PERIODS, DEFAULT_PERIOD)

    src = get_prices()
    start, end = range_dates(range_id, _today(src))
    result = error = None
    symbols = list(choice.weights or choice.shares)
    try:
        prices = {s: src.history(s, start, end) for s in symbols}
        weights = choice.weights or _weights_from_shares(choice.shares, prices)
        result = run_lab(prices, weights, start, end, months=months, period=period)
    except PriceSourceError as exc:
        log.warning("Strategy lab: no prices for %s: %s", ", ".join(symbols), exc)
        error = f"Could not get prices right now: {exc}"
    except AnalyticsError as exc:
        error = f"Can't run this one: {exc}. Try a later range or a different portfolio."

    return render_template(
        "learn/lab.html",
        examples=[c for c in choices if c.value.startswith(EXAMPLE_PREFIX)],
        mine=[c for c in choices if c.value.startswith(PORTFOLIO_PREFIX)], choice=choice, ranges=RANGES, range_id=range_id,
        dca_months=DCA_MONTHS, months=months, periods=REBALANCE_PERIODS, period=period,
        amount=LAB_AMOUNT, result=result, error=error,
        explanation=explain(result) if result else [],
        chart=chart_data(result) if result else None,
    )
