from __future__ import annotations

from decimal import Decimal

import pytest

from cashflow.money import from_minor, to_minor


@pytest.mark.parametrize(
    ("amount", "currency", "minor"),
    [
        ("12.34", "EUR", 1234),
        ("-878.70", "EUR", -87870),
        ("0.00", "EUR", 0),
        ("1500", "JPY", 1500),
        ("1.234", "KWD", 1234),
    ],
)
def test_round_trip(amount, currency, minor):
    assert to_minor(amount, currency) == minor
    assert Decimal(from_minor(minor, currency)) == Decimal(amount)


def test_from_minor_keeps_cents():
    assert from_minor(1200, "EUR") == "12.00"


def test_too_many_decimals_are_refused():
    with pytest.raises(ValueError, match="more decimals"):
        to_minor("1.005", "EUR")
