"""Validated request and response contracts."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class EmployeeCreate(BaseModel):
    """Fields accepted when HR creates an employee."""

    full_name: str = Field(min_length=2, max_length=120, examples=["Asha Rao"])
    email: EmailStr = Field(examples=["asha.rao@example.com"])
    department: str = Field(min_length=2, max_length=80, examples=["Engineering"])
    job_title: str = Field(min_length=2, max_length=120, examples=["Platform Engineer"])
    internal_notes: str | None = Field(
        default=None,
        max_length=2000,
        examples=["Internal HR note removed by APIM."],
    )

    @field_validator("full_name", "department", "job_title")
    @classmethod
    def strip_and_reject_blank(cls, value: str) -> str:
        """Normalize surrounding whitespace while disallowing blank values."""

        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be blank")
        return normalized

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Store email addresses in a stable lowercase form."""

        return value.lower()


class EmployeeResponse(EmployeeCreate):
    """Employee representation returned by the backend.

    APIM removes ``internal_notes`` before returning the public response.
    """

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """Health endpoint response."""

    status: str
    environment: str
    version: str


class ErrorResponse(BaseModel):
    """Stable error response used for documented application errors."""

    detail: str
