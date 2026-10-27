"""The "cash earns" option shared by the history page and the strategy lab.

Money waiting to be invested (the spread-out part of dollar-cost averaging,
or a holding's share before its first price) earns nothing unless the user
picks a fixed yearly rate or 13-week US Treasury bill rates.  T-bill rates
come from the price source as ^IRX, yearly yields in percent, which
investaround.analytics takes directly as ``cash_rate``.

Query parameters, the same on both pages:

  cash       none | fixed | tbill   (default none)
  cash_rate  the fixed yearly rate in percent, e.g. 4 or 2.5
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass

from ..analytics import ValueSeries
from ..models import PriceSeries
from ..prices.base import PriceSource, PriceSourceError

log = logging.getLogger(__name__)

TBILL_SYMBOL = "^IRX"
CASH_KINDS = (
    ("none", "Nothing (0%)"),
    ("fixed", "A fixed rate"),
    ("tbill", "Treasury bill rates"),
)
DEFAULT_KIND = "none"
DEFAULT_FIXED_RATE = "4"
MAX_FIXED_RATE = 20.0

CASH_TIP = ("Money that is waiting to be invested sits as cash. In real life it could earn a little "
            "interest in a savings account or money-market fund. Treasury bill rates use the actual "
            "yield of 13-week US government bills on each day.")


@dataclass
class CashForm:
    kind: str
    rate_text: str
    error: str | None = None


def read_cash(args) -> CashForm:
    """The cash choice from query args; an unknown kind falls back to none."""
    kind = args.get("cash", "").strip()
    if kind not in dict(CASH_KINDS):
        kind = DEFAULT_KIND
    text = args.get("cash_rate", "").strip() or DEFAULT_FIXED_RATE
    form = CashForm(kind, text)
    if kind == "fixed":
        try:
            pct = float(text.removesuffix("%").strip())
        except ValueError:
            form.error = "Give the rate as a number of percent a year, like 4 or 2.5"
        else:
            if not 0 <= pct <= MAX_FIXED_RATE:
                form.error = f"Pick a rate from 0% to {MAX_FIXED_RATE:g}% a year"
    return form


@dataclass(frozen=True)
class CashRate:
    kind: str
    rate: float | PriceSeries  # for analytics' cash_rate
    note: str | None = None  # a problem to tell the user, e.g. no T-bill rates

    @property
    def earns(self) -> bool:
        return self.kind != "none"

    def phrase(self, vs: ValueSeries) -> str:
        """What the cash in ``vs`` earned, to finish "waiting cash earned ...":
        "4% a year".  For T-bills, the average yield while cash was waiting."""
        if self.kind == "fixed":
            return f"{self.rate * 100:g}% a year"
        if self.kind == "tbill":
            avg = tbill_average(self.rate, vs)
            return "Treasury bill rates" + (f", about {avg:.1f}% a year on average" if avg is not None else "")
        return "nothing (0%)"


def tbill_average(yields: PriceSeries, vs: ValueSeries) -> float | None:
    """Yield in percent averaged over the days in ``vs``, weighted by the cash
    held each day; None when no cash waited."""
    bars = yields.bars
    j = 0
    last = None
    total = weighted = 0.0
    for d, c in zip(vs.dates, vs.cash):
        while j < len(bars) and bars[j].date <= d:
            last = bars[j].close
            j += 1
        if last is not None and c > 0.005:
            total += c
            weighted += c * last
    return weighted / total if total else None


NO_INTEREST = CashRate("none", 0.0)


def resolve_cash(form: CashForm, prices: PriceSource, start: dt.date | None, end: dt.date) -> CashRate:
    """The rate to run with.  T-bill trouble falls back to 0% with a note."""
    if form.kind == "fixed" and not form.error:
        return CashRate("fixed", float(form.rate_text.removesuffix("%").strip()) / 100)
    if form.kind != "tbill":
        return NO_INTEREST
    try:
        series = prices.history(TBILL_SYMBOL, start - dt.timedelta(days=7) if start else None, end)
    except PriceSourceError as exc:
        log.warning("T-bill rates (%s) failed: %s", TBILL_SYMBOL, exc)
        return CashRate("none", 0.0, "Could not get Treasury bill rates right now, "
                                     "so waiting cash earned nothing this time.")
    if not series.bars:
        return CashRate("none", 0.0, "There are no Treasury bill rates for these dates, "
                                     "so waiting cash earned nothing.")
    return CashRate("tbill", series)
