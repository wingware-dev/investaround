"""The "What if?" history page, driven as a user would."""

from investaround.models import Holding, Portfolio
from investaround.prices.fake import FakePriceSource
from tests.ui.harness import new_page, start_app


def chart_datasets(page) -> int:
    page.wait_for_function("() => !!Chart.getChart(document.getElementById('history-chart'))")
    return page.evaluate("() => Chart.getChart(document.getElementById('history-chart')).data.datasets.length")


def metric(page, key: str) -> list[str]:
    """The portfolio and benchmark values shown in a metrics row."""
    return [c.inner_text().splitlines()[0] for c in page.locator(f'#metrics tr[data-metric="{key}"] td').all()]


def test_first_visit_explains_and_runs_nothing(page):
    page.goto("/history/")
    assert page.title() == "What if? · investaround"
    assert page.locator("#history-empty").is_visible()
    assert page.locator("#results").count() == 0
    # With no saved portfolios the Three-fund example is picked to start with.
    assert page.locator("#what").input_value() == "e:three-fund"
    assert not page.locator("#symbols").is_visible()


def test_example_link_runs_ten_years_against_spy(page):
    page.goto("/history/?example=sixty-forty")
    assert page.locator("#what").input_value() == "e:sixty-forty"
    results = page.locator("#results")
    assert results.get_by_role("heading", name="60/40").is_visible()
    assert "$10,000 put in on Oct 27, 2016" in results.locator("[data-headline]").inner_text()
    assert results.locator("[data-final]").inner_text().startswith("$")
    assert "The same money in SPY (S&P 500)" in results.locator("[data-benchmark-line]").inner_text()
    assert page.get_by_role("button", name="10 years").get_attribute("aria-pressed") == "true"
    assert chart_datasets(page) == 2
    assert page.locator("#metrics tbody tr").count() == 7
    for key in ("cagr", "vol", "best", "worst"):
        values = metric(page, key)
        assert len(values) == 2 and all(v.endswith("%") for v in values), (key, values)
    assert metric(page, "dd")[0].startswith("-")
    # Every metric has a plain-English tooltip.
    tips = page.locator("#metrics tbody .tip")
    assert tips.count() == 7
    assert all(len(t.get_attribute("data-tip")) > 40 for t in tips.all())


def test_2008_preset_starts_late_holdings_late_and_says_so(page, live_app):
    page.goto("/history/?example=three-fund")
    page.get_by_role("button", name="2008 crash").click()
    page.wait_for_url("**range=2008**")
    assert "Oct 1, 2007" in page.locator("[data-headline]").inner_text()
    note = page.locator("#start-notes")
    assert "VXUS has no prices before Jan 28, 2011, so its 30% ($3,000) waited as cash" in note.inner_text()
    assert page.locator('#holdings tr[data-symbol="VXUS"]').get_by_text("Jan 28, 2011 (late)").is_visible()
    assert page.locator('#holdings tr[data-symbol="VTI"]').get_by_text("Oct 1, 2007").is_visible()
    assert chart_datasets(page) == 2


def test_own_mix_over_one_year_shows_na_for_yearly_numbers(page):
    page.goto("/history/")
    page.locator("#what").select_option("custom")
    symbols = page.locator("#symbols")
    assert symbols.is_visible()
    symbols.fill("AAPL 50, MSFT 50")
    page.get_by_role("button", name="1 year").click()
    page.wait_for_url("**range=1y**")
    assert page.locator("#results").get_by_role("heading", name="Your mix: 1 year").is_visible()
    assert metric(page, "cagr") == ["n/a", "n/a"]
    assert metric(page, "best") == ["n/a", "n/a"]
    assert metric(page, "worst") == ["n/a", "n/a"]
    assert [r.get_attribute("data-symbol") for r in page.locator("#holdings tbody tr").all()] == ["AAPL", "MSFT"]


def test_own_mix_with_uneven_weights_is_scaled(page):
    page.goto("/history/?what=custom&symbols=SPY+3,+BND+1&range=5y")
    assert "Your weights added up to 4%, so they were scaled to make 100%." in page.locator("#start-notes").inner_text()
    assert page.locator('#holdings tr[data-symbol="SPY"] td').nth(1).inner_text() == "75%"


def test_symbol_with_no_prices_in_range_stays_cash(page):
    page.goto("/history/?what=custom&symbols=SPY,+VXUS&range=custom&start=2008-01-01&end=2009-12-31")
    note = page.locator("#start-notes").inner_text()
    assert "VXUS has no prices at all in this range, so its 50% ($5,000) stayed as cash" in note
    assert page.locator('#holdings tr[data-symbol="VXUS"]').get_by_text("No prices: kept as cash").is_visible()
    assert page.locator('#holdings tr[data-symbol="cash"]').get_by_text("$5,000").is_visible()


