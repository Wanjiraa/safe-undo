"""SafeUndo API: shared backend for the USSD simulator and the simulated My OneApp (Android)."""
from __future__ import annotations

import hashlib
import random
import string
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import cases as case_svc
from . import features as F
from .config import FLAG_SCORE, USSD_DIR
from .db import clock_offset_hours, conn, init_db, iso, now, parse, set_clock_offset
from .guidance import REASON_LABELS, TYPE_LABELS, guidance
from .identifiers import mask, normalize, token, valid
from .ml import anomaly, eta
from .seed import BUY_GOODS_TILLS, PAYBILL_ACCOUNTS, PAYBILL_NUMBERS, seed

TxType = Literal["send_money", "pochi", "paybill", "buy_goods"]
Reason = Literal["wrong_number", "wrong_amount", "fraud", "refund", "other"]


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with conn() as c:
        empty = c.execute("SELECT COUNT(*) n FROM customers").fetchone()["n"] == 0
    if empty:
        seed()
    anomaly.load()
    eta.load()
    yield


app = FastAPI(title="SafeUndo API", version="1.0.0", lifespan=lifespan,
              description="Prototype backend. Uses synthetic data and simulated reversal statuses.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ScoreRequest(BaseModel):
    customer_id: str
    tx_type: TxType = "send_money"
    recipient: str
    amount: float = Field(gt=0, le=250000)
    timestamp: Optional[str] = None


class TxRequest(BaseModel):
    customer_id: str
    tx_type: TxType = "send_money"
    recipient: str
    amount: float = Field(gt=0, le=250000)
    recipient_name: Optional[str] = None
    account_ref: Optional[str] = None


class CaseRequest(BaseModel):
    customer_id: str
    transaction_id: str
    reason: Reason


class AdvanceRequest(BaseModel):
    hours: float = Field(default=4.0, ge=0, le=240)
    force_status: Optional[Literal["under_review", "approved", "rejected", "completed"]] = None


def _customer(c, cid: str):
    r = c.execute("SELECT * FROM customers WHERE id=?", (cid,)).fetchone()
    if not r:
        raise HTTPException(404, f"Unknown customer '{cid}'")
    return r


def _profile(c, cid: str) -> F.Profile:
    rows = c.execute("SELECT amount, ts, recipient_token FROM transactions WHERE customer_id=?", (cid,)).fetchall()
    return F.build_profile((r["amount"] for r in rows),
                           ((parse(r["ts"]).hour + parse(r["ts"]).minute / 60 + 3) % 24 for r in rows),
                           (r["recipient_token"] for r in rows))


def _kes(x: float) -> str:
    return f"KSh {x:,.0f}"


@app.get("/api/health")
def health():
    return {"status": "ok", "prototype": True, "data": "synthetic", "flag_score": FLAG_SCORE}


@app.get("/api/customers")
def customers():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT id, name, msisdn_masked, balance FROM customers ORDER BY id")]


@app.get("/api/customers/{cid}")
def customer(cid: str):
    with conn() as c:
        cust, prof = _customer(c, cid), _profile(c, cid)
        top = c.execute("SELECT recipient_name AS name, recipient_masked AS masked, COUNT(*) n FROM transactions "
                        "WHERE customer_id=? AND recipient_name IS NOT NULL AND tx_type='send_money' "
                        "GROUP BY recipient_token ORDER BY n DESC LIMIT 6", (cid,)).fetchall()
        return {"id": cust["id"], "name": cust["name"], "msisdn_masked": cust["msisdn_masked"],
                "balance": cust["balance"], "history_size": prof.n,
                "typical_amount": {"median": round(prof.median), "p25": round(prof.p25), "p75": round(prof.p75)},
                "frequent_contacts": [dict(r) for r in top]}


@app.get("/api/customers/{cid}/transactions")
def transactions(cid: str, limit: int = 10):
    with conn() as c:
        _customer(c, cid)
        rows = c.execute("SELECT * FROM transactions WHERE customer_id=? ORDER BY ts DESC LIMIT ?",
                         (cid, min(limit, 50))).fetchall()
        reported = {r["transaction_id"] for r in c.execute(
            "SELECT transaction_id FROM cases WHERE customer_id=? AND status NOT IN ('rejected','completed')", (cid,))}
        return [{**case_svc.tx_summary(r), "has_open_case": r["id"] in reported} for r in rows]


def _resolve_recipient(c, customer_id: str, tx_type: TxType, number: str) -> dict:
    """Simulates M-PESA Hakikisha name resolution: known contacts/merchants resolve; others get a stable name."""
    norm = normalize(tx_type, number)
    row = c.execute("SELECT recipient_name FROM transactions WHERE customer_id=? AND recipient_token=? "
                    "AND recipient_name IS NOT NULL LIMIT 1", (customer_id, token(tx_type, number))).fetchone()
    if row:
        return {"name": row["recipient_name"].upper(), "known": True, "simulated": True}
    if tx_type == "buy_goods" and norm in BUY_GOODS_TILLS:
        return {"name": BUY_GOODS_TILLS[norm].upper(), "known": True, "simulated": True}
    if tx_type == "paybill" and norm in PAYBILL_NUMBERS:
        return {"name": PAYBILL_NUMBERS[norm].upper(), "known": True, "simulated": True}
    h = int(hashlib.sha256(norm.encode()).hexdigest(), 16)
    if tx_type == "buy_goods":
        merchants = ["KILIMANI SUPERMARKET", "UMOJA HARDWARE", "WESTLANDS PHARMACY", "CBD ELECTRONICS",
                     "KASARANI MINI MART", "NYALI FRESH STORES", "ELDORET AGROVET", "THIKA AUTO SPARES"]
        return {"name": merchants[h % len(merchants)], "known": False, "simulated": True}
    if tx_type == "paybill":
        paybills = ["NAIROBI WATER PAYBILL", "SAFARICOM HOME FIBRE", "KENYA POWER POSTPAID", "ZUKU FIBRE PAYBILL",
                    "NHIF CONTRIBUTIONS", "KRA DOMESTIC TAXES", "STIMA SACCO PAYBILL", "MWALIMU NATIONAL SACCO"]
        return {"name": paybills[h % len(paybills)], "known": False, "simulated": True}
    first = ["DANIEL", "MARY", "JOSEPH", "ESTHER", "SAMUEL", "RUTH", "PETER", "NANCY"]
    last = ["RWAI", "KAMAU", "ODHIAMBO", "WAFULA", "CHEPKOECH", "MUTHONI", "OMONDI", "KARIUKI"]
    return {"name": f"{first[h % 8]} {last[(h // 8) % 8]}", "known": False, "simulated": True}


@app.get("/api/recipients/lookup")
def lookup(customer_id: str, tx_type: TxType, number: str):
    """Simulates M-PESA name resolution: known contacts resolve; others get a stable placeholder name."""
    if not valid(tx_type, number):
        raise HTTPException(422, "Enter a valid number")
    with conn() as c:
        _customer(c, customer_id)
        return _resolve_recipient(c, customer_id, tx_type, number)


@app.post("/api/protect/score")
def score(req: ScoreRequest):
    if not valid(req.tx_type, req.recipient):
        raise HTTPException(422, "Invalid recipient")
    with conn() as c:
        cust, prof = _customer(c, req.customer_id), _profile(c, req.customer_id)
        ts = parse(req.timestamp) if req.timestamp else now(c)
        recent = c.execute("SELECT COUNT(*) n FROM transactions WHERE customer_id=? AND ts>=? AND ts<=?",
                           (req.customer_id, iso(ts - timedelta(hours=1)), iso(ts))).fetchone()["n"]
        tok = token(req.tx_type, req.recipient)
        hour = (ts.hour + ts.minute / 60 + 3) % 24
        x = F.make_features(prof, req.amount, tok, hour, cust["balance"], recent)
        res = anomaly.risk_score(x)
        resolved = _resolve_recipient(c, req.customer_id, req.tx_type, req.recipient)
        recipient_name = resolved["name"]
        reasons = F.explain(x, prof, req.amount, recipient_name) if res["flagged"] else []
        new = bool(x[1])
        masked = mask(req.tx_type, req.recipient)
        title = "Unusual transaction detected"
        ussd = (f"{title}\n{_kes(req.amount)} to {recipient_name}"
                + (f"\n{reasons[0]}" if reasons else "") + "\n1. Yes, continue\n2. Cancel")
        return {
            "flagged": res["flagged"], "risk_score": res["risk_score"], "flag_threshold": FLAG_SCORE,
            "recipient_name": recipient_name,
            "reasons": reasons, "can_proceed": True,
            "warning": {"title": title, "amount": req.amount, "recipient": recipient_name,
                        "recipient_masked": masked, "recipient_name": recipient_name, "new_recipient": new,
                        "message": reasons[0] if reasons else "", "options": ["Yes, continue", "Cancel"]} if res["flagged"] else None,
            "ussd_text": ussd if res["flagged"] else None,
            "low_confidence": prof.n < F.MIN_HISTORY, "history_size": prof.n,
            "features": dict(zip(F.FEATURES, (round(float(v), 3) for v in x))),
            "model": "isolation_forest",
        }


@app.post("/api/transactions", status_code=201)
def create_transaction(req: TxRequest):
    """Records a simulated completed transaction so it can be reported/tracked later."""
    if not valid(req.tx_type, req.recipient):
        raise HTTPException(422, "Invalid recipient")
    with conn() as c:
        cust = _customer(c, req.customer_id)
        if req.amount > cust["balance"]:
            raise HTTPException(422, "Insufficient M-PESA balance")
        tid = f"tx_{random.getrandbits(48):012x}"
        ref = random.choice(string.ascii_uppercase) + "".join(random.choices(string.ascii_uppercase + string.digits, k=9))
        t = iso(now(c))
        rname = req.recipient_name or _resolve_recipient(c, req.customer_id, req.tx_type, req.recipient)["name"]
        c.execute("INSERT INTO transactions VALUES(?,?,?,?,?,?,?,?,?)",
                  (tid, req.customer_id, req.tx_type, token(req.tx_type, req.recipient),
                   mask(req.tx_type, req.recipient), rname, req.amount, t, ref))
        c.execute("UPDATE customers SET balance=balance-? WHERE id=?", (req.amount, req.customer_id))
        return {"id": tid, "mpesa_ref": ref, "tx_type": req.tx_type, "tx_type_label": TYPE_LABELS[req.tx_type],
                "amount": req.amount, "transaction_cost": 0.0, "ts": t, "recipient": mask(req.tx_type, req.recipient),
                "recipient_name": rname, "balance": cust["balance"] - req.amount, "simulated": True}


@app.get("/api/guidance")
def get_guidance(tx_type: TxType, reason: Optional[Reason] = None):
    return guidance(tx_type, reason)


@app.get("/api/reasons")
def reasons():
    return [{"id": k, "label": v} for k, v in REASON_LABELS.items()]


@app.post("/api/cases")
def open_case(req: CaseRequest):
    with conn() as c:
        _customer(c, req.customer_id)
        try:
            detail, duplicate = case_svc.create_case(c, req.customer_id, req.transaction_id, req.reason)
        except LookupError:
            raise HTTPException(404, "Transaction not found for this customer")
        return {**detail, "duplicate": duplicate}


@app.get("/api/customers/{cid}/cases")
def customer_cases(cid: str):
    with conn() as c:
        _customer(c, cid)
        return case_svc.list_cases(c, cid)


@app.get("/api/cases/{ref}")
def get_case(ref: str):
    with conn() as c:
        try:
            return case_svc.case_detail(c, ref)
        except LookupError:
            raise HTTPException(404, "Case not found")


@app.post("/api/cases/{ref}/simulate-advance")
def simulate_advance(ref: str, req: AdvanceRequest = AdvanceRequest()):
    """DEMO ONLY. Moves a case to its next simulated status and fast-forwards the demo clock."""
    with conn() as c:
        try:
            return case_svc.advance_case(c, ref, req.hours, req.force_status)
        except LookupError:
            raise HTTPException(404, "Case not found")
        except ValueError as e:
            raise HTTPException(409, str(e))


@app.get("/api/ml/metrics")
def ml_metrics():
    return {"anomaly_detection": anomaly.load()["metrics"], "reversal_prediction": eta.load()["metrics"],
            "note": "All figures are computed on synthetic data and do not represent real-world performance."}


@app.get("/api/demo/clock")
def demo_clock():
    with conn() as c:
        return {"now": iso(now(c)), "offset_hours": clock_offset_hours(c)}


@app.post("/api/demo/reset")
def demo_reset():
    seed(reset=True)
    return {"status": "reset"}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/ussd/")


@app.get("/presentation", include_in_schema=False)
def presentation():
    return RedirectResponse("/ussd/presentation.html")


if USSD_DIR.exists():
    app.mount("/ussd", StaticFiles(directory=USSD_DIR, html=True), name="ussd")
