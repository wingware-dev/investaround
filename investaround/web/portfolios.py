"""Build, edit and watch paper portfolios.

Each portfolio starts with ``start_cash`` (normally $10,000) of pretend money
split over its holdings by weight.  It is "bought" at each holding's last
closing price *before* the day it was created, so the starting point never
moves once set, and on the first day the gain since start equals today's
change.  That price and its date are recorded on each holding when the
portfolio is saved (and on first view for portfolios saved without them).
Values use the ratio of the current price to the start day's adjusted
close, re-fetched for that exact day, so dividends and splits since then
count toward the gain; if that bar can't be had the recorded price is used.

Changing the holdings or weights of a saved portfolio starts it again from
the day of the change; renaming it or editing its notes does not.

Also serves ``/api/search?q=...`` (symbol search for the builder) at the
site root, outside this blueprint's ``/portfolios`` prefix.
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass, field

from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from ..app import get_prices, get_store
from ..models import (DEFAULT_START_CASH, MAX_HOLDINGS, SUGGESTED_MIN_HOLDINGS, Holding, Portfolio, PriceBar,
                      Quote, ValidationError, normalize_symbol)
from ..prices.base import PriceSource, PriceSourceError
from ..storage import PortfolioNotFound

log = logging.getLogger(__name__)

bp = Blueprint("portfolios", __name__, url_prefix="/portfolios")

# How far back to look for the closing price a portfolio starts from.
START_LOOKBACK_DAYS = 14
SEARCH_LIMIT = 8
MAX_QUERY_LEN = 60


# ------------------------------------------------------------ valuation

@dataclass
class HoldingValue:
    symbol: str
    name: str = ""
    weight: float | None = None
    shares: float | None = None
    price: float | None = None
    change: float | None = None
    change_pct: float | None = None
    start_date: dt.date | None = None
    start_price: float | None = None
    shares_held: float | None = None
    cost: float | None = None
    value: float | None = None
    day_change: float | None = None
    gain: float | None = None
    gain_pct: float | None = None
    problem: str | None = None


@dataclass
class PortfolioValue:
    portfolio: Portfolio
    rows: list[HoldingValue]
    checked_at: dt.datetime
    prices_as_of: dt.datetime | None = None
    error: str | None = None
    start_dates: list[dt.date] = field(default_factory=list)

    @property
    def priced(self) -> list[HoldingValue]:
        return [r for r in self.rows if r.value is not None]

    @property
    def missing(self) -> list[str]:
        return [r.symbol for r in self.rows if r.value is None]

    @property
    def cost(self) -> float | None:
        return sum(r.cost for r in self.priced) if self.priced else None

    @property
    def value(self) -> float | None:
        return sum(r.value for r in self.priced) if self.priced else None

    @property
    def gain(self) -> float | None:
        return None if self.value is None else self.value - self.cost

    @property
    def gain_pct(self) -> float | None:
        return None if not self.cost else self.gain / self.cost * 100

    @property
    def day_change(self) -> float | None:
        known = [r.day_change for r in self.priced if r.day_change is not None]
        return sum(known) if known else None

    @property
    def day_change_pct(self) -> float | None:
        if self.day_change is None or not self.value or self.value == self.day_change:
            return None
        return self.day_change / (self.value - self.day_change) * 100

    @property
    def started_with(self) -> float:
        if all(r.weight is not None for r in self.rows):
            return self.portfolio.start_cash
        return sum(r.cost or 0 for r in self.rows)


def start_bar(prices: PriceSource, symbol: str, created: dt.date) -> PriceBar | None:
    """The last trading day before ``created``; else the first on or after it."""
    before = prices.history(symbol, created - dt.timedelta(days=START_LOOKBACK_DAYS), created - dt.timedelta(days=1))
    if before.bars:
        return before.bars[-1]
    after = prices.history(symbol, created, None)
    return after.bars[0] if after.bars else None


def _start_prices(prices: PriceSource, p: Portfolio, h: Holding, q: Quote) -> tuple[dt.date | None, float, float]:
    """``(start date, start close, start adjusted close)`` for valuing ``h``.

    The recorded start day's bar is re-fetched when it can be, since its
    adjusted close (dividends) and close (splits) change after the fact;
    without it the recorded price is used as is.
    """
    if h.start_price is not None:
        try:
            bars = prices.history(h.symbol, h.start_date, h.start_date).bars
        except PriceSourceError as exc:
            log.warning("No bar for %s on %s; using the recorded start price: %s", h.symbol, h.start_date, exc)
            bars = []
        if bars:
            return h.start_date, bars[0].close, bars[0].adjclose
        return h.start_date, h.start_price, h.start_price
    bar = start_bar(prices, h.symbol, p.created)
    if bar is None:
        # Nothing recorded around the start yet: start from the current price.
        return None, q.price, q.price
    return bar.date, bar.close, bar.adjclose


def _value_holding(prices: PriceSource, p: Portfolio, h: Holding, q: Quote | None) -> HoldingValue:
    row = HoldingValue(h.symbol, weight=h.weight, shares=h.shares)
    if q is None:
        row.problem = "No price found"
        return row
    row.name = q.name
    row.price, row.change, row.change_pct = q.price, q.change, q.change_pct
    try:
        row.start_date, start_close, start_adj = _start_prices(prices, p, h, q)
    except PriceSourceError as exc:
        log.warning("No start price for %s: %s", h.symbol, exc)
        row.problem = "Starting price unavailable"
        return row
    row.start_price = start_close
    row.cost = p.start_cash * h.weight / 100 if h.weight is not None else h.shares * start_close
    row.shares_held = h.shares if h.shares is not None else row.cost / start_close
    row.value = row.cost * q.price / start_adj
    row.gain = row.value - row.cost
    row.gain_pct = row.gain / row.cost * 100 if row.cost else None
    if q.previous_close:
        row.day_change = row.value * (1 - q.previous_close / q.price)
    return row


def record_start_prices(p: Portfolio, prices: PriceSource) -> bool:
    """Record a start price and date on each holding that lacks one.

    Uses the last close before ``p.created`` (else the first after it, else
    the current price).  Holdings whose prices can't be had now are left
    without; returns whether any holding changed.
    """
    changed = False
    for h in p.holdings:
        if h.start_price is not None:
            continue
        try:
            bar = start_bar(prices, h.symbol, p.created)
            if bar is not None:
                h.start_price, h.start_date = bar.close, bar.date
            else:
                h.start_price, h.start_date = prices.quote(h.symbol).price, p.created
        except PriceSourceError as exc:
            log.warning("Start price for %s not recorded yet: %s", h.symbol, exc)
            continue
        changed = True
    return changed


def value_portfolio(p: Portfolio, prices: PriceSource) -> PortfolioValue:
    """Current value of every holding; price problems are reported, not raised."""
    checked = dt.datetime.now(dt.timezone.utc)
    symbols = [h.symbol for h in p.holdings]
    try:
        quotes = prices.quotes(symbols)
    except PriceSourceError as exc:
        log.warning("Quotes for %s failed: %s", p.name, exc)
        rows = [HoldingValue(h.symbol, weight=h.weight, shares=h.shares, problem="Price unavailable")
                for h in p.holdings]
        return PortfolioValue(p, rows, checked, error=f"Could not get prices right now: {exc}")
    rows = [_value_holding(prices, p, h, quotes.get(h.symbol)) for h in p.holdings]
    stamps = [q.as_of for q in quotes.values() if q.as_of is not None]
    starts = sorted({r.start_date for r in rows if r.start_date})
    return PortfolioValue(p, rows, checked, prices_as_of=max(stamps) if stamps else None, start_dates=starts)


# ------------------------------------------------------------ formatting

def money(x: float | None, signed: bool = False) -> str:
    if x is None:
        return "—"
    sign = ("+" if x > 0 else "−" if x < 0 else "") if signed else ("−" if x < 0 else "")
    return f"{sign}${abs(x):,.2f}"


def dollars(x: float) -> str:
    """Like money() but without cents for a whole amount, for prose ("$10,000")."""
    return f"${x:,.0f}" if x == round(x) else money(x)


def pct(x: float | None, signed: bool = True) -> str:
    if x is None:
        return "—"
    sign = ("+" if x > 0 else "−" if x < 0 else "") if signed else ""
    return f"{sign}{abs(x):.2f}%"


def direction(x: float | None) -> str:
    if x is None or abs(x) < 0.005:
        return ""
    return "up" if x > 0 else "down"


def weight_text(w: float | None) -> str:
    return "" if w is None else f"{w:g}"


@bp.context_processor
def _helpers() -> dict:
    return {"money": money, "dollars": dollars, "pct": pct, "direction": direction, "weight_text": weight_text,
            "max_holdings": MAX_HOLDINGS, "suggested_min": SUGGESTED_MIN_HOLDINGS,
            "start_cash": DEFAULT_START_CASH}


# ------------------------------------------------------------ form handling

@dataclass
class FormRow:
    symbol: str
    name: str = ""
    weight: str = ""


def _names(symbols: list[str]) -> dict[str, str]:
    """Display names for symbols; blank when prices can't be had."""
    try:
        return {s: q.name for s, q in get_prices().quotes(symbols).items()}
    except PriceSourceError as exc:
        log.warning("No names for %s: %s", ", ".join(symbols), exc)
        return {}


