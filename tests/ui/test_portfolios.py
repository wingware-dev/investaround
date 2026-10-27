"""Building, watching, editing and deleting a portfolio the way a user would."""

import datetime as dt
import re

from playwright.sync_api import expect

from investaround.models import Holding, Portfolio
from investaround.prices.fake import FakePriceSource
from tests.ui.harness import new_page, start_app


def add_by_search(page, query, symbol):
    page.get_by_label("Find an investment").fill(query)
    page.locator(f'#search-results button[data-symbol="{symbol}"]').click()
    expect(page.locator(f'#holdings tr[data-symbol="{symbol}"]')).to_be_visible()


def seed(live, created=dt.date(2026, 10, 1), name="Starter mix"):
    p = Portfolio(name, [Holding("SPY", weight=60), Holding("BND", weight=40)], created=created)
    live.store.add(p)
    return p


def test_build_portfolio_from_scratch(page, live_app):
    page.goto("/portfolios/")
    page.get_by_role("link", name="Build your first portfolio").click()
    expect(page.get_by_role("heading", name="Build a portfolio")).to_be_visible()

    page.get_by_label("Portfolio name").fill("My first mix")
    add_by_search(page, "vanguard s&p", "VOO")
    expect(page.locator("#spread-hint")).to_contain_text("Most people use 5 to 20")
    # Enter picks the top match.
    page.get_by_label("Find an investment").fill("BND")
    expect(page.locator('#search-results button[data-symbol="BND"]')).to_be_visible()
    page.get_by_label("Find an investment").press("Enter")
    for query, sym in [("total international", "VXUS"), ("apple", "AAPL"), ("gold", "GLD")]:
        add_by_search(page, query, sym)

    # Untouched weights are split evenly and add up to 100%.
    weights = page.locator("#holdings input.weight")
    expect(weights).to_have_count(5)
    assert [weights.nth(i).input_value() for i in range(5)] == ["20", "20", "20", "20", "20"]
    expect(page.locator("#weight-total")).to_have_text("· weights add up to 100%")
    expect(page.locator("#spread-hint")).to_have_text("5 investments is a good spread.")
    expect(page.locator('#holdings tr[data-symbol="AAPL"] .holding-amount')).to_have_text("$2,000.00")

    page.get_by_role("button", name="Create portfolio").click()
    expect(page.get_by_role("heading", name="My first mix")).to_be_visible()
    (p,) = live_app.store.list()
    assert [(h.symbol, h.weight) for h in p.holdings] == [(s, 20) for s in ["VOO", "BND", "VXUS", "AAPL", "GLD"]]
    rows = page.locator(".watch-table tbody tr")
    expect(rows).to_have_count(5)
    expect(rows.first).to_contain_text("Vanguard S&P 500 ETF")
    expect(page.locator("#checked-at")).not_to_be_empty()


def test_already_added_and_removing(page):
    page.goto("/portfolios/new")
    add_by_search(page, "SPY", "SPY")
    add_by_search(page, "BND", "BND")
    page.get_by_label("Find an investment").fill("SPY")
    page.locator('#search-results button[data-symbol="SPY"]').click()
    expect(page.locator("#spread-hint")).to_have_text("SPY is already in the portfolio.")
    expect(page.locator("#holdings tr.holding-row")).to_have_count(2)
    page.get_by_role("button", name="Remove SPY").click()
    expect(page.locator("#holdings tr.holding-row")).to_have_count(1)
    expect(page.get_by_label("Weight for BND (%)")).to_have_value("100")


def test_search_with_no_results(page):
    page.goto("/portfolios/new")
    page.get_by_label("Find an investment").fill("qqqzzz nothing")
    expect(page.locator("#search-results")).to_contain_text("Nothing found for “qqqzzz nothing”")


def test_weights_must_add_up(page, live_app):
    page.goto("/portfolios/new")
    page.get_by_label("Portfolio name").fill("Lopsided")
    add_by_search(page, "SPY", "SPY")
    add_by_search(page, "BND", "BND")
    page.get_by_label("Weight for SPY (%)").fill("70")
    expect(page.locator("#weight-total")).to_have_text("· weights add up to 120% (they need to add up to 100%)")
    # Once weights are typed, a new holding gets what's left (nothing here).
    add_by_search(page, "GLD", "GLD")
    expect(page.get_by_label("Weight for GLD (%)")).to_have_value("0")

    page.get_by_role("button", name="Create portfolio").click()
    expect(page.get_by_role("alert")).to_contain_text("GLD: weight must be above 0")
    # The form comes back as entered.
    expect(page.get_by_label("Portfolio name")).to_have_value("Lopsided")
    expect(page.get_by_label("Weight for SPY (%)")).to_have_value("70")
    expect(page.locator('#holdings tr[data-symbol="BND"] .holding-name')).to_contain_text("Vanguard Total Bond")

    page.get_by_role("button", name="Remove GLD").click()
    page.get_by_label("Weight for BND (%)").fill("30")
    page.get_by_role("button", name="Create portfolio").click()
    expect(page.get_by_role("heading", name="Lopsided")).to_be_visible()
    expect(page.get_by_text("Only 2 holdings: spreading money over 5 or more")).to_be_visible()
    assert len(live_app.store.list()) == 1


