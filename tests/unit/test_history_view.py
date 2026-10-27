"""Input parsing and formatting for the "What if?" page."""

import datetime as dt

import pytest

from investaround.models import ValidationError
from investaround.web.history import (
    PRESETS, fmt_money, fmt_pct, fmt_signed_money, fmt_weight, parse_mix, resolve_range, thin, years_before,
)

TODAY = dt.date(2026, 10, 27)


def weights(holdings):
    return [(h.symbol, round(h.weight, 6)) for h in holdings]


class TestParseMix:
    def test_weights(self):
        holdings, note = parse_mix("vti 60, BND:40")
        assert weights(holdings) == [("VTI", 60), ("BND", 40)]
        assert note is None

    def test_percent_signs_and_newlines(self):
        holdings, _ = parse_mix("VTI 60%\nBND 40 %;")
        assert weights(holdings) == [("VTI", 60), ("BND", 40)]

    def test_no_weights_splits_evenly(self):
        holdings, note = parse_mix("VTI, VXUS, BND")
        assert weights(holdings) == [("VTI", 33.333333), ("VXUS", 33.333333), ("BND", 33.333333)]
        assert note is None

    def test_uneven_weights_are_scaled(self):
        holdings, note = parse_mix("SPY 3, BND 1")
        assert weights(holdings) == [("SPY", 75), ("BND", 25)]
        assert "added up to 4%" in note

    @pytest.mark.parametrize("text, message", [
        ("", "Type one or more symbols"),
        ("VTI 60, BND", "for every symbol, or for none"),
        ("VTI, vti", "Listed more than once: VTI"),
        ("VTI 0", "must be above 0"),
        ("VTI sixty", "Could not read"),
        ("BAD/SYM", "does not look like a ticker"),
        (",".join(f"S{i}" for i in range(21)), "At most 20"),
    ])
    def test_errors(self, text, message):
        with pytest.raises(ValidationError, match=message):
            parse_mix(text)


class TestResolveRange:
    def test_years_back_from_today(self):
        assert resolve_range("10y", "", "", TODAY) == (dt.date(2016, 10, 27), TODAY)
        assert resolve_range("1y", "", "", TODAY) == (dt.date(2025, 10, 27), TODAY)

    def test_max_has_no_start(self):
        assert resolve_range("max", "", "", TODAY) == (None, TODAY)

    def test_crash_presets_are_fixed(self):
        assert resolve_range("2008", "", "", TODAY) == (dt.date(2007, 10, 1), dt.date(2012, 12, 31))
        assert resolve_range("2020", "", "", TODAY) == (dt.date(2020, 1, 1), dt.date(2020, 12, 31))
        assert resolve_range("2022", "", "", TODAY) == (dt.date(2022, 1, 1), dt.date(2023, 12, 31))

    def test_fixed_preset_end_is_capped_at_today(self):
        assert resolve_range("2022", "", "", dt.date(2023, 6, 1)) == (dt.date(2022, 1, 1), dt.date(2023, 6, 1))

    def test_custom(self):
        assert resolve_range("custom", "2015-06-30", "2016-01-01", TODAY) == (dt.date(2015, 6, 30), dt.date(2016, 1, 1))
        assert resolve_range("custom", "2015-06-30", "", TODAY) == (dt.date(2015, 6, 30), TODAY)
        assert resolve_range("custom", "2015-06-30", "2099-01-01", TODAY) == (dt.date(2015, 6, 30), TODAY)

    @pytest.mark.parametrize("key, start, end, message", [
        ("custom", "", "", "year-month-day"),
        ("custom", "30/06/2015", "", "year-month-day"),
        ("custom", "2016-01-01", "2015-01-01", "must be before"),
        ("custom", "2030-01-01", "", "must be before"),
        ("17y", "", "", "Unknown date range"),
    ])
    def test_errors(self, key, start, end, message):
        with pytest.raises(ValidationError, match=message):
            resolve_range(key, start, end, TODAY)

    def test_every_preset_resolves(self):
        for p in PRESETS:
            start, end = resolve_range(p.key, "", "", TODAY)
            assert end <= TODAY and (start is None or start < end)


def test_years_before_leap_day():
    assert years_before(dt.date(2024, 2, 29), 1) == dt.date(2023, 2, 28)


def test_formatting():
    assert fmt_money(12345.6) == "$12,346"
    assert fmt_money(-0.001) == "$0"
    assert fmt_money(-250) == "-$250"
    assert fmt_signed_money(250) == "+$250"
    assert fmt_signed_money(-250) == "-$250"
    assert fmt_pct(0.1234) == "+12.3%"
    assert fmt_pct(-0.05) == "-5.0%"
    assert fmt_pct(0.15, signed=False) == "15.0%"
    assert fmt_pct(None) == "n/a"
    assert fmt_weight(0.3) == "30%"
    assert fmt_weight(1 / 3) == "33.3%"


def test_thin_keeps_first_and_last():
    assert thin(5, limit=10) == [0, 1, 2, 3, 4]
    idx = thin(2501, limit=1000)
    assert idx[0] == 0 and idx[-1] == 2500 and len(idx) <= 1001
    assert all(b > a for a, b in zip(idx, idx[1:]))
