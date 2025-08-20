# FarmHub Reporting Service (FastAPI)

A read-only microservice exposing aggregated analytics from the same PostgreSQL database used by the Django core.

## Quick start

1. Create a venv (optional if you want to reuse the root venv):
   - Windows PowerShell:
     - python -m venv .venv
     - .\.venv\Scripts\Activate.ps1
2. Install deps:
   - pip install -r reporting/requirements.txt
3. Configure environment (.env at repo root):
   - DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
4. Run server:
   - uvicorn reporting.main:app --reload --port 8001

## Notes
- The service connects read-only. Use a DB user with SELECT privileges only.
- CORS and auth are intentionally omitted in the skeleton; add before going public.
