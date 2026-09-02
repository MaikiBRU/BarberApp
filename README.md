# BarberApp

Full-stack booking and operations platform for a barbershop. Customers
book from real availability, barbers work their agenda, and the owner
manages catalog, staff and opening hours.

The MVP targets a single shop. Every table that would need it already
carries a nullable `shop_id`, so a multi-shop SaaS can be layered on
without rewriting the domain.

## Stack

| Layer | Technology |
| --- | --- |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2 async, Alembic |
| Database | PostgreSQL 16 (SQLite for a zero-setup local run) |
| Frontend | Next.js 16 App Router, TypeScript strict, TailwindCSS v4, TanStack Query, Zustand |
| Auth | Email/password, bcrypt, JWT access tokens |
| Infrastructure | Docker Compose, GitHub Actions |

## What it does

### Customer
Register and sign in, browse services with real prices and duration,
add optional extras, pick a barber (or let the shop assign one), choose
from slots the server actually has free, book, review the appointment,
cancel within the shop's cancellation window, and keep a history.

### Barber
A dashboard with today's figures and agenda, customer contact details
for their own appointments only, and the status transitions they are
allowed to perform.

### Administrator
Everything a barber sees for the whole shop, plus management of
services, extras, barber accounts and weekly opening hours, and a
filterable, paginated view of every appointment.

## The booking engine

This is the core of the project.

```text
service (+ extras)  ->  duration
        |
     barber                        business hours
        |                          existing appointments
      date        ------------->   barber time off      ---> free slots
        |                          lead time / horizon
   pick a slot
        |
   POST /appointments  --> every rule re-checked --> INSERT
```

Guarantees:

- **Availability is computed server-side.** The frontend renders exactly
  what `GET /api/v1/appointments/availability` returns and invents
  nothing.
- **The booking endpoint re-validates the slot** against every rule
  before writing, so a stale or hand-crafted request cannot slip
  through.
- **PostgreSQL refuses overlaps at the storage layer.** An exclusion
  constraint over `(barber_id, tstzrange(starts_at, ends_at))`, limited
  to `pending` and `confirmed`, closes the race between two concurrent
  bookings.
- **Service duration drives the grid.** A 90-minute service offers fewer
  starts than a 45-minute one, and extras extend the booked window.
- **Inactive services and barbers disappear** from availability and are
  rejected at booking time.
- **Timestamps are timezone-aware end to end.** A custom SQLAlchemy type
  normalizes every datetime to UTC, and opening hours are anchored to
  the shop's local wall clock so DST changes do not shift the schedule.

## Project structure

```text
backend/
  api/v1/routes/    thin HTTP controllers
  auth/             JWT creation, dependencies, password hashing
  core/             settings and logging
  db/               async engine and session dependency
  exceptions/       domain error hierarchy
  middleware/       error envelope, rate limiting, request context
  models/           SQLAlchemy models, enums, custom column types
  repositories/     data access
  schemas/          Pydantic request/response DTOs
  services/         business logic, including the booking engine
  alembic/          migrations
  scripts/          local seed and user creation
  tests/            unit and integration suites
frontend/
  app/              App Router pages and layouts
  components/       UI primitives, layout, auth guard
  features/         auth, booking, appointments, dashboard, profile
  services/         typed API clients
  lib/              api client, formatting, tokens, error mapping
  store/            session state
  tests/            Vitest suites
docs/               architecture notes
```

## Setup

Requires Python 3.12 and Node 22.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

```powershell
cd frontend
npm install
```

## Run locally without Docker

SQLite needs no database server and is the fastest way to see the app.

Terminal 1 - API:

```powershell
cd backend
$env:DATABASE_URL="sqlite+aiosqlite:///./dev.sqlite3"
..\.venv\Scripts\python.exe scripts\init_dev.py --create-tables
..\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Terminal 2 - web app:

```powershell
cd frontend
copy .env.local.example .env.local
npm run dev
```

- Web app: http://localhost:3000
- API: http://localhost:8000
- API docs: http://localhost:8000/api/docs

For PostgreSQL instead of SQLite, start the database, point
`DATABASE_URL` at it and run `alembic upgrade head` before the API.

### Development credentials

Created by `scripts/init_dev.py`. **Development only** - they exist in
seed code, never in a deployed environment.

| Email | Password | Role |
| --- | --- | --- |
| `admin@example.com` | `Password123!` | admin |
| `tomas@example.com` | `Password123!` | barber |
| `lucia@example.com` | `Password123!` | barber |
| `cliente@example.com` | `Password123!` | customer |

## Run with Docker

```powershell
copy .env.example .env
# set JWT_SECRET_KEY in .env, then:
docker compose up --build
docker compose exec backend python scripts/init_dev.py
```

Compose refuses to start without `JWT_SECRET_KEY`. Generate one with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

`docker-compose.override.yml` is applied automatically and switches both
services to hot-reload development mode. For the production-shaped
images, run `docker compose -f docker-compose.yml up --build`.

## Database migrations

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic check
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "message"
```

