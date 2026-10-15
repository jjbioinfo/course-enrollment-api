"""Describe accepted JSON input and returned JSON output using Pydantic models.

A model is a named collection of fields and validation rules. FastAPI reads these
rules before calling an endpoint and also uses them to build Swagger UI forms.
"""

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    """Input for POST /courses; the server assigns the course ID, not the caller."""

    # Strip surrounding spaces; reject misspelled or unexpected field names.
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(min_length=1, max_length=100, examples=["Python Basics"])
    description: str = Field(default="", max_length=500, examples=["Learn Python fundamentals"])


class Course(CourseCreate):
    """Output course record, including its server-generated positive ID."""

    # Frozen records cannot accidentally be edited after the store returns them.
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", frozen=True)
    id: int = Field(gt=0)


class EnrollmentCreate(BaseModel):
    """Input for POST /enroll; both IDs must be positive JSON integers."""

    model_config = ConfigDict(extra="forbid")
    # strict=True rejects true, 1.5, and "1" instead of converting them to IDs.
    student_id: int = Field(gt=0, strict=True, examples=[1])
    course_id: int = Field(gt=0, strict=True, examples=[1])


class Enrollment(EnrollmentCreate):
    """Output record connecting one existing student with one existing course."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    id: int = Field(gt=0)


class Cancellation(BaseModel):
    """Successful DELETE response; HTTP 200 is used because a body is returned."""

    message: str
    enrollment_id: int
