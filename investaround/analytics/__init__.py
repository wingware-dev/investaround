"""Pure portfolio analytics: value series, metrics and strategies (no Flask)."""

from .performance import (
    REBALANCE_PERIODS, AnalyticsError, Comparison, Drawdown, HoldingContribution, Metrics,
    ValueSeries, YearReturn, benchmark_series, compare_to_benchmark, daily_returns, growth_index,
    max_drawdown, metrics, portfolio_value_series, simulate, trading_calendar, yearly_returns,
)
from .strategies import (
    LumpSumVsDca, StrategyResult, buy_and_hold, dollar_cost_average, lump_sum_vs_dca,
    month_starts, rebalanced,
)

__all__ = [
    "REBALANCE_PERIODS", "AnalyticsError", "Comparison", "Drawdown", "HoldingContribution",
    "LumpSumVsDca", "Metrics", "StrategyResult", "ValueSeries", "YearReturn", "benchmark_series",
    "buy_and_hold", "compare_to_benchmark", "daily_returns", "dollar_cost_average",
    "growth_index", "lump_sum_vs_dca", "max_drawdown", "metrics", "month_starts",
    "portfolio_value_series", "rebalanced", "simulate", "trading_calendar", "yearly_returns",
]
