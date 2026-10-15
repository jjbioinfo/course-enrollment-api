#!/usr/bin/env bash
# LIVE DEMO: copy and paste ONE command at a time into your terminal.
# Commands below are active shell commands: no leading # needs to be removed.
# Lines beginning with # are explanations; you do not need to copy them.
# Do not run/source this whole file: stop at the browser step and inspect results.
# Stop if any command fails. Keep the same terminal open throughout.
# GitHub: jjbioinfo | Email: jibinbioinfo@gmail.com
# Repository: course-enrollment-api | Branch: feature/enrollment-api

# ============================================================================
# 1. ENTER THE PROJECT FOLDER AND CHECK THE ENVIRONMENT
# ============================================================================

cd /Users/JJOHN41/Documents/my_learning/euron_super30/assignment/october/oct6

pwd

# Confirm tools are available.
git --version

source /Users/JJOHN41/Documents/my_learning/euron_super30/.venv/bin/activate

python --version

# Expected: READY. If you see STOP, do not repeat initialization or delete history.
if [ -e .git ]; then printf '%s\n' 'STOP: local Git metadata already exists'; else printf '%s\n' 'READY: no local Git metadata'; fi

# Continue ONLY if the preceding check printed READY.
# If it printed STOP, do not repeat initialization; inspect your existing work.

# ============================================================================
# 2. INITIALIZE GIT AND SET YOUR IDENTITY
# ============================================================================

# Create Git metadata in THIS folder, even if a parent folder has its own Git repo.
git init --initial-branch=main

# Set your existing commit identity for this repository only.
git config user.name "jjbioinfo"

git config user.email "jibinbioinfo@gmail.com"

# Expected: the exact oct6 folder above. STOP if it shows a parent directory.
git rev-parse --show-toplevel

# Expected: No commits yet; prepared files appear as untracked (??).
git status --short --branch

# ============================================================================
# 3. COMMIT INPUT MODELS AND DEPENDENCIES
# ============================================================================

# Stage only this logical group, not everything at once.
git add .gitignore requirements.txt models.py

git diff --cached --stat

git commit -m "Define course and enrollment schemas with validation"

# ============================================================================
# 4. CREATE THE FEATURE BRANCH, TEST, COMMIT, AND MERGE
# ============================================================================

# Create a branch and switch to it.
git switch -c feature/enrollment-api

# Verify the complete API using the prepared test file before committing.
python -m unittest -v test_api

# Continue only if all 18 tests pass.
git add store.py main.py test_api.py

git diff --cached --check

git diff --cached --stat

git commit -m "Implement five enrollment endpoints with logging and tests"

# Combine this tested feature with main. --no-ff records an explicit merge.
git switch main

git merge --no-ff feature/enrollment-api -m "Merge tested enrollment API"

git log --oneline --graph --all --decorate

# ============================================================================
# 5. COMMIT README AND DEMONSTRATION GUIDES
# ============================================================================

git add README.md git_workflow.sh VALIDATION.md

git diff --cached --check

git commit -m "Document setup, API behavior, and live demonstration steps"

git status --short --branch

# ============================================================================
# 6. PAUSE TERMINAL COMMANDS: CREATE THE REPOSITORY IN YOUR BROWSER
# ============================================================================
# Open https://github.com/new and sign in as jjbioinfo.
# Owner: jjbioinfo
# Repository name: course-enrollment-api
# Visibility: Public
# Leave automatic README, .gitignore, and license creation unselected.
# Click Create repository. If the name already exists, inspect it before proceeding.
# Confirm its URL is https://github.com/jjbioinfo/course-enrollment-api.
# After completing that browser step, return to this same terminal for Step 7.

# ============================================================================
# 7. CONNECT YOUR GITHUB REPOSITORY AND PUSH
# ============================================================================

# Record the destination first; this does not upload anything yet.
git remote add origin https://github.com/jjbioinfo/course-enrollment-api.git

git remote -v

# Upload main and retain the feature branch as history evidence.
git push -u origin main

git push origin feature/enrollment-api

# ============================================================================
# 8. VERIFY THE UPLOAD
# ============================================================================

# See local commit history and confirm the branch tracks origin/main.
git log --oneline --graph --all --decorate

git status --short --branch

# Read the published main commit ID; compare it with the local ID below.
git ls-remote origin refs/heads/main

git rev-parse HEAD

# Done: show the repository in your browser and submit its URL with your video URL.
# API examples and explanations: README.md.
