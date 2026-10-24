-- Run ONCE in a fresh/dedicated Supabase project's SQL Editor.
-- No DROP statements: existing tables cause an error, not data deletion.
BEGIN;
CREATE TABLE public.student (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL CHECK (length(trim(name)) BETWEEN 1 AND 100),
    email text NOT NULL UNIQUE
);
CREATE TABLE public.courses (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title text NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 100),
    description text NOT NULL DEFAULT '' CHECK (length(description) <= 500)
);
CREATE TABLE public.enrollments (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id bigint NOT NULL REFERENCES public.student(id),
    course_id bigint NOT NULL REFERENCES public.courses(id),
    CONSTRAINT one_enrollment_per_course UNIQUE (student_id, course_id)
);
-- The backend uses a server-side service_role key. Public database clients have no policies.
ALTER TABLE public.student ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.enrollments ENABLE ROW LEVEL SECURITY;
GRANT ALL ON public.student, public.courses, public.enrollments TO service_role;
GRANT USAGE, SELECT ON SEQUENCE public.student_id_seq, public.courses_id_seq,
    public.enrollments_id_seq TO service_role;
-- Students are seeded because student creation is outside the five required APIs.
INSERT INTO public.student (name, email) VALUES
    ('Asha', 'asha@example.com'), ('Ben', 'ben@example.com'), ('Chen', 'chen@example.com');
COMMIT;
-- Copy these actual IDs into Swagger. Fresh tables assign 1, 2, 3.
SELECT id, name, email FROM public.student ORDER BY id;
