"""Shots of building and watching a portfolio."""

import datetime as dt

from investaround.models import Holding, Portfolio
from tools.shots import shot


def _add(page, query, symbol):
    page.get_by_label("Find an investment").fill(query)
    page.locator(f'#search-results button[data-symbol="{symbol}"]').click()
    page.locator(f'#holdings tr[data-symbol="{symbol}"]').wait_for()


@shot("10-build-portfolio", "Building a portfolio: search, add investments, weights split evenly")
def build_portfolio(page, live):
    page.goto("/portfolios/new")
    page.get_by_label("Portfolio name").fill("My first mix")
    for query, sym in [("VTI", "VTI"), ("total international", "VXUS"), ("BND", "BND"),
                       ("apple", "AAPL"), ("gold", "GLD")]:
        _add(page, query, sym)
    # Leave the search open on its results, as the user sees it mid-build.
    page.get_by_label("Find an investment").fill("microsoft")
    page.locator('#search-results button[data-symbol="MSFT"]').wait_for()


@shot("11-watch-portfolio", "Watching a portfolio: today's change and gain since start")
def watch_portfolio(page, live):
    p = Portfolio(
        "My first mix",
        [Holding("VTI", weight=30), Holding("VXUS", weight=20), Holding("BND", weight=20),
         Holding("AAPL", weight=10), Holding("NVDA", weight=10), Holding("GLD", weight=10)],
        created=dt.date(2026, 9, 1),
        notes="Mostly broad funds, plus two companies I know and some gold.",
    )
    live.store.add(p)
    page.goto(f"/portfolios/{p.id}/")
    page.locator(".watch-table").wait_for()
