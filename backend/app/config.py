"""Application configuration constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Prefer project-root .env, then backend/.env, then process cwd.
_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_DIR = Path(__file__).resolve().parents[1]


def reload_env() -> None:
    """Load .env files, allowing local .env to override stale process env."""
    load_dotenv(_ROOT / ".env", override=True)
    load_dotenv(_BACKEND_DIR / ".env", override=True)
    load_dotenv(override=True)


reload_env()


def get_openai_api_key() -> str:
    """Return the current API key (re-reads .env so demo restarts are less painful)."""
    reload_env()
    return (os.getenv("OPENAI_API_KEY") or "").strip()


OPENAI_DECISIONS_URL = "https://api.openai.com/v1/decisions"
DECISIONS_MODEL = "gpt-6-luna"

MAX_COMPLAINT_LENGTH = 2000
REQUEST_TIMEOUT_SECONDS = 30.0

# Application policy: recommend manual review when confidence is missing
# or below this value. Not statistically validated.
MANUAL_REVIEW_CONFIDENCE_THRESHOLD = 0.70

ALLOWED_CATEGORIES = frozenset({"billing", "technical", "shipping", "other"})

CATEGORY_DESCRIPTIONS = {
    "billing": "Payments, duplicate charges, invoices, and refunds.",
    "technical": "Login problems, software errors, and product malfunctions.",
    "shipping": "Delivery delays, tracking, and missing packages.",
    "other": "Requests that do not fit the other categories.",
}

CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")
