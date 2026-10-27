""""What if?" history backtests.

Pick a saved portfolio, an example or a quick mix of symbols, and a date
range (a preset or your own dates).  The page charts what the money would
have grown to next to a benchmark (SPY unless changed), with a metrics table
and a per-holding table.  It is all buy and hold with dividends reinvested
(adjusted closes), computed by investaround.analytics.

Query parameters (a GET form, so every result has an address to share):

  what       p:<portfolio id> | e:<example id> | custom
  portfolio, example   shortcuts for what=p:... / e:... (the Examples page
             links to ?example=<id>)
  symbols    the custom mix: "VTI 60, BND 40", or "VTI, BND" for equal weights
  range      a key of PRESETS, or "custom" with start= and end= (YYYY-MM-DD)
  benchmark  symbol to compare with, default SPY
"""

from __future__ import annotations

import datetime as dt
import logging
import math
import re
from dataclasses import dataclass, field

from flask import Blueprint, render_template, request

from ..analytics import AnalyticsError, Comparison, Metrics, ValueSeries, compare_to_benchmark, metrics
from ..analytics import portfolio_value_series
from ..app import get_prices, get_store
from ..models import DEFAULT_START_CASH, MAX_HOLDINGS, Holding, PriceSeries, ValidationError, normalize_symbol
from ..prices.base import PriceSource, PriceSourceError, UnknownSymbol
from ..storage import PortfolioNotFound
from .examples import get_example, load_examples

log = logging.getLogger(__name__)

bp = Blueprint("history", __name__, url_prefix="/history")

DEFAULT_BENCHMARK = "SPY"
BENCHMARK_NAMES = {"SPY": "S&P 500", "VOO": "S&P 500", "VTI": "US total market", "QQQ": "Nasdaq-100"}
DEFAULT_RANGE = "10y"
DEFAULT_EXAMPLE = "three-fund"
MAX_CHART_POINTS = 1000


@dataclass(frozen=True)
class Preset:
    key: str
    label: str
    blurb: str
    years: int | None = None  # back from today
    start: dt.date | None = None  # fixed window (both None and years None: as far back as known)
    end: dt.date | None = None


PRESETS = (
    Preset("1y", "1 year", "The last 12 months", years=1),
    Preset("5y", "5 years", "The last 5 years", years=5),
    Preset("10y", "10 years", "The last 10 years", years=10),
    Preset("max", "Max", "As far back as the prices go"),
    Preset("2008", "2008 crash", "Oct 2007 to Dec 2012: the financial-crisis fall and the slow climb back",
           start=dt.date(2007, 10, 1), end=dt.date(2012, 12, 31)),
    Preset("2020", "2020 crash", "Jan to Dec 2020: the sudden Covid fall and the fast rebound",
           start=dt.date(2020, 1, 1), end=dt.date(2020, 12, 31)),
    Preset("2022", "2022 bear", "Jan 2022 to Dec 2023: stocks and bonds fell together, then recovered",
           start=dt.date(2022, 1, 1), end=dt.date(2023, 12, 31)),
)
PRESETS_BY_KEY = {p.key: p for p in PRESETS}


# ------------------------------------------------------------ formatting

def fmt_date(d: dt.date | None) -> str:
    return "" if d is None else f"{d:%b} {d.day}, {d.year}"


def fmt_money(x: float) -> str:
    return f"-${-x:,.0f}" if x < -0.005 else f"${abs(x):,.0f}"


def fmt_signed_money(x: float) -> str:
    return fmt_money(x) if x < -0.005 else f"+${x:,.0f}"


def fmt_pct(x: float | None, signed: bool = True) -> str:
    if x is None:
        return "n/a"
    return f"{x * 100:+.1f}%" if signed else f"{x * 100:.1f}%"


def fmt_weight(x: float) -> str:
    """A weight fraction as a percent, without a needless ".0"."""
    return f"{x * 100:.1f}".removesuffix(".0") + "%"


def sign_class(x: float | None) -> str:
    if x is None or abs(x) < 1e-9:
        return ""
    return "up" if x > 0 else "down"


# ------------------------------------------------------------ inputs

def years_before(d: dt.date, n: int) -> dt.date:
    try:
        return d.replace(year=d.year - n)
    except ValueError:  # Feb 29
        return d.replace(year=d.year - n, day=28)


def resolve_range(key: str, start: str, end: str, today: dt.date) -> tuple[dt.date | None, dt.date]:
    """(start, end) for a preset key or a custom range; start None means as far back as known."""
    if key == "custom":
        try:
            s = dt.date.fromisoformat(start.strip())
            e = dt.date.fromisoformat(end.strip()) if end.strip() else today
        except ValueError:
            raise ValidationError("Give the dates as year-month-day, like 2015-06-30") from None
        e = min(e, today)
        if s >= e:
            raise ValidationError("The start date must be before the end date (and before today)")
        return s, e
    try:
        p = PRESETS_BY_KEY[key]
    except KeyError:
        raise ValidationError(f"Unknown date range {key!r}") from None
    if p.years:
        return years_before(today, p.years), today
    if p.start:
        return p.start, min(p.end, today)
    return None, today


