import os
import tempfile

os.environ["SAFEUNDO_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

import pytest
from fastapi.testclient import TestClient

from app.main import app

CID = "cust_amina"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_normal_transaction_not_flagged(client):
    r = client.post("/api/protect/score", json={"customer_id": CID, "recipient": "0700123401", "amount": 800}).json()
    assert r["flagged"] is False and r["warning"] is None


def test_large_amount_new_recipient_flagged(client):
    r = client.post("/api/protect/score", json={"customer_id": CID, "recipient": "0799999999", "amount": 20000}).json()
    assert r["flagged"] is True
    assert r["can_proceed"] is True            # SafeUndo warns; it never blocks
    assert any("higher than what you usually send" in x for x in r["reasons"])
    assert "1. Yes, continue" in r["ussd_text"]
    assert r["recipient_name"] in r["ussd_text"]
    assert "(new recipient)" not in r["ussd_text"]
    assert r["warning"]["recipient"] == r["recipient_name"]
    assert "0799999999" not in str(r)          # raw number never echoed back


def test_distinct_buy_goods_and_paybill_lookup(client):
    till = client.get("/api/recipients/lookup", params={"customer_id": CID, "tx_type": "buy_goods", "number": "841209"}).json()
    pb = client.get("/api/recipients/lookup", params={"customer_id": CID, "tx_type": "paybill", "number": "888880"}).json()
    assert till["name"] == "NAIVAS SUPERMARKET"
    assert pb["name"] == "KPLC PREPAID"
    assert till["name"] != pb["name"]


def test_invalid_recipient_rejected(client):
    assert client.post("/api/protect/score", json={"customer_id": CID, "recipient": "12", "amount": 10}).status_code == 422


def test_seeded_headline_case_has_prediction(client):
    d = client.get("/api/cases/SU-1042").json()
    assert d["status"] == "under_review" and d["simulated"] is True
    p = d["prediction"]
    assert 0 <= p["delay_risk"] <= 1 and p["low_hours"] <= p["remaining_hours"] <= p["high_hours"] + 1e-6
    assert d["guidance"]["steps"][0].startswith("Forward the original M-PESA confirmation SMS to 456")


def test_end_to_end_report_and_track(client):
    tx = client.post("/api/transactions", json={"customer_id": "cust_grace", "recipient": "0700323499",
                                                 "amount": 300}).json()
    body = {"customer_id": "cust_grace", "transaction_id": tx["id"], "reason": "wrong_number"}
    case = client.post("/api/cases", json=body).json()
    assert case["status"] == "submitted" and case["duplicate"] is False
    assert client.post("/api/cases", json=body).json()["ref"] == case["ref"]   # idempotent
    seen = []
    for _ in range(5):
        r = client.post(f"/api/cases/{case['ref']}/simulate-advance")
        if r.status_code == 409:
            break
        seen.append(r.json()["status"])
    assert seen[0] == "under_review" and seen[-1] in ("completed", "rejected")


def test_insufficient_balance(client):
    r = client.post("/api/transactions", json={"customer_id": "cust_grace", "recipient": "0700323401", "amount": 99999})
    assert r.status_code == 422


def test_metrics_labelled_synthetic(client):
    m = client.get("/api/ml/metrics").json()
    assert "synthetic" in m["note"]
    assert m["reversal_prediction"]["resolution_time_hours"]["mae_random_forest"] < \
           m["reversal_prediction"]["resolution_time_hours"]["mae_median_baseline"]
