import pytest

from investaround.app import create_app
from investaround.prices.base import PriceSourceError
from investaround.prices.fake import FakePriceSource

PAGES = ["/", "/portfolios/", "/history/", "/examples/", "/learn/"]


@pytest.fixture
def app(tmp_path):
    return create_app({"DATA_DIR": str(tmp_path / "data"), "PRICE_SOURCE": "fake", "TESTING": True})


@pytest.mark.parametrize("url", PAGES)
def test_every_page_renders_with_nav(app, url):
    resp = app.test_client().get(url)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    for page in PAGES:
        assert f'href="{page}"' in html
    assert html.count('aria-current="page"') == 1
    assert "chart.umd.min.js" in html
    assert "recorded sample data" in html


def test_static_assets_served(app):
    client = app.test_client()
    assert client.get("/static/css/app.css").status_code == 200
    assert client.get("/static/vendor/chart.umd.min.js").status_code == 200


def test_404_page(app):
    resp = app.test_client().get("/nowhere")
    assert resp.status_code == 404
    assert "Page not found" in resp.get_data(as_text=True)


def test_services(app, tmp_path):
    from investaround.app import get_prices, get_store

    with app.app_context():
        assert get_prices().name == "fake"
        assert get_store().path == tmp_path / "data" / "portfolios.json"


def test_price_source_object_override(tmp_path):
    src = FakePriceSource()
    app = create_app({"DATA_DIR": str(tmp_path), "PRICE_SOURCE_OBJ": src})
    assert app.extensions["investaround.prices"] is src


def test_env_selects_source(tmp_path, monkeypatch):
    monkeypatch.setenv("INVESTAROUND_PRICE_SOURCE", "bogus")
    with pytest.raises(ValueError, match="bogus"):
        create_app({"DATA_DIR": str(tmp_path)})


def test_price_error_page(app):
    @app.get("/boom")
    def boom():
        raise PriceSourceError("rate limited")

    resp = app.test_client().get("/boom")
    assert resp.status_code == 503
    assert "rate limited" in resp.get_data(as_text=True)
