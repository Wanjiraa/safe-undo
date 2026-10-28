"""Reversal case management, status tracking and predictive insights."""
from __future__ import annotations

import hashlib
import sqlite3

from .config import DELAY_TARGET_HOURS
from .db import iso, now, parse
from .guidance import REASON_LABELS, TYPE_LABELS, guidance
from .ml import eta

FLOW = ["submitted", "under_review", "approved", "completed"]
LABELS = {"submitted": "Submitted", "under_review": "Under review", "approved": "Approved",
          "completed": "Completed", "rejected": "Rejected"}
TERMINAL = {"completed", "rejected"}
REJECTION_REASONS_PERSON = [
    "Insufficient funds in the recipient's M-PESA account (funds already withdrawn or used). Contact 100 for further help.",
    "The recipient declined the reversal request. Contact Safaricom customer care (100) for guidance.",
    "Reversal could not be completed because the recipient's balance was below the transaction amount.",
]
REJECTION_REASONS_BUSINESS = [
    "The receiving business declined the reversal as the payment was already settled. Contact the business with your M-PESA ID.",
    "Merchant reversal requires direct authorisation from the business. Please contact the merchant or call 100.",
]


def _rejection_reason(ref: str, tx_type: str) -> str:
    h = int(hashlib.sha256(ref.encode()).hexdigest(), 16)
    pool = REJECTION_REASONS_BUSINESS if tx_type in ("paybill", "buy_goods") else REJECTION_REASONS_PERSON
    return pool[h % len(pool)]
DISCLAIMER = ("Status updates in this prototype are simulated. SafeUndo shows real statuses only when it "
              "receives trustworthy status data from an authorised source.")


def _hours(a, b) -> float:
    return max((b - a).total_seconds() / 3600.0, 0.0)


def _case_row(c: sqlite3.Connection, ref: str):
    r = c.execute("SELECT * FROM cases WHERE ref=?", (ref,)).fetchone()
    if not r:
        raise LookupError(ref)
    return r


def _predict(c, case, tx) -> dict | None:
    if case["status"] in TERMINAL:
        return None
    t = now(c)
    sub = parse(case["submitted_at"])
    local = sub.hour + 3
    features = {"tx_type": tx["tx_type"], "reason": case["reason"], "amount": tx["amount"],
                "submitted_hour": local % 24, "weekend": int(sub.weekday() >= 5),
                "elapsed": _hours(sub, t), "status_idx": eta.STATUS_IDX[case["status"]],
                "hours_in_status": _hours(parse(case["status_entered_at"]), t)}
    pred = eta.predict(features)
    pred["elapsed_hours"] = round(features["elapsed"], 1)
    pred["overdue"] = features["elapsed"] > DELAY_TARGET_HOURS
    pred["why"] = _why(features, pred, tx)
    pred["action"] = _action(case, tx, pred)
    return pred


def _why(f, pred, tx) -> list[str]:
    out = []
    if pred["overdue"]:
        out.append(f"This case has been open longer than the {DELAY_TARGET_HOURS}-hour target.")
    if tx["tx_type"] in ("paybill", "buy_goods"):
        out.append(f"{TYPE_LABELS[tx['tx_type']]} cases involve the receiving business, so they tend to take "
                   "longer in the demonstration dataset.")
    if f["reason"] in ("refund", "other", "fraud"):
        out.append(f"'{REASON_LABELS[f['reason']]}' requests have taken longer than wrong-number cases in the demo data.")
    if f["weekend"]:
        out.append("The request was submitted on a weekend, which slowed comparable demo cases.")
    if f["status_idx"] == 1 and f["hours_in_status"] > 8:
        out.append(f"It has been under review for about {f['hours_in_status']:.0f} hours.")
    if not out:
        out.append("The case is moving in line with comparable cases in the demonstration dataset.")
    out.append("Estimates come from a model trained on synthetic data, not real Safaricom case data.")
    return out


def _action(case, tx, pred) -> str:
    t = tx["tx_type"]
    if case["status"] == "approved":
        return "Check your M-PESA SMS and balance for the completed reversal."
    if pred["overdue"] or pred["risk_level"] == "Elevated":
        if t in ("paybill", "buy_goods"):
            return "Follow up with the receiving business using your transaction ID, or use Safaricom's official support channel."
        return "Monitor the case. If there is no update soon, follow up through Safaricom's official support channel."
    if pred["risk_level"] == "Moderate":
        return "Wait for the next update and check again later."
    return "No action needed. Wait for the next update."


def _tx(c, tid):
    return c.execute("SELECT * FROM transactions WHERE id=?", (tid,)).fetchone()


