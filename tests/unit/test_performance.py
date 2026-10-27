import datetime as dt
import math

import pytest

from investaround.analytics import (
    AnalyticsError, compare_to_benchmark, daily_returns, metrics, portfolio_value_series, simulate,
)
from investaround.models import Holding, PriceBar, PriceSeries

D = dt.date


def series(symbol, points, closes=None):
    """PriceSeries from [(date, adjclose)]; close defaults to adjclose."""
    closes = closes or [p for _, p in points]
    return PriceSeries(symbol, [PriceBar(d, c, p) for (d, p), c in zip(points, closes)])


DAYS = [D(2024, 1, 2), D(2024, 1, 3), D(2024, 1, 4)]
A = series("A", list(zip(DAYS, [100, 110, 121])))
B = series("B", list(zip(DAYS, [50, 50, 25])))


class TestBuyAndHold:
    def setup_method(self):
        self.vs = portfolio_value_series(
            [Holding("A", weight=50), Holding("B", weight=50)], {"A": A, "B": B}, start_cash=1000)
        self.m = metrics(self.vs)

    def test_values(self):
        # 5 units of A, 10 of B
        assert self.vs.values == pytest.approx([1000, 1050, 855])
        assert self.vs.holdings["A"] == pytest.approx([500, 550, 605])
        assert self.vs.holdings["B"] == pytest.approx([500, 500, 250])
        assert self.vs.cash == pytest.approx([0, 0, 0])

    def test_returns(self):
        assert self.m.deposited == 1000
        assert self.m.final_value == pytest.approx(855)
        assert self.m.gain == pytest.approx(-145)
        assert self.m.total_return == pytest.approx(-0.145)
        assert self.m.time_weighted_return == pytest.approx(-0.145)

    def test_volatility(self):
        r1, r2 = 0.05, 855 / 1050 - 1
        # stdev of two numbers is their distance over sqrt(2)
        assert self.m.volatility == pytest.approx(abs(r1 - r2) / math.sqrt(2) * math.sqrt(252))

    def test_drawdown(self):
        dd = self.m.max_drawdown
        assert dd.depth == pytest.approx(855 / 1050 - 1)
        assert (dd.peak, dd.trough, dd.recovered) == (DAYS[1], DAYS[2], None)

    def test_contribution(self):
        a, b = self.m.holdings
        assert (a.symbol, a.weight, a.invested, a.final_value) == ("A", 0.5, 500, pytest.approx(605))
        assert a.gain == pytest.approx(105)
        assert a.contribution == pytest.approx(0.105)
        assert a.price_return == pytest.approx(0.21)
        assert b.gain == pytest.approx(-250)
        assert b.contribution == pytest.approx(-0.25)
        assert b.price_return == pytest.approx(-0.5)
        assert a.contribution + b.contribution == pytest.approx(self.m.total_return)

    def test_short_range_has_no_cagr_or_years(self):
        assert self.m.cagr is None
        assert self.m.best_year is None and self.m.worst_year is None

    def test_date_range(self):
        vs = portfolio_value_series([Holding("A", weight=100)], {"A": A}, 1000, start=DAYS[1])
        assert vs.dates == DAYS[1:]
        assert vs.values == pytest.approx([1000, 1100])


class TestCagrAndYears:
    def test_cagr(self):
        s = series("A", [(D(2020, 1, 1), 100), (D(2022, 1, 1), 121)])
        m = metrics(portfolio_value_series([Holding("A", weight=100)], {"A": s}, 1000))
        assert m.years == pytest.approx(731 / 365.25)
        assert m.cagr == pytest.approx(1.21 ** (365.25 / 731) - 1)

    def test_yearly_best_worst(self):
        s = series("A", [(D(2020, 1, 2), 100), (D(2020, 6, 30), 120), (D(2020, 12, 31), 110),
                         (D(2021, 6, 30), 99), (D(2021, 12, 31), 132), (D(2022, 3, 1), 66)])
        m = metrics(portfolio_value_series([Holding("A", weight=100)], {"A": s}, 1000))
        assert [(y.year, round(y.ret, 9), y.partial) for y in m.yearly] == [
            (2020, 0.1, False), (2021, 0.2, False), (2022, -0.5, True)]
        # The partial 2022 is not a candidate for worst year
        assert m.best_year.year == 2021
        assert m.worst_year.year == 2020
        dd = m.max_drawdown
        assert dd.depth == pytest.approx(-0.5)
        assert (dd.peak, dd.trough, dd.recovered) == (D(2021, 12, 31), D(2022, 3, 1), None)

    def test_partial_first_year(self):
        s = series("A", [(D(2020, 3, 2), 100), (D(2020, 12, 31), 110), (D(2021, 12, 31), 99)])
        m = metrics(portfolio_value_series([Holding("A", weight=100)], {"A": s}, 1000))
        assert [y.partial for y in m.yearly] == [True, False]
        assert m.best_year == m.worst_year == m.yearly[1]

    def test_drawdown_recovery(self):
        days = [D(2024, 1, d) for d in (2, 3, 4, 5, 8)]
        s = series("A", list(zip(days, [100, 80, 90, 100, 105])))
        dd = metrics(portfolio_value_series([Holding("A", weight=100)], {"A": s}, 1000)).max_drawdown
        assert dd.depth == pytest.approx(-0.2)
        assert (dd.peak, dd.trough, dd.recovered) == (days[0], days[1], days[3])

    def test_never_falls(self):
        s = series("A", list(zip(DAYS, [100, 101, 102])))
        assert metrics(portfolio_value_series([Holding("A", weight=100)], {"A": s}, 1000)).max_drawdown is None


