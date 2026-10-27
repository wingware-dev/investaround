"""PortfolioStore: the user's paper portfolios in one JSON file."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path

from .models import Portfolio

FORMAT_VERSION = 1


class PortfolioNotFound(KeyError):
    pass


class PortfolioStore:
    """CRUD over ``<data_dir>/portfolios.json``, written atomically.

    The file is small, so every call re-reads it; that keeps several app
    instances (or a hand edit) from losing each other's changes.
    """

    def __init__(self, path: str | os.PathLike) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def _load(self) -> list[Portfolio]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as f:
            raw = json.load(f)
        return [Portfolio.from_dict(d) for d in raw.get("portfolios", [])]

    def _save(self, portfolios: list[Portfolio]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": FORMAT_VERSION, "portfolios": [p.to_dict() for p in portfolios]}
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".portfolios-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
                f.write("\n")
            os.replace(tmp, self.path)
        except BaseException:
            os.unlink(tmp)
            raise

    def list(self) -> list[Portfolio]:
        with self._lock:
            return self._load()

    def get(self, portfolio_id: str) -> Portfolio:
        for p in self.list():
            if p.id == portfolio_id:
                return p
        raise PortfolioNotFound(portfolio_id)

    def add(self, portfolio: Portfolio) -> list[str]:
        """Validate and store a new portfolio; returns soft warnings."""
        warnings = portfolio.validate()
        with self._lock:
            items = self._load()
            if any(p.id == portfolio.id for p in items):
                raise ValueError(f"Portfolio id {portfolio.id} already exists")
            items.append(portfolio)
            self._save(items)
        return warnings

    def update(self, portfolio: Portfolio) -> list[str]:
        warnings = portfolio.validate()
        with self._lock:
            items = self._load()
            for i, p in enumerate(items):
                if p.id == portfolio.id:
                    items[i] = portfolio
                    self._save(items)
                    return warnings
        raise PortfolioNotFound(portfolio.id)

    def delete(self, portfolio_id: str) -> None:
        with self._lock:
            items = self._load()
            kept = [p for p in items if p.id != portfolio_id]
            if len(kept) == len(items):
                raise PortfolioNotFound(portfolio_id)
            self._save(kept)
