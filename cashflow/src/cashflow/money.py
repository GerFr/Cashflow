"""Money as integer minor units (rule 1 in DESIGN.md); decimal strings only at the edges."""

from __future__ import annotations

from decimal import Decimal

# ISO 4217 currencies whose minor unit is not two digits; all others use cents.
EXPONENTS = {"BHD": 3, "CLP": 0, "ISK": 0, "JOD": 3, "JPY": 0, "KRW": 0, "KWD": 3, "OMR": 3, "TND": 3, "VND": 0}


def exponent(currency: str) -> int:
    return EXPONENTS.get(currency, 2)


def to_minor(amount: str | Decimal, currency: str) -> int:
    """'12.34' EUR → 1234. Refuses amounts with more decimals than the currency has."""
    value = Decimal(amount).scaleb(exponent(currency))
    if value != value.to_integral_value():
        raise ValueError(f"{amount} {currency} has more decimals than the currency allows")
    return int(value)


def from_minor(minor: int, currency: str) -> str:
    """1234 EUR → '12.34'."""
    return format(Decimal(minor).scaleb(-exponent(currency)), "f")
