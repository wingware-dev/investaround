import datetime as dt
import json

import pytest

from investaround.models import Holding, Portfolio, ValidationError
from investaround.storage import PortfolioNotFound, PortfolioStore


@pytest.fixture
def store(tmp_path):
    return PortfolioStore(tmp_path / "data" / "portfolios.json")


def _portfolio(name="Test", **kw):
    return Portfolio(name, [Holding("SPY", weight=60), Holding("BND", weight=40)], **kw)


def test_empty_when_missing(store):
    assert store.list() == []
    assert not store.path.exists()


def test_add_get_list(store):
    p = _portfolio()
    warnings = store.add(p)
    assert warnings and "Only 2 holdings" in warnings[0]
    assert store.get(p.id) == p
    assert [x.id for x in store.list()] == [p.id]
    # Persisted and readable by a fresh store
    assert PortfolioStore(store.path).get(p.id) == p


def test_loads_holdings_saved_without_start_prices(store):
    store.path.parent.mkdir(parents=True)
    store.path.write_text(json.dumps({"version": 1, "portfolios": [{
        "id": "old1", "name": "Old", "created": "2026-10-01",
        "holdings": [{"symbol": "SPY", "weight": 60}, {"symbol": "BND", "weight": 40}],
    }]}))
    (p,) = store.list()
    assert [(h.start_price, h.start_date) for h in p.holdings] == [(None, None), (None, None)]


def test_start_prices_persist(store):
    p =Portfolio("New", [Holding("SPY", weight=100, start_price=655.46, start_date=dt.date(2026, 9, 30))])
    store.add(p)
    assert PortfolioStore(store.path).get(p.id).holdings[0].start_price == 655.46


def test_add_validates_and_writes_nothing(store):
    with pytest.raises(ValidationError):
        store.add(Portfolio("Bad", [Holding("SPY", weight=50)]))
    assert not store.path.exists()


def test_duplicate_id_rejected(store):
    p = _portfolio()
    store.add(p)
    with pytest.raises(ValueError):
        store.add(p)


def test_update(store):
    p = _portfolio()
    store.add(p)
    p.name = "Renamed"
    store.update(p)
    assert store.get(p.id).name == "Renamed"
    with pytest.raises(PortfolioNotFound):
        store.update(_portfolio("Never added"))


def test_delete(store):
    a, b = _portfolio("A"), _portfolio("B")
    store.add(a)
    store.add(b)
    store.delete(a.id)
    assert [x.name for x in store.list()] == ["B"]
    with pytest.raises(PortfolioNotFound):
        store.delete(a.id)
    with pytest.raises(PortfolioNotFound):
        store.get(a.id)


def test_file_format_and_no_temp_left(store):
    store.add(_portfolio())
    raw = json.loads(store.path.read_text())
    assert raw["version"] == 1
    assert raw["portfolios"][0]["holdings"][0] == {"symbol": "SPY", "weight": 60.0}
    assert [f.name for f in store.path.parent.iterdir()] == ["portfolios.json"]


def test_failed_write_keeps_old_file(store, monkeypatch):
    p = _portfolio()
    store.add(p)
    before = store.path.read_text()

    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr("investaround.storage.os.replace", boom)
    with pytest.raises(OSError):
        store.add(_portfolio("Other"))
    assert store.path.read_text() == before
    assert [f.name for f in store.path.parent.iterdir()] == ["portfolios.json"]