_MIX_ITEM = re.compile(r"^(?P<sym>[^\s:=]+)(?:\s*[:=]?\s*(?P<w>\d+(?:\.\d+)?)\s*%?)?$")


def parse_mix(text: str) -> tuple[list[Holding], str | None]:
    """Holdings from "VTI 60, BND 40" (or "VTI, BND" for equal weights), plus
    a note when the weights had to be scaled to add up to 100%."""
    items = [t.strip() for t in re.split(r"[,;\n]+", text or "") if t.strip()]
    if not items:
        raise ValidationError("Type one or more symbols, like VTI 60, BND 40")
    if len(items) > MAX_HOLDINGS:
        raise ValidationError(f"At most {MAX_HOLDINGS} symbols")
    parsed = []
    for item in items:
        m = _MIX_ITEM.match(item)
        if not m:
            raise ValidationError(f"Could not read {item!r}: write a symbol, then a weight if you like (VTI 60)")
        weight = float(m["w"]) if m["w"] else None
        if weight is not None and weight <= 0:
            raise ValidationError(f"{item!r}: the weight must be above 0")
        parsed.append((normalize_symbol(m["sym"]), weight))
    syms = [s for s, _ in parsed]
    dupes = sorted({s for s in syms if syms.count(s) > 1})
    if dupes:
        raise ValidationError(f"Listed more than once: {', '.join(dupes)}")
    weights = [w for _, w in parsed]
    if all(w is None for w in weights):
        return [Holding(s, weight=100 / len(parsed)) for s in syms], None
    if any(w is None for w in weights):
        raise ValidationError("Give a weight for every symbol, or for none of them (to split evenly)")
    total = sum(weights)
    note = None
    if abs(total - 100) > 0.01:
        note = f"Your weights added up to {total:g}%, so they were scaled to make 100%."
    return [Holding(s, weight=w * 100 / total) for s, w in parsed], note


@dataclass
class Subject:
    """What is being tested."""

    what: str  # the form value: p:<id>, e:<id> or custom
    name: str
    holdings: list[Holding]
    start_cash: float = DEFAULT_START_CASH


@dataclass
class Form:
    what: str
    symbols: str
    range: str
    start: str
    end: str
    benchmark: str
    submitted: bool
    errors: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def read_form(args) -> Form:
    what = args.get("what", "").strip()
    if not what:
        if args.get("portfolio"):
            what = "p:" + args["portfolio"].strip()
        elif args.get("example"):
            what = "e:" + args["example"].strip()
        elif args.get("symbols", "").strip():
            what = "custom"
    submitted = bool(what)
    return Form(
        what=what, symbols=args.get("symbols", "").strip(),
        range=args.get("range", "").strip() or DEFAULT_RANGE,
        start=args.get("start", "").strip(), end=args.get("end", "").strip(),
        benchmark=args.get("benchmark", "").strip() or DEFAULT_BENCHMARK,
        submitted=submitted)


def resolve_subject(form: Form) -> Subject | None:
    """The subject the form names, or None with the reason in form.errors."""
    kind, _, key = form.what.partition(":")
    if form.what == "custom":
        try:
            holdings, note = parse_mix(form.symbols)
        except ValidationError as exc:
            form.errors["symbols"] = str(exc)
            return None
        if note:
            form.notes.append(note)
        return Subject("custom", "Your mix", holdings)
    if kind == "p":
        try:
            p = get_store().get(key)
        except PortfolioNotFound:
            form.errors["what"] = "That portfolio is not in My portfolios any more. Pick another one."
            return None
        return Subject(form.what, p.name, p.holdings, p.start_cash)
    if kind == "e":
        try:
            ex = get_example(key)
        except KeyError:
            form.errors["what"] = "There is no example by that name. Pick one from the list."
            return None
        return Subject(form.what, ex.name, [Holding(h.symbol, weight=h.weight) for h in ex.holdings])
    form.errors["what"] = "Pick a portfolio, an example or your own mix."
    return None


# ------------------------------------------------------------ running

class PriceTrouble(Exception):
    """Prices could not be fetched; the message is for the user."""


def fetch_histories(prices: PriceSource, symbols: list[str], start: dt.date | None,
                    end: dt.date) -> tuple[dict[str, PriceSeries], list[str]]:
    """Price series by symbol, and the symbols the source does not know."""
    out: dict[str, PriceSeries] = {}
    unknown: list[str] = []
    for sym in symbols:
        try:
            out[sym] = prices.history(sym, start, end)
        except UnknownSymbol:
            unknown.append(sym)
        except PriceSourceError as exc:
            log.warning("History for %s failed: %s", sym, exc)
            raise PriceTrouble(f"Could not get prices for {sym} right now ({exc}). Try again in a minute.") from exc
    return out, unknown


