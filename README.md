# SafeUndo

AI-powered M-PESA transaction protection and reversal tracking. Hackathon prototype for the
Safaricom Interns Hackathon (AI, Machine Learning & Predictive Analytics).

SafeUndo (1) warns a customer before an unusual transaction, (2) guides them through the existing
reversal process, and (3) tracks the request with a predicted resolution time and delay risk.
It **complements** existing M-PESA reversal mechanisms. It never reverses anything itself.

> **Prototype boundaries.** All customers, transactions and reversal cases are **synthetic**.
> Reversal status changes are **simulated** and labelled as such in every interface. The Android app
> *simulates* how SafeUndo would look inside My OneApp; it does not modify or connect to the real app,
> and the USSD simulator does not touch the live `*334#` service.

## What's in the repo

| Path | What it is |
|---|---|
| `backend/` | FastAPI + SQLite + scikit-learn. One shared brain for both channels |
| `ussd-sim/` | Web USSD simulator (`*334#`) at `/ussd/`, 3-minute interactive Anime Cinema Presentation at `/presentation` (`ussd-sim/presentation.html`), and rendered 1080p MP4 film (`ussd-sim/SafeUndo_Anime_Demo_3min.mp4`) |
| `android/` | Kotlin + Jetpack Compose app that mimics My OneApp's dark UI with SafeUndo integrated |
| `scripts/render_anime_film.py` | Reproducible 1920×1080 30fps (`5,400` frames = `180.00s`) MP4 video and stereo 44.1 kHz audio renderer |
| `docs/` | Technical Brief (`docs/TECHNICAL_BRIEF.md`, `docs/SafeUndo_Technical_Brief.docx`), Architecture (`docs/ARCHITECTURE.md`), 4-minute demo script (`docs/DEMO.md`), and Anime Film Production Book (`docs/ANIME_FILM_PRODUCTION_BOOK.md`) |
| `.devcontainer/` | GitHub Codespaces / Dev Container config (Python 3.12, port 8000) |
| `.github/workflows/` | GitHub Actions CI (`ci.yml`) running `python -m app.bootstrap` and `pytest` |

## Run it

### 1. Backend + USSD simulator

**Windows (PowerShell — no venv activation needed):**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

**macOS / Linux:**
```bash
cd backend
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

**GitHub Codespaces:**
Open the repo in Codespaces (dependencies install automatically via `.devcontainer/devcontainer.json`), then run:
```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

First start seeds the demo database and trains both models (a few seconds).
Open **http://localhost:8000/** (redirects to `/ussd/`) for the USSD simulator, **/docs** for the interactive OpenAPI docs, and **/api/ml/metrics** for model evaluation.
Run `.\.venv\Scripts\python -m app.bootstrap` (or `./.venv/bin/python -m app.bootstrap`) to re-seed and retrain, and `.\.venv\Scripts\python -m pytest` to run the test suite.

### 2. Android app
Open `android/` in Android Studio (Koala or newer, JDK 17) and run on an emulator.
The emulator reaches the backend at `http://10.0.2.2:8000/` (default).
For a physical phone, set `safeundo.apiBaseUrl=http://<your-LAN-IP>:8000/` in `android/gradle.properties`
and start uvicorn with `--host 0.0.0.0`.

## How it works

**A. Transaction protection.** Per-customer behavioural profile (typical amount, known recipients,
usual hours) turned into five customer-relative features: amount vs usual, new recipient, hour rarity,
transactions in the last hour, amount vs balance. An **Isolation Forest** scores them; the score is
calibrated so that ~3% of ordinary synthetic transactions are flagged. The warning explains *why* in
plain language and always lets the customer continue. Recipient numbers are salted and hashed at rest.

**B. Guided reversal and tracking.** Guidance per transaction type (Send Money: forward the confirmation
SMS to 456; Pochi la Biashara, PayBill and Buy Goods are deliberately cautious and flagged for
verification). Cases get a reference like `SU-1042`, a status timeline, and are idempotent (one open
case per transaction). Both channels read the same cases.

**C. Predictive tracking (the differentiator).** A **Random Forest regressor** estimates remaining
resolution time (with an 80% interval), a **Random Forest classifier** estimates the probability of
exceeding a 24-hour target, and rules turn that into a suggested next action with reasons.

## Model evaluation (synthetic data, held-out customers/cases)

Run `GET /api/ml/metrics` for the live numbers. Typical results:

| Model | Result |
|---|---|
| Isolation Forest | ROC-AUC ~0.99, ~3% false-positive rate, ~90% recall (weakest on subtle "night + new recipient" cases) |
| Naive baseline (new recipient OR >5x amount) | ~12% false-positive rate, ~83% recall |
| Resolution-time RF vs median baseline | MAE ~2.4h vs ~6.1h; 80% interval coverage ~79% |
| Delay-risk classifier | ROC-AUC ~0.99, Brier ~0.04 vs ~0.22 prevalence baseline |

**Read these honestly.** The synthetic generator and the models share assumptions, and a case's status and
elapsed time are derived from its hidden duration, which flatters the reversal model. These numbers show the
pipeline works and is evaluated properly on held-out data. They say nothing about real-world performance.
Validation against real, authorised historical outcomes is the first production step.

## Working, simulated, future

* **Working:** simulated customer journeys, API, case storage, ML training and inference.
* **Simulated:** My OneApp integration, production-channel interception, real reversal statuses/notifications.
* **Future:** authorised My OneApp/USSD integration, supported M-PESA interfaces, live case-status sync,
  Data Protection Act compliance review, consent, model monitoring.

SafeUndo does not promise that a transaction will be reversed, guarantee approval, or reduce resolution time.