The backend container applies migrations before starting the API.

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_ENV` | `development` | `production` enables the startup safety checks |
| `DEBUG` | `true` | Serves `/api/docs`; must be off in production |
| `DATABASE_URL` | - | Full async SQLAlchemy URL |
| `JWT_SECRET_KEY` | dev default | Signing key; production refuses the default |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token lifetime |
| `CORS_ORIGINS` | localhost:3000 | Comma-separated allowlist |
| `RATE_LIMIT_ENABLED` | `true` | Throttles the credential endpoints |
| `SHOP_TIMEZONE` | `America/Argentina/Buenos_Aires` | IANA zone for opening hours |
| `CURRENCY` | `ARS` | Currency reported by the dashboard |
| `BOOKING_SLOT_MINUTES` | `15` | Spacing of the slot grid |
| `BOOKING_MIN_LEAD_MINUTES` | `60` | Minimum notice before a booking |
| `BOOKING_MAX_ADVANCE_DAYS` | `60` | How far ahead customers may book |
| `BOOKING_CANCELLATION_CUTOFF_MINUTES` | `120` | Customer self-cancellation window |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API base URL for the browser |

Full examples in `.env.example` (Docker), `backend/.env.example` and
`frontend/.env.local.example`. `.env` files are gitignored.

## API

Interactive documentation at `/api/docs` while `DEBUG` is on.

| Method | Path | Access |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register` | public (customers only) |
| `POST` | `/api/v1/auth/login` | public |
| `GET` | `/api/v1/auth/me` | authenticated |
| `GET` | `/api/v1/catalog/services` | public |
| `POST` `PATCH` | `/api/v1/catalog/services[/{id}]` | admin |
| `GET` | `/api/v1/catalog/admin/services` | admin |
| `GET` | `/api/v1/catalog/extras` | public |
| `POST` `PATCH` | `/api/v1/catalog/extras[/{id}]` | admin |
| `GET` | `/api/v1/catalog/admin/extras` | admin |
| `GET` | `/api/v1/users/barbers` | public (no contact details) |
| `GET` | `/api/v1/users/admin/barbers` | admin |
| `POST` `PATCH` | `/api/v1/users/barbers[/{id}]` | admin |
| `GET` `PATCH` | `/api/v1/users/me/profile` | authenticated |
| `GET` | `/api/v1/schedule/business-hours` | public |
| `PUT` | `/api/v1/schedule/business-hours` | admin |
| `GET` `POST` `DELETE` | `/api/v1/schedule/barbers/{id}/time-off` | admin or that barber |
| `GET` | `/api/v1/appointments/availability` | public |
| `GET` | `/api/v1/appointments` | authenticated, scoped by role |
| `POST` | `/api/v1/appointments` | customer or admin |
| `POST` | `/api/v1/appointments/admin` | admin |
| `GET` | `/api/v1/appointments/{id}` | owner, assigned barber, admin |
| `PATCH` | `/api/v1/appointments/{id}/status` | per the transition matrix |
| `GET` | `/api/v1/dashboard/summary` | admin, barber |
| `GET` | `/api/v1/dashboard/today` | admin, barber |
| `GET` | `/health`, `/api/v1/health`, `/api/v1/ready` | public |

Every error, including validation failures, uses one envelope:

```json
{
  "error": {
    "type": "slot_unavailable",
    "message": "The selected time slot is no longer available",
    "details": null
  }
}
```

## Authorization

Enforced in the backend on every request; the frontend guard is a
navigation convenience only.

| Action | Customer | Barber | Admin |
| --- | --- | --- | --- |
| Book for themselves | yes | no | yes (any customer) |
| Read an appointment | own only | assigned only | all |
| Cancel | own, before the cutoff | assigned | all |
| Confirm / complete / no-show | no | assigned | all |
| See customer contact details | no | assigned only | all |
| Manage catalog, staff, hours | no | no | yes |

Appointment states move `pending -> confirmed -> completed`, with
`cancelled` and `no_show` reachable from either active state. Terminal
states are final. Each response carries `allowed_transitions` for the
caller, so the UI only ever offers actions the server will accept.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
cd frontend; npm test
```

82 backend tests (unit plus integration against an isolated SQLite
database) and 34 frontend tests. They cover authentication and account
enumeration, the role matrix, IDOR and mass-assignment attempts, slot
generation, double booking, overlap, inactive resources, time off,
closed days, status transitions, cancellation policy, dashboard
figures, configuration safety and the error-versus-empty distinction in
the UI.

## Validation commands

```powershell
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m compileall -q backend
.\.venv\Scripts\python.exe -m pytest backend\tests
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic check
```

```powershell
cd frontend
npm run lint
npm run type-check
npm test
npm run build
npm audit --omit=dev --audit-level=high
```

```powershell
copy .env.example .env
docker compose config --quiet
```

GitHub Actions runs all of the above on every pull request, with the
backend job executing migrations and tests against a real PostgreSQL
service container.

## Security notes

- Passwords hashed with bcrypt at cost 12; login verifies a dummy hash
  when the account does not exist, so the endpoint neither confirms nor
  denies that an email is registered.
- JWT algorithm is pinned; tokens carry a type claim and are rejected if
  it does not match.
- Roles are read from the database on every request, never from a claim
  the client controls.
- Public registration cannot assign a privileged role.
- `customer_id` and `duration_minutes` are not accepted from booking
  requests; the owner comes from the token and the duration from the
  catalog.
- Contact details are redacted per viewer.
- Reading someone else's appointment returns 404, not 403, so ids cannot
  be probed.
- Credential endpoints are rate limited per IP.
- Responses carry `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy` and `Cross-Origin-Opener-Policy`.
- In production the API refuses to start with the default JWT secret,
  `DEBUG` on, SQL echo on, or a wildcard CORS allowlist.

## Known limitations

- Rate limiting is in-process. A multi-replica deployment needs a shared
  store such as Redis.
- Payments are recorded as an intent (`payment_method`,
  `payment_status`); no provider is integrated, so nothing pretends to
  charge a card.
- No refresh tokens: the access token expires and the user signs in
  again.
- No email or push notifications.
- Google OAuth is not implemented.
- Sessions are stored in `localStorage`, which is appropriate for this
  MVP but would move to httpOnly cookies alongside a refresh-token flow.
