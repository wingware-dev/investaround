"""Portfolio performance: value series and the numbers people ask about.

Pure functions over PriceSeries, with no Flask and no I/O.  Everything runs
on adjusted closes, so dividends and splits count (total return).  Yahoo's
``close`` is already split-adjusted and ``adjclose`` adds dividends on top,
so no split handling is needed here; share counts are on today's split basis.

The core is simulate(): it walks a trading calendar day by day, holding units
of each symbol plus cash, and applies deposits, scheduled buys and optional
rebalancing.  Buy & hold, rebalancing and dollar-cost averaging in
strategies.py are all schedules fed to it.

A symbol with no price yet on the first day "starts late": its share of the
money waits as cash until its first price, then is invested.  A symbol with
no prices at all in the range keeps its share as cash throughout.  Both are
reported on the ValueSeries so the UI can say so.
"""

from __future__ import annotations

import datetime as dt
import math
import statistics
from bisect import bisect_left
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from ..models import DEFAULT_START_CASH, Holding, PriceSeries

TRADING_DAYS_PER_YEAR = 252
DAYS_PER_YEAR = 365.25
REBALANCE_PERIODS = ("monthly", "quarterly", "yearly")

# How far before the first calendar day a price may come from and still count
# as "available on day one" (covers holidays that differ between markets)
_LOOKBACK = dt.timedelta(days=7)


class AnalyticsError(ValueError):
    """Raised when there is not enough data or the inputs make no sense."""


@dataclass
class ValueSeries:
    """Day-by-day state of a simulated portfolio, all lists aligned to ``dates``."""

    dates: list[dt.date]
    values: list[float]
    holdings: dict[str, list[float]]  # value of each holding
    cash: list[float]  # money not invested (waiting to be, or reserved)
    deposits: list[float]  # money added from outside on each date
    buys: list[float]  # money moved from cash into holdings on schedule
    prices: dict[str, list[float | None]]  # adjusted close, forward-filled
    net_invested: dict[str, float]  # money put into each holding, less sales
    weights: dict[str, float]  # target weights as fractions summing to 1
    late_starts: dict[str, dt.date]  # symbol -> first date it had a price
    no_data: list[str]  # symbols with no prices at all in the range

    @property
    def start(self) -> dt.date:
        return self.dates[0]

    @property
    def end(self) -> dt.date:
        return self.dates[-1]

    @property
    def total_deposited(self) -> float:
        return sum(self.deposits)

    @property
    def final_value(self) -> float:
        return self.values[-1]


@dataclass(frozen=True)
class Drawdown:
    depth: float  # fraction, negative (-0.25 is a 25% fall)
    peak: dt.date
    trough: dt.date
    recovered: dt.date | None  # first date back at the peak, None if not yet


@dataclass(frozen=True)
class YearReturn:
    year: int
    ret: float
    partial: bool  # range starts or ends partway through the year


@dataclass(frozen=True)
class HoldingContribution:
    symbol: str
    weight: float  # target weight, fraction
    invested: float  # money put in, less sales
    final_value: float
    gain: float
    contribution: float  # gain as a fraction of all money deposited
    price_return: float | None  # the symbol's own total return while held
    started: dt.date | None  # first date with a price, None if never


@dataclass(frozen=True)
class Metrics:
    start: dt.date
    end: dt.date
    years: float
    deposited: float
    final_value: float
    gain: float
    total_return: float  # final value / money deposited - 1
    time_weighted_return: float  # growth ignoring when money came in
    cagr: float | None  # yearly rate, None under a year
    volatility: float | None  # annualized standard deviation of daily returns
    max_drawdown: Drawdown | None  # None if it never fell
    yearly: list[YearReturn]
    best_year: YearReturn | None  # among full calendar years only
    worst_year: YearReturn | None
    holdings: list[HoldingContribution]


@dataclass(frozen=True)
class Comparison:
    portfolio: Metrics
    benchmark: Metrics
    benchmark_symbol: str
    benchmark_series: ValueSeries  # same dates and money flows as the portfolio
    excess_return: float  # portfolio total return minus benchmark's
    excess_cagr: float | None


