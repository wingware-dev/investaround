"""Portfolio valuation, form parsing and the routes behind the builder and watch page."""

import datetime as dt

import pytest
from werkzeug.datastructures import MultiDict

from investaround.app import create_app
from investaround.models import Holding, Portfolio
from investaround.prices.base import PriceSourceError
from investaround.prices.fake import FakePriceSource
from investaround.web.portfolios import money, parse_form, pct, start_bar, value_portfolio


@pytest.fixture(scope="module")
def prices():
    return FakePriceSource()


@pytest.fixture
def app(tmp_path):
    return create_app({"DATA_DIR": str(tmp_path / "data"), "PRICE_SOURCE": "fake", "TESTING": True})


@pytest.fixture
def client(app):
    return app.test_client()


def _adj(prices, sym, day):
    return next(b for b in prices.history(sym, day, day).bars).adjclose


# ------------------------------------------------------------ valuation

def test_start_bar_is_last_close_before_created(prices):
    # 2026-10-05 is a Monday: the start is Friday's close.
    assert start_bar(prices, "SPY", dt.date(2026, 10, 5)).date == dt.date(2026, 10, 2)
    assert start_bar(prices, "SPY", dt.date(2026, 10, 1)).date == dt.date(2026, 9, 30)


def test_start_bar_falls_back_to_first_close_after(prices):
    first = prices.history("VXUS").first_date
    assert start_bar(prices, "VXUS", first - dt.timedelta(days=60)).date == first


def test_start_bar_none_past_the_data(prices):
    assert start_bar(prices, "SPY", prices.today + dt.timedelta(days=30)) is None


def test_value_by_weight(prices):
    p = Portfolio("Mix", [Holding("SPY", weight=60), Holding("BND", weight=40)], created=dt.date(2026, 10, 1))
    pv = value_portfolio(p, prices)
    spy, bnd = pv.rows
    assert spy.cost == pytest.approx(6000)
    assert spy.value == pytest.approx(6000 * 680.0 / _adj(prices, "SPY", dt.date(2026, 9, 30)))
    assert bnd.value == pytest.approx(4000 * 72.0 / _adj(prices, "BND", dt.date(2026, 9, 30)))
    assert spy.gain == pytest.approx(spy.value - 6000)
    assert spy.day_change == pytest.approx(spy.value * (1 - 674.432439 / 680.0))
    assert pv.value == pytest.approx(spy.value + bnd.value)
    assert pv.gain_pct == pytest.approx((pv.value / 10000 - 1) * 100)
    assert pv.day_change_pct == pytest.approx(pv.day_change / (pv.value - pv.day_change) * 100)
    assert pv.started_with == 10000
    assert pv.start_dates == [dt.date(2026, 9, 30)]
    assert pv.missing == [] and pv.error is None
    assert pv.prices_as_of is not None


def test_first_day_gain_is_todays_change(prices):
    p = Portfolio("New", [Holding("SPY", weight=100)], created=prices.today)
    pv = value_portfolio(p, prices)
    assert pv.gain == pytest.approx(pv.day_change)


def test_value_by_shares(prices):
    p = Portfolio("Shares", [Holding("SPY", shares=2)], created=dt.date(2026, 10, 1))
    pv = value_portfolio(p, prices)
    close = prices.history("SPY", dt.date(2026, 9, 30), dt.date(2026, 9, 30)).bars[0].close
    assert pv.rows[0].cost == pytest.approx(2 * close)
    assert pv.started_with == pytest.approx(2 * close)


def test_unknown_symbol_left_out_of_totals(prices):
    p = Portfolio("Odd", [Holding("SPY", weight=50), Holding("NOPE", weight=50)], created=dt.date(2026, 10, 1))
    pv = value_portfolio(p, prices)
    assert pv.missing == ["NOPE"]
    assert pv.rows[1].problem == "No price found"
    assert pv.value == pytest.approx(pv.rows[0].value)
    assert pv.cost == pytest.approx(5000)


def test_price_source_down_reports_error(prices):
    down = FakePriceSource(fail_symbols={"BND"})
    p = Portfolio("Mix", [Holding("SPY", weight=60), Holding("BND", weight=40)])
    pv = value_portfolio(p, down)
    assert "Could not get prices" in pv.error
    assert pv.value is None and pv.gain is None and pv.day_change is None
    assert pv.missing == ["SPY", "BND"]


def test_formatting():
    assert money(1234.5) == "$1,234.50"
    assert money(-3, signed=True) == "−$3.00"
    assert money(3, signed=True) == "+$3.00"
    assert money(None) == "—"
    assert pct(1.234) == "+1.23%"
    assert pct(-0.5) == "−0.50%"
    assert pct(None) == "—"


# ------------------------------------------------------------ form parsing

def test_parse_form():
    form = MultiDict([("name", " Mine "), ("notes", "n"), ("symbol", "spy"), ("weight", "60"),
                      ("symbol", "BND"), ("weight", "40"), ("holding_name", "S&P"), ("holding_name", "Bonds")])
    name, notes, rows, holdings, errors = parse_form(form)
    assert (name, notes, errors) == ("Mine", "n", [])
    assert [h.to_dict() for h in holdings] == [{"symbol": "SPY", "weight": 60.0}, {"symbol": "BND", "weight": 40.0}]
    assert [(r.symbol, r.name, r.weight) for r in rows] == [("SPY", "S&P", "60"), ("BND", "Bonds", "40")]


