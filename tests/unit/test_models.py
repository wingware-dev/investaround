import datetime as dt

import pytest

from investaround.models import (
    Holding, Portfolio, PriceBar, PriceSeries, Quote, ValidationError, normalize_symbol,
)


def _weights(*pairs):
    return [Holding(s, weight=w) for s, w in pairs]


class TestSymbols:
    def test_normalizes_case_and_space(self):
        assert normalize_symbol("  voo ") == "VOO"
        assert normalize_symbol("brk-b") == "BRK-B"
        assert normalize_symbol("^gspc") == "^GSPC"

    @pytest.mark.parametrize("bad", ["", "   ", "AB CD", "X" * 16, "A;B"])
    def test_rejects_bad(self, bad):
        with pytest.raises(ValidationError):
            normalize_symbol(bad)


class TestHolding:
    def test_weight_or_shares_exclusive(self):
        with pytest.raises(ValidationError):
            Holding("SPY")
        with pytest.raises(ValidationError):
            Holding("SPY", weight=50, shares=3)

    @pytest.mark.parametrize("w", [0, -1, 100.5])
    def test_weight_bounds(self, w):
        with pytest.raises(ValidationError):
            Holding("SPY", weight=w)

    def test_shares_positive(self):
        with pytest.raises(ValidationError):
            Holding("SPY", shares=0)

    def test_round_trip(self):
        for h in (Holding("spy", weight=60), Holding("BND", shares=12.5),
                  Holding("SPY", weight=60, start_price=655.46, start_date=dt.date(2026, 9, 30))):
            assert Holding.from_dict(h.to_dict()) == h

    def test_start_price_and_date(self):
        h = Holding("SPY", weight=60, start_price="655.46", start_date=dt.date(2026, 9, 30))
        assert h.start_price == 655.46
        assert h.to_dict() == {"symbol": "SPY", "weight": 60.0, "start_price": 655.46, "start_date": "2026-09-30"}
        assert "start_price" not in Holding("SPY", weight=60).to_dict()
        assert h.position == Holding("SPY", weight=60).position == ("SPY", 60.0, None)

    def test_start_price_needs_date_and_must_be_positive(self):
        with pytest.raises(ValidationError):
            Holding("SPY", weight=60, start_price=10)
        with pytest.raises(ValidationError):
            Holding("SPY", weight=60, start_date=dt.date(2026, 9, 30))
        with pytest.raises(ValidationError):
            Holding("SPY", weight=60, start_price=0, start_date=dt.date(2026, 9, 30))


class TestPortfolio:
    def test_valid_with_five_has_no_warning(self):
        p = Portfolio("Mix", _weights(("VTI", 40), ("VXUS", 20), ("BND", 20), ("GLD", 10), ("VNQ", 10)))
        assert p.validate() == []

    def test_few_holdings_warns(self):
        p = Portfolio("Just one", _weights(("SPY", 100)))
        [warning] = p.validate()
        assert "Only 1 holding:" in warning

    def test_weights_must_sum_to_100(self):
        p = Portfolio("Bad", _weights(("SPY", 60), ("BND", 30)))
        with pytest.raises(ValidationError, match="90%"):
            p.validate()

    def test_tolerates_float_rounding(self):
        p = Portfolio("Thirds", _weights(("SPY", 33.33), ("BND", 33.33), ("GLD", 33.34)))
        p.validate()

    def test_holding_count_limits(self):
        with pytest.raises(ValidationError):
            Portfolio("Empty", []).validate()
        many = [Holding(f"S{i}", shares=1) for i in range(21)]
        with pytest.raises(ValidationError, match="At most 20"):
            Portfolio("Many", many).validate()
        Portfolio("Twenty", many[:20]).validate()

    def test_duplicates_rejected(self):
        p = Portfolio("Dup", _weights(("SPY", 50), ("spy", 50)))
        with pytest.raises(ValidationError, match="SPY"):
            p.validate()

    def test_mixed_weights_and_shares_rejected(self):
        p = Portfolio("Mixed", [Holding("SPY", weight=100), Holding("BND", shares=3)])
        with pytest.raises(ValidationError):
            p.validate()

    def test_name_required_and_trimmed(self):
        with pytest.raises(ValidationError):
            Portfolio("   ", _weights(("SPY", 100))).validate()
        p = Portfolio("  Mine ", _weights(("SPY", 100)))
        p.validate()
        assert p.name == "Mine"

    def test_round_trip(self):
        p = Portfolio("RT", _weights(("SPY", 100)), start_cash=5000, created=dt.date(2024, 1, 2),
                      notes="n", source_example="sp500")
        assert Portfolio.from_dict(p.to_dict()) == p

    def test_ids_unique(self):
        assert Portfolio("a", []).id != Portfolio("b", []).id


class TestPrices:
    def test_quote_change(self):
        q = Quote("SPY", 110.0, 100.0)
        assert q.change == pytest.approx(10)
        assert q.change_pct == pytest.approx(10)
        assert Quote("SPY", 1.0, None).change_pct is None

    def test_series_sorted_and_sliced(self):
        d = dt.date
        s = PriceSeries("X", [PriceBar(d(2024, 1, 3), 3, 3), PriceBar(d(2024, 1, 1), 1, 1), PriceBar(d(2024, 1, 2), 2, 2)])
        assert [b.close for b in s.bars] == [1, 2, 3]
        assert s.first_date == d(2024, 1, 1) and s.last_date == d(2024, 1, 3)
        assert [b.close for b in s.between(d(2024, 1, 2), None).bars] == [2, 3]
        assert len(s.between(d(2025, 1, 1), None)) == 0
        assert s.between(d(2025, 1, 1), None).first_date is None