def test_split_evenly_button(page):
    page.goto("/portfolios/new")
    for sym in ["SPY", "BND", "GLD"]:
        add_by_search(page, sym, sym)
    page.get_by_label("Weight for SPY (%)").fill("90")
    page.get_by_role("button", name="Split evenly").click()
    assert [page.get_by_label(f"Weight for {s} (%)").input_value() for s in ["SPY", "BND", "GLD"]] == \
        ["33.34", "33.33", "33.33"]
    expect(page.locator("#weight-total")).to_have_text("· weights add up to 100%")


def test_watch_shows_values_since_start(page, live_app):
    p = seed(live_app)
    page.goto("/portfolios/")
    page.get_by_role("link", name="Starter mix").click()
    expect(page.get_by_text("Started Oct 1, 2026 with $10,000 of pretend money, "
                            "bought at the closing prices of Sep 30, 2026.")).to_be_visible()
    spy = page.locator('.watch-table tr[data-symbol="SPY"]')
    expect(spy).to_contain_text("60%")
    expect(spy).to_contain_text("$680.00")
    expect(spy).to_contain_text("+$5.57")
    # 6000 * 680.00 / 655.462873 (SPY's Sep 30 close)
    expect(spy).to_contain_text("$6,224.61")
    expect(spy).to_contain_text("+$224.61")
    gain = page.locator('[data-stat="gain"]')
    expect(gain).to_have_class(re.compile(r"\bup\b"))
    assert live_app.store.get(p.id).created == dt.date(2026, 10, 1)


def test_refresh_updates_last_updated(page, live_app):
    p = seed(live_app)
    page.goto(f"/portfolios/{p.id}/")
    before = page.locator("#checked-at").get_attribute("datetime")
    page.wait_for_timeout(20)
    with page.expect_response(re.compile(r"/table$")):
        page.get_by_role("button", name="Refresh prices").click()
    expect(page.get_by_role("button", name="Refresh prices")).to_be_enabled()
    expect(page.locator("#checked-at")).not_to_have_attribute("datetime", before)
    expect(page.locator("#prices-as-of")).to_contain_text("prices from")
    expect(page.locator(".watch-table tbody tr")).to_have_count(2)


def test_edit_then_delete(page, live_app):
    p = seed(live_app)
    page.goto(f"/portfolios/{p.id}/")
    page.get_by_role("link", name="Edit").click()
    expect(page.get_by_label("Portfolio name")).to_have_value("Starter mix")
    expect(page.get_by_label("Weight for SPY (%)")).to_have_value("60")
    expect(page.get_by_text("Changing investments or weights starts the portfolio again")).to_be_visible()
    page.get_by_label("Portfolio name").fill("Renamed mix")
    page.get_by_role("button", name="Save changes").click()
    expect(page.get_by_role("heading", name="Renamed mix")).to_be_visible()
    assert live_app.store.get(p.id).created == dt.date(2026, 10, 1)

    page.get_by_role("link", name="Delete").click()
    expect(page.get_by_role("heading", name="Delete Renamed mix?")).to_be_visible()
    page.get_by_role("button", name="Delete portfolio").click()
    expect(page.get_by_role("status")).to_contain_text("Deleted Renamed mix.")
    expect(page.get_by_role("link", name="Build your first portfolio")).to_be_visible()
    assert live_app.store.list() == []


def test_list_shows_each_portfolio(page, live_app):
    seed(live_app, name="First")
    seed(live_app, name="Second", created=dt.date(2026, 10, 20))
    page.goto("/portfolios/")
    rows = page.locator(".portfolio-list tbody tr")
    expect(rows).to_have_count(2)
    expect(rows.nth(0)).to_contain_text("First")
    expect(rows.nth(0)).to_contain_text("Oct 1, 2026")
    expect(rows.nth(0)).to_contain_text("$10,272.33")
    expect(rows.nth(0)).to_contain_text("+$272.33 (+2.72%)")


def test_watch_when_prices_are_down(browser, tmp_path):
    live = start_app(tmp_path / "data", PRICE_SOURCE_OBJ=FakePriceSource(fail_symbols={"BND"}))
    errors = []
    page = new_page(browser, live, errors)
    try:
        p = seed(live)
        page.goto(f"/portfolios/{p.id}/")
        expect(page.get_by_role("alert")).to_contain_text("Could not get prices right now")
        expect(page.locator('[data-stat="value"]')).to_have_text("—")
        assert not errors
    finally:
        page.context.close()
        live.stop()
