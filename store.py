"""Keep the assignment data in memory and implement the enrollment rules.

There is deliberately no database. One store belongs to one running server
process. Restarting the server clears courses/enrollments and resets their IDs.
"""

from threading import Lock

from models import Course, CourseCreate, Enrollment, EnrollmentCreate


class StoreError(Exception):
    """Expected business failure: carry an HTTP status and a readable message."""

    def __init__(self, status_code: int, message: str) -> None:
        """Save the response status and message for the API's error helper."""
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class EnrollmentStore:
    """Coordinate dictionaries holding students, courses, and enrollments."""

    def __init__(self) -> None:
        """Start with three demo students and empty course/enrollment records."""
        # Dictionary keys are IDs: looking up students[1] finds Asha directly.
        # Students are predefined because student creation is outside this task.
        self.students = {1: "Asha", 2: "Ben", 3: "Chen"}
        self.courses: dict[int, Course] = {}
        self.enrollments: dict[int, Enrollment] = {}
        self._next_course_id = 1
        self._next_enrollment_id = 1
        # FastAPI can run normal def endpoints in different threads. The lock
        # prevents two requests from checking/inserting the same enrollment at once.
        self._lock = Lock()

    def create_course(self, data: CourseCreate) -> Course:
        """Store validated input, assign a new ID, and return the created course."""
        with self._lock:
            # Copy each validated field explicitly so its source is easy to follow.
            course = Course(
                id=self._next_course_id,
                title=data.title,
                description=data.description,
            )
            self.courses[course.id] = course
            self._next_course_id += 1
            return course

    def list_courses(self) -> list[Course]:
        """Return a list of all courses; an empty store produces an empty list."""
        with self._lock:
            # Return a new list, not the internal dictionary itself.
            return list(self.courses.values())

    def enroll(self, data: EnrollmentCreate) -> Enrollment:
        """Create an enrollment; raise StoreError(404/409) before any failed write."""
        with self._lock:
            if data.student_id not in self.students:
                raise StoreError(404, f"Student {data.student_id} not found")
            if data.course_id not in self.courses:
                raise StoreError(404, f"Course {data.course_id} not found")

            # Duplicate means the SAME student-course pair, not either ID alone.
            # Different students may join one course; one student may join many.
            for enrollment in self.enrollments.values():
                if (enrollment.student_id == data.student_id
                        and enrollment.course_id == data.course_id):
                    raise StoreError(409, "Student is already enrolled in this course")

            # Write only after all checks pass. Failed requests consume no ID.
            enrollment = Enrollment(
                id=self._next_enrollment_id,
                student_id=data.student_id,
                course_id=data.course_id,
            )
            self.enrollments[enrollment.id] = enrollment
            self._next_enrollment_id += 1
            return enrollment

    def student_courses(self, student_id: int) -> list[Course]:
        """Return a known student's courses; missing student is 404, no courses is []."""
        with self._lock:
            if student_id not in self.students:
                raise StoreError(404, f"Student {student_id} not found")
            # Walk through the relationships and collect this student's courses.
            result = []
            for enrollment in self.enrollments.values():
                if enrollment.student_id == student_id:
                    course = self.courses[enrollment.course_id]
                    result.append(course)
            return result

    def cancel(self, enrollment_id: int) -> None:
        """Remove an enrollment; raise StoreError(404) when it does not exist."""
        with self._lock:
            if enrollment_id not in self.enrollments:
                raise StoreError(404, f"Enrollment {enrollment_id} not found")
            # Delete just the relationship, leaving the student and course intact.
            # A later re-enrollment is allowed and receives a new enrollment ID.
            del self.enrollments[enrollment_id]
