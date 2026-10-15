# Course Enrollment API

A FastAPI application that allows students to enroll in courses. It provides
endpoints for creating and listing courses, enrolling students, viewing a
student's courses, and cancelling enrollments. Duplicate enrollments are
rejected, and missing records return meaningful HTTP errors.

## Features

- Create courses with a title and optional description.
- List all available courses.
- Enroll an existing student in an existing course.
- Prevent duplicate enrollment in the same course.
- List the courses associated with a student.
- Cancel an enrollment without deleting the student or course.
- Validate request data and log requests and errors.
- Explore and test the API through Swagger UI.

## Technology

| Package | Purpose |
|---|---|
| FastAPI | Defines HTTP endpoints and generates interactive API documentation |
| Pydantic | Validates request data and defines response structures |
| Uvicorn | Runs the application as a web server |
| HTTPX | Supports HTTP requests made by the automated test client |

Python 3.10 or newer is required. All package versions are listed in
`requirements.txt`. The application uses Python dictionaries for in-memory storage.

## Installation and execution

Open a terminal in the project directory containing `main.py`.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open [Swagger UI](http://127.0.0.1:8000/docs) in a browser. Select an endpoint,
click **Try it out**, enter the required input, and click **Execute**. The page
shows the response status and JSON body.

`main:app` identifies the `app` object in `main.py`. The `--reload` option restarts
the server when source files change. Stop the server with `Ctrl+C`.

## Project structure

| File | Responsibility |
|---|---|
| `main.py` | API routes, operation logging, and HTTP error handling |
| `models.py` | Request and response models with validation rules |
| `store.py` | In-memory records and enrollment business rules |
| `test_api.py` | Automated API tests |
| `requirements.txt` | Dependencies for running the application and tests |
| `git_workflow.sh` | Step-by-step Git command reference |
| `.gitignore` | Excludes virtual environments, caches, and local generated files |

## API concepts

An **endpoint** combines an HTTP method and a URL path, such as `POST /courses`.
A **request body** contains data sent to the API, usually as JSON. A **path
parameter** is a value within the URL, such as the student ID in
`/students/1/courses`. A **status code** indicates whether a request succeeded or
why it failed.

JSON represents structured data using objects (`{}`), arrays (`[]`), strings,
numbers, booleans, and null. FastAPI validates incoming data using the Pydantic
models before calling an endpoint function.

## Data and enrollment rules

The application starts with three predefined students:

| Student ID | Name |
|---|---|
| 1 | Asha |
| 2 | Ben |
| 3 | Chen |

Courses and enrollments are initially empty. Course IDs and enrollment IDs are
assigned automatically, starting at 1. These identify different record types:
**cancellation requires the enrollment ID returned by `POST /enroll`.**

- A student may enroll in multiple courses.
- A course may have multiple students.
- The same student-course pair may exist only once at a time.
- Different courses may share a title; their IDs distinguish them.
- Cancellation removes the enrollment relationship only.
- A student can enroll again after cancellation and receives a new enrollment ID.
- A known student with no enrollments receives an empty list; an unknown student
  receives a `404` error.

## Endpoints

| Method | Path | Operation | Success |
|---|---|---|---|
| POST | `/courses` | Create a course | 201 Created |
| GET | `/courses` | List all courses | 200 OK |
| POST | `/enroll` | Enroll a student | 201 Created |
| GET | `/students/{student_id}/courses` | List a student's courses | 200 OK |
| DELETE | `/enroll/{enrollment_id}` | Cancel an enrollment | 200 OK |

The examples below form a sequence starting with an empty course catalog.

### 1. Create a course

**POST `/courses`**

Request body:

```json
{
  "title": "Python Basics",
  "description": "Learn Python fundamentals"
}
```

Response — **201 Created**:

```json
{
  "title": "Python Basics",
  "description": "Learn Python fundamentals",
  "id": 1
}
```

### 2. List courses

**GET `/courses`** — no request body.

Response — **200 OK**:

```json
[
  {
    "title": "Python Basics",
    "description": "Learn Python fundamentals",
    "id": 1
  }
]
```

An empty catalog returns `[]`.

### 3. Enroll a student

**POST `/enroll`**

Request body:

```json
{
  "student_id": 1,
  "course_id": 1
}
```

Response — **201 Created**:

```json
{
  "student_id": 1,
  "course_id": 1,
  "id": 1
}
```

Here, `id` is the new enrollment ID. Repeating the same request returns **409
Conflict**:

```json
{
  "detail": "Student is already enrolled in this course"
}
```

### 4. List a student's courses

**GET `/students/1/courses`** — no request body.

Response — **200 OK**:

```json
[
  {
    "title": "Python Basics",
    "description": "Learn Python fundamentals",
    "id": 1
  }
]
```

### 5. Cancel an enrollment

**DELETE `/enroll/1`** — no request body.

Response — **200 OK**:

```json
{
  "message": "Enrollment cancelled",
  "enrollment_id": 1
}
```

After cancellation, `GET /students/1/courses` returns `[]`, while `GET /courses`
still contains the course. Repeating the cancellation returns **404 Not Found**:

```json
{
  "detail": "Enrollment 1 not found"
}
```

## Validation and error responses

| Condition | Status | Response detail |
|---|---|---|
| Student does not exist | 404 | `Student 99 not found`, for example |
| Course does not exist | 404 | `Course 99 not found`, for example |
| Enrollment does not exist | 404 | `Enrollment 99 not found`, for example |
| Duplicate student-course pair | 409 | `Student is already enrolled in this course` |
| Invalid request body or path ID | 422 | A list identifying the invalid fields |
| Unsupported HTTP method | 405 | `Method Not Allowed` |
| Unexpected application failure | 500 | `Internal server error` |

Course titles must contain 1–100 characters after surrounding whitespace is
removed. Descriptions are optional, default to an empty string, and allow up to
500 characters. Unknown body fields are rejected.

Enrollment body IDs must be positive JSON integers. Values such as `0`, `-1`,
`true`, `"1"`, `1.5`, and `null` are rejected. Path IDs are parsed from URL text
and must also be positive integers.

For enrollment requests, the student is checked before the course. If both are
missing, the response reports the missing student first. Rejected requests do
not create records or consume IDs.

## Application design

```text
Client request
    -> FastAPI input validation
    -> Endpoint function in main.py
    -> EnrollmentStore business rules
    -> Response model or HTTP error
    -> JSON response
```

`models.py` defines the accepted fields and validation rules. `main.py` maps each
HTTP method and path to a small function. These functions call `EnrollmentStore`
methods in `store.py`, keeping the business rules separate from HTTP handling.

Enrollment follows four steps: check the student, check the course, check for an
existing pair, then save the new relationship. A lock protects these checks and
the write so simultaneous requests cannot create duplicate enrollments within
the same server process.

Each endpoint uses a regular `def` function with a `try/except` block. The `try`
block calls the store method, logs the result, and returns it. If the operation
fails, the `except` block calls the shared `handle_error` function.

`handle_error` logs expected business failures and raises `HTTPException` with
`404` or `409`. For unexpected failures, it logs the traceback and raises a
`500` error with a generic message. FastAPI converts `HTTPException` into a JSON
response. This keeps the same error rules in one small function.

Input validation occurs before an endpoint runs. FastAPI handles invalid input
with `422`, unknown routes with `404`, and unsupported methods with `405`.
`Path(..., gt=0)` declares a required positive integer in the URL.

Logs appear in the server terminal. Application `INFO` messages record successful
operations, `WARNING` messages record business-rule rejections, and `ERROR`
messages capture unexpected failures. Uvicorn's access log also records HTTP
requests and status codes, including validation failures.

## Testing

With the virtual environment activated, run:

```bash
python -m unittest -v test_api
```

The test suite contains **18 tests** covering successful requests, invalid
inputs, missing records, duplicate prevention, cancellation, re-enrollment,
concurrent enrollment requests, logging, unexpected failures, and API documentation.
Each test uses a fresh store and does not modify a separately running server.

Successful execution ends with `Ran 18 tests` and `OK`.

## Limitations

- Data exists only in memory and resets when the server restarts or reloads.
- The application supports one server process; multiple workers would have
  separate data stores.
- Students are predefined; there is no student-registration endpoint.
- Authentication, persistent storage, and production deployment are outside
  the scope of this application.

## References

- [FastAPI request bodies](https://fastapi.tiangolo.com/tutorial/body/)
- [FastAPI error handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python logging](https://docs.python.org/3/howto/logging.html)
