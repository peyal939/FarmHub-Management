# FarmHub — Management Platform

FarmHub is a modular farm management platform built with Django REST Framework (core API) and FastAPI (read-only reporting). It uses PostgreSQL as the only database and implements role-based access control for SuperAdmin, Agent, and Farmer.

## Contents
- Project Overview
- Tech Stack and Roles
- Data Model
- Local Setup (Windows/Powershell)
- Running the Services
- Environment Variables
- API Endpoints (examples)
- Seed Data
- Postman Collection
- Troubleshooting

---

## Project Overview

Core features
- Farm management (assign Agent to Farm)
- Farmer onboarding (FarmerProfile per User)
- Cow management per Farm and Farmer
- Activities (vaccination, birth, health, other)
- Milk production tracking and aggregations

Services
- core/ — Django + DRF CRUD API with RBAC
- reporting/ — FastAPI read-only service (aggregations)

Strict rule: PostgreSQL only (DB name: `farmhub`).

---

## Tech Stack and Roles

- Backend: Django 5 + DRF
- Reporting: FastAPI + SQLAlchemy
- DB: PostgreSQL
- Auth: JWT (SimpleJWT) with DRF default IsAuthenticated

User roles
- SUPERADMIN — full access; creates Agents/Farmers; audits
- AGENT — manages assigned farms; can onboard farmers to their farms
- FARMER — manages own cows; logs milk and activities

Role access summary
- Farm: SuperAdmin all; Agent limited to farms they manage; Farmer read-only if applicable
- FarmerProfile: SuperAdmin all; Agent can create/update only within their farms; Farmer read-only (own)
- Cow: SuperAdmin all; Agent within managed farms; Farmer only own cows in their farm
- Activity/MilkRecord: SuperAdmin all; Agent only cows in managed farms; Farmer only their own cows

---

## Data Model

- accounts.User (custom): username, password, role {SUPERADMIN, AGENT, FARMER}
- farms.Farm: name, location, agent → FK(User)
- farms.FarmerProfile: user → OneToOne(User), farm → FK(Farm)
- livestock.Cow: tag (unique per farm), breed, dob?, farm → FK(Farm), owner → FK(FarmerProfile)
- livestock.Activity: cow → FK(Cow), type, notes, date
- production.MilkRecord: cow → FK(Cow), date, liters

Relationships
- User ↔ FarmerProfile = 1–1
- Farm ↔ FarmerProfile = 1–many
- Farm ↔ Agent(User) = 1–1
- Farm ↔ Cow = 1–many
- FarmerProfile ↔ Cow = 1–many
- Cow ↔ Activity = 1–many
- Cow ↔ MilkRecord = 1–many

---

## Local Setup (Windows PowerShell)

Prereqs
- Python 3.12+
- PostgreSQL running locally with a database named `farmhub`

Create venv and install deps

```powershell
cd C:\Users\User\Desktop\FarmHub-Management
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Database settings (root .env)

```
DB_NAME=farmhub
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432

DJANGO_SECRET_KEY=dev-secret-not-for-production
DJANGO_DEBUG=true
```

Apply migrations and seed data

```powershell
cd core
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py createsuperuser  # optional (seed includes superadmin)
```

Seeded users are created by migration `accounts/0002_seed_initial_data.py` if not already present (see Seed Data below).

---

## Running the Services

Run Django (core API)

```powershell
cd C:\Users\User\Desktop\FarmHub-Management\core
..\.venv\Scripts\python.exe manage.py runserver
```

Visit
- DRF browsable API: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Health: http://127.0.0.1:8000/healthz/

Run FastAPI (reporting)

```powershell
cd C:\Users\User\Desktop\FarmHub-Management\reporting
..\.venv\Scripts\python.exe -m pip install -r requirements.txt  # once
..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Reporting health: http://127.0.0.1:8001/health

---

## Environment Variables

Used by both services via python-decouple.

- DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
- DJANGO_SECRET_KEY, DJANGO_DEBUG

---

## API Endpoints (examples)

