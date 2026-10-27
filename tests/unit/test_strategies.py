import datetime as dt

import pytest

from investaround.analytics import (
    AnalyticsError, buy_and_hold, dollar_cost_average, lump_sum_vs_dca, month_starts, rebalanced,
)
from investaround.models import PriceBar, PriceSeries

D = dt.date


def series(symbol, dates, prices):
    return PriceSeries(symbol, [PriceBar(d, p, p) for d, p in zip(dates, prices)])


def pair(dates):
    """A doubles then halves back; B stays flat.  50/50 in A and B."""
    return {"A": series("A", dates, [100, 200, 200, 100]),
            "B": series("B", dates, [100, 100, 100, 100])}, {"A": 50, "B": 50}


JAN_FEB = [D(2024, 1, 2), D(2024, 1, 31), D(2024, 2, 1), D(2024, 2, 29)]
MAR_APR = [D(2024, 3, 1), D(2024, 3, 28), D(2024, 4, 1), D(2024, 4, 30)]
DEC_JAN = [D(2024, 12, 2), D(2024, 12, 31), D(2025, 1, 2), D(2025, 1, 31)]


class TestBuyAndHold:
    def test_round_trip_is_flat(self):
        prices, weights = pair(JAN_FEB)
        r = buy_and_hold(prices, weights, 1000)
        assert r.key == "buy_and_hold"
        assert r.series.values == pytest.approx([1000, 1500, 1500, 1000])
        assert r.metrics.total_return == pytest.approx(0)


class TestRebalancing:
    @pytest.mark.parametrize("period,dates", [
        ("monthly", JAN_FEB), ("monthly", MAR_APR), ("quarterly", MAR_APR), ("yearly", DEC_JAN)])
    def test_rebalances_at_period_start(self, period, dates):
        # At the 3rd date 1500 is reset to 750/750: 3.75 units of A, 7.5 of B,
        # so A's halving leaves 375 + 750
        prices, weights = pair(dates)
        r = rebalanced(prices, weights, period, 1000)
        assert r.key == f"rebalance_{period}"
        assert r.series.values == pytest.approx([1000, 1500, 1500, 1125])
        assert r.series.holdings["A"] == pytest.approx([500, 1000, 750, 375])
        a, b = r.metrics.holdings
        # A: 500 in, 250 taken out at the rebalance; B: 500 in, 250 more
        assert (a.invested, a.gain) == (pytest.approx(250), pytest.approx(125))
        assert (b.invested, b.gain) == (pytest.approx(750), pytest.approx(0))
        assert r.metrics.gain == pytest.approx(125)

    @pytest.mark.parametrize("period,dates", [("quarterly", JAN_FEB), ("yearly", MAR_APR)])
    def test_no_rebalance_within_period(self, period, dates):
        prices, weights = pair(dates)
        assert rebalanced(prices, weights, period, 1000).series.values == pytest.approx(
            [1000, 1500, 1500, 1000])

    def test_rebalance_keeps_late_starter_share_as_cash(self):
        a = series("A", JAN_FEB, [100, 200, 200, 200])
        b = series("B", JAN_FEB[3:], [10])
        r = rebalanced({"A": a, "B": b}, {"A": 50, "B": 50}, "monthly", 1000)
        # Feb 1: 1000 in A + 500 cash reset to 750 in A + 750 cash for B
        assert r.series.cash == pytest.approx([500, 500, 750, 0])
        assert r.series.values == pytest.approx([1000, 1500, 1500, 1500])

    def test_unknown_period(self):
        prices, weights = pair(JAN_FEB)
        with pytest.raises(AnalyticsError):
            rebalanced(prices, weights, "weekly")


DCA_DAYS = [D(2024, 1, 2), D(2024, 1, 15), D(2024, 2, 1), D(2024, 3, 1)]


class TestDollarCostAveraging:
    def test_month_starts(self):
        assert month_starts(DCA_DAYS) == [D(2024, 1, 2), D(2024, 2, 1), D(2024, 3, 1)]
        assert month_starts([D(2024, 1, 15), D(2024, 1, 16), D(2024, 2, 2)]) == [
            D(2024, 1, 15), D(2024, 2, 2)]

    def test_monthly_amount(self):
        # Buys 1 unit at 100, 2 at 50, 0.5 at 200: 3.5 units for 300
        a = series("A", DCA_DAYS, [100, 50, 50, 200])
        r = dollar_cost_average({"A": a}, {"A": 100}, 100)
        assert r.series.deposits == pytest.approx([100, 0, 100, 100])
        assert r.series.values == pytest.approx([100, 50, 150, 700])
        m = r.metrics
        assert m.deposited == 300
        assert m.total_return == pytest.approx(700 / 300 - 1)
        # Time-weighted growth is just the price's: 100 -> 200
        assert m.time_weighted_return == pytest.approx(1.0)
        dd = m.max_drawdown
        assert dd.depth == pytest.approx(-0.5)
        assert (dd.peak, dd.trough, dd.recovered) == (DCA_DAYS[0], DCA_DAYS[1], DCA_DAYS[3])

    def test_initial_amount(self):
        a = series("A", DCA_DAYS, [100, 50, 50, 200])
        r = dollar_cost_average({"A": a}, {"A": 100}, 100, initial=900)
        # 10 units, then 2, then 0.5
        assert r.series.values == pytest.approx([1000, 500, 600, 2500])
        assert r.metrics.deposited == 1200

    def test_bad_amounts(self):
        a = series("A", DCA_DAYS, [100, 50, 50, 200])
        with pytest.raises(AnalyticsError):
            dollar_cost_average({"A": a}, {"A": 1}, 0)
        with pytest.raises(AnalyticsError):
            dollar_cost_average({"A": a}, {"A": 1}, 100, initial=-1)


