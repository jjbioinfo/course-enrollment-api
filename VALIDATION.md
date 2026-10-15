# Application validation

Environment: macOS, Python 3.13.5. Dependencies: FastAPI 0.142.2,
Pydantic 2.13.5, Uvicorn 0.54.0, HTTPX 0.28.1.

## Automated tests

Run from the project folder:

```bash
python -m unittest -v test_api
```

Expected: 18 tests, no failures or errors. Observed: **18 tests passed** with
regular endpoint functions and the shared `handle_error` helper.

| Scenario | Expected and observed result |
|---|---|
| Empty catalog and known student without courses | 200 and empty lists |
| Course creation/listing | 201 with generated IDs; 200 with saved courses |
| Course field boundaries | Valid maximum lengths accepted; missing, blank, oversized, null, or extra input rejected with 422 |
| Valid enrollment | 201 with enrollment ID; course appears in student's list |
| Repeated student-course pair | 409; no extra record or consumed ID |
| Missing student, course, or enrollment | 404 with meaningful detail |
| Invalid body IDs | Nonpositive values, booleans, floats, strings, nulls, and missing fields rejected with 422 |
| Invalid JSON or missing body | 422 |
| Invalid path IDs | 422 |
| Many-to-many enrollment | Students can join multiple courses; courses can have multiple students |
| Cancellation and re-enrollment | 200 cancellation; repeat deletion 404; re-enrollment 201 with new ID |
| Cancellation identity | Deletion uses enrollment ID, preserving other students' records |
| Simultaneous duplicate requests | Exactly one 201 and one 409 |
| Unexpected failure in each of the five endpoints | Generic 500 response; internal error and traceback recorded in logs |
| Expected-error logging | Missing enrollment produces a WARNING and a 404 response |
| Unknown route or unsupported method | 404 or 405; Allow header preserved |
| Swagger and OpenAPI | Documentation HTML served; all five required method/path combinations declared |

Unexpected failures are deliberately injected with unittest.mock. This verifies
the error handling; it is not a test of a real database or infrastructure outage.

## Local server verification

A temporary Uvicorn server on localhost handled 17 ordered HTTP requests:
empty catalog, create course, list courses, enroll, list student courses,
duplicate enrollment, missing student, missing course, missing student's course
list, known student with no courses, blank title, invalid student ID, cancellation,
empty student list after cancellation, preserved catalog, repeated cancellation,
and re-enrollment.

All statuses matched. Valid and business-error bodies matched their expected
objects/lists. Both invalid-input responses returned field-error lists. The
Swagger HTML returned 200. The temporary server was stopped after verification.

## Source and workflow checks

The application uses regular functions and has no asynchronous function syntax
or custom startup/shutdown hook. Expected errors are converted to HTTPException
by a shared helper called from each endpoint's except block. FastAPI supplies
its standard validation and framework error responses.

The Git handout contains directly copyable commands. Its Bash syntax and file
references were checked; no Git workflow commands were executed.

## Validation limits

- Tests ran on Python 3.13.5, not on every supported Python version.
- Existing installed dependencies were used; a clean installation was not repeated.
- Swagger HTML and route schemas were verified; the browser interface was not
  manually exercised. API requests were verified through TestClient and real HTTP.
- The application is single-process and in-memory. Persistence, authentication,
  multiple-worker behavior, and production deployment are outside its scope.
