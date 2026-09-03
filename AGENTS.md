# NaboShare contributor guidance

## Scope

This repository is an MVP monorepo. Keep product features small and independently testable. Do not place business logic in route handlers or React page components.

## Architecture

- `frontend/` is a React, TypeScript, Vite, and Tailwind CSS application.
- `backend/` is a FastAPI application using SQLAlchemy, PostgreSQL, and Alembic.
- Backend HTTP endpoints live under `/api/v1`.
- Backend configuration must come from environment variables via `app.core.config`.
- Database models inherit from `app.db.base.Base`; schema changes require Alembic migrations.

## Quality gates

Before finishing a change, run the checks relevant to the files changed:

- Frontend: `npm run check` and `npm run build` from `frontend/`.
- Backend: `ruff check .`, `ruff format --check .`, `mypy app`, and `pytest` from `backend/`.
- Do not commit `.env` files, credentials, generated build output, or virtual environments.