def test_parse_form_bad_weights():
    form = MultiDict([("symbol", "SPY"), ("weight", "lots"), ("symbol", "BND"), ("weight", "0")])
    _, _, rows, holdings, errors = parse_form(form)
    assert holdings == []
    assert errors == ["SPY: enter a weight in percent, like 10", "BND: weight must be above 0 and at most 100"]
    assert len(rows) == 2


# ------------------------------------------------------------ routes

def _create(client, name="Mine", pairs=(("SPY", "60"), ("BND", "40"))):
    data = MultiDict([("name", name)] + [kv for s, w in pairs for kv in (("symbol", s), ("weight", w))])
    return client.post("/portfolios/new", data=data)


def test_create_redirects_to_watch(client, app):
    resp = _create(client)
    assert resp.status_code == 303
    with app.app_context():
        from investaround.app import get_store
        (p,) = get_store().list()
    assert resp.location == f"/portfolios/{p.id}/"
    assert p.created == dt.date.today()
    page = client.get(resp.location).get_data(as_text=True)
    assert "Gain since start" in page and "State Street SPDR" in page


@pytest.mark.parametrize("pairs, message", [
    ((("SPY", "60"), ("BND", "30")), "Weights add up to 90%, not 100%"),
    ((("SPY", "50"), ("ZZZZ", "50")), "No prices found for ZZZZ"),
    ((("SPY", "50"), ("SPY", "50")), "Listed more than once: SPY"),
    ((), "Add at least one holding"),
    ([(f"S{i}", "4") for i in range(21)], "At most 20 holdings"),
])
def test_create_rejects(client, pairs, message):
    resp = _create(client, pairs=pairs)
    assert resp.status_code == 400
    assert message in resp.get_data(as_text=True)


def test_create_without_name_says_so_with_other_errors(client):
    resp = _create(client, name="", pairs=(("SPY", "x"),))
    body = resp.get_data(as_text=True)
    assert "Give the portfolio a name" in body and "SPY: enter a weight" in body


def _seed(app, created=dt.date(2026, 10, 1)):
    p = Portfolio("Seeded", [Holding("SPY", weight=60), Holding("BND", weight=40)], created=created)
    app.extensions["investaround.store"].add(p)
    return p


def test_edit_name_only_keeps_start(client, app):
    p = _seed(app)
    resp = client.post(f"/portfolios/{p.id}/edit", data=MultiDict(
        [("name", "Renamed"), ("symbol", "SPY"), ("weight", "60"), ("symbol", "BND"), ("weight", "40")]))
    assert resp.status_code == 303
    q = app.extensions["investaround.store"].get(p.id)
    assert (q.name, q.created) == ("Renamed", dt.date(2026, 10, 1))


def test_edit_holdings_restarts(client, app):
    p = _seed(app)
    client.post(f"/portfolios/{p.id}/edit", data=MultiDict(
        [("name", "Seeded"), ("symbol", "SPY"), ("weight", "100")]))
    q = app.extensions["investaround.store"].get(p.id)
    assert q.created == dt.date.today()
    assert [h.symbol for h in q.holdings] == ["SPY"]


def test_delete(client, app):
    p = _seed(app)
    assert client.get(f"/portfolios/{p.id}/delete").status_code == 200
    resp = client.post(f"/portfolios/{p.id}/delete")
    assert resp.status_code == 303 and "deleted=Seeded" in resp.location
    assert app.extensions["investaround.store"].list() == []
    assert client.get(f"/portfolios/{p.id}/").status_code == 404


def test_watch_table_fragment(client, app):
    p = _seed(app)
    body = client.get(f"/portfolios/{p.id}/table").get_data(as_text=True)
    assert body.lstrip().startswith("<div id=\"watch-live\"")
    assert "<html" not in body


def test_unknown_portfolio_404(client):
    for url in ("/portfolios/nope/", "/portfolios/nope/edit", "/portfolios/nope/table", "/portfolios/nope/delete"):
        assert client.get(url).status_code == 404


def test_api_search(client):
    data = client.get("/api/search?q=vanguard").get_json()
    assert data["query"] == "vanguard"
    assert {"symbol": "VOO", "name": "Vanguard S&P 500 ETF", "type": "ETF", "exchange": "NYSEArca"} in data["results"]
    assert client.get("/api/search?q=").get_json()["results"] == []


def test_api_search_unavailable(tmp_path):
    class Down(FakePriceSource):
        def search(self, query, limit=10):
            raise PriceSourceError("rate limited")

    app = create_app({"DATA_DIR": str(tmp_path), "PRICE_SOURCE_OBJ": Down(), "TESTING": True})
    resp = app.test_client().get("/api/search?q=spy")
    assert resp.status_code == 503
    assert "rate limited" in resp.get_json()["error"]
