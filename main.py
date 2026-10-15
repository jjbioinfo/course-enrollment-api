"""Course Enrollment API using regular functions, try/except, and logging.

Run: python -m uvicorn main:app --reload
Open: http://127.0.0.1:8000/docs
"""

import logging

from fastapi import FastAPI, HTTPException, Path

from models import Cancellation, Course, CourseCreate, Enrollment, EnrollmentCreate
from store import EnrollmentStore, StoreError

# Configure readable messages in the terminal; no startup function is needed.
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Course Enrollment API",
    description="Enroll predefined students (1=Asha, 2=Ben, 3=Chen) in courses. Data is in memory.",
    version="1.0.0",
)

# One store holds the records for this running application.
store = EnrollmentStore()


def handle_error(error: Exception) -> None:
    """Log an error caught by an endpoint and raise the appropriate HTTP response.

    StoreError represents an expected business failure (404 or 409).
    Other exceptions indicate an unexpected failure and produce a generic 500.
    This helper always raises; it never returns a successful response.
    """
    if isinstance(error, StoreError):
        logger.warning("Request rejected: %s", error.message)
        # FastAPI turns HTTPException into JSON: {"detail": "the message"}.
        raise HTTPException(status_code=error.status_code, detail=error.message) from error

    # Called from an except block, exception() includes the debugging traceback.
    # Keep the internal error details in the log, not in the public response.
    logger.exception("Unexpected application error")
    raise HTTPException(status_code=500, detail="Internal server error") from error


@app.post("/courses", response_model=Course, status_code=201, tags=["Courses"])
def create_course(data: CourseCreate) -> Course:
    """Create a validated course and return its generated ID with HTTP 201."""
    try:
        course = store.create_course(data)
        logger.info("Course created: %s", course.id)
        return course
    except Exception as error:
        handle_error(error)


@app.get("/courses", response_model=list[Course], tags=["Courses"])
def list_courses() -> list[Course]:
    """Return the course catalog; an empty catalog is a valid empty list."""
    try:
        courses = store.list_courses()
        logger.info("Courses listed: %s", len(courses))
        return courses
    except Exception as error:
        handle_error(error)


@app.post("/enroll", response_model=Enrollment, status_code=201, tags=["Enrollments"],
          responses={404: {"description": "Student or course not found"},
                     409: {"description": "Student already enrolled"}})
def enroll_student(data: EnrollmentCreate) -> Enrollment:
    """Enroll a student; return 404 for missing records or 409 for a duplicate."""
    try:
        enrollment = store.enroll(data)
        logger.info("Enrollment created: %s", enrollment.id)
        return enrollment
    except Exception as error:
        # The helper preserves StoreError's 404/409 rather than changing it to 500.
        handle_error(error)


@app.get("/students/{student_id}/courses", response_model=list[Course], tags=["Students"],
         responses={404: {"description": "Student not found"}})
def get_student_courses(student_id: int = Path(..., gt=0)) -> list[Course]:
    """Return a student's courses; an unknown student produces HTTP 404."""
    # Path(..., gt=0) means the URL ID is required and must be greater than zero.
    # FastAPI validates it before calling this function, returning 422 if invalid.
    try:
        courses = store.student_courses(student_id)
        logger.info("Courses listed for student %s: %s", student_id, len(courses))
        return courses
    except Exception as error:
        handle_error(error)


@app.delete("/enroll/{enrollment_id}", response_model=Cancellation, tags=["Enrollments"],
            responses={404: {"description": "Enrollment not found"}})
def cancel_enrollment(enrollment_id: int = Path(..., gt=0)) -> Cancellation:
    """Cancel by enrollment ID, returning HTTP 200 or 404 if it does not exist."""
    try:
        store.cancel(enrollment_id)
        logger.info("Enrollment cancelled: %s", enrollment_id)
        return Cancellation(message="Enrollment cancelled", enrollment_id=enrollment_id)
    except Exception as error:
        handle_error(error)