Core API (DRF)
- GET /api/farms/ — list farms
- POST /api/farms/ — create farm (role-based)
- GET /api/cows/ — list cows
- POST /api/milk-records/ — create milk record (farmer)

Quick JWT flow (PowerShell)
```powershell
$token = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/auth/token/" -ContentType "application/json" -Body '{"username":"farmer_sunamganj","password":"Farmer@123"}'
$headers = @{ Authorization = "Bearer $($token.access)" }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/cows/" -Headers $headers
```

Reporting (FastAPI)
- GET /summary — totals across all farms
- GET /reports/farm/{farm_id}/summary — farmers, cows, total milk
- GET /reports/farm/{farm_id}/milk-production — totals by cow
- GET /reports/farm/{farm_id}/daily-milk — daily totals (date range optional)

---

## Auth (JWT)

Endpoints
- POST /auth/token/ — obtain access/refresh (body: username, password)
- POST /auth/token/refresh/ — refresh access token

Usage
- Add header to protected API calls: `Authorization: Bearer <access_token>`
- DRF default permission is `IsAuthenticated` globally; viewsets add stricter role checks.

Example (PowerShell, optional)

```powershell
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/auth/token/" -ContentType "application/json" -Body '{"username":"farmer_sunamganj","password":"Farmer@123"}'
```

---

## Seed Data

Created by `accounts/migrations/0002_seed_initial_data.py` (if users don’t already exist):

- SuperAdmin: username `superadmin`, password `SuperAdmin@123`
- Agent: username `agent_rajshahi`, password `Agent@123`
- Farmer: username `farmer_sunamganj`, password `Farmer@123`
- Farm: Padma Dairy Farm (Rajshahi, Bangladesh)
- Cows: BD-RJ-001 (Red Chittagong), BD-RJ-002 (Sahiwal), BD-RJ-003 (Latest)
- Milk records and activities for sample dates

---

## Postman Collection

This repo includes an exported Postman collection at `postman/FarmHub API.postman_collection.json` covering:
- Auth (Obtain/Refresh) with tests capturing tokens into collection variables
- Farms, Farmer Profiles, Cows, Activities, Milk Records (role-aware sample bodies)
- Reporting endpoints (incl. DB health)

The provided collection is organized as:
- 01 - Authentication
- 02 - Role Scenarios (RBAC)
- 03 - Core API Examples (CRUD)
- 04 - Reporting API

How to use it
1) Import the file `postman/FarmHub API.postman_collection.json` into Postman.
2) Create a Postman Environment (recommended) with:
	- baseUrl = http://127.0.0.1:8000
	- reportUrl = http://127.0.0.1:8001
	- username/password for the role you want to test (e.g., farmer_sunamganj / Farmer@123)
3) Obtain a JWT access token:
	- Make a POST to `${baseUrl}/auth/token/` with body `{ "username": "<user>", "password": "<pass>" }`.
	- Copy the `access` value and paste it into the Bearer Token auth for the requests you plan to run (tokens in the sample may be expired).
	- To refresh, POST to `${baseUrl}/auth/token/refresh/` with body `{ "refresh": "<refresh>" }`.
4) Run the scenarios in "02 - Role Scenarios (RBAC)" and "03 - Core API Examples (CRUD)" using a valid token for the correct role:
	- SuperAdmin can create farms; Agent can create only for themselves; Farmer is forbidden from creating farms.
	- Farmers can list their cows and manage only their own milk records.
5) For "04 - Reporting API", ensure requests point to `${reportUrl}` for endpoints like `/summary`, `/reports/farm/{id}/summary`, `/health`, `/health/db`.

Notes
- Some requests in the collection may include placeholder IDs or previously captured tokens. Replace them with current values or environment variables as needed.
- JWT access tokens expire; obtain a fresh token or use refresh when you get 401 errors.

---

## Troubleshooting

- 404 at root: The DRF browsable API is available at `/` and `/api/`.
- Database errors: ensure PostgreSQL is running and `.env` has correct credentials.
- Reporting DB errors: ensure the same DB env vars are visible to the FastAPI process.
- Missing tables: run migrations in `core/` before starting reporting.

---

## License

MIT (or your choice)
