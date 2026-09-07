# NaboShare

NaboShare is a hyperlocal peer-to-peer rental marketplace for verified communities such as colleges, hostels, and residential societies. This repository contains the MVP foundation: a React client, a FastAPI service, PostgreSQL infrastructure, and shared development conventions.

The current scope deliberately stops before product features such as identity verification, listings, rental requests, payments, deposits, returns, and commissions.

## Architecture

```text
naboshare/
├── frontend/                 React + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── lib/              API and shared client utilities
│   │   └── test/             Test setup
│   └── ...                   Build, lint, and TypeScript configuration
├── backend/                  FastAPI + SQLAlchemy application
│   ├── alembic/              Database migration environment
│   │   └── versions/         Generated migration revisions
│   ├── app/
│   │   ├── api/              Versioned HTTP routes
│   │   ├── core/             Environment-backed settings
│   │   └── db/               SQLAlchemy base, engine, and sessions
│   └── tests/                API tests
├── .env.example              Docker Compose environment template
├── docker-compose.yml        Local PostgreSQL service
└── AGENTS.md                 Repository contribution guidance
```

The browser communicates with versioned endpoints under `/api/v1`. During development, Vite proxies `/api` requests to FastAPI at `http://127.0.0.1:8000`, avoiding cross-origin complexity. The backend creates short-lived SQLAlchemy sessions per request and Alembic owns all schema evolution.

### Health endpoints

| Endpoint | Purpose | Database required |
| --- | --- | --- |
| `GET /api/v1/health` | Process liveness | No |
| `GET /api/v1/health/ready` | Application readiness (`SELECT 1`) | Yes |

Interactive API documentation is available at `http://localhost:8000/docs` outside production.

### Authentication endpoints

| Endpoint | Purpose | Authentication |
| --- | --- | --- |
| `POST /api/v1/auth/register` | Create a user account | Public |
| `POST /api/v1/auth/login` | Exchange email and password for an access token | Public |
| `GET /api/v1/auth/me` | Return the current public user profile | Bearer token |

Passwords are hashed with Argon2 and are never returned by the API. Access tokens are signed JWTs with issuer, audience, issued-at, and expiry claims. The browser persists the access token in local storage for this MVP and clears it when validation fails or the user logs out. A production hardening phase should move session persistence to secure, HTTP-only cookies alongside CSRF protection and refresh-token rotation.

### Verified community endpoints

| Endpoint | Purpose | Authentication |
| --- | --- | --- |
| `POST /api/v1/communities` | Create a community and join it as its first member | Bearer token |
| `POST /api/v1/communities/join` | Join a community using its invite code | Bearer token |
| `GET /api/v1/communities/me` | Return the current user's community | Bearer token |

Supported community types are `college`, `hostel`, `apartment_society`, and `corporate_campus`. Invite codes are unique, cryptographically generated eight-character codes. A user can belong to one community in the MVP and cannot switch communities through the public API.

Community-owned resources must use the backend's `require_current_community` dependency. This resolves community scope from the authenticated user and prevents item endpoints from accepting or trusting an arbitrary client-provided community ID. When item listings are introduced, every item query must filter by this resolved community ID.

## Prerequisites

- Node.js 22 or newer and npm 10 or newer
- Python 3.12 or newer
- Docker Desktop with Docker Compose v2
- Git

## Local setup

### 1. Configure the environment

From the repository root, copy the templates:

```powershell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

The checked-in defaults are intended only for local development. Do not use them in a deployed environment. In particular, set a strong `POSTGRES_PASSWORD` and `JWT_SECRET_KEY` in staging and production. If the database credentials in the root `.env` change, update `DATABASE_URL` in `backend/.env` to match.

`CORS_ORIGINS` is a JSON array, for example:

```dotenv
CORS_ORIGINS=["http://localhost:5173","https://app.example.com"]
```

### 2. Start PostgreSQL

```powershell
docker compose up -d postgres
docker compose ps
```

Wait until the service reports `healthy`. PostgreSQL is exposed on `localhost:5432` by default and stores data in the named `postgres_data` volume.

### 3. Set up and run the backend

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

On macOS or Linux, activate the environment with `source .venv/bin/activate` instead.

Verify the API in another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health/ready
```

### 4. Set up and run the frontend

```powershell
Set-Location frontend
npm install
npm run dev
```

Open `http://localhost:5173`. For a separately hosted API, set `VITE_API_URL` in `frontend/.env` to its origin. Leave it empty for the local Vite proxy.

## Quality checks

Run frontend checks from `frontend/`:

```powershell
npm run check
npm run build
```

`npm run check` runs ESLint, Prettier verification, the TypeScript compiler, and Vitest.

Run backend checks from `backend/` with the virtual environment active:

```powershell
ruff check .
ruff format --check .
mypy app
pytest
```

The API test suite overrides the database dependency, so it does not require PostgreSQL. The readiness endpoint itself should also be checked against the Compose database before merging infrastructure changes.

## Database migrations

Import each new SQLAlchemy model from `app/db/base.py` (or from a model aggregator imported there) so Alembic can discover its metadata. Then run:

```powershell
Set-Location backend
alembic revision --autogenerate -m "describe the schema change"
alembic upgrade head
```

Review every generated migration before applying it. To roll back one revision, use `alembic downgrade -1`.

## Environment reference

### Backend

| Variable | Default | Description |
| --- | --- | --- |
| `APP_NAME` | `NaboShare API` | OpenAPI application name |
| `APP_ENV` | `development` | `development`, `test`, `staging`, or `production` |
| `DEBUG` | `false` | FastAPI debug mode |
| `API_V1_PREFIX` | `/api/v1` | Versioned API prefix |
| `DATABASE_URL` | Local PostgreSQL URL | SQLAlchemy connection URL |
| `DATABASE_CONNECT_TIMEOUT_SECONDS` | `5` | Maximum initial database connection wait |
| `CORS_ORIGINS` | Local Vite origin | JSON array of allowed browser origins |
| `JWT_SECRET_KEY` | Development placeholder | JWT signing secret; replace outside local development |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ISSUER` | `naboshare-api` | Required token issuer |
| `JWT_AUDIENCE` | `naboshare-web` | Required token audience |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access-token lifetime |

### Frontend

| Variable | Default | Description |
| --- | --- | --- |
| `VITE_API_URL` | Empty | API origin; empty uses same-origin paths and the dev proxy |

## Next implementation slices

Suggested feature order:

1. Item listings, images, availability, and community-scoped discovery.
2. Refresh-token rotation and secure cookie-based sessions.
3. Rental requests and an explicit rental state machine.
4. Payment-provider integration, deposits, commissions, and idempotent webhooks.
5. Return confirmation, disputes, reviews, notifications, and audit events.

Keep authorization community-scoped at the query/service layer, use decimal database types for money, store times in UTC, and model rental transitions explicitly rather than with loosely related booleans.
