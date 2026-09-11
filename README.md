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

## Item marketplace

Signed-in community members can browse `/marketplace`, publish at `/items/new`,
and view `/items/:id`. Owners can edit or delete their listings from the detail page.
Prices are displayed in INR. Availability is a boolean flag, not a reservation calendar.
Image URLs are optional HTTP(S) links; uploads and rental bookings are not included yet.

All item endpoints are under `/api/v1/items`: `POST` and `GET` on the collection,
and `GET`, `PATCH`, `DELETE` on `/{id}`. Ownership and community are assigned by the
server. Every read and mutation is community-scoped; only owners may edit/delete.
Cross-community IDs return 404. Users without membership receive 403.

List filters: `category`, `min_price`, `max_price`, `search`, `availability`.
Pagination uses `limit` (default 24, maximum 100) and `offset`; responses contain
`items` and `total`. Prices are nonnegative decimal strings with up to two decimal
places. PATCH supports partial updates; only `image_url` can be cleared with null.
Run `alembic upgrade head` from `backend/` to apply `20260909_0003` before use.

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

## Rental transactions

Apply the rental schema with `alembic upgrade head` from `backend/` before starting the API. In the frontend, open another member's item, choose pickup and return dates, and request to borrow. Open **Rentals** to switch between Borrowing and Lending and manage requests.

All endpoints require a bearer token and community membership. Only the borrower and owner can read a rental; other users receive 404.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/v1/rentals` | Request with `item_id`, `start_date`, `end_date` |
| GET | `/api/v1/rentals` | Participant requests; optional `role=borrower\|owner`, `status`, `limit` (1–100), `offset` |
| GET | `/api/v1/rentals/{id}` | Read a participant's request |
| POST | `/api/v1/rentals/{id}/accept` | Owner: PENDING → ACCEPTED |
| POST | `/api/v1/rentals/{id}/reject` | Owner: PENDING → REJECTED |
| POST | `/api/v1/rentals/{id}/cancel` | Either participant: PENDING/ACCEPTED → CANCELLED |
| POST | `/api/v1/rentals/{id}/start` | Owner confirms pickup: ACCEPTED → ACTIVE |
| POST | `/api/v1/rentals/{id}/return` | Owner confirms physical return: ACTIVE → RETURNED |

- Dates are UTC calendar dates. End date is exclusive: September 10–12 is two days. Duration must be 1–365 days; new requests cannot start in the past.
- The server snapshots daily price × days, security deposit, and a 10% platform commission, using decimal arithmetic and half-up rounding to two places. Commission is **included in** the rental amount, not added to it. The deposit is separate. These records do not collect payment, recognize revenue, or issue refunds; payment-provider integration remains future work.
- Self-rentals and unavailable items are rejected. Owner and borrower must share the item's community; this is rechecked at acceptance and pickup.
- Pending requests do not reserve dates. ACCEPTED and ACTIVE reservations cannot overlap; adjacent bookings are allowed. All booking writers acquire the same PostgreSQL item-row lock before checking conflicts. Keep the default PostgreSQL READ COMMITTED isolation level.
- Exact duplicate pending requests return 409. Pricing/status/identity fields supplied by clients are rejected. Invalid transitions and booking conflicts return 409; forbidden owner actions return 403; invalid dates return 422.
- Accepted bookings can be cancelled only before the start date. Pickup must occur inside the booked interval and cannot occur while another rental is still ACTIVE, even if overdue. Owner-confirmed return releases the reservation, including an early return. Rejected, returned, and cancelled requests are terminal. There is no automatic expiry or no-show resolution yet.
- Items with rental history cannot be deleted. Mark them unavailable instead; history and financial snapshots remain intact.

`pytest` includes the state-transition matrix and HTTP integration tests using SQLite. To verify simultaneous approvals against real PostgreSQL, set `TEST_POSTGRES_URL` to a **dedicated test database** (SQLAlchemy `postgresql+psycopg://...` URL), then run `pytest tests/test_rental_concurrency.py`. The test creates and removes a uniquely named schema and requires schema-creation permission. Without that variable it is explicitly skipped; SQLite tests do not prove locking behavior.

## NaboScore

Every account starts at 100 and every score mutation is recorded once in the
`nabo_score_events` audit table. The scoring formula lives independently in
`app.services.scoring`, and both service and database constraints clamp scores to
0–100.

| Event | Score change |
| --- | ---: |
| Successful return on or before the return date | +2 borrower |
| Rating of 4 or 5 after return | +1 rated user |
| Return after the return date | −5 borrower |
| Owner reports item damage during/after an active rental | −10 borrower |
| Either participant cancels an accepted booking | −5 cancelling user |

Labels are Excellent (90–100), Good (75–89), Average (60–74), and Risky (below
60). Rental responses include community-safe borrower and owner profiles with
their current score and label. `GET /api/v1/users/{id}` exposes the same public
profile only to members of that user's community; it never exposes email, phone,
or password data.

After a rental is returned, either participant can submit one 1–5 rating with
`POST /api/v1/rentals/{id}/rating`. Owners can create one damage report with
`POST /api/v1/rentals/{id}/damage-dispute`. Duplicate submissions return 409.
Apply migration `20260911_0005` with `alembic upgrade head` before use.

## Next implementation slices

Suggested feature order:

1. Image uploads and moderation.
2. Refresh-token rotation and secure cookie-based sessions.
3. No-show resolution and rental expiry policies.
4. Payment-provider integration, deposits, commissions, and idempotent webhooks.
5. Return confirmation, disputes, reviews, notifications, and audit events.

Keep authorization community-scoped at the query/service layer, use decimal database types for money, store times in UTC, and model rental transitions explicitly rather than with loosely related booleans.
