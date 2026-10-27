"""Central configuration. Everything here is demo-grade, not production config."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("SAFEUNDO_DB", BASE_DIR / "data" / "safeundo.db"))
MODEL_DIR = Path(os.getenv("SAFEUNDO_MODELS", BASE_DIR / "models"))
USSD_DIR = BASE_DIR.parent / "ussd-sim"

# Recipient identifiers are never stored in the clear: they are salted and hashed.
SALT = os.getenv("SAFEUNDO_SALT", "safeundo-demo-salt")

EAT_OFFSET_H = 3          # East Africa Time (UTC+3), used for time-of-day features
DELAY_TARGET_HOURS = 24   # configured resolution target used for delay-risk
FLAG_SCORE = 60.0         # risk score at/above which a warning is shown
SEED = 7
