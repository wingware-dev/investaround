"""The "cash earns" option shared by the history page and the strategy lab."""

import datetime as dt

import pytest

from investaround.analytics import simulate
from investaround.models import PriceBar, PriceSeries
from investaround.prices.fake import FakePriceSource
from investaround.web.cash import CashForm, read_cash, resolve_cash, tbill_average

D = dt.date


class TestReadCash:
    def test_default_is_nothing(self):
        form = read_cash({})
        assert (form.kind, form.error) == ("none", None)

    def test_unknown_kind_falls_back(self):
        assert read_cash({"cash": "bitcoin"}).kind == "none"

    @pytest.mark.parametrize("text", ["4", "2.5", "0", "20", " 3 % "])
    def test_fixed_rates(self, text):
        form = read_cash({"cash": "fixed", "cash_rate": text})
        assert (form.kind, form.error) == ("fixed", None)

    def test_fixed_rate_defaults_to_four(self):
        assert read_cash({"cash": "fixed"}).rate_text == "4"

    @pytest.mark.parametrize("text,message", [
        ("abc", "Give the rate as a number"), ("-1", "from 0% to 20%"), ("25", "from 0% to 20%")])
    def test_bad_fixed_rates(self, text, message):
        assert message in read_cash({"cash": "fixed", "cash_rate": text}).error

    def test_rate_text_ignored_unless_fixed(self):
        assert read_cash({"cash": "tbill", "cash_rate": "abc"}).error is None


class TestResolveCash:
    START, END = D(2023, 1, 1), D(2023, 12, 31)

    def test_none_and_fixed(self):
        src = FakePriceSource()
        none = resolve_cash(CashForm("none", "4"), src, self.START, self.END)
        assert (none.earns, none.rate) == (False, 0.0)
        fixed = resolve_cash(read_cash({"cash": "fixed", "cash_rate": "2.5%"}), src, self.START, self.END)
        assert (fixed.earns, fixed.rate, fixed.note) == (True, pytest.approx(0.025), None)

    def test_tbill_uses_recorded_irx_yields(self):
        cash = resolve_cash(CashForm("tbill", ""), FakePriceSource(), self.START, self.END)
        assert cash.earns and cash.note is None
        assert cash.rate.symbol == "^IRX"
        assert all(4 < b.close < 5.5 for b in cash.rate.between(self.START, self.END).bars)

    def test_tbill_failure_falls_back_to_nothing_with_a_note(self):
        cash = resolve_cash(CashForm("tbill", ""), FakePriceSource(fail_symbols={"^IRX"}), self.START, self.END)
        assert (cash.earns, cash.rate) == (False, 0.0)
        assert "Could not get Treasury bill rates right now" in cash.note

    def test_tbill_with_no_rates_in_range(self):
        cash = resolve_cash(CashForm("tbill", ""), FakePriceSource(), D(1990, 1, 1), D(1990, 12, 31))
        assert not cash.earns
        assert "no Treasury bill rates for these dates" in cash.note


class TestPhrase:
    DAYS = [D(2024, 1, 2), D(2024, 1, 3), D(2024, 1, 4)]

    def test_fixed_and_none(self):
        src = FakePriceSource()
        vs = simulate({"A": PriceSeries("A", [PriceBar(d, 1, 1) for d in self.DAYS])}, {"A": 1},
                      deposits={self.DAYS[0]: 100})
        assert resolve_cash(read_cash({"cash": "fixed", "cash_rate": "4"}), src, None, self.DAYS[-1]).phrase(vs) \
            == "4% a year"
        assert resolve_cash(read_cash({}), src, None, self.DAYS[-1]).phrase(vs) == "nothing (0%)"

    def test_tbill_average_is_weighted_by_cash_waiting(self):
        a = PriceSeries("A", [PriceBar(d, 1, 1) for d in self.DAYS])
        # 300 waits on day one at 3%, 100 on day two at 6% (forward-filled), none on day three
        irx = PriceSeries("^IRX", [PriceBar(self.DAYS[0], 3, 3), PriceBar(D(2023, 12, 1), 9, 9),
                                   PriceBar(self.DAYS[1], 6, 6)])
        vs = simulate({"A": a}, {"A": 1}, deposits={self.DAYS[0]: 400},
                      buys={self.DAYS[0]: 100, self.DAYS[1]: 200, self.DAYS[2]: 1e9})
        assert vs.cash[0] == 300 and vs.cash[2] == 0
        assert tbill_average(irx, vs) == pytest.approx((300 * 3 + vs.cash[1] * 6) / (300 + vs.cash[1]))

    def test_tbill_average_none_without_waiting_cash(self):
        a = PriceSeries("A", [PriceBar(d, 1, 1) for d in self.DAYS])
        vs = simulate({"A": a}, {"A": 1}, deposits={self.DAYS[0]: 100})
        irx = PriceSeries("^IRX", [PriceBar(self.DAYS[0], 3, 3)])
        assert tbill_average(irx, vs) is None
