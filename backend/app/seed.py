"""Seed demo customers, histories and reversal cases (all synthetic)."""
from __future__ import annotations

import random
import string
from datetime import timedelta

import numpy as np

from . import synthetic as syn
from .config import SEED
from .db import conn, init_db, iso, now, set_clock_offset
from .identifiers import mask, token

DEMO = [
    dict(id="cust_amina", name="Amina Wanjiru", masked="07XX XXX 118", balance=24310.50,
         arch=syn.Archetype(900, 0.5, 13, 3, 20000, []),
         contacts=[("0700123401", "Mama Wanjiru"), ("0700123402", "Kevin Otieno"), ("0700123403", "Faith Njeri"),
                   ("0700123404", "Landlord Mwangi"), ("0700123405", "Lucy Akinyi")]),
    dict(id="cust_brian", name="Brian Mutua", masked="07XX XXX 562", balance=61200.00,
         arch=syn.Archetype(2500, 0.55, 11, 3, 50000, []),
         contacts=[("0700223401", "Stockist Hassan"), ("0700223402", "Njoroge Supplies"), ("0700223403", "Mercy Wambui"),
                   ("0700223404", "Transport Joe"), ("0700223405", "Rose Cheptoo"), ("0700223406", "Dennis Kiprop")]),
    dict(id="cust_grace", name="Grace Achieng", masked="07XX XXX 790", balance=1850.00,
         arch=syn.Archetype(300, 0.45, 17, 2.5, 1500, []),
         contacts=[("0700323401", "Mum"), ("0700323402", "Tabitha Roommate"), ("0700323403", "Campus Cafe"),
                   ("0700323404", "Peter Study Group")]),
]
BUY_GOODS_TILLS: dict[str, str] = {
    "523417": "Njoroge Hardware",
    "841209": "Naivas Supermarket",
    "619304": "Java House",
    "738291": "Quickmart",
    "904512": "Goodlife Pharmacy",
}
PAYBILL_NUMBERS: dict[str, str] = {
    "247247": "Equity Paybill",
    "888880": "KPLC Prepaid",
    "400200": "Co-op Bank",
    "522522": "KCB Paybill",
    "303030": "Absa Bank",
}
PAYBILL_ACCOUNTS: list[str] = ["ACC001", "MTR-77412", "14289901", "INV-2049", "PLOT-12B"]
CONTACT_NAMES: dict[str, dict[str, str]] = {}


def mpesa_ref(rng: random.Random) -> str:
    return rng.choice(string.ascii_uppercase) + "".join(rng.choices(string.ascii_uppercase + string.digits, k=9))


def seed(reset: bool = True) -> None:
    init_db(reset=reset)
    rng, pyrng = np.random.default_rng(SEED), random.Random(SEED)
    with conn() as c:
        set_clock_offset(c, 0.0)
        t_now = now(c)
        for d in DEMO:
            a = d["arch"]
            a.contacts = [num for num, _ in d["contacts"]]
            names = dict(d["contacts"])
            c.execute("INSERT INTO customers VALUES(?,?,?,?)", (d["id"], d["name"], d["masked"], d["balance"]))
            for h in syn.simulate_history(a, 110, rng, t_now - timedelta(hours=12)):
                t = h["tx_type"]
                rid = h["rid"]
                c.execute("INSERT INTO transactions VALUES(?,?,?,?,?,?,?,?,?)",
                          (f"tx_{pyrng.getrandbits(48):012x}", d["id"], t, token(t, rid), mask(t, rid),
                           names.get(rid), h["amount"], iso(h["ts"]), mpesa_ref(pyrng)))

        def add_tx(cust, t, rid, name, amount, hours_ago):
            tid = f"tx_{pyrng.getrandbits(48):012x}"
            c.execute("INSERT INTO transactions VALUES(?,?,?,?,?,?,?,?,?)",
                      (tid, cust, t, token(t, rid), mask(t, rid), name, amount,
                       iso(t_now - timedelta(hours=hours_ago)), mpesa_ref(pyrng)))
            return tid

        def add_case(n, cust, tid, reason, status, submitted_h, entered_h, history, rejection=None):
            ref = f"SU-{1040 + n}"
            cur = c.execute("INSERT INTO cases(ref,customer_id,transaction_id,reason,status,submitted_at,"
                            "status_entered_at,rejection_reason,simulated) VALUES(?,?,?,?,?,?,?,?,1)",
                            (ref, cust, tid, reason, status, iso(t_now - timedelta(hours=submitted_h)),
                             iso(t_now - timedelta(hours=entered_h)), rejection))
            for st, h_ago, note in history:
                c.execute("INSERT INTO status_history(case_id,status,ts,note) VALUES(?,?,?,?)",
                          (cur.lastrowid, st, iso(t_now - timedelta(hours=h_ago)), note))

        # Amina: older completed case and the headline in-progress case (mirrors the solution doc).
        t0 = add_tx("cust_amina", "send_money", "0700123499", None, 1200, 140)
        add_case(0, "cust_amina", t0, "wrong_number", "completed", 138, 120,
                 [("submitted", 138, "Request submitted"), ("under_review", 133, "Under review"),
                  ("approved", 124, "Approved"), ("completed", 120, "Completed")])
        t2 = add_tx("cust_amina", "send_money", "0700999842", None, 5000, 6.5)
        add_case(2, "cust_amina", t2, "wrong_number", "under_review", 5.5, 3.5,
                 [("submitted", 5.5, "Request submitted"), ("under_review", 3.5, "Under review")])
        # Brian: PayBill case that is slower by nature.
        t3 = add_tx("cust_brian", "paybill", "247247", "Utility paybill", 8400, 30)
        add_case(3, "cust_brian", t3, "wrong_amount", "approved", 28, 4,
                 [("submitted", 28, "Request submitted"), ("under_review", 22, "Under review"),
                  ("approved", 4, "Approved")])
        # Brian: an overdue Buy Goods refund request (shows elevated delay risk and follow-up advice).
        t4 = add_tx("cust_brian", "buy_goods", "523417", "Njoroge Hardware", 12000, 31)
        add_case(4, "cust_brian", t4, "refund", "under_review", 27, 22,
                 [("submitted", 27, "Request submitted"), ("under_review", 22, "Under review")])
        # Grace: a recent mistaken payment she has not reported yet (for the report flow demo).
        add_tx("cust_grace", "send_money", "0700323499", None, 450, 1.2)
