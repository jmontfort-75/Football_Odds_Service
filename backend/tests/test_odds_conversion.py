import pytest

from app.providers.odds_conversion import fractional_to_decimal


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1/1", 2.0),
        ("1/2", 1.5),
        ("5/2", 3.5),
        ("2/9", 1.222),
        ("evs", 2.0),
        ("EVS", 2.0),
        (" 5/2 ", 3.5),
    ],
)
def test_fractional_to_decimal_known_values(raw, expected):
    assert fractional_to_decimal(raw) == expected


@pytest.mark.parametrize("malformed", ["", "SP", "5-2", "5/0", "abc/def", "5/"])
def test_fractional_to_decimal_rejects_malformed_input(malformed):
    with pytest.raises(ValueError):
        fractional_to_decimal(malformed)
