"""Tests for /api/classify — all HTTP calls to OpenAI are mocked."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.decisions_client import (
    DecisionsApiError,
    build_decisions_payload,
    parse_decisions_response,
)
from app.main import app

client = TestClient(app)

VALID_API_RESPONSE = {
    "model": "gpt-6-luna",
    "answers": [
        {
            "name": "department",
            "choice": "billing",
            "confidence": 0.93,
            "probabilities": [
                {"value": "billing", "probability": 0.95},
                {"value": "technical", "probability": 0.02},
                {"value": "shipping", "probability": 0.01},
                {"value": "other", "probability": 0.02},
            ],
        }
    ],
}


def test_empty_complaint_rejected():
    response = client.post("/api/classify", json={"complaint": ""})
    assert response.status_code == 422


def test_whitespace_complaint_rejected():
    response = client.post("/api/classify", json={"complaint": "   "})
    assert response.status_code == 422


def test_overlong_complaint_rejected():
    response = client.post(
        "/api/classify",
        json={"complaint": "x" * 2001},
    )
    assert response.status_code == 422


def test_build_payload_contains_model_choice_and_categories():
    payload = build_decisions_payload("I was charged twice for my order.")
    assert payload["model"] == "gpt-6-luna"
    assert payload["input"] == "I was charged twice for my order."
    assert len(payload["questions"]) == 1
    question = payload["questions"][0]
    assert question["type"] == "choice"
    assert question["name"] == "department"
    values = {c["value"] for c in question["choices"]}
    assert values == {"billing", "technical", "shipping", "other"}


def test_parse_valid_mocked_api_response():
    parsed = parse_decisions_response(VALID_API_RESPONSE)
    assert parsed["category"] == "billing"
    assert parsed["confidence"] == 0.93
    assert parsed["model"] == "gpt-6-luna"
    assert len(parsed["probabilities"]) == 4


def test_missing_confidence_handled_safely():
    payload = {
        "model": "gpt-6-luna",
        "answers": [{"name": "department", "choice": "technical"}],
    }
    parsed = parse_decisions_response(payload)
    assert parsed["category"] == "technical"
    assert parsed["confidence"] is None
    assert parsed["probabilities"] is None


def test_unexpected_category_raises():
    payload = {
        "answers": [{"name": "department", "choice": "legal"}],
    }
    with pytest.raises(DecisionsApiError):
        parse_decisions_response(payload)


def test_malformed_response_raises():
    with pytest.raises(DecisionsApiError):
        parse_decisions_response({"answers": "not-a-list"})


def test_missing_answers_raises():
    with pytest.raises(DecisionsApiError):
        parse_decisions_response({})


@pytest.mark.asyncio
async def test_upstream_timeout_safe_error():
    with patch("app.decisions_client.get_openai_api_key", return_value="test-key"):
        with patch(
            "app.decisions_client.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.side_effect = httpx.TimeoutException("timed out")
            mock_client_cls.return_value = mock_client

            response = client.post(
                "/api/classify",
                json={"complaint": "I was charged twice for my order."},
            )

    assert response.status_code == 504
    body = response.json()
    assert body["success"] is False
    assert "timed out" in body["error"].lower()


def test_api_error_translated_safely():
    mock_response = httpx.Response(
        500,
        request=httpx.Request("POST", "https://api.openai.com/v1/decisions"),
        json={"error": {"message": "internal"}},
    )

    with patch("app.decisions_client.get_openai_api_key", return_value="test-key"):
        with patch(
            "app.decisions_client.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            response = client.post(
                "/api/classify",
                json={"complaint": "I cannot log into my account."},
            )

    assert response.status_code == 502
    body = response.json()
    assert body["success"] is False
    assert "error" in body
    assert "test-key" not in str(body)


def test_successful_classify_with_mocked_api():
    mock_response = httpx.Response(
        200,
        request=httpx.Request("POST", "https://api.openai.com/v1/decisions"),
        json=VALID_API_RESPONSE,
    )

    with patch("app.decisions_client.get_openai_api_key", return_value="test-key"):
        with patch(
            "app.decisions_client.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            response = client.post(
                "/api/classify",
                json={"complaint": "I was charged twice for my order."},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["category"] == "billing"
    assert body["confidence"] == 0.93
    assert body["model"] == "gpt-6-luna"
