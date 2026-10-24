# Validation record — 23 October 2026

Command: `python -m unittest -v test_api`

Observed: **13 tests passed** using the existing course Python environment and the versions in requirements.txt.

The tests run FastAPI routes through TestClient and use the real Supabase SDK with HTTPX MockTransport. Responses from Supabase are simulated; the request paths, methods, filters, and JSON bodies are inspected.

Validated cases:

- Course creation: trimmed title, server-returned ID, 201, correct insert JSON.
- Empty/populated course lists: 200 and ID ordering.
- Enrollment: checks both referenced records before insertion, returns 201.
- Missing student/course: descriptive 404; no insert request sent.
- Database duplicate error 23505: 409.
- Foreign-key error 23503 after existence checks: 404.
- Student courses: relationship query and student filter verified; known empty student gives [], unknown student gives 404.
- Cancellation: DELETE targets enrollment ID; success 200, absent/repeated deletion 404.
- Invalid body/path: blanks, oversized strings, missing/null fields, extra fields, nonpositive/fractional/string/boolean body IDs return 422 without database queries.
- Valid boundaries: title 100 and description 500 accepted; description defaults to empty.
- Missing schema, access errors, network failures: 503 without exposing raw error messages.
- Unexpected exception: generic 500.
- Missing configuration: 503; documentation and five route definitions remain available.
- Missing/malformed JSON: 422.

Not executed: schema.sql against PostgreSQL, live Supabase requests, actual database duplicate/concurrency enforcement, hosted permissions/RLS, fresh dependency installation, manual Swagger/Postman demonstration, Git changes/commits/push, or video upload. Real credentials are not configured. The SQL constraints use documented PostgreSQL syntax, but their deployment must be verified in the dedicated Supabase project.

Earlier in-memory application test results do not validate this replacement. No claims of live database readiness are made.
