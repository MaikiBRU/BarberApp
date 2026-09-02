# AGENTS.md - Working conventions for BarberApp

Product and setup documentation lives in `README.md`; design rationale
lives in `docs/ARCHITECTURE.md`. This file covers only the conventions
to follow when changing the code.

## Architecture rules

- Routes convert HTTP and declare the role dependency. Nothing else.
- Services hold business decisions and raise `exceptions.errors.AppError`
  subclasses, never `fastapi.HTTPException`.
- Repositories run queries and never commit; the session dependency owns
  the transaction.
- Models own persistence and database-level constraints.
- Availability rules that can be pure stay pure, in
  `services/availability.py`, so they are unit testable.
- Never trust a role, an owner id or a duration that arrives in a
  request body. Read them from the token or the catalog.

## Code style

- Maximum 300 lines per file, 80 characters per line. Alembic
  migrations are exempt: they are generated DDL, and splitting one
  across files would break the revision graph.
- Python: `snake_case` modules, `PascalCase` classes, docstrings on
  every public module, class and function. Enforced by `ruff` with
  pydocstyle, bugbear, pyupgrade and bandit rules enabled.
- TypeScript: `kebab-case` files, strict mode, no `any`. Props typed
  explicitly rather than inferred from a query result.
- Import order (Python): standard library, third party, first party.
- Import order (TypeScript): React, third party, `@/*`, relative.
- Comments explain why, not what. Do not narrate the obvious.

## Testing

- Backend: `backend/tests/unit/` for pure logic, `backend/tests/
  integration/` for the HTTP API. Shared builders in
  `backend/tests/factories.py`.
- Frontend: `frontend/tests/`, Vitest plus Testing Library.
- Test behaviour that could actually break: authorization, conflicts,
  state transitions, error handling. Do not add tests purely to move a
  coverage number.

## Frontend states

Every asynchronous surface must distinguish four states: loading,
success with data, success with no data, and failure. `EmptyState` and
`ErrorState` are not interchangeable. Never render an empty list when a
request failed.

## Adding an endpoint

1. Schema in `schemas/`, omitting anything the server should decide.
2. Repository method if a new query is needed.
3. Service method holding the rules, raising domain errors.
4. Route with the correct role dependency and `response_model`.
5. Register it in `api/v1/routers.py` if it is a new router.
6. Tests: at least the happy path and the authorization failure.
7. Typed client in `frontend/services/` and the matching type in
   `frontend/types/domain.ts`.
8. Update the endpoint table in `README.md`.

## Before opening a pull request

```powershell
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m pytest backend\tests
.\.venv\Scripts\python.exe -m alembic check
cd frontend; npm run lint; npm run type-check; npm test; npm run build
```

## Never

- Commit `.env` files or real secrets.
- Hardcode data that belongs in the database.
- Leave a placeholder button, a dead route or a broken API call.
- Widen a schema to accept a field the client should not control.
- Change a migration that has already been applied anywhere.