def tx_summary(tx) -> dict:
    return {"id": tx["id"], "mpesa_ref": tx["mpesa_ref"], "tx_type": tx["tx_type"],
            "tx_type_label": TYPE_LABELS[tx["tx_type"]], "amount": tx["amount"], "ts": tx["ts"],
            "recipient": tx["recipient_masked"], "recipient_name": tx["recipient_name"]}


def case_detail(c: sqlite3.Connection, ref: str) -> dict:
    case = _case_row(c, ref)
    tx = _tx(c, case["transaction_id"])
    hist = c.execute("SELECT status, ts, note FROM status_history WHERE case_id=? ORDER BY id", (case["id"],)).fetchall()
    steps = FLOW if case["status"] != "rejected" else ["submitted", "under_review", "rejected"]
    reached = {h["status"] for h in hist}
    return {
        "ref": case["ref"], "customer_id": case["customer_id"], "reason": case["reason"],
        "reason_label": REASON_LABELS[case["reason"]], "status": case["status"],
        "status_label": LABELS[case["status"]], "submitted_at": case["submitted_at"],
        "rejection_reason": case["rejection_reason"], "simulated": bool(case["simulated"]),
        "transaction": tx_summary(tx),
        "history": [{"status": h["status"], "label": LABELS[h["status"]], "ts": h["ts"], "note": h["note"]} for h in hist],
        "timeline": [{"status": s, "label": LABELS[s], "reached": s in reached} for s in steps],
        "prediction": _predict(c, case, tx),
        "guidance": guidance(tx["tx_type"], case["reason"]),
        "disclaimer": DISCLAIMER,
    }


def list_cases(c, customer_id: str) -> list[dict]:
    rows = c.execute("SELECT ref FROM cases WHERE customer_id=? ORDER BY id DESC", (customer_id,)).fetchall()
    out = []
    for r in rows:
        d = case_detail(c, r["ref"])
        out.append({k: d[k] for k in ("ref", "status", "status_label", "reason_label", "transaction", "prediction", "simulated")})
    return out


def create_case(c, customer_id: str, transaction_id: str, reason: str) -> tuple[dict, bool]:
    tx = c.execute("SELECT * FROM transactions WHERE id=? AND customer_id=?", (transaction_id, customer_id)).fetchone()
    if not tx:
        raise LookupError("transaction")
    dup = c.execute("SELECT ref FROM cases WHERE transaction_id=? AND status NOT IN ('rejected','completed')",
                    (transaction_id,)).fetchone()
    if dup:  # idempotent: one open case per transaction
        return case_detail(c, dup["ref"]), True
    n = c.execute("SELECT COALESCE(MAX(id),0)+1 AS n FROM cases").fetchone()["n"]
    ref, t = f"SU-{1040 + n}", iso(now(c))
    cur = c.execute("INSERT INTO cases(ref,customer_id,transaction_id,reason,status,submitted_at,status_entered_at,"
                    "simulated) VALUES(?,?,?,?,?,?,?,1)", (ref, customer_id, transaction_id, reason, "submitted", t, t))
    c.execute("INSERT INTO status_history(case_id,status,ts,note) VALUES(?,?,?,?)",
              (cur.lastrowid, "submitted", t, "Request submitted (simulated)"))
    return case_detail(c, ref), False


def advance_case(c, ref: str, hours: float = 4.0, force: str | None = None) -> dict:
    """DEMO ONLY: move a case to its next simulated status and fast-forward the demo clock."""
    from .db import clock_offset_hours, set_clock_offset
    case = _case_row(c, ref)
    if case["status"] in TERMINAL:
        raise ValueError("Case is already closed")
    set_clock_offset(c, clock_offset_hours(c) + hours)
    t = iso(now(c))
    if force:
        nxt = force
    elif case["status"] == "submitted":
        nxt = "under_review"
    elif case["status"] == "under_review":
        # Deterministic ~12% rejection so demos are repeatable.
        nxt = "rejected" if int(hashlib.sha256(ref.encode()).hexdigest(), 16) % 100 < 12 else "approved"
    else:
        nxt = "completed"
    tx = _tx(c, case["transaction_id"])
    rej = _rejection_reason(ref, tx["tx_type"]) if nxt == "rejected" else None
    c.execute("UPDATE cases SET status=?, status_entered_at=?, rejection_reason=? WHERE id=?", (nxt, t, rej, case["id"]))
    c.execute("INSERT INTO status_history(case_id,status,ts,note) VALUES(?,?,?,?)",
              (case["id"], nxt, t, f"{LABELS[nxt]} (simulated)" + (f": {rej}" if rej else "")))
    return case_detail(c, ref)
