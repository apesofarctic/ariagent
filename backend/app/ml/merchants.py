"""Phase 1.2 — merchant-string normaliser.

Strips payment-rail prefixes, reference numbers and city suffixes off a
raw statement string down to a canonical merchant key. This is applied
in front of BOTH the rules incumbent and the embedding challenger — the
point is to give the incumbent its best shot, not to beat a strawman.
"""
from __future__ import annotations

import re

from .population import RAIL_PREFIX, CITY_SUFFIX

_PREFIX_RE = re.compile(
    "^(" + "|".join(re.escape(p) for p in RAIL_PREFIX if p) + ")", re.IGNORECASE,
)
_CITY_RE = re.compile("(" + "|".join(CITY_SUFFIX) + ")$")
_REF_RUN_RE = re.compile(r"\d{5,}")  # long digit runs are reference numbers, not the name


def normalize_merchant(raw: str) -> str:
    """raw statement string -> canonical-ish merchant key (uppercase, no digits/city)."""
    s = raw.upper()
    s = _PREFIX_RE.sub("", s)
    s = _CITY_RE.sub("", s)
    s = _REF_RUN_RE.sub("", s)
    s = re.sub(r"[^A-Z]", "", s)
    return s.strip()
