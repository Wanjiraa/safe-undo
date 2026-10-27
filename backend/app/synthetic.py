"""Synthetic customers, histories and reversal cases. NOTHING here is real customer data."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import numpy as np

from .config import EAT_OFFSET_H

TX_TYPES = ["send_money", "pochi", "paybill", "buy_goods"]


@dataclass
class Archetype:
    median: float
    sigma: float
    peak: float
    hour_sd: float
    balance_typ: float
    contacts: list = field(default_factory=list)  # recipient ids (raw)


def new_id(rng) -> str:
    return "07" + "".join(str(d) for d in rng.integers(0, 10, size=8))


def random_archetype(rng) -> Archetype:
    med = float(np.exp(rng.uniform(np.log(300), np.log(4000))))
    return Archetype(med, rng.uniform(0.4, 0.7), rng.uniform(8, 20), rng.uniform(2, 4),
                     med * rng.uniform(5, 15), [new_id(rng) for _ in range(int(rng.integers(5, 13)))])


def sample_hour(arch: Archetype, rng) -> float:
    if rng.random() < 0.85:
        return float(rng.normal(arch.peak, arch.hour_sd) % 24)
    return float(rng.uniform(5, 23))  # deep night (23:00-05:00) is genuinely rare


def draw_amount(arch: Archetype, rng) -> float:
    return float(max(10, round(rng.lognormal(np.log(arch.median), arch.sigma) / 10) * 10))


def pick_contact(arch: Archetype, rng) -> str:
    w = 1.0 / np.arange(1, len(arch.contacts) + 1)
    return arch.contacts[int(rng.choice(len(arch.contacts), p=w / w.sum()))]


def to_utc(day: datetime, hour_eat: float) -> datetime:
    local_midnight = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    return local_midnight + timedelta(hours=hour_eat - EAT_OFFSET_H)


def simulate_history(arch: Archetype, n: int, rng, end: datetime, days: int = 90) -> list[dict]:
    out = []
    for _ in range(n):
        hour = sample_hour(arch, rng)
        day = (end + timedelta(hours=EAT_OFFSET_H)) - timedelta(days=int(rng.integers(1, days)))
        rid = pick_contact(arch, rng) if rng.random() < 0.88 else new_id(rng)
        t = str(rng.choice(TX_TYPES, p=[0.70, 0.05, 0.12, 0.13]))
        out.append({"ts": to_utc(day, hour), "hour": hour, "amount": draw_amount(arch, rng),
                    "rid": rid, "tx_type": t})
    return sorted(out, key=lambda r: r["ts"])


def normal_point(arch: Archetype, rng) -> dict:
    known = rng.random() < 0.88
    balance = arch.balance_typ * float(rng.lognormal(0, 0.25))
    amount = min(draw_amount(arch, rng), balance * 0.9)
    return {"amount": amount, "rid": pick_contact(arch, rng) if known else new_id(rng),
            "hour": sample_hour(arch, rng), "balance": balance,
            "recent": int(rng.choice([0, 1, 2], p=[0.90, 0.09, 0.01]))}


ANOMALY_KINDS = ["big_new", "big_known", "night_new", "burst", "drain_new"]


def anomalous_point(kind: str, arch: Archetype, rng) -> dict:
    p = normal_point(arch, rng)
    if kind == "big_new":
        p.update(amount=arch.median * rng.uniform(8, 40), rid=new_id(rng))
    elif kind == "big_known":  # subtle: known recipient, large amount
        p.update(amount=arch.median * rng.uniform(6, 20), rid=pick_contact(arch, rng))
    elif kind == "night_new":  # subtle: ordinary amount, odd hour, new recipient
        p.update(amount=arch.median * rng.uniform(1, 3), rid=new_id(rng), hour=float(rng.uniform(0.5, 4.5)))
    elif kind == "burst":
        p.update(amount=arch.median * rng.uniform(1, 3), recent=int(rng.integers(3, 7)))
    elif kind == "drain_new":
        p.update(balance=arch.balance_typ, rid=new_id(rng))
        p["amount"] = p["balance"] * rng.uniform(0.85, 0.98)
    if p["balance"] < p["amount"] * 1.05:
        p["balance"] = p["amount"] * rng.uniform(1.05, 1.6)
    return p


# ---- reversal cases ---------------------------------------------------------------------
REASONS = ["wrong_number", "wrong_amount", "fraud", "refund", "other"]
# Assumed (invented) behaviour used ONLY to generate demonstration data.
BASE_HOURS = {"send_money": 6.0, "pochi": 10.0, "paybill": 30.0, "buy_goods": 36.0}
REASON_MULT = {"wrong_number": 1.0, "wrong_amount": 1.1, "fraud": 1.35, "refund": 1.7, "other": 1.5}


def simulate_cases(n: int, rng) -> list[dict]:
    rows = []
    for _ in range(n):
        t = str(rng.choice(TX_TYPES, p=[0.55, 0.10, 0.20, 0.15]))
        r = str(rng.choice(REASONS, p=[0.40, 0.20, 0.10, 0.12, 0.18]))
        amount = float(np.clip(rng.lognormal(np.log(1500), 1.0), 20, 150000))
        hour = int(rng.integers(0, 24))
        weekend = int(rng.random() < 2 / 7)
        total = (BASE_HOURS[t] * REASON_MULT[r] * (max(amount, 100) / 2000) ** 0.08
                 * (1.3 if weekend else 1.0) * (1.15 if hour >= 20 or hour < 6 else 1.0)
                 * float(rng.lognormal(0, 0.5)))
        u = float(rng.uniform(0, 0.95))
        status = 0 if u < 0.15 else (1 if u < 0.80 else 2)
        entered = [0.0, 0.15, 0.80][status] * total
        elapsed = u * total
        rows.append({"tx_type": t, "reason": r, "amount": amount, "submitted_hour": hour,
                     "weekend": weekend, "elapsed": elapsed, "status_idx": status,
                     "hours_in_status": elapsed - entered, "remaining": total - elapsed, "total": total})
    return rows
