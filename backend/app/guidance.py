"""Transaction-type-specific reversal guidance.

SafeUndo complements the existing M-PESA reversal mechanisms; it never claims to reverse anything.
Only the Send Money self-service step (forward the confirmation SMS to 456) is stated as an
established method. Every other entry is deliberately cautious and flagged for verification.
"""
from __future__ import annotations

REASON_LABELS = {"wrong_number": "Wrong number", "wrong_amount": "Wrong amount", "fraud": "Fraud",
                 "refund": "Refund", "other": "Other reason"}
TYPE_LABELS = {"send_money": "Send Money", "pochi": "Pochi la Biashara",
               "paybill": "PayBill", "buy_goods": "Buy Goods"}

_VERIFY = ("Eligibility and exact steps depend on Safaricom's current rules. "
           "Confirm the official procedure before relying on this guidance.")

_GUIDE = {
    "send_money": {
        "title": "Reverse a Send Money transaction",
        "steps": ["Forward the original M-PESA confirmation SMS to 456.",
                  "Follow the instructions Safaricom sends back.",
                  "Keep the transaction ID handy and track the request in SafeUndo."],
        "verified": True,
    },
    "pochi": {
        "title": "Reverse a Pochi la Biashara payment",
        "steps": ["Pochi la Biashara needs transaction-specific guidance. Do not assume the Send Money method applies.",
                  "Note the transaction ID, amount and recipient.",
                  "Ask Safaricom's official support channel how to reverse a Pochi la Biashara payment."],
        "verified": False,
    },
    "paybill": {
        "title": "Reverse a PayBill payment",
        "steps": ["Contact the receiving organisation with the transaction ID, amount and account number.",
                  "Ask them to confirm whether they can return the payment.",
                  "If they cannot help, use Safaricom's official support channel."],
        "verified": False,
    },
    "buy_goods": {
        "title": "Reverse a Buy Goods payment",
        "steps": ["Contact the merchant with the till number, transaction ID and amount.",
                  "Ask the merchant whether they can refund or reverse the payment.",
                  "If the merchant cannot help, use Safaricom's official support channel."],
        "verified": False,
    },
}


def guidance(tx_type: str, reason: str | None = None) -> dict:
    g = _GUIDE[tx_type]
    steps = list(g["steps"])
    if reason == "fraud":
        steps.insert(0, "If you suspect fraud, report it through Safaricom's official channels straight away.")
    return {"tx_type": tx_type, "tx_type_label": TYPE_LABELS[tx_type], "title": g["title"], "steps": steps,
            "verified_procedure": g["verified"], "note": _VERIFY,
            "disclaimer": "SafeUndo does not reverse transactions or guarantee approval."}