def thin(n: int, limit: int = MAX_CHART_POINTS) -> list[int]:
    """Indices of at most about ``limit`` evenly spread points, always keeping the last."""
    step = max(1, math.ceil(n / limit))
    idx = list(range(0, n, step))
    if idx[-1] != n - 1:
        idx.append(n - 1)
    return idx


@dataclass
class Result:
    subject: Subject
    series: ValueSeries
    metrics: Metrics
    comparison: Comparison | None
    benchmark: str
    benchmark_name: str
    benchmark_problem: str | None
    start: dt.date | None  # as asked; None for "as far back as known"
    end: dt.date


def run(subject: Subject, start: dt.date | None, end: dt.date, benchmark: str, form: Form) -> Result | None:
    prices = get_prices()
    symbols = [h.symbol for h in subject.holdings]
    try:
        series, unknown = fetch_histories(prices, symbols, start, end)
    except PriceTrouble as exc:
        form.errors["prices"] = str(exc)
        return None
    if unknown:
        key = "symbols" if subject.what == "custom" else "prices"
        form.errors[key] = (f"No prices are known for {', '.join(unknown)}. "
                            "Check the spelling, or look the symbol up on the My portfolios page.")
        return None
    try:
        vs = portfolio_value_series(subject.holdings, series, subject.start_cash, start, end)
    except AnalyticsError as exc:
        log.info("No backtest for %s %s..%s: %s", symbols, start, end, exc)
        form.errors["prices"] = (f"None of these have prices between {fmt_date(start) or 'the start'} "
                                 f"and {fmt_date(end)}. Try a later range.")
        return None

    comparison = None
    problem = None
    try:
        bench = prices.history(benchmark, vs.start - dt.timedelta(days=7), vs.end)
        comparison = compare_to_benchmark(vs, bench)
    except UnknownSymbol:
        form.errors["benchmark"] = f"No prices are known for {benchmark}, so there is no comparison."
    except PriceSourceError as exc:
        log.warning("Benchmark %s failed: %s", benchmark, exc)
        problem = f"Could not get {benchmark} prices right now, so there is no comparison this time."
    except AnalyticsError:
        problem = f"{benchmark} has no prices in this range, so there is no comparison."
    return Result(subject=subject, series=vs, metrics=comparison.portfolio if comparison else metrics(vs),
                  comparison=comparison, benchmark=benchmark,
                  benchmark_name=BENCHMARK_NAMES.get(benchmark, benchmark),
                  benchmark_problem=problem, start=start, end=end)


# ------------------------------------------------------------ view models

def start_notes(r: Result) -> list[str]:
    """Plain words for holdings that started late or had no prices at all."""
    vs = r.series
    out = []
    for sym, first in sorted(vs.late_starts.items(), key=lambda kv: kv[1]):
        out.append(f"{sym} has no prices before {fmt_date(first)}, so its {fmt_weight(vs.weights[sym])} "
                   f"({fmt_money(vs.weights[sym] * vs.total_deposited)}) waited as cash until then "
                   "and was invested at that day's price.")
    for sym in vs.no_data:
        if sym in vs.weights:
            out.append(f"{sym} has no prices at all in this range, so its {fmt_weight(vs.weights[sym])} "
                       f"({fmt_money(vs.weights[sym] * vs.total_deposited)}) stayed as cash the whole time. "
                       "Try a later start to include it.")
        else:  # share holdings with no price to cost them at are left out
            out.append(f"{sym} has no prices at all in this range, so it is left out.")
    if r.comparison:
        for sym, first in r.comparison.benchmark_series.late_starts.items():
            out.append(f"The comparison, {sym}, has no prices before {fmt_date(first)}, "
                       "so its money waited as cash until then.")
    return out


METRIC_TIPS = {
    "final": "What the money would be worth on the last day, with dividends reinvested.",
    "gain": "How much more (or less) than the money put in, in dollars and as a percent.",
    "cagr": ("The steady yearly rate that turns the starting money into the ending money. "
             "Shows n/a for ranges under a year, where a yearly rate would mislead."),
    "vol": ("How much the value bounced around, as a yearly figure. Higher means a bumpier ride: "
            "about 15-20% is typical for a stock fund, about 5% for a bond fund."),
    "dd": ("The biggest fall from a high point to a later low, and when it got back to that high. "
           "It shows how much nerve it took to hold on."),
    "best": "The best full calendar year in the range. Shows n/a when the range has no full year.",
    "worst": "The worst full calendar year in the range. Shows n/a when the range has no full year.",
}


