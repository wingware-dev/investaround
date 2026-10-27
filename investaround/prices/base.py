"""The PriceSource contract every price provider implements."""

from __future__ import annotations

import datetime as dt
from typing import Protocol, runtime_checkable

from ..models import PriceSeries, Quote, SearchHit


class PriceSourceError(Exception):
    """The source could not answer (network down, rate limited, ...)."""


class UnknownSymbol(PriceSourceError):
    """The source has no data at all for this symbol."""

    def __init__(self, symbol: str) -> None:
        super().__init__(f"No data for symbol {symbol!r}")
        self.symbol = symbol


@runtime_checkable
class PriceSource(Protocol):
    name: str

    def quote(self, symbol: str) -> Quote:
        """Latest price; raises UnknownSymbol or PriceSourceError."""
        ...

    def quotes(self, symbols: list[str]) -> dict[str, Quote]:
        """Latest prices for several symbols; unknown ones are left out."""
        ...

    def history(self, symbol: str, start: dt.date | None = None, end: dt.date | None = None) -> PriceSeries:
        """Daily bars from start to end inclusive (None = as far as known).

        An empty series means the symbol exists but has no bars in range.
        """
        ...

    def search(self, query: str, limit: int = 10) -> list[SearchHit]:
        ...