def _rows_for(p: Portfolio) -> list[FormRow]:
    names = _names([h.symbol for h in p.holdings])
    return [FormRow(h.symbol, names.get(h.symbol, ""), weight_text(h.weight)) for h in p.holdings]


def parse_form(form) -> tuple[str, str, list[FormRow], list[Holding], list[str]]:
    """``(name, notes, rows, holdings, errors)`` from the builder form."""
    name = form.get("name", "").strip()
    notes = form.get("notes", "").strip()
    symbols, weights, names = form.getlist("symbol"), form.getlist("weight"), form.getlist("holding_name")
    names += [""] * (len(symbols) - len(names))
    rows = [FormRow(s.strip().upper(), n, w.strip()) for s, w, n in zip(symbols, weights, names)]
    errors, holdings = [], []
    for row in rows:
        try:
            sym = normalize_symbol(row.symbol)
        except ValidationError as exc:
            errors.append(str(exc))
            continue
        try:
            weight = float(row.weight)
        except ValueError:
            errors.append(f"{sym}: enter a weight in percent, like 10")
            continue
        try:
            holdings.append(Holding(sym, weight=weight))
        except ValidationError as exc:
            errors.append(str(exc))
    return name, notes, rows, holdings, errors


def check_symbols(holdings: list[Holding]) -> list[str]:
    """Errors for symbols the price source doesn't know."""
    symbols = [h.symbol for h in holdings]
    if not symbols:
        return []
    try:
        known = get_prices().quotes(symbols)
    except PriceSourceError as exc:
        return [f"Could not check prices right now ({exc}); try again in a minute"]
    unknown = [s for s in symbols if s not in known]
    if unknown:
        return [f"No prices found for {', '.join(unknown)}: check the symbol with the search box"]
    return []