def metric_cells(m: Metrics) -> dict[str, dict]:
    dd = m.max_drawdown
    if dd is None:
        dd_text, dd_detail = "None", "It never fell below where it started."
    else:
        dd_text = fmt_pct(dd.depth)
        recovered = (f"back by {fmt_date(dd.recovered)}" if dd.recovered else "not back to that high yet")
        dd_detail = f"{fmt_date(dd.peak)} to {fmt_date(dd.trough)}, {recovered}"

    def year(y):
        return ("n/a", "") if y is None else (fmt_pct(y.ret), str(y.year))

    best, best_detail = year(m.best_year)
    worst, worst_detail = year(m.worst_year)
    return {
        "final": {"text": fmt_money(m.final_value), "cls": ""},
        "gain": {"text": fmt_signed_money(m.gain), "detail": fmt_pct(m.total_return), "cls": sign_class(m.gain)},
        "cagr": {"text": fmt_pct(m.cagr), "cls": sign_class(m.cagr)},
        "vol": {"text": fmt_pct(m.volatility, False), "cls": ""},
        "dd": {"text": dd_text, "detail": dd_detail, "cls": "down" if dd else ""},
        "best": {"text": best, "detail": best_detail, "cls": sign_class(m.best_year and m.best_year.ret)},
        "worst": {"text": worst, "detail": worst_detail, "cls": sign_class(m.worst_year and m.worst_year.ret)},
    }


METRIC_ROWS = (
    ("final", "Worth at the end"),
    ("gain", "Gain or loss"),
    ("cagr", "Yearly growth rate"),
    ("vol", "Ups and downs (volatility)"),
    ("dd", "Worst drop"),
    ("best", "Best year"),
    ("worst", "Worst year"),
)


def holding_rows(r: Result) -> list[dict]:
    vs = r.series
    rows = []
    for h in r.metrics.holdings:
        if h.started is None:
            started = "No prices: kept as cash"
        elif h.symbol in vs.late_starts:
            started = f"{fmt_date(h.started)} (late)"
        else:
            started = fmt_date(h.started)
        rows.append({
            "symbol": h.symbol, "weight": fmt_weight(h.weight), "started": started,
            "late": h.symbol in vs.late_starts or h.started is None,
            "invested": fmt_money(h.invested), "final": fmt_money(h.final_value),
            "gain": fmt_signed_money(h.gain), "gain_cls": sign_class(h.gain),
            "own": fmt_pct(h.price_return), "own_cls": sign_class(h.price_return),
            "contribution": fmt_pct(h.contribution), "contribution_cls": sign_class(h.contribution),
        })
    return rows


def chart_data(r: Result) -> dict:
    vs = r.series
    idx = thin(len(vs.dates))
    bench = r.comparison.benchmark_series.values if r.comparison else None
    return {
        "dates": [vs.dates[i].isoformat() for i in idx],
        "values": [round(vs.values[i], 2) for i in idx],
        "benchmark": [round(bench[i], 2) for i in idx] if bench else None,
        "label": r.subject.name,
        "benchmarkLabel": f"{r.benchmark} ({r.benchmark_name})" if r.benchmark_name != r.benchmark else r.benchmark,
        "years": (vs.end - vs.start).days / 365.25,
    }


# ------------------------------------------------------------ view

@bp.get("/")
def index():
    prices = get_prices()
    # The fake source has a frozen "today"; real sources use the real one.
    today = getattr(prices, "today", None) or dt.date.today()
    form = read_form(request.args)
    portfolios = get_store().list()
    examples = load_examples()
    if not form.what:
        form.what = f"p:{portfolios[0].id}" if portfolios else f"e:{DEFAULT_EXAMPLE}"

    result = None
    if form.submitted:
        try:
            benchmark = normalize_symbol(form.benchmark)
        except ValidationError as exc:
            form.errors["benchmark"] = str(exc)
            benchmark = None
        try:
            start, end = resolve_range(form.range, form.start, form.end, today)
        except ValidationError as exc:
            form.errors["range"] = str(exc)
            start = end = None
        subject = resolve_subject(form)
        if subject and benchmark and end and not form.errors:
            result = run(subject, start, end, benchmark, form)

    ctx = {"form": form, "portfolios": portfolios, "examples": examples, "presets": PRESETS,
           "result": result, "today": today, "fmt_date": fmt_date, "fmt_money": fmt_money}
    if result:
        ctx.update(
            start_notes=start_notes(result), metric_rows=METRIC_ROWS, metric_tips=METRIC_TIPS,
            cells=metric_cells(result.metrics),
            bench_cells=metric_cells(result.comparison.benchmark) if result.comparison else None,
            holding_rows=holding_rows(result), chart_data=chart_data(result),
            preset=PRESETS_BY_KEY.get(form.range))
    return render_template("history/index.html", **ctx)
