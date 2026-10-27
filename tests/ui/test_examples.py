"""The example portfolios gallery, driven as a user would."""

from investaround.prices.fake import FakePriceSource
from investaround.web.examples import load_examples
from tests.ui.harness import new_page, start_app

EXAMPLES = load_examples()


def test_gallery_shows_every_example_with_a_chart(page):
    page.goto("/examples/")
    assert page.title() == "Examples · investaround"
    cards = page.locator("article.example-card")
    assert cards.count() == len(EXAMPLES)
    for ex in EXAMPLES:
        card = page.locator(f"#example-{ex.id}")
        assert card.get_by_role("heading", name=ex.name).is_visible()
        for label in ("What's in it", "The idea", "The risks"):
            assert card.get_by_role("heading", name=label).is_visible()
        for h in ex.holdings:
            assert card.locator(".holdings").get_by_text(h.symbol, exact=True).is_visible()
        assert card.locator("[data-final]").inner_text().startswith("$")
        assert card.locator("[data-drawdown]").inner_text().startswith("-")
        assert card.get_by_role("button", name="Try it as my portfolio").is_visible()
    # Chart.js drew a chart with the example and the S&P 500 in every card.
    drawn = page.evaluate("""() => [...document.querySelectorAll('canvas[data-example]')]
        .map(c => { const ch = Chart.getChart(c); return ch ? ch.data.datasets.length : 0; })""")
    assert drawn == [2] * len(EXAMPLES)


def test_try_it_copies_the_example_to_my_portfolios(page, live_app):
    page.goto("/examples/")
    card = page.locator("#example-three-fund")
    card.get_by_role("button", name="Try it as my portfolio").click()
    # It opens the new portfolio's own watch page.
    page.wait_for_url(live_app.url + "/portfolios/*/")
    [p] = live_app.store.list()
    assert page.url == f"{live_app.url}/portfolios/{p.id}/"
    assert page.get_by_role("heading", level=1).inner_text() == "Three-fund portfolio"
    assert page.get_by_text("Copied from the “Three-fund portfolio” example.").is_visible()
    assert p.name == "Three-fund portfolio"
    assert p.source_example == "three-fund"
    assert [(h.symbol, h.weight) for h in p.holdings] == [("VTI", 50), ("VXUS", 30), ("BND", 20)]

    # Trying it again makes a second copy rather than overwriting the first.
    page.goto("/examples/")
    page.locator("#example-three-fund").get_by_role("button", name="Try it as my portfolio").click()
    page.get_by_role("heading", level=1, name="Three-fund portfolio (2)").wait_for()
    assert sorted(p.name for p in live_app.store.list()) == ["Three-fund portfolio", "Three-fund portfolio (2)"]


def test_try_in_the_strategy_lab(page, live_app):
    page.goto("/examples/")
    page.locator("#example-gold-reit").get_by_role("link", name="Try in the strategy lab").click()
    page.wait_for_url(live_app.url + "/learn/lab?portfolio=example:gold-reit")
    assert page.get_by_label("Portfolio", exact=True).locator("option:checked").inner_text() == (
        "Gold and real-estate diversifier")
    page.locator("#what-this-shows").wait_for()
    assert "VNQ 15%" in page.locator("#lab-summary").inner_text()


def test_see_how_it_did_links_to_history(page, live_app):
    page.goto("/examples/")
    page.locator("#example-sixty-forty").get_by_role("link", name="See how it would have done").click()
    page.wait_for_url(live_app.url + "/history/?example=sixty-forty")


def test_cards_without_prices_say_so(browser, tmp_path):
    live = start_app(tmp_path / "data", PRICE_SOURCE_OBJ=FakePriceSource(fail_symbols={"GLD", "SPY"}))
    errors: list[str] = []
    page = new_page(browser, live, errors)
    try:
        page.goto("/examples/")
        with_gold = [ex.id for ex in EXAMPLES if "GLD" in ex.symbols]
        assert with_gold
        for ex in EXAMPLES:
            card = page.locator(f"#example-{ex.id}")
            unavailable = card.get_by_text("Price history is unavailable right now.")
            assert unavailable.count() == (1 if ex.id in with_gold else 0)
            # The S&P 500 comparison is dropped, but the example's own chart stays.
            assert "S&P 500:" not in card.inner_text()
            card.get_by_role("button", name="Try it as my portfolio").wait_for()
    finally:
        page.context.close()
        live.stop()
    assert not errors
