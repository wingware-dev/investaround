"""Investing strategies, each a money schedule run through simulate().

- buy_and_hold: invest everything on day one and leave it.
- rebalanced: as buy & hold, but reset to the target weights every month,
  quarter or year.
- dollar_cost_average: invest a fixed amount on the first trading day of
  every month.
- lump_sum_vs_dca: the same pot of money invested all at once, or spread
  over some months with the rest waiting as cash.

``weights`` everywhere maps symbol to weight in any units (percent is fine).
Each takes an optional keyword ``cash_rate`` for interest on uninvested cash
(see performance.py); the default 0 means cash earns nothing.
"""

from __future__ import annotations

import datetime as dt
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ..models import DEFAULT_START_CASH, PriceSeries
from .performance import (
    REBALANCE_PERIODS, AnalyticsError, Metrics, ValueSeries, metrics, simulate, trading_calendar,
)


@dataclass(frozen=True)
class StrategyResult:
    key: str  # stable id, e.g. "rebalance_quarterly"
    label: str  # for people, e.g. "Rebalance quarterly"
    series: ValueSeries
    metrics: Metrics


@dataclass(frozen=True)
class LumpSumVsDca:
    lump: StrategyResult
    dca: StrategyResult
    months: int
    difference: float  # lump sum final value minus DCA final value
    winner: str  # "lump", "dca" or "tie"


def _calendar(prices: Mapping[str, PriceSeries], weights: Mapping[str, float],
              start: dt.date | None, end: dt.date | None) -> list[dt.date]:
    cal = trading_calendar((prices.get(s) for s in weights), start, end)
    if not cal:
        raise AnalyticsError("No prices in that date range")
    return cal


def month_starts(calendar: Sequence[dt.date]) -> list[dt.date]:
    """The first calendar date, then the first trading day of each later month."""
    return [d for i, d in enumerate(calendar)
            if i == 0 or (d.year, d.month) != (calendar[i - 1].year, calendar[i - 1].month)]


def _result(key: str, label: str, vs: ValueSeries) -> StrategyResult:
    return StrategyResult(key, label, vs, metrics(vs))


def buy_and_hold(prices: Mapping[str, PriceSeries], weights: Mapping[str, float],
                 amount: float = DEFAULT_START_CASH, start: dt.date | None = None,
                 end: dt.date | None = None, *,
                 cash_rate: float | PriceSeries = 0.0) -> StrategyResult:
    if amount <= 0:
        raise AnalyticsError("Amount must be above 0")
    vs = simulate(prices, weights, deposits={dt.date.min: amount}, start=start, end=end,
                  cash_rate=cash_rate)
    return _result("buy_and_hold", "Buy & hold", vs)


def rebalanced(prices: Mapping[str, PriceSeries], weights: Mapping[str, float], period: str,
               amount: float = DEFAULT_START_CASH, start: dt.date | None = None,
               end: dt.date | None = None, *,
               cash_rate: float | PriceSeries = 0.0) -> StrategyResult:
    if period not in REBALANCE_PERIODS:
        raise AnalyticsError(f"Unknown rebalancing period {period!r}")
    if amount <= 0:
        raise AnalyticsError("Amount must be above 0")
    vs = simulate(prices, weights, deposits={dt.date.min: amount}, rebalance=period,
                  start=start, end=end, cash_rate=cash_rate)
    return _result(f"rebalance_{period}", f"Rebalance {period}", vs)


def dollar_cost_average(prices: Mapping[str, PriceSeries], weights: Mapping[str, float],
                        monthly_amount: float, start: dt.date | None = None,
                        end: dt.date | None = None, initial: float = 0.0,
                        rebalance: str | None = None, *,
                        cash_rate: float | PriceSeries = 0.0) -> StrategyResult:
    """``initial`` (if any) plus ``monthly_amount`` on the first day, then
    ``monthly_amount`` on the first trading day of each later month."""
    if monthly_amount <= 0:
        raise AnalyticsError("Monthly amount must be above 0")
    if initial < 0:
        raise AnalyticsError("Initial amount must not be negative")
    cal = _calendar(prices, weights, start, end)
    deposits = {d: monthly_amount for d in month_starts(cal)}
    deposits[cal[0]] += initial
    vs = simulate(prices, weights, deposits=deposits, rebalance=rebalance, calendar=cal,
                  cash_rate=cash_rate)
    return _result("dca", f"Invest {monthly_amount:,.0f} a month", vs)


def lump_sum_vs_dca(prices: Mapping[str, PriceSeries], weights: Mapping[str, float],
                    total: float = DEFAULT_START_CASH, months: int = 12,
                    start: dt.date | None = None, end: dt.date | None = None, *,
                    cash_rate: float | PriceSeries = 0.0) -> LumpSumVsDca:
    """Both start with ``total`` in hand.  DCA invests it in ``months`` equal
    parts on the first trading day of each month; whatever the range is too
    short to invest stays as cash.  With ``cash_rate`` the waiting cash earns
    interest, and the last part invests all that is left."""
    if total <= 0:
        raise AnalyticsError("Amount must be above 0")
    if months < 1:
        raise AnalyticsError("Spread over at least one month")
    cal = _calendar(prices, weights, start, end)
    lump = simulate(prices, weights, deposits={cal[0]: total}, calendar=cal, cash_rate=cash_rate)
    buys = {d: total / months for d in month_starts(cal)[:months]}
    if len(buys) == months:
        # simulate() caps a buy at the cash on hand, so this sweeps in the interest
        buys[max(buys)] = math.inf
    dca = simulate(prices, weights, deposits={cal[0]: total}, buys=buys, calendar=cal,
                   cash_rate=cash_rate)
    diff = lump.final_value - dca.final_value
    tol = 1e-9 * total
    return LumpSumVsDca(
        lump=_result("lump_sum", "All at once", lump),
        dca=_result("dca", f"Spread over {months} month{'s' if months != 1 else ''}", dca),
        months=months, difference=diff,
        winner="tie" if abs(diff) <= tol else "lump" if diff > 0 else "dca")
