"""Predictive reversal tracking: resolution-time regression, delay-risk classifier, baseline."""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import brier_score_loss, roc_auc_score

from .. import synthetic as syn
from ..config import DELAY_TARGET_HOURS, MODEL_DIR, SEED

PATH = MODEL_DIR / "eta.joblib"
STATUS_IDX = {"submitted": 0, "under_review": 1, "approved": 2}
COLUMNS = ([f"type_{t}" for t in syn.TX_TYPES] + [f"reason_{r}" for r in syn.REASONS]
           + ["log_amount", "submitted_hour", "weekend", "elapsed", "status_idx", "hours_in_status"])
_models = None


def vectorize(rows: list[dict]) -> np.ndarray:
    out = []
    for r in rows:
        out.append([float(r["tx_type"] == t) for t in syn.TX_TYPES]
                   + [float(r["reason"] == x) for x in syn.REASONS]
                   + [np.log1p(r["amount"]), r["submitted_hour"], r["weekend"], r["elapsed"],
                      r["status_idx"], r["hours_in_status"]])
    return np.array(out)


def train(seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    rows = syn.simulate_cases(9000, rng)
    df = pd.DataFrame(rows)
    n = len(rows)
    tr, ca, te = rows[: int(n * .7)], rows[int(n * .7): int(n * .85)], rows[int(n * .85):]
    X = {k: vectorize(v) for k, v in (("tr", tr), ("ca", ca), ("te", te))}
    y = {k: np.array([r["remaining"] for r in v]) for k, v in (("tr", tr), ("ca", ca), ("te", te))}
    tot = {k: np.array([r["total"] for r in v]) for k, v in (("tr", tr), ("ca", ca), ("te", te))}

    reg = RandomForestRegressor(n_estimators=200, min_samples_leaf=4, n_jobs=-1, random_state=seed)
    reg.fit(X["tr"], np.log1p(y["tr"]))
    resid = np.log1p(y["ca"]) - reg.predict(X["ca"])
    q10, q90 = float(np.percentile(resid, 10)), float(np.percentile(resid, 90))

    clf = RandomForestClassifier(n_estimators=200, min_samples_leaf=4, n_jobs=-1, random_state=seed)
    clf.fit(X["tr"], (tot["tr"] > DELAY_TARGET_HOURS).astype(int))

    # Baseline: median remaining hours per (type, status) from the training split.
    base_df = pd.DataFrame(tr)
    base = base_df.groupby(["tx_type", "status_idx"])["remaining"].median().to_dict()
    glob = float(base_df["remaining"].median())
    base_pred = np.array([base.get((r["tx_type"], r["status_idx"]), glob) for r in te])

    p_log = reg.predict(X["te"])
    point = np.expm1(p_log)
    lo, hi = np.expm1(p_log + q10), np.expm1(p_log + q90)
    y_delay = (tot["te"] > DELAY_TARGET_HOURS).astype(int)
    p_delay = clf.predict_proba(X["te"])[:, 1]
    mae_rf, mae_base = float(np.mean(np.abs(point - y["te"]))), float(np.mean(np.abs(base_pred - y["te"])))
    metrics = {
        "data": "synthetic demonstration cases; cannot establish real reversal performance",
        "n_train": len(tr), "n_test": len(te),
        "resolution_time_hours": {
            "mae_random_forest": round(mae_rf, 2), "mae_median_baseline": round(mae_base, 2),
            "improvement_vs_baseline_pct": round(100 * (1 - mae_rf / mae_base), 1),
            "interval_coverage_80pct_target": round(float(((y["te"] >= lo) & (y["te"] <= hi)).mean()), 3)},
        "delay_risk": {"target_hours": DELAY_TARGET_HOURS,
                       "roc_auc": round(float(roc_auc_score(y_delay, p_delay)), 3),
                       "brier": round(float(brier_score_loss(y_delay, p_delay)), 3),
                       "brier_prevalence_baseline": round(float(brier_score_loss(y_delay, np.full(len(y_delay), y_delay.mean()))), 3),
                       "prevalence": round(float(y_delay.mean()), 3)},
        "group_median_total_hours": {t: round(float(df[df.tx_type == t]["total"].median()), 1) for t in syn.TX_TYPES},
    }
    bundle = {"reg": reg, "clf": clf, "q10": q10, "q90": q90, "metrics": metrics}
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, PATH)
    return bundle


def load() -> dict:
    global _models
    if _models is None:
        _models = joblib.load(PATH) if PATH.exists() else train()
    return _models


def predict(case: dict) -> dict:
    m = load()
    x = vectorize([case])
    p = float(m["reg"].predict(x)[0])
    point, lo, hi = (float(np.expm1(max(p + d, 0))) for d in (0.0, m["q10"], m["q90"]))
    risk = float(m["clf"].predict_proba(x)[0][1])
    level = "Low" if risk < 0.35 else ("Moderate" if risk < 0.65 else "Elevated")
    return {"remaining_hours": round(point, 1), "low_hours": round(lo, 1), "high_hours": round(hi, 1),
            "label": fmt_range(lo, hi), "delay_risk": round(risk, 2), "risk_level": level,
            "target_hours": DELAY_TARGET_HOURS}


def fmt_hours(h: float) -> str:
    if h < 1:
        return f"{max(int(round(h * 60 / 5) * 5), 5)} min"
    if h < 36:
        return f"{h:.0f}" if h >= 10 else f"{h:.1f}".rstrip("0").rstrip(".")
    return f"{h / 24:.1f}".rstrip("0").rstrip(".")


def fmt_range(lo: float, hi: float) -> str:
    if hi < 1:
        return "under 1 hour"
    unit = "days" if hi >= 36 else "hours"
    a = lo / 24 if unit == "days" else lo
    b = hi / 24 if unit == "days" else hi
    fa = f"{a:.0f}" if a >= 10 or unit == "hours" else f"{a:.1f}"
    fb = f"{b:.0f}" if b >= 10 or unit == "hours" else f"{b:.1f}"
    return f"{fa}\u2013{fb} {unit}" if fa != fb else f"about {fb} {unit}"
