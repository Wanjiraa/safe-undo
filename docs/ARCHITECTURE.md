# Architecture

```
 Android (Compose)  ──┐
                      ├──►  FastAPI  ──►  SQLite (customers, transactions, cases, status_history)
 USSD simulator (web) ┘        │
                               └──►  ML engine (scikit-learn): IsolationForest, RF regressor, RF classifier
```

* Both channels call the same endpoints, so a case opened on one is visible on the other.
* `POST /api/protect/score` returns a risk score, reasons and ready-to-render USSD text.
* `POST /api/cases` is idempotent per open transaction. `POST /api/cases/{ref}/simulate-advance` is demo-only.
* Demo clock (`/api/demo/clock`) lets a demo fast-forward time so predictions visibly update.
* Privacy by design: recipients are salted-hash tokens plus masked display strings; no raw numbers are stored or returned.
