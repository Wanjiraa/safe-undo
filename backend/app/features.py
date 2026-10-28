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
    """Plain-language reasons derived from the same features the model sees."""
    ratio = math.expm1(x[0])
    reasons = []
    if ratio >= 3:
        reasons.append(f"This is about {ratio:.0f}x your usual send amount (usually around KSh {p.median:,.0f}).")
    if x[1] == 1.0 and p.n >= 5:
        who = recipient_name or "this recipient"
        reasons.append(f"You have not sent to {who} before.")
    if x[2] >= 0.9:
        reasons.append("This is an unusual time of day for your transactions.")
    if x[3] >= 3:
        reasons.append(f"You made {int(x[3])} other transactions in the last hour.")
    if x[4] >= 0.7:
        reasons.append(f"This is {x[4] * 100:.0f}% of your available balance.")
    return reasons
