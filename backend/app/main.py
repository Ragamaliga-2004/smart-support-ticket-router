"""FastAPI application for Smart Support Ticket Router."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .config import CORS_ORIGIN
from .decisions_client import DecisionsApiError, classify_complaint
from .schemas import ClassifyRequest, ClassifyResponse, ErrorResponse

app = FastAPI(
    title="Smart Support Ticket Router",
    description="Demo backend that classifies support complaints via OpenAI Decisions API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/classify",
    response_model=ClassifyResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
async def classify(body: ClassifyRequest) -> ClassifyResponse | JSONResponse:
    """Classify a customer complaint into a support category."""
    try:
        result = await classify_complaint(body.complaint)
        return ClassifyResponse(
            success=True,
            category=result["category"],
            confidence=result.get("confidence"),
            probabilities=result.get("probabilities"),
            model=result.get("model"),
        )
    except DecisionsApiError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=exc.message).model_dump(),
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
