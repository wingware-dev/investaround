"""Home dashboard: every portfolio at a glance and a "start here" path.

Each portfolio row shows the same value, today's change and gain as its
watch page (from ``portfolios.value_portfolio``) plus a sparkline of what
its current holdings did over the last ``SPARK_DAYS`` days.  The sparkline
is drawn server-side as an inline SVG, so it needs no JavaScript.

The page also says where prices come from and how fresh they are, and puts
an error banner across the top when they could not be had.
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass

from flask import Blueprint, render_template

from ..analytics.performance import AnalyticsError, portfolio_value_series
from ..app import get_prices, get_store
from ..models import DEFAULT_START_CASH, Portfolio
from ..prices.base import PriceSource, PriceSourceError
from .portfolios import PortfolioValue, direction, dollars, money, pct, value_portfolio

log = logging.getLogger(__name__)

bp = Blueprint("home", __name__)

SPARK_DAYS = 91
SPARK_WIDTH = 120
SPARK_HEIGHT = 32
SPARK_PAD = 2


@dataclass
class Sparkline:
    points: str  # SVG polyline points
    first: float
    last: float
    start: dt.date
    end: dt.date

    @property
    def change_pct(self) -> float:
        return (self.last / self.first - 1) * 100 if self.first else 0.0

    @property
    def label(self) -> str:
        return (f"{pct(self.change_pct)} from {self.start.strftime('%b %-d')} "
                f"to {self.end.strftime('%b %-d, %Y')}")


def sparkline_points(values: list[float], width: int = SPARK_WIDTH, height: int = SPARK_HEIGHT,
                     pad: int = SPARK_PAD) -> str:
    """SVG polyline points scaling ``values`` to fill the box, highest at the top."""
    if len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    span = hi - lo or 1.0
    step = (width - 2 * pad) / (len(values) - 1)
    inner = height - 2 * pad
    return " ".join(f"{pad + i * step:.1f},{pad + (hi - v) / span * inner:.1f}" for i, v in enumerate(values))


def today_for(prices: PriceSource) -> dt.date:
    # The fake source has a frozen "today"; real sources use the real one.
    return getattr(prices, "today", None) or dt.date.today()


def sparkline(p: Portfolio, prices: PriceSource, end: dt.date, days: int = SPARK_DAYS) -> Sparkline | None:
    """Buy and hold of ``p``'s holdings over the ``days`` up to ``end``; None when prices are missing."""
    start = end - dt.timedelta(days=days)
    try:
        series = {h.symbol: prices.history(h.symbol, start, end) for h in p.holdings}
        vs = portfolio_value_series(p.holdings, series, p.start_cash, start, end)
    except (PriceSourceError, AnalyticsError) as exc:
        log.warning("No sparkline for %s: %s", p.name, exc)
        return None
    if len(vs.values) < 2:
        return None
    return Sparkline(sparkline_points(vs.values), vs.values[0], vs.values[-1], vs.start, vs.end)


@dataclass
class Row:
    pv: PortfolioValue
    spark: Sparkline | None


@dataclass
class Totals:
    value: float | None
    day_change: float | None
    day_change_pct: float | None
    unpriced: int = 0  # portfolios left out for want of prices


def totals(values: list[PortfolioValue]) -> Totals:
    priced = [pv for pv in values if pv.value is not None]
    value = sum(pv.value for pv in priced) if priced else None
    changes = [pv.day_change for pv in priced if pv.day_change is not None]
    day = sum(changes) if changes else None
    day_pct = None
    if day is not None and value and value != day:
        day_pct = day / (value - day) * 100
    return Totals(value, day, day_pct, len(values) - len(priced))


@dataclass
class SourceStatus:
    name: str
    description: str
    as_of: dt.datetime | None
    errors: list[str]


def source_status(prices: PriceSource, values: list[PortfolioValue]) -> SourceStatus:
    stamps = [pv.prices_as_of for pv in values if pv.prices_as_of is not None]
    errors = sorted({pv.error for pv in values if pv.error})
    if prices.name == "fake":
        desc = f"Made-up sample prices, frozen at {today_for(prices).strftime('%b %-d, %Y')}"
    elif prices.name == "yahoo":
        desc = "Yahoo Finance (free and unofficial; prices may be 15 minutes or more behind)"
    else:
        desc = prices.name
    return SourceStatus(prices.name, desc, max(stamps) if stamps else None, errors)


@bp.get("/")
def index():
    prices = get_prices()
    portfolios = get_store().list()
    end = today_for(prices)
    values = [value_portfolio(p, prices) for p in portfolios]
    rows = [Row(pv, sparkline(pv.portfolio, prices, end) if not pv.error else None) for pv in values]
    return render_template(
        "home/index.html", rows=rows, totals=totals(values), status=source_status(prices, values),
        spark_days=SPARK_DAYS, spark_width=SPARK_WIDTH, spark_height=SPARK_HEIGHT, start_cash=DEFAULT_START_CASH,
        money=money, dollars=dollars, pct=pct, direction=direction,
    )
