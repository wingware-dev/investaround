"""Shots of the home dashboard."""

import datetime as dt

from investaround.models import Holding, Portfolio
from investaround.prices.fake import FakePriceSource
from tools.shots import shot


def _seed(live):
    live.store.add(Portfolio(
        "My first mix",
        [Holding("VTI", weight=30), Holding("VXUS", weight=20), Holding("BND", weight=20),
         Holding("AAPL", weight=10), Holding("NVDA", weight=10), Holding("GLD", weight=10)],
        created=dt.date(2026, 9, 1)))
    live.store.add(Portfolio(
        "Three-fund portfolio",
        [Holding("VTI", weight=50), Holding("VXUS", weight=30), Holding("BND", weight=20)],
        created=dt.date(2026, 10, 6), source_example="three-fund"))
    live.store.add(Portfolio(
        "Big tech bet",
        [Holding("AAPL", weight=25), Holding("MSFT", weight=25), Holding("AMZN", weight=25),
         Holding("NVDA", weight=25)],
        created=dt.date(2026, 8, 3)))


@shot("50-home-dashboard", "Home: every portfolio with today's change and a 3-month sparkline")
def home_dashboard(page, live):
    _seed(live)
    page.goto("/")
    page.locator("svg.spark").last.wait_for()


@shot("51-home-first-visit", "Home on a first visit: the start-here path")
def home_first_visit(page, live):
    page.goto("/")
    page.locator("aside.start-here").wait_for()


@shot("52-home-price-error", "Home when prices can't be fetched: the error banner")
def home_price_error(page, live):
    _seed(live)
    live.app.extensions["investaround.prices"] = FakePriceSource(fail_symbols={"BND"})
    page.goto("/")
    page.get_by_role("alert").wait_for()
