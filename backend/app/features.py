"""Behavioural profile + feature engineering shared by training and live scoring."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

FEATURES = ["log_amount_ratio", "new_recipient", "hour_rarity", "velocity_1h", "balance_ratio"]
MIN_HISTORY = 15


@dataclass
class Profile:
    n: int
    median: float
    p25: float
    p75: float
    hours: np.ndarray
    known: set = field(default_factory=set)

    def hour_familiarity(self, hour: float) -> float:
        """Share of past transactions within +/-2h (circular) of this hour of day."""
        if self.n == 0:
            return 0.5
        d = np.abs(self.hours - hour)
        d = np.minimum(d, 24 - d)
        return float((d <= 2).mean())


def build_profile(amounts, hours, tokens) -> Profile:
    a = np.asarray(list(amounts), dtype=float)
    if a.size == 0:
        return Profile(0, 500.0, 200.0, 1000.0, np.array([]), set())
    return Profile(int(a.size), float(max(np.median(a), 50.0)), float(np.percentile(a, 25)),
                   float(np.percentile(a, 75)), np.asarray(list(hours), dtype=float), set(tokens))


def make_features(p: Profile, amount: float, tok: str, hour: float, balance: float,
                  recent_count: int) -> np.ndarray:
    bal_ratio = min(amount / max(balance, 1.0), 1.5)
    vel = float(min(recent_count, 6))
    if p.n < 5:  # too little history to judge amount/recipient/time: stay neutral
        return np.array([math.log1p(1.0), 0.0, 0.0, vel, bal_ratio])
    return np.array([
        math.log1p(amount / p.median),
        0.0 if tok in p.known else 1.0,
        1.0 - p.hour_familiarity(hour),
        vel,
        bal_ratio,
    ])


def explain(x: np.ndarray, p: Profile, amount: float, recipient_name: str | None = None) -> list[str]:
    """Plain-language reasons focused on behavioural anomalies (Hakikisha already shows the recipient/till name)."""
    ratio = math.expm1(x[0])
    reasons = []
    if ratio >= 3:
        reasons.append("This amount is higher than what you usually transact. Please confirm the recipient name and amount.")
    if x[2] >= 0.9:
        reasons.append("You rarely make transactions at this hour.")
    if x[3] >= 3:
        reasons.append("You have made several transactions in a short time.")
    if x[4] >= 0.7:
        reasons.append("This payment uses most of your available M-PESA balance.")
    if not reasons:
        reasons.append("Please confirm the recipient name and amount before continuing.")
    return reasons