def _render_form(p: Portfolio | None, name: str, notes: str, rows: list[FormRow], errors: list[str], status=200):
    return render_template("portfolios/form.html", portfolio=p, name=name, notes=notes, rows=rows,
                           errors=errors, start_cash=p.start_cash if p else DEFAULT_START_CASH), status


def _save(existing: Portfolio | None):
    name, notes, rows, holdings, errors = parse_form(request.form)
    if existing is None:
        p = Portfolio(name=name, holdings=holdings, notes=notes)
    else:
        changed = [h.position for h in holdings] != [h.position for h in existing.holdings]
        if not changed:
            holdings = existing.holdings
        p = Portfolio(name=name, holdings=holdings, notes=notes, start_cash=existing.start_cash,
                      created=dt.date.today() if changed else existing.created,
                      source_example=existing.source_example, id=existing.id)
    if errors:
        if not name:
            errors.insert(0, "Give the portfolio a name")
    else:
        try:
            p.validate()
        except ValidationError as exc:
            errors.append(str(exc))
    if not errors:
        errors = check_symbols(holdings)
    if errors:
        return _render_form(existing, name, notes, rows, errors, 400)
    record_start_prices(p, get_prices())
    store = get_store()
    if existing is None:
        store.add(p)
    else:
        store.update(p)
    return redirect(url_for("portfolios.watch", portfolio_id=p.id), code=303)


