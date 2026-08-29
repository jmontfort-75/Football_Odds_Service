"""Fractional <-> decimal odds conversion.

Oddschecker's embedded odds data carries both a fractional string (e.g. "2/9")
and Oddschecker's own decimal value. We convert the fractional string
ourselves (rather than trusting their decimal field blindly) so the raw
source value and our normalized value can be cross-checked during validation.
"""

import re

_FRACTION_RE = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*$")

# A handful of odds are quoted as "EVS" (evens) instead of a fraction.
_EVENS_ALIASES = {"evs", "evens"}


def fractional_to_decimal(raw_odds: str) -> float:
    """Convert a fractional odds string (e.g. "5/2") to decimal odds (3.5).

    Raises ValueError on anything that isn't a recognizable fractional or
    evens price, so callers can fail explicitly instead of fabricating data.
    """
    text = raw_odds.strip()
    if text.lower() in _EVENS_ALIASES:
        return 2.0

    match = _FRACTION_RE.match(text)
    if not match:
        raise ValueError(f"Unrecognized fractional odds format: {raw_odds!r}")

    numerator, denominator = int(match.group(1)), int(match.group(2))
    if denominator == 0:
        raise ValueError(f"Fractional odds with zero denominator: {raw_odds!r}")

    return round(numerator / denominator + 1, 3)
