"""UI test harness: a live app per test and a headless Playwright browser.

Each ``LiveApp`` is its own Flask app on an OS-assigned port with the fake
price source and a private data dir, served from a background thread, so
any number can run at once (several tests, or tests beside tools/shots.py).

The browser is headless installed Chrome (``channel="chrome"``), falling
back to Playwright's bundled Chromium when Chrome isn't installed.

Fixtures (registered by tests/ui/conftest.py):

  live_app   LiveApp for this test: ``.url``, ``.app``, ``.store``, ``.data_dir``
  browser    one headless browser per session
  page       a fresh page for this test, with ``base_url`` = live_app.url so
             ``page.goto("/portfolios/")`` works; fails the test on any
             uncaught JavaScript error in the page
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import pytest
from flask import Flask
from werkzeug.serving import BaseWSGIServer, WSGIRequestHandler, make_server

from investaround.app import create_app
from investaround.storage import PortfolioStore

log = logging.getLogger(__name__)

VIEWPORT = {"width": 1280, "height": 800}


class _QuietHandler(WSGIRequestHandler):
    """Drops the per-request access log line; errors are still logged."""

    def log_request(self, code="-", size="-") -> None:
        pass


@dataclass
class LiveApp:
    app: Flask
    url: str
    data_dir: Path
    _server: BaseWSGIServer = field(repr=False)
    _thread: threading.Thread = field(repr=False)

    @property
    def store(self) -> PortfolioStore:
        return self.app.extensions["investaround.store"]

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


def start_app(data_dir: str | os.PathLike, **config: Any) -> LiveApp:
    """Start an app on 127.0.0.1 with an OS-assigned port; caller must ``stop()`` it.

    Uses the fake price source unless ``config`` says otherwise (pass
    ``PRICE_SOURCE_OBJ=FakePriceSource(fail_symbols={...})`` for error paths).
    """
    data_dir = Path(data_dir)
    cfg = {"DATA_DIR": str(data_dir), "PRICE_SOURCE": "fake", "TESTING": True}
    cfg.update(config)
    app = create_app(cfg)
    server = make_server("127.0.0.1", 0, app, threaded=True, request_handler=_QuietHandler)
    url = f"http://127.0.0.1:{server.server_port}"
    thread = threading.Thread(target=server.serve_forever, name=f"live-app-{server.server_port}", daemon=True)
    thread.start()
    return LiveApp(app=app, url=url, data_dir=data_dir, _server=server, _thread=thread)


def launch_browser(playwright):
    """Headless installed Chrome, else Playwright's bundled Chromium."""
    try:
        return playwright.chromium.launch(channel="chrome", headless=True)
    except Exception as exc:
        log.info("Installed Chrome unavailable (%s); using Playwright Chromium", exc)
        return playwright.chromium.launch(headless=True)


def new_page(browser, live: LiveApp, errors: list[str] | None = None):
    """A page in a fresh context aimed at ``live``; JS errors go to ``errors``."""
    context = browser.new_context(base_url=live.url, viewport=VIEWPORT)
    page = context.new_page()
    if errors is not None:
        page.on("pageerror", lambda exc: errors.append(str(exc)))
    return page


# ---------------------------------------------------------------- fixtures

@pytest.fixture
def live_app(tmp_path, monkeypatch) -> Iterator[LiveApp]:
    # Belt and braces: nothing in a UI test may reach a live price source.
    monkeypatch.setenv("INVESTAROUND_PRICE_SOURCE", "fake")
    live = start_app(tmp_path / "data")
    try:
        yield live
    finally:
        live.stop()


@pytest.fixture(scope="session")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        b = launch_browser(pw)
        try:
            yield b
        finally:
            b.close()


@pytest.fixture
def page(browser, live_app):
    errors: list[str] = []
    pg = new_page(browser, live_app, errors)
    try:
        yield pg
    finally:
        pg.context.close()
    assert not errors, f"JavaScript errors in page: {errors}"