def _with_start_prices(p: Portfolio) -> Portfolio:
    """Record and save start prices on a portfolio saved without them
    (before they were recorded, or copied from an example)."""
    if all(h.start_price is not None for h in p.holdings):
        return p
    if record_start_prices(p, get_prices()):
        try:
            get_store().update(p)
        except (PortfolioNotFound, ValidationError) as exc:
            log.warning("Could not save start prices for %s: %s", p.name, exc)
    return p


def _get_or_404(portfolio_id: str) -> Portfolio:
    try:
        return get_store().get(portfolio_id)
    except PortfolioNotFound:
        abort(404)


# ------------------------------------------------------------ views

@bp.get("/")
def index():
    prices = get_prices()
    values = [value_portfolio(_with_start_prices(p), prices) for p in get_store().list()]
    return render_template("portfolios/index.html", values=values, deleted=request.args.get("deleted"))


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        return _save(None)
    return _render_form(None, "", "", [], [])


@bp.get("/<portfolio_id>/")
def watch(portfolio_id: str):
    p = _with_start_prices(_get_or_404(portfolio_id))
    try:
        warnings = p.validate()
    except ValidationError as exc:
        warnings = [str(exc)]
    return render_template("portfolios/watch.html", pv=value_portfolio(p, get_prices()), warnings=warnings)


@bp.get("/<portfolio_id>/table")
def watch_table(portfolio_id: str):
    """Just the watch table, for the page's Refresh button."""
    p = _with_start_prices(_get_or_404(portfolio_id))
    return render_template("portfolios/_watch_table.html", pv=value_portfolio(p, get_prices()))


@bp.route("/<portfolio_id>/edit", methods=["GET", "POST"])
def edit(portfolio_id: str):
    p = _get_or_404(portfolio_id)
    if request.method == "POST":
        return _save(p)
    return _render_form(p, p.name, p.notes, _rows_for(p), [])


@bp.route("/<portfolio_id>/delete", methods=["GET", "POST"])
def delete(portfolio_id: str):
    p = _get_or_404(portfolio_id)
    if request.method == "POST":
        get_store().delete(p.id)
        return redirect(url_for("portfolios.index", deleted=p.name), code=303)
    return render_template("portfolios/delete.html", portfolio=p)


def api_search():
    q = request.args.get("q", "").strip()[:MAX_QUERY_LEN]
    if not q:
        return jsonify({"query": q, "results": []})
    try:
        hits = get_prices().search(q, limit=SEARCH_LIMIT)
    except PriceSourceError as exc:
        log.warning("Search for %r failed: %s", q, exc)
        return jsonify({"query": q, "results": [], "error": f"Search is unavailable right now: {exc}"}), 503
    return jsonify({"query": q, "results": [
        {"symbol": h.symbol, "name": h.name, "type": h.instrument_type, "exchange": h.exchange} for h in hits
    ]})


# /api/search lives at the site root, outside this blueprint's url_prefix.
bp.record_once(lambda state: state.app.add_url_rule("/api/search", "api_search", api_search))