class TestMissingData:
    def test_late_start_waits_as_cash(self):
        days = [D(2024, 1, d) for d in (2, 3, 4, 5)]
        a = series("A", list(zip(days, [10, 20, 20, 20])))
        b = series("B", list(zip(days[2:], [5, 10])))
        vs = portfolio_value_series([Holding("A", weight=50), Holding("B", weight=50)],
                                    {"A": a, "B": b}, 1000)
        assert vs.late_starts == {"B": days[2]}
        assert vs.no_data == []
        assert vs.cash == pytest.approx([500, 500, 0, 0])
        assert vs.holdings["B"] == pytest.approx([0, 0, 500, 1000])
        assert vs.values == pytest.approx([1000, 1500, 1500, 2000])
        hb = metrics(vs).holdings[1]
        assert (hb.started, hb.invested, hb.gain, hb.price_return) == (days[2], 500, 1000 - 500, 1.0)

    def test_no_data_symbol_stays_cash(self):
        vs = portfolio_value_series([Holding("A", weight=75), Holding("ZZZ", weight=25)],
                                    {"A": A}, 1000)
        assert vs.no_data == ["ZZZ"]
        assert vs.cash == pytest.approx([250, 250, 250])
        assert vs.values == pytest.approx([1000, 750 * 1.1 + 250, 750 * 1.21 + 250])
        hz = metrics(vs).holdings[1]
        assert (hz.started, hz.price_return, hz.gain) == (None, None, 0)

    def test_prices_forward_fill_across_gaps(self):
        days = [D(2024, 1, d) for d in (2, 3, 4)]
        a = series("A", list(zip(days, [10, 11, 12])))
        b = series("B", [(days[0], 100), (days[2], 120)])  # closed on the 3rd
        vs = portfolio_value_series([Holding("A", weight=50), Holding("B", weight=50)],
                                    {"A": a, "B": b}, 1000)
        assert vs.holdings["B"] == pytest.approx([500, 500, 600])
        assert vs.late_starts == {}

    def test_nothing_in_range(self):
        with pytest.raises(AnalyticsError):
            portfolio_value_series([Holding("A", weight=100)], {"A": A}, 1000, start=D(2030, 1, 1))
        with pytest.raises(AnalyticsError):
            portfolio_value_series([Holding("Q", weight=100)], {}, 1000)


class TestShares:
    def test_share_holdings_use_close_for_cost_and_adjclose_for_growth(self):
        # Adjusted closes are half the closes (past dividends); growth is 20%
        a = series("A", [(DAYS[0], 50), (DAYS[1], 60)], closes=[100, 110])
        vs = portfolio_value_series([Holding("A", shares=2)], {"A": a})
        assert vs.values == pytest.approx([200, 240])
        assert metrics(vs).total_return == pytest.approx(0.2)

    def test_mixed_rejected(self):
        with pytest.raises(AnalyticsError):
            portfolio_value_series([Holding("A", weight=50), Holding("B", shares=1)], {"A": A, "B": B})


class TestInputs:
    @pytest.mark.parametrize("weights", [{}, {"A": 0}, {"A": -1}, {"A": float("nan")}])
    def test_bad_weights(self, weights):
        with pytest.raises(AnalyticsError):
            simulate({"A": A}, weights, deposits={DAYS[0]: 1000})

    def test_bad_rebalance(self):
        with pytest.raises(AnalyticsError):
            simulate({"A": A}, {"A": 1}, deposits={DAYS[0]: 1000}, rebalance="weekly")

    def test_needs_money_on_day_one(self):
        with pytest.raises(AnalyticsError):
            simulate({"A": A}, {"A": 1}, deposits={DAYS[1]: 1000})

    def test_deposits_do_not_count_as_returns(self):
        vs = simulate({"A": A}, {"A": 1}, deposits={DAYS[0]: 1000, DAYS[1]: 1100})
        assert vs.values == pytest.approx([1000, 2200, 2420])
        assert daily_returns(vs) == pytest.approx([0.1, 0.1])


class TestBenchmark:
    def test_buy_and_hold_vs_benchmark(self):
        spy = series("SPY", list(zip(DAYS, [200, 210, 220])))
        vs = portfolio_value_series([Holding("A", weight=100)], {"A": A}, 1000)
        c = compare_to_benchmark(vs, spy)
        assert c.benchmark_symbol == "SPY"
        assert c.benchmark_series.values == pytest.approx([1000, 1050, 1100])
        assert c.portfolio.total_return == pytest.approx(0.21)
        assert c.benchmark.total_return == pytest.approx(0.10)
        assert c.excess_return == pytest.approx(0.11)
        assert c.excess_cagr is None

    def test_benchmark_gets_same_money_on_same_days(self):
        spy = series("SPY", list(zip(DAYS, [200, 100, 100])))
        vs = simulate({"A": A}, {"A": 1}, deposits={DAYS[0]: 1000, DAYS[1]: 1000})
        c = compare_to_benchmark(vs, spy)
        # 5 units, then 10 more at 100
        assert c.benchmark_series.values == pytest.approx([1000, 1500, 1500])
        assert c.benchmark.deposited == 2000

    def test_benchmark_without_data(self):
        vs = portfolio_value_series([Holding("A", weight=100)], {"A": A}, 1000)
        with pytest.raises(AnalyticsError):
            compare_to_benchmark(vs, PriceSeries("SPY", [PriceBar(D(2030, 1, 1), 1, 1)]))
