"""Plain data types shared across the app.

These are deliberately simple dataclasses with dict round-tripping so the
JSON store, the price sources and the analytics code can all agree on them
without importing each other.
"""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass, field

MIN_HOLDINGS = 1
MAX_HOLDINGS = 20
SUGGESTED_MIN_HOLDINGS = 5
DEFAULT_START_CASH = 10_000.0


class ValidationError(ValueError):
    """Raised when user-supplied portfolio data is not acceptable."""


def normalize_symbol(symbol: str) -> str:
    sym = (symbol or "").strip().upper()
    if not sym:
        raise ValidationError("Symbol is empty")
    if len(sym) > 15 or not all(c.isalnum() or c in ".-^=" for c in sym):
        raise ValidationError(f"Symbol {symbol!r} does not look like a ticker")
    return sym


@dataclass
class Holding:
    """One position in a portfolio.

    Exactly one of ``weight`` (percent of start cash, 0-100] or ``shares``
    (fixed share count) is set.
    """

    symbol: str
    weight: float | None = None
    shares: float | None = None

    def __post_init__(self) -> None:
        self.symbol = normalize_symbol(self.symbol)
        if (self.weight is None) == (self.shares is None):
            raise ValidationError(f"{self.symbol}: give either a weight or a share count")
        if self.weight is not None:
            self.weight = float(self.weight)
            if not 0 < self.weight <= 100:
                raise ValidationError(f"{self.symbol}: weight must be above 0 and at most 100")
        if self.shares is not None:
            self.shares = float(self.shares)
            if self.shares <= 0:
                raise ValidationError(f"{self.symbol}: share count must be above 0")

    def to_dict(self) -> dict:
        d: dict = {"symbol": self.symbol}
        if self.weight is not None:
            d["weight"] = self.weight
        if self.shares is not None:
            d["shares"] = self.shares
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Holding:
        return cls(symbol=d["symbol"], weight=d.get("weight"), shares=d.get("shares"))


@dataclass
class Portfolio:
    name: str
    holdings: list[Holding]
    start_cash: float = DEFAULT_START_CASH
    created: dt.date = field(default_factory=dt.date.today)
    notes: str = ""
    source_example: str | None = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def validate(self) -> list[str]:
        """Raise ValidationError for hard errors; return soft warnings."""
        self.name = (self.name or "").strip()
        if not self.name:
            raise ValidationError("Give the portfolio a name")
        if len(self.name) > 80:
            raise ValidationError("Name is too long (80 characters at most)")
        n = len(self.holdings)
        if n < MIN_HOLDINGS:
            raise ValidationError("Add at least one holding")
        if n > MAX_HOLDINGS:
            raise ValidationError(f"At most {MAX_HOLDINGS} holdings")
        syms = [h.symbol for h in self.holdings]
        dupes = sorted({s for s in syms if syms.count(s) > 1})
        if dupes:
            raise ValidationError(f"Listed more than once: {', '.join(dupes)}")
        if not self.start_cash or self.start_cash <= 0:
            raise ValidationError("Starting cash must be above 0")
        weighted = [h for h in self.holdings if h.weight is not None]
        if weighted and len(weighted) != n:
            raise ValidationError("Use weights for every holding or share counts for every holding")
        if weighted:
            total = sum(h.weight for h in weighted)
            if abs(total - 100) > 0.01:
                raise ValidationError(f"Weights add up to {total:g}%, not 100%")
        warnings = []
        if n < SUGGESTED_MIN_HOLDINGS:
            warnings.append(
                f"Only {n} holding{'s' if n != 1 else ''}: spreading money over "
                f"{SUGGESTED_MIN_HOLDINGS} or more lowers the risk from any one of them"
            )
        return warnings

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "holdings": [h.to_dict() for h in self.holdings],
            "start_cash": self.start_cash,
            "created": self.created.isoformat(),
            "notes": self.notes,
            "source_example": self.source_example,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Portfolio:
        return cls(
            id=d["id"],
            name=d["name"],
            holdings=[Holding.from_dict(h) for h in d.get("holdings", [])],
            start_cash=float(d.get("start_cash", DEFAULT_START_CASH)),
            created=dt.date.fromisoformat(d["created"]),
            notes=d.get("notes", ""),
            source_example=d.get("source_example"),
        )


@dataclass(frozen=True)
class Quote:
    """Latest known price for a symbol."""

    symbol: str
    price: float
    previous_close: float | None
    currency: str = "USD"
    name: str = ""
    instrument_type: str = ""
    as_of: dt.datetime | None = None

    @property
    def change(self) -> float | None:
        if self.previous_close is None:
            return None
        return self.price - self.previous_close

    @property
    def change_pct(self) -> float | None:
        if not self.previous_close:
            return None
        return (self.price / self.previous_close - 1) * 100


@dataclass(frozen=True)
class PriceBar:
    """One trading day.  ``adjclose`` includes dividends and splits."""

    date: dt.date
    close: float
    adjclose: float


@dataclass
class PriceSeries:
    symbol: str
    bars: list[PriceBar]

    def __post_init__(self) -> None:
        self.bars.sort(key=lambda b: b.date)

    @property
    def first_date(self) -> dt.date | None:
        return self.bars[0].date if self.bars else None

    @property
    def last_date(self) -> dt.date | None:
        return self.bars[-1].date if self.bars else None

    def between(self, start: dt.date | None, end: dt.date | None) -> PriceSeries:
        return PriceSeries(
            self.symbol,
            [b for b in self.bars if (start is None or b.date >= start) and (end is None or b.date <= end)],
        )

    def __len__(self) -> int:
        return len(self.bars)


@dataclass(frozen=True)
class SearchHit:
    symbol: str
    name: str
    instrument_type: str = ""
    exchange: str = ""
