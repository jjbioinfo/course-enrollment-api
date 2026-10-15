"""Exercise real FastAPI routing/validation in memory, without a network server.

Run: python -m unittest -v test_api
Each test gets a fresh store so tests cannot affect your running demo's records.
"""

import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from fastapi.testclient import TestClient

import main
from store import EnrollmentStore


class EnrollmentAPITests(unittest.TestCase):
    """Verify response codes, response bodies, and state after failures."""

    def setUp(self):
        """Replace only this test process's store and start a temporary TestClient."""
        self.store_patch = patch.object(main, "store", EnrollmentStore())
        self.store_patch.start()
        self.addCleanup(self.store_patch.stop)
        self.client = TestClient(main.app)
        self.addCleanup(self.client.close)

    def create_course(self, title="Python Basics"):
        """Create a valid course fixture and assert the setup request succeeds."""
        response = self.client.post("/courses", json={"title": title})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_empty_catalog_and_known_student(self):
        """A known student with no courses is not a missing student."""
        self.assertEqual(self.client.get("/courses").json(), [])
        response = self.client.get("/students/1/courses")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_create_and_list_courses(self):
        """Creation trims spaces, supplies defaults, and assigns unique IDs."""
        first = self.create_course("  Python Basics  ")
        self.assertEqual(first, {"id": 1, "title": "Python Basics", "description": ""})
        second = self.create_course("FastAPI")
        self.assertEqual(second["id"], 2)
        response = self.client.get("/courses")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [first, second])

    def test_course_input_boundaries(self):
        """Missing, blank, oversized, null, and unexpected fields produce 422."""
        invalid = [{}, {"title": ""}, {"title": "   "}, {"title": None},
                   {"title": 17}, {"title": "x" * 101},
                   {"title": "Python", "description": "x" * 501},
                   {"title": "Python", "description": None},
                   {"title": "Python", "id": 10}]
        for body in invalid:
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/courses", json=body).status_code, 422)
        self.assertEqual(self.client.get("/courses").json(), [])
        response = self.client.post("/courses", json={"title": "x" * 100, "description": "y" * 500})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], 1)

    def test_enroll_and_list_student_courses(self):
        course = self.create_course()
        response = self.client.post("/enroll", json={"student_id": 1, "course_id": 1})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"id": 1, "student_id": 1, "course_id": 1})
        self.assertEqual(self.client.get("/students/1/courses").json(), [course])

    def test_duplicate_rejected_without_extra_record(self):
        self.create_course()
        body = {"student_id": 1, "course_id": 1}
        self.client.post("/enroll", json=body)
        response = self.client.post("/enroll", json=body)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {"detail": "Student is already enrolled in this course"})
        self.assertEqual(len(self.client.get("/students/1/courses").json()), 1)
        next_response = self.client.post("/enroll", json={"student_id": 2, "course_id": 1})
        self.assertEqual(next_response.json()["id"], 2)  # Failed request used no ID.

    def test_missing_student_and_course(self):
        self.create_course()
        for body, message in [({"student_id": 99, "course_id": 1}, "Student 99 not found"),
                              ({"student_id": 1, "course_id": 99}, "Course 99 not found")]:
            with self.subTest(body=body):
                response = self.client.post("/enroll", json=body)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json(), {"detail": message})
        self.assertEqual(main.store.enrollments, {})
        self.assertEqual(self.client.get("/students/99/courses").status_code, 404)

    def test_enrollment_input_validation(self):
        self.create_course()
        for field in ("student_id", "course_id"):
            for invalid in (0, -1, True, 1.5, "1", None):
                body = {"student_id": 1, "course_id": 1, field: invalid}
                with self.subTest(body=body):
                    self.assertEqual(self.client.post("/enroll", json=body).status_code, 422)
        for body in ({}, {"student_id": 1}, {"course_id": 1},
                     {"student_id": 1, "course_id": 1, "extra": "bad"}):
            self.assertEqual(self.client.post("/enroll", json=body).status_code, 422)
        self.assertEqual(main.store.enrollments, {})

    def test_invalid_json_and_missing_body(self):
        for path in ("/courses", "/enroll"):
            response = self.client.post(path, content="{broken", headers={"Content-Type": "application/json"})
            self.assertEqual(response.status_code, 422)
            self.assertEqual(self.client.post(path).status_code, 422)

    def test_path_validation(self):
        for value in ("0", "-1", "abc", "1.5"):
            with self.subTest(value=value):
                self.assertEqual(self.client.get(f"/students/{value}/courses").status_code, 422)
                self.assertEqual(self.client.delete(f"/enroll/{value}").status_code, 422)

    def test_many_to_many_relationship(self):
        """Duplicate prevention still permits different student-course pairs."""
        self.create_course("Python")
        self.create_course("FastAPI")
        for student, course in ((1, 1), (1, 2), (2, 1)):
            self.assertEqual(self.client.post("/enroll", json={"student_id": student, "course_id": course}).status_code, 201)
        self.assertEqual(len(self.client.get("/students/1/courses").json()), 2)
        self.assertEqual(len(self.client.get("/students/2/courses").json()), 1)
        self.assertEqual(self.client.get("/students/3/courses").json(), [])

    def test_cancel_and_reenroll(self):
        self.create_course()
        body = {"student_id": 1, "course_id": 1}
        self.client.post("/enroll", json=body)
        response = self.client.delete("/enroll/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Enrollment cancelled", "enrollment_id": 1})
        self.assertEqual(self.client.get("/students/1/courses").json(), [])
        self.assertEqual(len(self.client.get("/courses").json()), 1)
        self.assertEqual(self.client.delete("/enroll/1").status_code, 404)
        response = self.client.post("/enroll", json=body)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], 2)

    def test_missing_enrollment(self):
        response = self.client.delete("/enroll/999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Enrollment 999 not found"})

    def test_cancel_uses_enrollment_id_not_course_id(self):
        self.create_course()
        for student in (1, 2):
            self.client.post("/enroll", json={"student_id": student, "course_id": 1})
        self.assertEqual(self.client.delete("/enroll/2").status_code, 200)
        self.assertEqual(len(self.client.get("/students/1/courses").json()), 1)
        self.assertEqual(self.client.get("/students/2/courses").json(), [])

    def test_concurrent_duplicate_requests(self):
        """Two simultaneous requests must create only one student-course pair."""
        self.create_course()
        def send_request(_):
            return self.client.post("/enroll", json={"student_id": 1, "course_id": 1}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(send_request, range(2)))
        self.assertEqual(sorted(statuses), [201, 409])
        self.assertEqual(len(main.store.enrollments), 1)

    def test_unexpected_error_is_logged_and_sanitized(self):
        """Each endpoint must log an unexpected failure and return a safe 500."""
        cases = [
            ("create_course", "POST", "/courses", {"title": "Python"}),
            ("list_courses", "GET", "/courses", None),
            ("enroll", "POST", "/enroll", {"student_id": 1, "course_id": 1}),
            ("student_courses", "GET", "/students/1/courses", None),
            ("cancel", "DELETE", "/enroll/1", None),
        ]
        for method, verb, path, body in cases:
            with self.subTest(endpoint=path, verb=verb):
                with patch.object(main.store, method, side_effect=RuntimeError("private debugging detail")):
                    with self.assertLogs("main", level="ERROR") as captured:
                        response = self.client.request(verb, path, json=body)
                self.assertEqual(response.status_code, 500)
                self.assertEqual(response.json(), {"detail": "Internal server error"})
                self.assertIn("private debugging detail", "\n".join(captured.output))

    def test_expected_errors_are_logged(self):
        with self.assertLogs("main", level="WARNING") as captured:
            response = self.client.delete("/enroll/999")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Enrollment 999 not found", "\n".join(captured.output))

    def test_unknown_route_and_wrong_method(self):
        self.assertEqual(self.client.get("/missing-route").status_code, 404)
        response = self.client.post("/students/1/courses")
        self.assertEqual(response.status_code, 405)
        self.assertIn("GET", response.headers["allow"])

    def test_swagger_and_openapi(self):
        """Check that documentation HTML and all five route definitions exist."""
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("swagger-ui", response.text)
        paths = self.client.get("/openapi.json").json()["paths"]
        expected = {"/courses": {"get", "post"}, "/enroll": {"post"},
                    "/students/{student_id}/courses": {"get"},
                    "/enroll/{enrollment_id}": {"delete"}}
        self.assertEqual({path: set(methods) for path, methods in paths.items()}, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
