"""The Learn page and the Strategy lab, driven as a user would."""

LESSONS = ["Stocks", "Bonds", "Funds and ETFs", "Diversification", "Fees", "Volatility and drawdown",
           "Time in the market", "Dollar-cost averaging", "Rebalancing"]


def test_learn_page_has_lessons_glossary_and_disclaimer(page):
    page.goto("/learn/")
    assert page.title() == "Learn · investaround"
    assert "Not financial advice." in page.get_by_role("note").inner_text()
    toc = page.get_by_role("navigation", name="Lessons")
    for i, name in enumerate(LESSONS, 1):
        assert page.get_by_role("heading", name=f"{i}. {name}").is_visible()
        toc.get_by_role("link", name=name, exact=True).wait_for()
    toc.get_by_role("link", name="Glossary").click()
    page.wait_for_url("**/learn/#glossary")
    assert page.get_by_role("heading", name="Glossary").is_visible()


def test_glossary_filter(page):
    page.goto("/learn/")
    terms = page.locator(".glossary dt")
    total = terms.count()
    assert total > 20
    page.get_by_label("Find a term").fill("fund")
    visible = [t for t in terms.all() if t.is_visible()]
    assert {"ETF", "Index fund", "Mutual fund", "Expense ratio"} <= {t.inner_text() for t in visible}
    assert not page.get_by_text("Bull market", exact=True).is_visible()
    page.get_by_label("Find a term").fill("zzz")
    assert page.get_by_text("No terms match.").is_visible()
    page.get_by_label("Find a term").fill("")
    assert sum(t.is_visible() for t in terms.all()) == total


def test_lab_shows_three_strategies_side_by_side(page):
    page.goto("/learn/")
    page.get_by_role("link", name="Open the strategy lab").click()
    page.wait_for_url("**/learn/lab")
    assert page.title() == "Strategy lab · investaround"
    cards = page.locator("article.strategy")
    assert [c.get_attribute("data-strategy") for c in cards.all()] == ["lump_sum", "dca", "rebalance_yearly"]
    for c in cards.all():
        assert c.locator("[data-final]").inner_text().startswith("$")
    shows = page.locator("#what-this-shows")
    assert "earns nothing (0%)" in shows.inner_text()
    # Chart.js drew three strategies plus the money-invested line.
    assert page.evaluate("() => Chart.getChart(document.getElementById('lab-chart')).data.datasets.length") == 4


def test_lab_form_changes_portfolio_range_and_options(page):
    page.goto("/learn/lab")
    page.get_by_label("Portfolio", exact=True).select_option(label="S&P 500 only")
    page.get_by_label("When", exact=True).select_option("2020")
    page.get_by_label("Spread over", exact=True).select_option("6")
    page.get_by_label("Rebalance", exact=True).select_option("quarterly")
    page.get_by_role("button", name="Run it").click()
    page.wait_for_url("**/learn/lab?portfolio=example%3Asp500&range=2020&months=6&period=quarterly&cash=none")
    assert "Spread over 6 months" in page.locator("article[data-strategy=dca]").inner_text()
    assert page.locator("article[data-strategy=rebalance_quarterly]").is_visible()
    assert "VOO 100%" in page.locator("#lab-summary").inner_text()
    assert "Feb 19, 2020" in page.locator("#lab-summary").inner_text()
    assert "only one holding there is nothing to rebalance" in page.locator("#what-this-shows").inner_text()
    # The form remembers the choices.
    assert page.get_by_label("When", exact=True).input_value() == "2020"


def test_lab_offers_my_portfolios(page, live_app):
    from investaround.models import Holding, Portfolio

    live_app.store.add(Portfolio(name="Tech bet", holdings=[Holding("QQQ", weight=70), Holding("NVDA", weight=30)]))
    page.goto("/learn/lab")
    page.get_by_label("Portfolio", exact=True).select_option(label="Tech bet")
    page.get_by_role("button", name="Run it").click()
    page.locator("#lab-summary").get_by_text("Tech bet:").wait_for()
    assert "QQQ 70%" in page.locator("#lab-summary").inner_text()
    assert "drifted from 70% QQQ / 30% NVDA" in page.locator("#what-this-shows").inner_text()


def test_lab_offers_every_example_portfolio(page):
    from investaround.web.examples import load_examples

    page.goto("/learn/lab")
    picker = page.get_by_label("Portfolio", exact=True)
    examples = picker.locator("optgroup[label='Example portfolios'] option")
    assert examples.all_inner_texts() == [ex.name for ex in load_examples()]
    assert picker.locator("option:checked").inner_text() == "60/40 stocks and bonds"
    assert page.locator("optgroup[label='My portfolios']").count() == 0


def test_lab_waiting_cash_can_earn_interest(page):
    page.goto("/learn/lab")
    assert not page.get_by_label("Fixed rate, percent a year").is_visible()
    assert page.locator("[data-interest]").count() == 0
    page.get_by_label("Waiting cash earns").select_option(label="A fixed rate")
    page.get_by_label("Fixed rate, percent a year").fill("5")
    page.get_by_role("button", name="Run it").click()
    page.wait_for_url("**cash=fixed&cash_rate=5")
    dca = page.locator("article[data-strategy=dca]")
    assert "the rest waits as cash earning 5% a year" in dca.inner_text()
    assert dca.locator("[data-interest]").inner_text() != "$0"
    shows = page.locator("#what-this-shows").inner_text()
    assert "money waiting to be invested earned 5% a year: $" in shows
    assert "earns nothing" not in shows

    page.get_by_label("Waiting cash earns").select_option(label="Treasury bill rates")
    assert not page.get_by_label("Fixed rate, percent a year").is_visible()
    page.get_by_role("button", name="Run it").click()
    page.wait_for_url("**cash=tbill**")
    assert "earning Treasury bill rates, about" in page.locator("article[data-strategy=dca]").inner_text()