LVD_DAYS = [D(2024, 1, 2), D(2024, 1, 31), D(2024, 2, 1), D(2024, 3, 1)]


class TestLumpSumVsDca:
    def test_rising_market_favours_lump_sum(self):
        a = series("A", LVD_DAYS, [100, 200, 200, 400])
        r = lump_sum_vs_dca({"A": a}, {"A": 1}, total=300, months=3)
        # Lump: 3 units.  DCA: 1 at 100, 0.5 at 200, 0.25 at 400
        assert r.lump.series.values == pytest.approx([300, 600, 600, 1200])
        assert r.dca.series.values == pytest.approx([300, 400, 400, 700])
        assert r.dca.series.cash == pytest.approx([200, 200, 100, 0], abs=1e-9)
        assert r.lump.metrics.deposited == r.dca.metrics.deposited == 300
        assert r.difference == pytest.approx(500)
        assert r.winner == "lump"
        assert r.dca.label == "Spread over 3 months"

    def test_falling_market_favours_dca(self):
        a = series("A", LVD_DAYS, [100, 50, 50, 25])
        r = lump_sum_vs_dca({"A": a}, {"A": 1}, total=300, months=3)
        # Lump: 3 units -> 75.  DCA: 1 + 2 + 4 units -> 175
        assert r.lump.metrics.final_value == pytest.approx(75)
        assert r.dca.metrics.final_value == pytest.approx(175)
        assert r.winner == "dca"

    def test_flat_market_ties(self):
        a = series("A", LVD_DAYS, [100, 100, 100, 100])
        assert lump_sum_vs_dca({"A": a}, {"A": 1}, total=300, months=3).winner == "tie"

    def test_range_shorter_than_spread_leaves_cash(self):
        a = series("A", LVD_DAYS, [100, 50, 50, 25])
        r = lump_sum_vs_dca({"A": a}, {"A": 1}, total=1200, months=12)
        # Three 100 installments made: 1 + 2 + 4 units, 900 still cash
        assert r.dca.series.cash[-1] == pytest.approx(900)
        assert r.dca.metrics.final_value == pytest.approx(7 * 25 + 900)

    def test_bad_inputs(self):
        a = series("A", LVD_DAYS, [100, 50, 50, 25])
        with pytest.raises(AnalyticsError):
            lump_sum_vs_dca({"A": a}, {"A": 1}, total=0)
        with pytest.raises(AnalyticsError):
            lump_sum_vs_dca({"A": a}, {"A": 1}, months=0)
        with pytest.raises(AnalyticsError):
            lump_sum_vs_dca({"A": a}, {"A": 1}, start=D(2030, 1, 1))

    def test_waiting_cash_earns_interest(self):
        # Flat prices, so the only difference is interest on DCA's waiting cash
        a = series("A", LVD_DAYS, [100, 100, 100, 100])
        r = lump_sum_vs_dca({"A": a}, {"A": 1}, total=300, months=3, cash_rate=0.05)
        f = lambda days: 1.05 ** (days / 365.25)  # noqa: E731
        cash = 200 * f(29) * f(1)  # Jan 2 -> Jan 31 -> Feb 1
        cash = (cash - 100) * f(29)  # second part bought; Feb 1 -> Mar 1
        # The last part sweeps in all remaining cash, interest included
        assert r.dca.series.cash[-1] == pytest.approx(0, abs=1e-9)
        assert r.dca.metrics.final_value == pytest.approx(200 + cash)
        assert r.dca.metrics.interest_earned == pytest.approx(cash - 100)
        assert r.lump.metrics.final_value == pytest.approx(300)
        assert r.winner == "dca"


class TestCashRateKeyword:
    def test_passed_through(self):
        a = series("A", JAN_FEB, [100, 200, 200, 200])
        b = series("B", JAN_FEB[3:], [10])
        prices, weights = {"A": a, "B": b}, {"A": 50, "B": 50}
        for r in (buy_and_hold(prices, weights, 1000, cash_rate=0.05),
                  rebalanced(prices, weights, "monthly", 1000, cash_rate=0.05),
                  dollar_cost_average(prices, weights, 100, cash_rate=0.05)):
            m = r.metrics
            assert m.interest_earned > 0, r.key
            assert m.gain == pytest.approx(sum(h.gain for h in m.holdings) + m.interest_earned)
