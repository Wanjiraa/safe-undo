"""One-shot setup: seed the database and train both models. Run: python -m app.bootstrap"""
import json

from .ml import anomaly, eta
from .seed import seed

if __name__ == "__main__":
    seed(reset=True)
    print("Seeded demo data.")
    print(json.dumps(anomaly.train()["metrics"], indent=2))
    print(json.dumps(eta.train()["metrics"], indent=2))
