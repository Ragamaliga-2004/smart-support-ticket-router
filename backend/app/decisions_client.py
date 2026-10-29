"""OpenAI Decisions API client and response parsing."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from .config import (
    ALLOWED_CATEGORIES,
    DECISIONS_MODEL,
    OPENAI_DECISIONS_URL,
    REQUEST_TIMEOUT_SECONDS,
    get_openai_api_key,
)


class DecisionsApiError(Exception):
    """Raised when the Decisions API call fails or returns unusable data."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def build_decisions_payload(complaint: str) -> dict[str, Any]:
    """Build the request body for a choice classification."""
    return {
        "model": DECISIONS_MODEL,
        "input": complaint,
        "questions": [
            {
                "type": "choice",
                "name": "department",
                "instructions": (
                    "Choose the support department that best matches the "
                    "customer's complaint. Classify by meaning, not just keywords."
                ),
                "choices": [
                    {
                        "value": "billing",
                        "description": (
                            "Payments, duplicate charges, invoices, and refunds."
                        ),
                    },
                    {
                        "value": "technical",
                        "description": (
                            "Login problems, software errors, and product malfunctions."
                        ),
                    },
                    {
                        "value": "shipping",
                        "description": (
                            "Delivery delays, tracking, and missing packages."
                        ),
                    },
                    {
                        "value": "other",
                        "description": (
                            "Requests that do not fit the other categories."
                        ),
                    },
                ],
            }
        ],
    }


def _find_department_answer(payload: dict[str, Any]) -> dict[str, Any]:
    answers = payload.get("answers")
    if not isinstance(answers, list) or not answers:
        raise DecisionsApiError("Decisions API response missing answers.")

    for answer in answers:
        if not isinstance(answer, dict):
            continue
        name = answer.get("name")
        if name == "department" or name is None:
            return answer

    first = answers[0]
    if isinstance(first, dict):
        return first
    raise DecisionsApiError("Decisions API response has malformed answers.")


def _extract_choice(answer: dict[str, Any]) -> str:
    choice = answer.get("choice")
    if isinstance(choice, str) and choice.strip():
        return choice.strip()

    # Some shapes may nest the selected value
    selected = answer.get("selected") or answer.get("value")
    if isinstance(selected, str) and selected.strip():
        return selected.strip()

    raise DecisionsApiError("Decisions API response missing a choice value.")


def _extract_confidence(answer: dict[str, Any]) -> Optional[float]:
    confidence = answer.get("confidence")
    if confidence is None:
        return None
    try:
        return float(confidence)
    except (TypeError, ValueError):
        return None


def _extract_probabilities(
    answer: dict[str, Any],
) -> Optional[list[dict[str, float | str]]]:
    raw = answer.get("probabilities")
    if raw is None:
        return None
    if not isinstance(raw, list):
        return None

    items: list[dict[str, float | str]] = []
    for entry in raw:
        if isinstance(entry, dict):
            value = entry.get("value")
            probability = entry.get("probability")
            if value is None or probability is None:
                continue
            try:
                items.append({"value": str(value), "probability": float(probability)})
            except (TypeError, ValueError):
                continue
        # Alternate shape: {"billing": 0.9, ...} is handled separately if needed
    return items or None


def parse_decisions_response(payload: Any) -> dict[str, Any]:
    """
    Parse a Decisions API response into a frontend-friendly dict.

    Returns keys: category, confidence, probabilities, model
    Raises DecisionsApiError on unusable payloads.
    """
    if not isinstance(payload, dict):
        raise DecisionsApiError("Decisions API returned a non-object response.")

    answer = _find_department_answer(payload)
    category = _extract_choice(answer)

    if category not in ALLOWED_CATEGORIES:
        raise DecisionsApiError(
            f"Decisions API returned unexpected category '{category}'."
        )

    model = payload.get("model")
    if not isinstance(model, str) or not model:
        model = DECISIONS_MODEL

    return {
        "category": category,
        "confidence": _extract_confidence(answer),
        "probabilities": _extract_probabilities(answer),
        "model": model,
    }


def _safe_upstream_message(response: httpx.Response) -> str:
    """Extract a short upstream error message without leaking secrets."""
    try:
        body = response.json()
    except ValueError:
        return ""
    if not isinstance(body, dict):
        return ""
    error = body.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()[:240]
    if isinstance(error, str) and error.strip():
        return error.strip()[:240]
    return ""


async def classify_complaint(complaint: str) -> dict[str, Any]:
    """Call the OpenAI Decisions API and return a parsed result."""
    api_key = get_openai_api_key()
    if not api_key:
        raise DecisionsApiError(
            "OPENAI_API_KEY is not configured on the server.",
            status_code=500,
        )

    payload = build_decisions_payload(complaint)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                OPENAI_DECISIONS_URL,
                json=payload,
                headers=headers,
            )
    except httpx.TimeoutException as exc:
        raise DecisionsApiError(
            "The Decisions API request timed out. Please try again.",
            status_code=504,
        ) from exc
    except httpx.RequestError as exc:
        raise DecisionsApiError(
            "Could not reach the Decisions API. Check network connectivity.",
            status_code=502,
        ) from exc

    upstream = _safe_upstream_message(response)

    if response.status_code == 401:
        detail = f" Upstream: {upstream}" if upstream else ""
        raise DecisionsApiError(
            "OpenAI API authentication failed. Check OPENAI_API_KEY."
            " Restart the backend after updating .env."
            f"{detail}",
            status_code=502,
        )
    if response.status_code == 403:
        detail = f" Upstream: {upstream}" if upstream else ""
        raise DecisionsApiError(
            "OpenAI API access denied. Confirm project permissions and model access for gpt-6-luna."
            f"{detail}",
            status_code=502,
        )
    if response.status_code == 429:
        detail = f" Upstream: {upstream}" if upstream else ""
        raise DecisionsApiError(
            "OpenAI API rate limit or quota exceeded. Try again later."
            f"{detail}",
            status_code=502,
        )
    if response.status_code >= 400:
        detail = f" Upstream: {upstream}" if upstream else ""
        raise DecisionsApiError(
            f"Decisions API returned HTTP {response.status_code}. "
            "Confirm endpoint availability and model access for gpt-6-luna."
            f"{detail}",
            status_code=502,
        )

    try:
        body = response.json()
    except ValueError as exc:
        raise DecisionsApiError(
            "Decisions API returned a non-JSON response.",
            status_code=502,
        ) from exc

    return parse_decisions_response(body)
