<div align="center">

# FarmHub

End‑to‑end farm management (Django + DRF) with a read‑only reporting service (FastAPI). PostgreSQL only. Fully role‑aware (SUPERADMIN / AGENT / FARMER) with secure CRUD + aggregate reports.

</div>

## 1. Why This Project (Interview Context)
Demonstrates: clean data model, enforced RBAC, consistent API design, admin usability, reporting separation, containerized deployment.

## 2. Architecture Overview
Monorepo layout:
```
core/        Django + DRF (auth, RBAC, CRUD)
reporting/   FastAPI (read-only aggregation endpoints)
docker-compose.yml (web=DRF, web-1=FastAPI, db=Postgres)
```
Cross-cutting:
- Shared Postgres schema
- JWT auth (SimpleJWT)
- Role scoping at queryset + permission + serializer validation layers
- Consistent response envelope for explicit create/update (farms, livestock, milk records)

## 3. Roles & Access (Summary Table)
| Resource | SUPERADMIN | AGENT | FARMER |
|----------|------------|-------|--------|
| Users    | Full       | Read  | Read self |
| Farms    | Full       | Own farms | Read scoped |
| FarmerProfiles | Full | Create/Update within own farms | Own (read) |
| Cows     | Full       | Cows in managed farms | Own cows |
| Activities | Full    | Cows in managed farms | Own cows |
| Milk Records | Full  | Cows in managed farms | Own cows |

Enforcement techniques:
- Custom permission classes (e.g. `FarmRBACPermission`, livestock permissions)
- Queryset scoping (`get_queryset` per viewset)
- Serializer `validate()` for ownership / role invariants

## 4. Data Model (Key Entities)
```
User(role) ─1─┐
			 │ (OneToOne)
FarmerProfile ┘      Farm ──< Cow ──< Activity
	(farm FK)  ^                └─< MilkRecord
			   │ (agent = User with AGENT role)
```
Constraints:
- Cow tag unique per farm
- MilkRecord unique (cow, date)
- FarmerProfile single farm membership

## 5. Reporting Service (FastAPI)
Read‑only aggregation endpoints (examples):
- Global summary (farms / farmers / cows / total milk)
- Farm summary & per‑cow milk production
- Daily milk (date range filters)
- Farmer summary (their cows + milk in range)
- Recent activities (optional farm filter)

Isolation rationale: avoids coupling write workload to analytic aggregate queries; easy to scale horizontally.

## 6. Docker Quick Start (One Command)
Prereqs: Docker & Docker Compose; create `.env` at repo root:
```
POSTGRES_DB=farmhub
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_NAME=farmhub
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
DJANGO_SECRET_KEY=dev-secret
DJANGO_DEBUG=true
```
Start stack:
```bash
docker compose up --build
```
Services:
- Core API: http://localhost:8000
- Admin:   http://localhost:8000/admin/
- Reporting: http://localhost:8001

The web container auto‑runs migrations; superuser creation is attempted (ignored if exists).

## 7. Local (Non‑Docker) Setup (Windows PowerShell)
```powershell
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r requirements.txt
cd core
../.venv/Scripts/python.exe manage.py migrate
```
Run core:
```powershell
../.venv/Scripts/python.exe manage.py runserver
```
Run reporting:
```powershell
cd ..\reporting
../.venv/Scripts/python.exe -m pip install -r requirements.txt
../.venv/Scripts/python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## 8. Authentication (JWT)
Endpoints:
- POST /auth/token/
- POST /auth/token/refresh/
Header: `Authorization: Bearer <access>`
Example (PowerShell):
```powershell
$t = Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/auth/token/ -ContentType application/json -Body '{"username":"farmer_sunamganj","password":"Farmer@123"}'
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/cows/ -Headers @{Authorization = "Bearer $($t.access)"}
```

## 9. Sample Core Endpoints
| Action | Method | Path |
|--------|--------|------|
| List Farms | GET | /api/farms/ |
| Create Farm | POST | /api/farms/ |
| List Cows | GET | /api/cows/ |
| Create Milk Record | POST | /api/milk-records/ |
| List Activities | GET | /api/activities/ |

Explicit responses for create/update/destroy include `{ "message": ..., "data": ... }`.

## 10. Reporting Endpoints (Examples)
| Endpoint | Purpose |
|----------|---------|
| GET /summary | Global counts & totals |
| GET /reports/farm/{id}/summary | Farm metrics |
| GET /reports/farm/{id}/milk-production | Per‑cow totals |
| GET /reports/farm/{id}/daily-milk?date_from=&date_to= | Daily aggregation |
| GET /reports/farmer/{user_id}/summary | Farmer milk & cows |
| GET /reports/activities/recent?farm_id=&limit= | Latest activities |

## 11. Seed Data (Migration 0002)
Created if absent:
- SUPERADMIN: `superadmin` / `SuperAdmin@123`
- AGENT: `agent_rajshahi` / `Agent@123`
- FARMER: `farmer_sunamganj` / `Farmer@123`
- Farm + sample cows (3), activities, milk records

## 12. Postman Collection
File: `postman/FarmHub API.postman_collection.json`
Folders: Auth / RBAC Scenarios / Core CRUD / Reporting.
Login requests auto‑store tokens in `superAdminToken`, `agentToken`, `farmerToken`.
Variables: `core_url`, `reporting_url`.

## 13. Evaluation Mapping
| Criterion | Evidence |
|-----------|----------|
| Correctness & Scope | Full CRUD + milk + activities + reporting queries |
| Role-based Security | Permissions + queryset scoping + serializer validation |
| Django Admin | Search, list_filter, inlines (activities & milk under cow; farmer profile inline under user) |
| FastAPI Reporting | Aggregated endpoints & filtering |
| Architecture & Reasoning | Separation of concerns, explicit methods, dockerized services |
| Code Quality & Docs | Typed serializers, structured viewsets, this README, Postman |

## 14. Troubleshooting
- 401: Re-authenticate; token expired.
- Empty lists: Role scoping hiding data (check user role).
- Docker Postgres auth: Ensure `.env` POSTGRES_* matches compose service.
- Migration race (first up): Restart web if DB wasn’t ready (compose handles via dependency, usually fine).

## 15. Possible Next Enhancements
- Add `recorded_by` to `MilkRecord` for provenance
- Global search/filter backends in DRF
- Caching layer for heavy reporting queries
- Async task queue for large imports

## 16. License
MIT (adjust as needed).

---
Interview friendly summary: FarmHub delivers secure multi‑role farm operations plus isolated reporting with a clean, testable architecture and production‑style container setup.
