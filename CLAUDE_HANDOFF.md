# Handoff

## Bug found

`POST /api/career-profiles/analyze` loaded `get_latest_user_resume(user_id)` whenever the current request had no uploaded file. A portfolio-only request could therefore merge a previously stored resume with the new portfolio.

## Files changed

- `backend/app/routes/career_profiles.py`: removed the historical-resume fallback; current multipart inputs are now the sole sources for this endpoint.
- `backend/test_ai_pipeline.py`: added regression coverage for resume analysis followed by portfolio-only analysis for the same user.
- `frontend/src/lib/profile-store.ts`: added `clearProfile` and fixed profile subscribers to clear their in-memory state when storage is empty.
- `frontend/src/routes/index.tsx`: clears prior analysis before submitting, sends only present current fields, and separates Resume and Portfolio into distinct optional input cards with dynamic validation, status, and button labels.
- `frontend/src/routes/analysis.tsx`: adds source clarity in the header plus per-skill and per-project source badges.

## Tests performed

- `python -m compileall -q app` — passed.
- `npm.cmd run build` in `frontend` — passed.
- `python -m unittest test_ai_pipeline.py` could not run because the active Python environment is missing the project dependency `httpx`.

## Remaining steps

Install backend dependencies from `backend/requirements.txt`, start the backend with MongoDB/Gemini configuration, then run `python -m unittest test_ai_pipeline.py`. Manually exercise: resume-only, portfolio-only after resume, and resume-plus-portfolio.
