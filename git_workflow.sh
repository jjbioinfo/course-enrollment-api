#!/usr/bin/env bash
# Copy and run ONE command at a time. Stop if a command fails.
# This project already uses main and the configured GitHub repository.

# 1. Open the project folder.
cd /Users/JJOHN41/Documents/my_learning/euron_super30/assignment/october/1_course_nrollment_API

# 2. Set the name and email recorded on commits in this repository.
git config user.name "jjbioinfo"

git config user.email "jibinbioinfo@gmail.com"

# 3. See which files changed.
git status

# 4. Select project changes. The private .env is excluded by .gitignore.
git add .

# 5. Check the selected files. Do not continue if .env appears as staged.
git status

# 6. Save the changes in Git.
git commit -m "Update course enrollment API with Supabase"

# 7. Upload to the existing GitHub repository.
git push origin main

# Repository: https://github.com/jjbioinfo/course-enrollment-api
