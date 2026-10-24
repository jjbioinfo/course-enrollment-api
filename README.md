# Course Enrollment API

A small FastAPI application backed by Supabase PostgreSQL. Students can enroll in courses, view their courses, and cancel an enrollment. A database constraint prevents the same student from enrolling in the same course twice.

## Features and endpoints

| Method | Path | Successful result |
|---|---|---|
| POST | `/courses` | 201, created course |
| GET | `/courses` | 200, list of courses |
| POST | `/enroll` | 201, enrollment record |
| GET | `/students/{student_id}/courses` | 200, student's courses |
| DELETE | `/enroll/{enrollment_id}` | 200, cancellation confirmation |

The API uses normal Python `def` functions, Pydantic validation, `.env` settings, Supabase queries, try/except, and logging. Data persists in the database across server restarts.

## Installation and database setup

Requires Python 3.10+ and a Supabase project. Use a dedicated project with no existing `student`, `courses`, or `enrollments` tables. The setup intentionally refuses to overwrite existing tables.

1. In your Supabase project's SQL Editor, paste and run [schema.sql](schema.sql) once. It creates the tables and three fictional students. Note the returned student IDs.
2. In the project directory, create/activate a Python environment and install the single dependency file:

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
python -m pip install -r requirements.txt
```

3. Create a local `.env` using `.env.example` as the template. The prepared local folder already has a blank `.env`; fill it rather than overwriting it. For a fresh clone, copy without overwriting:

```bash
cp -n .env.example .env
```

Set `SUPABASE_URL` to your project URL and `SUPABASE_KEY` to its **server-side service_role key**. The table setup enables row-level security without public policies, so an anonymous key is not sufficient. Never put this backend credential in browser code, GitHub, logs, or the video. No real credentials are included in the project.

`load_dotenv` loads this project's file. Exported environment values take priority; restart after editing settings. The client is created when first needed and reused. Missing configuration returns 503 while Swagger documentation remains available.

4. Start the server:

```bash
python -m uvicorn main:app --reload
```

Open [Swagger UI](http://127.0.0.1:8000/docs). Click a route, **Try it out**, fill its inputs, and **Execute**.

## Request and response examples

Create a course with POST `/courses`:

```json
{"title":"Python Basics","description":"Learn Python fundamentals"}
```

Expected 201, with an ID assigned by PostgreSQL:

```json
{"title":"Python Basics","description":"Learn Python fundamentals","id":1}
```

`title` must be nonblank and at most 100 characters. `description` is optional, defaults to an empty string, and is limited to 500 characters. Surrounding spaces are trimmed. Extra fields, including a supplied course ID, are rejected.

GET `/courses` returns an array of course objects. No courses means `[]` with 200.

Enroll with POST `/enroll`, using the actual student and course IDs:

```json
{"student_id":1,"course_id":1}
```

Expected 201:

```json
{"student_id":1,"course_id":1,"id":1}
```

Both IDs must be positive JSON integers. Missing/null values, strings such as `"1"`, booleans, fractional IDs, and extra fields are rejected with 422. The student and course must exist. Repeating the same pair returns 409. Different students may enroll in the same course, and a student may enroll in multiple courses.

GET `/students/1/courses` returns course objects, not enrollment objects. An existing student without enrollments receives `[]`; a missing student receives 404.

DELETE `/enroll/1` uses the **enrollment ID returned by POST /enroll**, not the course or student ID. Expected 200:

```json
{"message":"Enrollment cancelled","enrollment_id":1}
```

Only the enrollment is removed. The student and course remain. A second delete returns 404. The student may enroll again afterward; database-generated IDs can have gaps and should never be assumed from request counts.

## Architecture and class concepts

| File | Purpose |
|---|---|
| main.py | Five route functions, record checks, and HTTP error handling |
| models.py | Request/response models and validation rules |
| database.py | `.env` loading and Supabase client creation |
| schema.sql | Tables, constraints, security settings, and sample students |
| test_api.py | Offline route tests using the real Supabase SDK with mocked HTTP |
| DEMO_GUIDE.md | Ordered Swagger/video walkthrough |
| git_workflow.sh | Commands to copy one at a time for the existing repository |

An **API** lets a client program send requests to a server. An **endpoint** is an HTTP method and path. **JSON** is the structured request/response format. A **path parameter** is a value in the URL, such as the student ID. FastAPI maps each route decorator to a function; Uvicorn runs the HTTP server.

A **Pydantic model** defines data fields and validation rules. `Field` defines limits. `response_model` describes the returned JSON. `model_dump()` converts validated data into a dictionary for Supabase; it is the current Pydantic equivalent of `.dict()` in the class example.

Supabase provides a PostgreSQL database and an API for accessing it. The code follows the class pattern `client.table(...).select/insert/delete(...).eq(...).execute()`. `eq` filters by equality; `execute` sends the request; `response.data` contains the returned records. `Depends(get_client)` asks FastAPI to supply the shared database client. `lru_cache(maxsize=1)` retains that client so it is not constructed for every request.

A **primary key** uniquely identifies a row. A **foreign key** connects an enrollment to a real student/course and prevents invalid references. The **unique constraint** on `(student_id, course_id)` prevents duplicate pairs, including simultaneous inserts. An application-only check could miss a concurrent request, so PostgreSQL enforces this rule. `23505` is the database error code for a unique violation; it becomes HTTP 409. The class's login example also catches database uniqueness errors.

The application checks student/course existence for descriptive 404 responses before inserting. A foreign-key failure after those checks also becomes 404, covering deletion by another database client between requests. The course-list query uses the foreign-key relationship to fetch related course objects in one query.

A **try/except** block catches failures. `HTTPException` creates a deliberate JSON error response. The error helper preserves these responses and maps database failures to useful status codes. The logger records operation outcomes and error types/codes without logging secrets. It does not log raw database error messages.

This project uses the supplied `supabaseapi.py` CRUD style and `login.py`'s environment/error-handling concepts. Login/JWT is not required for this enrollment assignment and is not added. CORS and rate limiting are also unnecessary for the local Swagger demonstration.

## Errors

| Code | Meaning |
|---|---|
| 404 | Student, course, or enrollment does not exist |
| 409 | Student is already enrolled in the course |
| 422 | Invalid request fields or nonpositive/noninteger path ID |
| 503 | Missing configuration, missing database tables, connection failure, or database access failure |
| 500 | Unexpected application failure |

If a 503 mentions missing tables, run the SQL in the correct project. If a database request fails, confirm the server-side key, table names, and project URL. If tables already exist, inspect their definitions before deciding on a migration; do not delete class data to make setup succeed.

## Testing and scope

```bash
python -m unittest -v test_api
```

The 13 offline tests cover all endpoints, validation, missing records, duplicate-error handling, and failure responses. They use the actual Supabase query builder with a mocked HTTP transport: no real credentials or database are needed. **They do not prove the hosted schema, permissions, or concurrency behavior have been deployed.** See [VALIDATION.md](VALIDATION.md).

The application is a local assignment demonstration without user authentication. Use fictional records; do not expose the backend publicly with unrestricted write access. Supabase's configured API row limit applies to list responses; pagination is outside this small assignment. Student creation is done through the supplied SQL setup, not an extra endpoint.

## Submission

Use [DEMO_GUIDE.md](DEMO_GUIDE.md) to demonstrate every API and explain the validation/database logic. Follow [git_workflow.sh](git_workflow.sh) to commit and publish from the existing repository. Submit the actual GitHub repository URL and YouTube video URL.

## References

- [Supabase Python inserts](https://supabase.com/docs/reference/python/insert)
- [Supabase Python queries and relationships](https://supabase.com/docs/reference/python/select)
- [PostgreSQL unique and foreign-key constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