# ---------------------------------------------------------------------------
# Building value series


def normalize_weights(weights: Mapping[str, float]) -> dict[str, float]:
    """Scale weights (any units, say percent) to fractions summing to 1."""
    if not weights:
        raise AnalyticsError("No holdings given")
    for sym, w in weights.items():
        if not w or w < 0 or not math.isfinite(w):
            raise AnalyticsError(f"{sym}: weight must be above 0")
    total = sum(weights.values())
    return {sym: w / total for sym, w in weights.items()}


def trading_calendar(series: Iterable[PriceSeries | None], start: dt.date | None = None,
                     end: dt.date | None = None) -> list[dt.date]:
    """Every date any of the series has a price on, within [start, end]."""
    dates = set()
    for s in series:
        if s is None:
            continue
        dates.update(b.date for b in s.bars
                     if (start is None or b.date >= start) and (end is None or b.date <= end))
    return sorted(dates)


def _aligned(series: PriceSeries | None, calendar: Sequence[dt.date],
             attr: str = "adjclose") -> list[float | None]:
    """Prices on each calendar date, forward-filled; None before the first."""
    out: list[float | None] = []
    if series is None or not calendar:
        return [None] * len(calendar)
    earliest = calendar[0] - _LOOKBACK
    bars = [b for b in series.bars if earliest <= b.date <= calendar[-1]]
    j = 0
    last = None
    for d in calendar:
        while j < len(bars) and bars[j].date <= d:
            last = getattr(bars[j], attr)
            j += 1
        out.append(last)
    return out


def _on_calendar(schedule: Mapping[dt.date, float], calendar: Sequence[dt.date]) -> list[float]:
    """Amounts per calendar date; each lands on the first trading day on or
    after its date, and amounts after the last day are dropped."""
    out = [0.0] * len(calendar)
    for d, amount in schedule.items():
        if amount < 0:
            raise AnalyticsError("Amounts must not be negative")
        i = bisect_left(calendar, d)
        if i < len(calendar):
            out[i] += amount
    return out


def _period(d: dt.date, rebalance: str) -> tuple[int, int]:
    if rebalance == "monthly":
        return d.year, d.month
    if rebalance == "quarterly":
        return d.year, (d.month - 1) // 3
    return d.year, 0


