"""Diagnose OPENAI_API_KEY without printing the secret."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

key = (os.getenv("OPENAI_API_KEY") or "").strip()
print("key_present:", bool(key))
print("key_length:", len(key))
print("key_prefix:", key[:8] + "..." if key else "(empty)")
print("starts_with_sk:", key.startswith("sk-"))
print("has_whitespace:", any(c.isspace() for c in key))

if not key:
    sys.exit(1)

headers = {"Authorization": f"Bearer {key}"}

print("\n--- GET /v1/models (auth check) ---")
with httpx.Client(timeout=30.0) as client:
    models = client.get("https://api.openai.com/v1/models", headers=headers)
    print("status:", models.status_code)
    try:
        body = models.json()
    except Exception:
        print("body:", models.text[:500])
    else:
        if models.status_code >= 400:
            err = body.get("error", body)
            print("error:", err)
        else:
            ids = [m.get("id") for m in body.get("data", [])[:8]]
            print("ok; sample models:", ids)
            luna = [m.get("id") for m in body.get("data", []) if "luna" in (m.get("id") or "").lower()]
            decisions = [m.get("id") for m in body.get("data", []) if "decision" in (m.get("id") or "").lower()]
            print("luna-related models:", luna or "(none listed)")
            print("decision-related models:", decisions or "(none listed)")

print("\n--- POST /v1/decisions (demo call) ---")
payload = {
    "model": "gpt-6-luna",
    "input": "I was charged twice for my order.",
    "questions": [
        {
            "type": "choice",
            "name": "department",
            "instructions": "Choose the support department.",
            "choices": [
                {"value": "billing", "description": "Billing"},
                {"value": "technical", "description": "Technical"},
                {"value": "shipping", "description": "Shipping"},
                {"value": "other", "description": "Other"},
            ],
        }
    ],
}
with httpx.Client(timeout=30.0) as client:
    resp = client.post(
        "https://api.openai.com/v1/decisions",
        headers={**headers, "Content-Type": "application/json"},
        json=payload,
    )
    print("status:", resp.status_code)
    try:
        body = resp.json()
    except Exception:
        print("body:", resp.text[:800])
    else:
        if resp.status_code >= 400:
            print("error:", body.get("error", body))
        else:
            print("ok; keys:", list(body.keys()))
