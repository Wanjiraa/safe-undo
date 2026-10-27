"""Recipient identifier handling. Raw numbers are hashed; only masked forms are stored/shown."""
from __future__ import annotations

import hashlib
import re

from .config import SALT

PHONE_TYPES = {"send_money", "pochi"}


def normalize(tx_type: str, raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if tx_type in PHONE_TYPES:
        if digits.startswith("254") and len(digits) == 12:
            digits = "0" + digits[3:]
        elif len(digits) == 9 and digits[0] in "17":
            digits = "0" + digits
    return digits


def token(tx_type: str, raw: str) -> str:
    return hashlib.sha256(f"{SALT}:{tx_type}:{normalize(tx_type, raw)}".encode()).hexdigest()[:12]


def mask(tx_type: str, raw: str) -> str:
    n = normalize(tx_type, raw)
    if len(n) == 10 and n[0] == "0":
        return f"{n[:2]}XX XXX {n[-3:]}"
    return n  # till / paybill numbers are public business identifiers


def valid(tx_type: str, raw: str) -> bool:
    n = normalize(tx_type, raw)
    if tx_type in PHONE_TYPES:
        return len(n) == 10 and n[0] == "0"
    return 5 <= len(n) <= 7