def simulate(prices: Mapping[str, PriceSeries], weights: Mapping[str, float], *,
             deposits: Mapping[dt.date, float], buys: Mapping[dt.date, float] | None = None,
             rebalance: str | None = None, start: dt.date | None = None, end: dt.date | None = None,
             calendar: Sequence[dt.date] | None = None) -> ValueSeries:
    """Run a portfolio over time.

    ``deposits``: money added from outside, by date.  ``buys``: money moved
    from cash into the holdings (split by weight), by date; by default each
    deposit is invested at once.  Dates land on the first trading day on or
    after them; a date before the range lands on its first day.
    ``rebalance``: one of REBALANCE_PERIODS, to reset the holdings to their
    weights on the first trading day of each new period.  ``calendar``: the
    dates to run on; by default every date any holding has a price on
    within [start, end].
    """
    w = normalize_weights(weights)
    if rebalance is not None and rebalance not in REBALANCE_PERIODS:
        raise AnalyticsError(f"Unknown rebalancing period {rebalance!r}")
    if calendar is None:
        calendar = trading_calendar((prices.get(s) for s in w), start, end)
    calendar = list(calendar)
    if not calendar:
        raise AnalyticsError("No prices in that date range")
    n = len(calendar)
    px = {s: _aligned(prices.get(s), calendar) for s in w}
    dep = _on_calendar(deposits, calendar)
    buy = list(dep) if buys is None else _on_calendar(buys, calendar)
    if dep[0] <= 0:
        raise AnalyticsError("Nothing is deposited on the first day")

    units = dict.fromkeys(w, 0.0)
    pending = dict.fromkeys(w, 0.0)  # cash set aside for symbols with no price yet
    net = dict.fromkeys(w, 0.0)
    reserve = 0.0  # cash not yet scheduled to be invested
    values: list[float] = []
    cash: list[float] = []
    bought: list[float] = []
    hold: dict[str, list[float]] = {s: [] for s in w}

    for i, d in enumerate(calendar):
        reserve += dep[i]

        # Symbols that just got their first price buy what was set aside
        for s in w:
            p = px[s][i]
            if pending[s] and p is not None:
                units[s] += pending[s] / p
                net[s] += pending[s]
                pending[s] = 0.0

        amount = 0.0
        if buy[i]:
            # Snap to the whole reserve when within rounding of it, so
            # installments that add up to it leave no dust behind
            amount = reserve if buy[i] >= reserve * (1 - 1e-12) else buy[i]
            reserve -= amount
            for s, ws in w.items():
                part = ws * amount
                p = px[s][i]
                if p is None:
                    pending[s] += part
                else:
                    units[s] += part / p
                    net[s] += part
        bought.append(amount)

        if rebalance and i > 0 and _period(d, rebalance) != _period(calendar[i - 1], rebalance):
            invested = sum(pending.values()) + sum(
                units[s] * px[s][i] for s in w if px[s][i] is not None)
            for s, ws in w.items():
                target = ws * invested
                p = px[s][i]
                if p is None:
                    pending[s] = target
                else:
                    net[s] += target - units[s] * p
                    units[s] = target / p

        total = 0.0
        for s in w:
            p = px[s][i]
            v = units[s] * p if p is not None else 0.0
            hold[s].append(v)
            total += v
        c = reserve + sum(pending.values())
        cash.append(c)
        values.append(total + c)

    late_starts = {}
    no_data = []
    for s in w:
        first = next((i for i in range(n) if px[s][i] is not None), None)
        if first is None:
            no_data.append(s)
        elif first > 0:
            late_starts[s] = calendar[first]

    return ValueSeries(dates=calendar, values=values, holdings=hold, cash=cash, deposits=dep,
                       buys=bought, prices=px, net_invested=net, weights=w,
                       late_starts=late_starts, no_data=no_data)


def portfolio_value_series(holdings: Sequence[Holding], prices: Mapping[str, PriceSeries],
                           start_cash: float = DEFAULT_START_CASH, start: dt.date | None = None,
                           end: dt.date | None = None) -> ValueSeries:
    """Buy & hold of a saved portfolio's holdings.

    Weighted holdings split ``start_cash`` by weight on the first day.  Share
    holdings start with that many shares, bought at each symbol's first close
    in the range, and ``start_cash`` is not used.
    """
    if not holdings:
        raise AnalyticsError("No holdings given")
    if all(h.weight is not None for h in holdings):
        if not start_cash or start_cash <= 0:
            raise AnalyticsError("Starting cash must be above 0")
        return simulate(prices, {h.symbol: h.weight for h in holdings},
                        deposits={dt.date.min: start_cash}, start=start, end=end)
    if not all(h.shares is not None for h in holdings):
        raise AnalyticsError("Use weights for every holding or share counts for every holding")

    calendar = trading_calendar((prices.get(h.symbol) for h in holdings), start, end)
    cost = {}
    unpriced = []
    for h in holdings:
        first_close = next((c for c in _aligned(prices.get(h.symbol), calendar, "close")
                            if c is not None), None)
        if first_close is None:
            unpriced.append(h.symbol)
        else:
            cost[h.symbol] = h.shares * first_close
    if not cost:
        raise AnalyticsError("No prices in that date range")
    vs = simulate(prices, cost, deposits={dt.date.min: sum(cost.values())}, calendar=calendar)
    vs.no_data.extend(unpriced)
    return vs


# ---------------------------------------------------------------------------
# Measuring them


def daily_returns(vs: ValueSeries) -> list[float]:
    """Return from each date to the next, not counting money deposited."""
    out = []
    for i in range(1, len(vs.values)):
        out.append((vs.values[i] - vs.deposits[i]) / vs.values[i - 1] - 1)
    return out


def growth_index(vs: ValueSeries) -> list[float]:
    """Growth of 1 (time-weighted), aligned to vs.dates."""
    idx = [1.0]
    for r in daily_returns(vs):
        idx.append(idx[-1] * (1 + r))
    return idx


