# Course Enrollment API: recording guide

## Prepare before recording

Use a dedicated Supabase project. Run schema.sql once, note the student IDs, and fill the private .env with the project URL and server-side key. Do not show the key in the recording. These database setup steps have not been executed automatically.

Run these commands one at a time:

```bash
cd /Users/JJOHN41/Documents/my_learning/euron_super30/assignment/october/1_course_nrollment_API
```

```bash
source /Users/JJOHN41/Documents/my_learning/euron_super30/.venv/bin/activate
```

```bash
python -m unittest -v test_api
```

Expect 13 tests and OK. Explain these are offline tests of the routes and database query construction, not live database tests.

```bash
python -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs. If port 8000 is busy, stop the other assignment server first.

## Explain the problem and architecture

“This API lets existing students enroll in courses. FastAPI handles requests, Pydantic validates inputs, and Supabase stores the records. Each enrollment links a student and a course. A unique constraint prevents the same pair from appearing twice.”

Show models.py, database.py, main.py, and schema.sql. Show .env.example to explain configuration, not the private .env. Explain regular def functions, route decorators, Depends, Supabase queries, try/except, and logging using the README explanations.

## Swagger demonstration in order

Use actual returned IDs. Below, S means a seeded student ID, C a course ID, and E an enrollment ID. These letters are reminders, not literal API inputs.

1. GET /courses: 200, [] on a fresh database.
2. POST /courses with `{"title":"Python Basics","description":"Learn Python fundamentals"}`: 201. Record C.
3. GET /courses: 200, contains that course.
4. POST /enroll with `{"student_id":1,"course_id":1}`, replacing IDs with S and C: 201. Record E.
5. Repeat the exact enrollment: 409. Explain the unique pair constraint.
6. GET /students/S/courses: 200, contains the course.
7. POST /enroll using a confirmed nonexistent student ID: 404.
8. POST /enroll using S and a confirmed nonexistent course ID: 404.
9. POST /enroll with student_id 0: 422. Try a blank course title with POST /courses: 422.
10. GET /students/S/courses again: original course still present.
11. DELETE /enroll/E: 200 cancellation. Explain why E is not necessarily equal to C.
12. GET /students/S/courses: 200, [] if it was the only enrollment.
13. Repeat DELETE /enroll/E: 404.
14. GET /courses: course still exists; cancellation did not delete it.
15. Enroll S in C again: 201 with a new enrollment ID. PostgreSQL sequences may have gaps after failed inserts.
16. GET /students/{missing_id}/courses: 404; contrast with the existing student with no courses.

In Postman use the same URLs and raw JSON bodies. No authentication header is required for these local routes.

## GitHub and submission

Stop the server with Ctrl+C. Copy commands from git_workflow.sh one at a time. This folder already has Git history and a remote; the workflow continues that repository rather than initializing it again. Show git status, git add, git commit, git push, and the README on GitHub. Upload the recorded video and submit the actual repository and YouTube links.
