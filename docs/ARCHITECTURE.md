# BarberApp Architecture

## Goal

A working single-shop booking product with boundaries clean enough to
grow into a multi-shop SaaS. The hard parts are availability, conflict
prevention and authorization; everything else stays deliberately plain.

## Layering

```text
HTTP route      converts request/response, declares the role dependency
   |
service         business rules, raises domain errors
   |
repository      SQLAlchemy queries, no business decisions
   |
model           persistence and database-level constraints
```

Routes never touch the ORM. Services never import FastAPI exceptions:
they raise from `exceptions/errors.py`, and `middleware` turns those
into one HTTP envelope. That keeps business rules testable without a
web server and gives the frontend a single error contract.

Repositories never commit. The request-scoped session dependency owns
the transaction, so one request that writes through several
repositories either lands whole or not at all.

## Domain

| Model | Purpose |
| --- | --- |
| `User` | Account and role (`admin`, `barber`, `customer`) |
| `BarberProfile` | Display name, bio, phone, active flag |
| `CustomerProfile` | Full name, phone, notes |
| `Service` | Bookable service: duration and price |
| `ProductExtra` | Optional add-on: extra duration and price |
| `BusinessHours` | Opening window per weekday |
| `BarberTimeOff` | Windows where a barber is unavailable |
| `Appointment` | The booking, with its occupied time range |
| `Payment` | Payment record attached to an appointment |

Nullable `shop_id` columns on `users`, `services`, `product_extras`,
`business_hours` and `appointments` are the seam for multi-tenancy.
Introducing shops means populating them and adding a tenant filter in
the repositories, not reshaping the schema.

## Booking engine

`services/availability.py` is pure: given opening hours, a duration, a
slot size, busy ranges and a horizon, it returns start times. No
database, no framework, so the rules are unit tested directly.

`services/availability_service.py` supplies that function with real
data: active barbers, blocking appointments, time off and the weekday's
opening window.

`services/booking_service.py` writes. It re-runs the whole availability
calculation for the exact requested slot before inserting, then relies
on the database for the last word.

### Why the exclusion constraint

Two customers can pass the availability check at the same instant and
both try to insert. Application checks cannot close that window without
serializing every booking. PostgreSQL can:

```sql
EXCLUDE USING gist (
    barber_id WITH =,
    tstzrange(starts_at, ends_at) WITH &&
) WHERE (status IN ('pending', 'confirmed'))
```

The loser's `INSERT` raises `IntegrityError`, which the service turns
into a `409 slot_unavailable`. The partial `WHERE` clause is what lets
a cancelled appointment free its slot again.

SQLite has no equivalent, so the local development path keeps only the
application-level check. That difference is deliberate and documented
rather than hidden.

### Time

`models/types.py` defines `UTCDateTime`, which rejects naive datetimes
on write and attaches UTC on read. PostgreSQL keeps the offset in
`timestamptz`; SQLite does not, and without this type a SQLite-backed
run would return naive datetimes and break every comparison against
`datetime.now(timezone.utc)`.

Opening hours are stored as local wall-clock times and combined with a
date in the shop timezone, so 09:00 stays 09:00 across a DST change.

## Authorization

Every protected route declares a role dependency that reads the user
row from the database; no role is ever trusted from a token claim or a
request body. Ownership is enforced inside the query, not by filtering
the response, so paging cannot leak another customer's rows.

`services/appointment_view.py` decides what each viewer sees. A
customer never receives staff contact details; a barber receives the
customer's phone only for their own appointments. The same module
computes `allowed_transitions`, which the API returns so the UI can
render exactly the actions the server will accept.

Reading an appointment the caller may not see returns 404 rather than
403, so ids cannot be probed for existence.

## Frontend

App Router with client components for anything that reads the session.
TanStack Query owns server state; Zustand owns only the session.

`lib/api-client.ts` maps the backend envelope onto a typed `ApiError`
and distinguishes a network failure from an HTTP failure. That is what
lets every screen separate three states that are easy to conflate:
loading, "no data", and "the request failed". `EmptyState` and
`ErrorState` are visually distinct and never substituted for each
other.

The booking wizard keeps its state in one reducer-like hook. Changing
the service, extras, barber or date clears the selected slot, because
any of those changes can invalidate it.

## Deferred

- Payment provider integration
- Refresh tokens and httpOnly cookie sessions
- Email and push notifications
- Google OAuth
- Multi-shop tenancy
- Shared-store rate limiting
