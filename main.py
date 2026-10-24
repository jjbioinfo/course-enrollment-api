"""Course enrollment using the class's regular def and Supabase query pattern."""

import logging
import httpx
from fastapi import Depends, FastAPI, HTTPException, Path
from postgrest.exceptions import APIError
from supabase import Client
from database import get_client
from models import Cancellation, Course, CourseCreate, Enrollment, EnrollmentCreate

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)
app = FastAPI(
    title="Course Enrollment API",
    version="2.0.0",
    description="Enroll students in courses stored in Supabase.",
)


def handle_error(error: Exception) -> None:
    """Keep deliberate HTTP errors; translate database errors into useful responses."""
    if isinstance(error, HTTPException):
        logger.warning("Request rejected: %s", error.detail)
        raise error
    if isinstance(error, APIError):
        # A database UNIQUE constraint is the final duplicate guard, even in a race.
        if error.code == "23505":
            raise HTTPException(
                409, "Student is already enrolled in this course"
            ) from error
        if error.code == "23503":
            raise HTTPException(404, "Student or course no longer exists") from error
        if error.code in ("PGRST205", "42P01"):
            raise HTTPException(
                503, "Database tables are missing; run schema.sql"
            ) from error
        logger.error("Database operation failed (code=%s)", error.code)
        raise HTTPException(
            503, "Database request failed; check server configuration"
        ) from error
    if isinstance(error, httpx.RequestError):
        logger.error("Database connection failed")
        raise HTTPException(503, "Database is unavailable") from error
    logger.error("Unexpected application failure (%s)", type(error).__name__)
    raise HTTPException(500, "Internal server error") from error


def require_record(client: Client, table: str, record_id: int, label: str) -> None:
    """Shared existence check; table names come from code, never from user input."""
    response = client.table(table).select("id").eq("id", record_id).execute()
    if not response.data:
        raise HTTPException(404, f"{label} {record_id} not found")


@app.post("/courses", response_model=Course, status_code=201)
def create_course(data: CourseCreate, client: Client = Depends(get_client)):
    """Validate the body; let the database generate the course ID."""
    try:
        # model_dump() is the current Pydantic equivalent of the class's .dict().
        response = client.table("courses").insert(data.model_dump()).execute()
        logger.info("Course created")
        return response.data[0]
    except Exception as error:
        handle_error(error)


@app.get("/courses", response_model=list[Course])
def list_courses(client: Client = Depends(get_client)):
    """List courses in ID order, or return an empty JSON array."""
    try:
        response = client.table("courses").select("*").order("id").execute()
        return response.data
    except Exception as error:
        handle_error(error)


@app.post("/enroll", response_model=Enrollment, status_code=201)
def enroll(data: EnrollmentCreate, client: Client = Depends(get_client)):
    """Both records must exist; the unique student/course pair prevents duplicates."""
    try:
        require_record(client, "student", data.student_id, "Student")
        require_record(client, "courses", data.course_id, "Course")
        response = client.table("enrollments").insert(data.model_dump()).execute()
        logger.info("Enrollment created")
        return response.data[0]
    except Exception as error:
        handle_error(error)


@app.get("/students/{student_id}/courses", response_model=list[Course])
def student_courses(
    student_id: int = Path(..., gt=0), client: Client = Depends(get_client)
):
    """Check the student, then use the foreign-key relationship to fetch their courses."""
    try:
        require_record(client, "student", student_id, "Student")
        response = (
            client.table("enrollments")
            .select("courses(id,title,description)")
            .eq("student_id", student_id)
            .order("id")
            .execute()
        )
        # Supabase returns each related course inside a 'courses' object.
        return [row["courses"] for row in response.data]
    except Exception as error:
        handle_error(error)


@app.delete("/enroll/{enrollment_id}", response_model=Cancellation)
def cancel_enrollment(
    enrollment_id: int = Path(..., gt=0), client: Client = Depends(get_client)
):
    """Delete only the enrollment, not its student or course."""
    try:
        response = (
            client.table("enrollments").delete().eq("id", enrollment_id).execute()
        )
        if not response.data:
            raise HTTPException(404, f"Enrollment {enrollment_id} not found")
        logger.info("Enrollment cancelled: %s", enrollment_id)
        return Cancellation(message="Enrollment cancelled", enrollment_id=enrollment_id)
    except Exception as error:
        handle_error(error)
