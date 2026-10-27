"""Flask app factory.

Configuration (``create_app(config)`` keys, else environment, else default):

  DATA_DIR      INVESTAROUND_DATA_DIR       ./data   portfolios.json, price cache
  PRICE_SOURCE  INVESTAROUND_PRICE_SOURCE   see DEFAULT_PRICE_SOURCE  ("yahoo" | "fake")
  PRICE_SOURCE_OBJ  (config only)  a ready PriceSource instance, overriding PRICE_SOURCE
  FIXTURES_DIR  (config only)  fixtures for the fake source

Views reach shared services with ``get_store()`` and ``get_prices()``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Callable

from flask import Flask, current_app, render_template

from . import __version__
from .prices.base import PriceSource, PriceSourceError
from .storage import PortfolioStore

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_PRICE_SOURCE = "yahoo"

NAV = [
    ("home.index", "Home"),
    ("portfolios.index", "My portfolios"),
    ("history.index", "What if?"),
    ("examples.index", "Examples"),
    ("learn.index", "Learn"),
]


def _make_fake(app: Flask) -> PriceSource:
    from .prices.fake import DEFAULT_FIXTURES, FakePriceSource

    return FakePriceSource(app.config.get("FIXTURES_DIR") or DEFAULT_FIXTURES)


def _make_yahoo(app: Flask) -> PriceSource:
    from .prices.cache import CachingPriceSource
    from .prices.yahoo import YahooPriceSource

    return CachingPriceSource(YahooPriceSource(), Path(app.config["DATA_DIR"]) / "prices.sqlite")


PRICE_SOURCE_FACTORIES: dict[str, Callable[[Flask], PriceSource]] = {
    "fake": _make_fake,
    "yahoo": _make_yahoo,
}


def make_price_source(app: Flask) -> PriceSource:
    if app.config.get("PRICE_SOURCE_OBJ") is not None:
        return app.config["PRICE_SOURCE_OBJ"]
    kind = app.config["PRICE_SOURCE"]
    try:
        factory = PRICE_SOURCE_FACTORIES[kind]
    except KeyError:
        raise ValueError(f"Unknown price source {kind!r}; choose from {', '.join(PRICE_SOURCE_FACTORIES)}") from None
    return factory(app)


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        DATA_DIR=os.environ.get("INVESTAROUND_DATA_DIR", str(ROOT / "data")),
        PRICE_SOURCE=os.environ.get("INVESTAROUND_PRICE_SOURCE", DEFAULT_PRICE_SOURCE),
    )
    app.config.update(config or {})

    data_dir = Path(app.config["DATA_DIR"])
    data_dir.mkdir(parents=True, exist_ok=True)
    app.extensions["investaround.store"] = PortfolioStore(data_dir / "portfolios.json")
    app.extensions["investaround.prices"] = make_price_source(app)

    from .web import examples, history, home, learn, portfolios

    for mod in (home, portfolios, history, examples, learn):
        app.register_blueprint(mod.bp)

    @app.context_processor
    def _globals() -> dict:
        return {"nav": NAV, "app_version": __version__, "price_source_name": get_prices().name}

    @app.errorhandler(404)
    def _not_found(exc):
        return render_template("error.html", title="Page not found",
                               message="There is nothing at this address."), 404

    @app.errorhandler(PriceSourceError)
    def _price_error(exc):
        log.warning("Price source error: %s", exc)
        return render_template("error.html", title="Prices unavailable",
                               message=f"Could not get prices right now: {exc}"), 503

    return app


def get_store() -> PortfolioStore:
    return current_app.extensions["investaround.store"]


def get_prices() -> PriceSource:
    return current_app.extensions["investaround.prices"]
