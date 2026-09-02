# BarberApp Backend

FastAPI service for the BarberApp booking platform. See the repository
root `README.md` for the full setup and the API surface, and
`docs/ARCHITECTURE.md` for the design decisions.

## Modules

| Path | Responsibility |
| --- | --- |
| `api/v1/routes/` | HTTP conversion and role dependencies only |
| `auth/` | Token creation and verification, password hashing |
| `core/` | Pydantic settings, logging |
| `db/` | Async engine, session dependency |
| `exceptions/` | Domain error hierarchy raised by services |
| `middleware/` | Error envelope, rate limiting, request context |
| `models/` | SQLAlchemy models, enums, `UTCDateTime` |
| `repositories/` | Queries; never commit |
| `schemas/` | Request and response DTOs |
| `services/` | Business logic, including the booking engine |
| `alembic/` | Migrations |
| `scripts/` | Local seed and account creation |

## Commands

Run from the repository root unless noted.

```powershell
# install
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

# quick local run on SQLite
cd backend
$env:DATABASE_URL="sqlite+aiosqlite:///./dev.sqlite3"
..\.venv\Scripts\python.exe scripts\init_dev.py --create-tables
..\.venv\Scripts\python.exe -m uvicorn main:app --reload

# migrations (PostgreSQL)
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic check

# quality gates
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m compileall -q backend
.\.venv\Scripts\python.exe -m pytest backend\tests
```

## Creating internal accounts

Public registration only ever creates customers. Admin and barber
accounts come from the CLI or the admin-only API endpoints.

```powershell
cd backend
..\.venv\Scripts\python.exe scripts\create_user.py `
  --email owner@barberapp.local --password "a-strong-password" --role admin
```

## Tests

- `tests/unit/` covers pure logic: slot generation, the rate-limit
  counter, settings parsing and the production safety checks.
- `tests/integration/` drives the HTTP API against a disposable SQLite
  database: authentication, the role matrix, the booking engine,
  appointment lifecycle and the dashboard.
- `tests/factories.py` holds the seed data and the `ApiHelper` used to
  keep the API tests readable.

Note that the PostgreSQL exclusion constraint cannot be exercised on
SQLite. The application-level conflict check is tested here; CI runs the
migration against a real PostgreSQL service container.