def test_saved_portfolio_is_offered_first(page, live_app):
    live_app.store.add(Portfolio(name="My first try", holdings=[
        Holding("VOO", weight=70), Holding("BND", weight=30)]))
    page.goto("/history/")
    assert page.locator("#what option:checked").inner_text() == "My first try"
    page.get_by_role("button", name="5 years").click()
    page.wait_for_url("**range=5y**")
    assert page.locator("#results").get_by_role("heading", name="My first try: 5 years").is_visible()


def test_bad_inputs_get_friendly_messages(page):
    page.goto("/history/?example=no-such-example")
    assert page.get_by_text("There is no example by that name. Pick one from the list.").is_visible()
    assert page.locator("#results").count() == 0

    page.goto("/history/?what=custom&symbols=VTI+60,+NOTREAL+40")
    assert "No prices are known for NOTREAL" in page.locator("#symbols-field").inner_text()

    page.goto("/history/?what=custom&symbols=VTI+60,+BND")
    assert "Give a weight for every symbol, or for none" in page.locator("#symbols-field").inner_text()

    page.goto("/history/?what=custom&symbols=VTI&range=custom&start=2020-05-01&end=2019-01-01")
    assert page.get_by_text("The start date must be before the end date").is_visible()

    page.goto("/history/?portfolio=gone")
    assert page.get_by_text("That portfolio is not in My portfolios any more").is_visible()


def test_benchmark_failure_still_shows_the_portfolio(browser, tmp_path):
    live = start_app(tmp_path / "data", PRICE_SOURCE_OBJ=FakePriceSource(fail_symbols={"SPY"}))
    errors: list[str] = []
    page = new_page(browser, live, errors)
    try:
        page.goto("/history/?example=three-fund")
        assert page.locator("[data-final]").inner_text().startswith("$")
        assert "Could not get SPY prices right now" in page.locator("#start-notes").inner_text()
        assert page.locator("[data-benchmark-line]").count() == 0
        assert chart_datasets(page) == 1
        assert len(metric(page, "final")) == 1
    finally:
        page.context.close()
        live.stop()
    assert not errors


def test_price_failure_for_a_holding_says_so(browser, tmp_path):
    live = start_app(tmp_path / "data", PRICE_SOURCE_OBJ=FakePriceSource(fail_symbols={"BND"}))
    errors: list[str] = []
    page = new_page(browser, live, errors)
    try:
        page.goto("/history/?example=three-fund")
        alert = page.locator(".notice-error")
        assert "Could not get prices for BND right now" in alert.inner_text()
        assert page.locator("#results").count() == 0
    finally:
        page.context.close()
        live.stop()
    assert not errors


def test_cash_waiting_for_a_late_holding_can_earn_tbill_rates(page):
    page.goto("/history/?example=three-fund&range=2008")
    # Off by default: no interest row, and the rate box is hidden.
    assert page.locator('#metrics tr[data-metric="interest"]').count() == 0
    assert not page.locator("#cash_rate").is_visible()
    worth_at_zero = page.locator("[data-final]").inner_text()

    page.get_by_label("Waiting cash earns").select_option(label="Treasury bill rates")
    assert not page.locator("#cash_rate").is_visible()
    page.get_by_role("button", name="2008 crash").click()
    page.wait_for_url("**cash=tbill**")
    note = page.locator("#start-notes").inner_text()
    assert "Cash waiting to be invested earned Treasury bill rates, about" in note
    assert "in interest, counted in the results" in note
    interest = metric(page, "interest")
    assert interest[0].startswith("$") and interest[0] != "$0"
    assert interest[1] == "$0"  # SPY had prices from the start, so nothing waited
    assert page.locator("[data-final]").inner_text() != worth_at_zero
    assert page.get_by_label("Waiting cash earns").input_value() == "tbill"


def test_cash_at_a_fixed_rate(page):
    page.goto("/history/?example=three-fund&range=2008")
    page.get_by_label("Waiting cash earns").select_option(label="A fixed rate")
    rate = page.get_by_label("Fixed rate, percent a year")
    assert rate.is_visible() and rate.input_value() == "4"
    rate.fill("3")
    page.get_by_role("button", name="Show me").click()
    page.wait_for_url("**cash=fixed&cash_rate=3**")
    assert "earned 3% a year: $" in page.locator("#start-notes").inner_text()

    rate = page.get_by_label("Fixed rate, percent a year")
    rate.fill("lots")
    page.get_by_role("button", name="Show me").click()
    page.wait_for_url("**cash_rate=lots**")
    assert "Give the rate as a number of percent a year" in page.locator("#cash-field").inner_text()
    assert page.locator("#results").count() == 0
