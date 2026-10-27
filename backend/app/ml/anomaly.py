"""Transaction anomaly detection: Isolation Forest on customer-relative features."""
from __future__ import annotations

from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score

from .. import synthetic as syn
from ..config import FLAG_SCORE, MODEL_DIR, SEED
from ..features import FEATURES, build_profile, make_features
from ..identifiers import token

PATH = MODEL_DIR / "anomaly.joblib"
_REF_END = datetime(2026, 10, 1, tzinfo=timezone.utc)
_model = None


def _point_features(profile, p):
    return make_features(profile, p["amount"], token("send_money", p["rid"]), p["hour"], p["balance"], p["recent"])


def _dataset(n_customers: int, rng, n_hist=(60, 140), n_normal=25, n_anom=10):
    normal, anom, kinds = [], [], []
    for _ in range(n_customers):
        arch = syn.random_archetype(rng)
        hist = syn.simulate_history(arch, int(rng.integers(*n_hist)), rng, _REF_END)
        prof = build_profile((h["amount"] for h in hist), (h["hour"] for h in hist),
                             (token("send_money", h["rid"]) for h in hist))
        normal += [_point_features(prof, syn.normal_point(arch, rng)) for _ in range(n_normal)]
        for _ in range(n_anom):
            k = str(rng.choice(syn.ANOMALY_KINDS))
            kinds.append(k)
            anom.append(_point_features(prof, syn.anomalous_point(k, arch, rng)))
    return np.array(normal), np.array(anom), np.array(kinds)


def train(seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    Xn_tr, _, _ = _dataset(300, rng)
    Xn_va, Xa_va, _ = _dataset(100, rng)
    Xn_te, Xa_te, kinds_te = _dataset(200, rng)

    forest = IsolationForest(n_estimators=200, max_samples=256, random_state=seed).fit(Xn_tr)
    raw = lambda X: -forest.score_samples(X)  # higher = more anomalous

    va_n, va_a = raw(Xn_va), raw(Xa_va)
    p50, thr, hi = float(np.percentile(va_n, 50)), float(np.percentile(va_n, 97)), float(np.percentile(va_a, 50))

    te_n, te_a = raw(Xn_te), raw(Xa_te)
    y = np.r_[np.zeros(len(te_n)), np.ones(len(te_a))]
    s = np.r_[te_n, te_a]

    def rule(X):  # naive baseline: big amount OR new recipient
        return (X[:, 0] > np.log1p(5)) | (X[:, 1] == 1.0)

    def amount_rule(X):
        return X[:, 0] > np.log1p(5)

    metrics = {
        "data": "synthetic (held-out customers); not real M-PESA data",
        "n_test_normal": int(len(te_n)), "n_test_anomalous": int(len(te_a)),
        "roc_auc": round(float(roc_auc_score(y, s)), 3),
        "isolation_forest": {"false_positive_rate": round(float((te_n >= thr).mean()), 3),
                             "recall": round(float((te_a >= thr).mean()), 3)},
        "baseline_new_recipient_or_5x_amount": {"false_positive_rate": round(float(rule(Xn_te).mean()), 3),
                                                "recall": round(float(rule(Xa_te).mean()), 3)},
        "baseline_5x_amount_only": {"false_positive_rate": round(float(amount_rule(Xn_te).mean()), 3),
                                    "recall": round(float(amount_rule(Xa_te).mean()), 3)},
        "recall_by_anomaly_kind": {k: round(float((te_a[kinds_te == k] >= thr).mean()), 3)
                                   for k in syn.ANOMALY_KINDS},
        "calibration": {"flag_threshold_percentile_of_normal": 97, "flag_at_risk_score": FLAG_SCORE},
    }
    bundle = {"forest": forest, "p50": p50, "thr": thr, "hi": hi, "features": FEATURES, "metrics": metrics}
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, PATH)
    return bundle


def load() -> dict:
    global _model
    if _model is None:
        _model = joblib.load(PATH) if PATH.exists() else train()
    return _model


def risk_score(x: np.ndarray) -> dict:
    m = load()
    raw = float(-m["forest"].score_samples(x.reshape(1, -1))[0])
    p50, thr, hi = m["p50"], m["thr"], max(m["hi"], m["thr"] + 1e-6)
    if raw <= p50:
        score = 0.0
    elif raw <= thr:
        score = FLAG_SCORE * (raw - p50) / (thr - p50)
    else:
        score = FLAG_SCORE + (100 - FLAG_SCORE) * min(1.0, (raw - thr) / (hi - thr))
    return {"raw": raw, "risk_score": round(score, 1), "flagged": raw >= thr}