def max_drawdown(dates: Sequence[dt.date], index: Sequence[float]) -> Drawdown | None:
    """Largest fall from a high to a later low, or None if it never fell."""
    peak = 0
    depth, at_peak, at_trough = 0.0, 0, 0
    for i, v in enumerate(index):
        if v > index[peak]:
            peak = i
        dd = v / index[peak] - 1
        if dd < depth:
            depth, at_peak, at_trough = dd, peak, i
    if depth >= 0:
        return None
    level = index[at_peak] * (1 - 1e-12)
    recovered = next((dates[j] for j in range(at_trough + 1, len(index)) if index[j] >= level), None)
    return Drawdown(depth, dates[at_peak], dates[at_trough], recovered)


def yearly_returns(dates: Sequence[dt.date], index: Sequence[float]) -> list[YearReturn]:
    """Calendar-year returns.  The first and last years are partial when the
    range starts after the first week of January or ends before Christmas."""
    last_of_year: dict[int, int] = {}
    for i, d in enumerate(dates):
        last_of_year[d.year] = i
    years = sorted(last_of_year)
    out = []
    base = index[0]
    for y in years:
        i = last_of_year[y]
        partial = ((y == years[0] and dates[0] > dt.date(y, 1, 7))
                   or (y == years[-1] and dates[-1] < dt.date(y, 12, 24)))
        out.append(YearReturn(y, index[i] / base - 1, partial))
        base = index[i]
    return out


def metrics(vs: ValueSeries) -> Metrics:
    idx = growth_index(vs)
    rets = daily_returns(vs)
    years = (vs.end - vs.start).days / DAYS_PER_YEAR
    twr = idx[-1] - 1
    deposited = vs.total_deposited
    gain = vs.final_value - deposited
    yearly = yearly_returns(vs.dates, idx)
    full = [y for y in yearly if not y.partial]

    holdings = []
    for s, wt in vs.weights.items():
        final = vs.holdings[s][-1]
        known = [p for p in vs.prices[s] if p is not None]
        started = next((d for d, p in zip(vs.dates, vs.prices[s]) if p is not None), None)
        hgain = final - vs.net_invested[s]
        holdings.append(HoldingContribution(
            symbol=s, weight=wt, invested=vs.net_invested[s], final_value=final, gain=hgain,
            contribution=hgain / deposited,
            price_return=known[-1] / known[0] - 1 if known else None, started=started))

    return Metrics(
        start=vs.start, end=vs.end, years=years, deposited=deposited, final_value=vs.final_value,
        gain=gain, total_return=gain / deposited, time_weighted_return=twr,
        cagr=(1 + twr) ** (1 / years) - 1 if years >= 1 else None,
        volatility=statistics.stdev(rets) * math.sqrt(TRADING_DAYS_PER_YEAR) if len(rets) >= 2 else None,
        max_drawdown=max_drawdown(vs.dates, idx), yearly=yearly,
        best_year=max(full, key=lambda y: y.ret) if full else None,
        worst_year=min(full, key=lambda y: y.ret) if full else None,
        holdings=holdings)


def benchmark_series(vs: ValueSeries, benchmark: PriceSeries) -> ValueSeries:
    """What the same money, put in on the same days, would have done in the
    benchmark alone."""
    bs = simulate({benchmark.symbol: benchmark}, {benchmark.symbol: 1.0},
                  deposits=dict(zip(vs.dates, vs.deposits)), buys=dict(zip(vs.dates, vs.buys)),
                  calendar=vs.dates)
    if bs.no_data:
        raise AnalyticsError(f"No {benchmark.symbol} prices in that date range")
    return bs


def compare_to_benchmark(vs: ValueSeries, benchmark: PriceSeries) -> Comparison:
    bs = benchmark_series(vs, benchmark)
    pm, bm = metrics(vs), metrics(bs)
    return Comparison(
        portfolio=pm, benchmark=bm, benchmark_symbol=benchmark.symbol, benchmark_series=bs,
        excess_return=pm.total_return - bm.total_return,
        excess_cagr=pm.cagr - bm.cagr if pm.cagr is not None and bm.cagr is not None else None)
