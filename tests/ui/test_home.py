"""The home dashboard, driven as a user would."""

import datetime as dt

from investaround.models import Holding, Portfolio
from investaround.prices.fake import FakePriceSource

START_HERE = [
    ("Look at some examples", "/examples/"),
    ("Build your own portfolio", "/portfolios/new"),
    ("Watch it day by day", "/portfolios/"),
    ("See how it would have done", "/history/"),
    ("Learn the basics", "/learn/"),
    ("Compare strategies in the lab", "/learn/lab"),
]


def _mix(name="Mix", created=dt.date(2026, 9, 1)):
    return Portfolio(name, [Holding("VTI", weight=60), Holding("BND", weight=40)], created=created)


def test_first_visit_shows_start_here_path(page, live_app):
    page.goto("/")
    assert page.locator("#no-portfolios").is_visible()
    path = page.locator("aside.start-here")
    links = path.get_by_role("link")
    assert [(links.nth(i).inner_text(), links.nth(i).get_attribute("href")) for i in range(links.count())] == START_HERE
    assert "Made-up sample prices" in page.locator("#source-status").inner_text()
    assert page.locator("#price-error").count() == 0

    page.locator("#no-portfolios").get_by_role("link", name="Start from an example").click()
    page.wait_for_url(live_app.url + "/examples/")


def test_portfolios_listed_with_today_and_sparkline(page, live_app):
    a, b = _mix("Broad mix"), Portfolio("Tech bet", [Holding("AAPL", weight=50), Holding("MSFT", weight=50)],
                                        created=dt.date(2026, 10, 1))
    live_app.store.add(a)
    live_app.store.add(b)
    page.goto("/")
    rows = page.locator("table.dashboard tbody tr")
    assert rows.count() == 2
    for p in (a, b):
        row = page.locator(f'tr[data-portfolio="{p.id}"]')
        assert row.get_by_role("link", name=p.name).is_visible()
        assert row.locator("td.num").first.inner_text().startswith("$")
        assert "%" in row.locator("[data-today]").inner_text()
        spark = row.locator("svg.spark")
        assert spark.is_visible()
        assert len(spark.locator("polyline").get_attribute("points").split()) > 40
        assert spark.get_attribute("aria-label").startswith(p.name + ": ")
    assert page.locator("#totals").inner_text().count("$") == 2
    assert "Latest price from" in page.locator("#source-status").inner_text()

    # "Watch it day by day" goes to the first portfolio's watch page.
    page.locator("aside.start-here").get_by_role("link", name="Watch it day by day").click()
    page.wait_for_url(f"{live_app.url}/portfolios/{a.id}/")


def test_home_matches_the_watch_page(page, live_app):
    p = _mix()
    live_app.store.add(p)
    page.goto(f"/portfolios/{p.id}/")
    page.locator(".watch-table").wait_for()
    watch_text = page.locator(".watch-table").inner_text()
    page.goto("/")
    value = page.locator(f'tr[data-portfolio="{p.id}"] td.num').first.inner_text()
    assert value in watch_text


def test_price_failure_shows_error_banner(page, live_app):
    live_app.store.add(_mix())
    live_app.app.extensions["investaround.prices"] = FakePriceSource(fail_symbols={"BND"})
    page.goto("/")
    banner = page.get_by_role("alert")
    assert banner.is_visible()
    assert "Some prices are missing" in banner.inner_text()
    assert "Simulated failure for BND" in banner.inner_text()
    row = page.locator("table.dashboard tbody tr")
    assert row.locator("td.num").first.inner_text() == "—"
    assert row.locator("svg.spark").count() == 0
    assert "Portfolios with prices (0 of 1)" in page.locator("#totals").inner_text()
