"""Registry of named screenshots for tools/shots.py.

Each feature adds its shots in its own module here (tools/shots/<feature>.py),
so steps never edit a shared file:

    from tools.shots import shot

    @shot("10-build-portfolio", "Building a portfolio")
    def build_portfolio(page, live):
        live.store.add(...)          # seed data straight into the app's store
        page.goto("/portfolios/")    # page.base_url is the live app
        page.get_by_role("button", name="Add").click()

The shot function leaves ``page`` showing what to capture; tools/shots.py
then writes docs/shots/<name>.png.  Every shot gets a fresh app (fake price
source, empty temp data dir) and a fresh 1280x800 page.  Names are
``NN-words``: 0x skeleton, 1x portfolios, 2x history, 3x examples, 4x learn, 5x home dashboard.
"""

from __future__ import annotations

import importlib
import pkgutil
import re
from dataclasses import dataclass
from typing import Callable

NAME_RE = re.compile(r"^\d\d-[a-z0-9]+(-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Shot:
    name: str
    description: str
    func: Callable
    full_page: bool
    module: str


REGISTRY: dict[str, Shot] = {}


def shot(name: str, description: str = "", *, full_page: bool = True) -> Callable:
    """Register the decorated ``func(page, live)`` as the shot ``name``."""
    if not NAME_RE.match(name):
        raise ValueError(f"Shot name {name!r} must look like '12-some-words'")

    def register(func: Callable) -> Callable:
        existing = REGISTRY.get(name)
        if existing is not None and existing.module != func.__module__:
            raise ValueError(f"Shot {name!r} is defined in both {existing.module} and {func.__module__}")
        REGISTRY[name] = Shot(name, description or (func.__doc__ or "").strip(), func, full_page, func.__module__)
        return func

    return register


def load_all() -> dict[str, Shot]:
    """Import every shot module in this package; return the registry sorted by name."""
    for info in pkgutil.iter_modules(__path__):
        importlib.import_module(f"{__name__}.{info.name}")
    return dict(sorted(REGISTRY.items()))
