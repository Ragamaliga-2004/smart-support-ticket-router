"""Request and response schemas for the classify endpoint."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from .config import MAX_COMPLAINT_LENGTH

Category = Literal["billing", "technical", "shipping", "other"]


class ClassifyRequest(BaseModel):
    complaint: str = Field(..., min_length=1, max_length=MAX_COMPLAINT_LENGTH)

    @field_validator("complaint")
    @classmethod
    def complaint_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Complaint cannot be empty or whitespace only.")
        if len(stripped) > MAX_COMPLAINT_LENGTH:
            raise ValueError(
                f"Complaint must be at most {MAX_COMPLAINT_LENGTH} characters."
            )
        return stripped


class ProbabilityItem(BaseModel):
    value: str
    probability: float


class ClassifyResponse(BaseModel):
    success: bool
    category: Optional[Category] = None
    confidence: Optional[float] = None
    probabilities: Optional[list[ProbabilityItem]] = None
    model: Optional[str] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    category: None = None
    confidence: None = None
    probabilities: None = None
    model: None = None
