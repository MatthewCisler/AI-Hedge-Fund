# Paper Hedge Fund Simulator

Educational and experimental full-stack paper-trading application for U.S. stocks and ETFs. The system is intentionally designed so AI can analyze and rank ideas, but it cannot directly place trades. Every trade idea must pass a deterministic rules engine before it can be queued or sent to the Alpaca paper trading API.

## Project structure

```text
.
├── backend
│   ├── app
│   │   ├── api
│   │   ├── core
│   │   ├── db
│   │   ├── jobs
│   │   ├── models
│   │   ├── repositories
│   │   ├── schemas
│   │   ├── services
│   │   └── utils
│   ├── .env.example
│   └── requirements.txt
└── frontend
    ├── public
    └── src
        ├── app
        ├── components
        └── lib
```

## Architecture choices

- Backend: FastAPI + SQLAlchemy
- Database: PostgreSQL
- Scheduler: APScheduler for the initial scaffold
- Queue/cache placeholder: Redis
- Frontend: Next.js App Router
- Broker: Alpaca paper trading abstraction
- AI: local-model interface abstraction with a safe stub implementation
- News: pluggable provider abstraction with a safe stub implementation
- Reporting: database-backed daily reports plus CSV export

## Core safety constraints

- Paper trading only
- U.S. stocks and ETFs only
- AI cannot directly execute trades
- Deterministic rules engine is the execution gatekeeper
- Alpaca integration is scaffolded for paper mode only
- This repository is for educational simulation, not investment advice

## Current scaffold status

Implemented:

- Multi-user data model with user-isolated portfolios
- Portfolio creation and editable rule defaults by risk profile
- Order, trade, queued trade, AI decision, news, report, and audit log models
- FastAPI routes for auth, dashboard, portfolios, settings, trades, and reports
- Service abstractions for auth, portfolios, AI, news, broker, rules, dashboard, and reporting
- APScheduler stubs for intraday checks, evening scans, market-open queued orders, and daily reports at about 3:10 PM Central
- Next.js frontend skeleton with login, register, dashboard, portfolio detail, rules, trades, and reports pages

Stubbed on purpose:

- Real JWT request auth middleware
- Real Alpaca paper API HTTP client calls
- Real local LLM inference adapter
- Real RSS/news feed ingestion pipeline
- Alembic migrations
- Full frontend forms, mutations, and charts
- Market calendar holiday awareness

## Assumptions

- Scheduling and display should use Central Time where relevant.
- Market hours are approximated as 8:30 AM to 3:00 PM Central for the MVP.
- The app will run on a home server behind the user’s own network, reverse proxy, or VPN.
- Commission-free enforcement will depend on the broker/account capabilities and should be verified at integration time.
- The initial version uses APScheduler for simplicity, though Celery + Redis can be swapped in later if workload grows.
- Auth routes currently issue tokens, but authenticated API access is temporarily stubbed with the `X-User-Id` header to keep the scaffold runnable while the rest of the system is wired up.

## Backend setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Copy environment variables:

```bash
cp .env.example .env
```

4. Update `.env` with your PostgreSQL, Redis, JWT, and Alpaca paper credentials.
5. Create the PostgreSQL database.
6. Start the backend:

```bash
uvicorn app.main:app --reload
```

## Frontend setup

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Set the API base URL:

```bash
echo 'NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1' > .env.local
```

3. Start the frontend:

```bash
npm run dev
```

## Home server deployment notes

- Use Docker Compose or systemd services for FastAPI, PostgreSQL, Redis, and the frontend.
- Put the app behind a reverse proxy like Nginx, Caddy, or Traefik.
- Use HTTPS even on a private network if remote access is possible.
- Restrict access with VPN, Tailscale, or firewall rules if hosted at home.
- Keep Alpaca credentials in environment variables only.
- Add backup and log-rotation policies before storing meaningful historical data.

## Suggested next steps

1. Add Alembic migrations and seed data.
2. Replace the header-based auth stub with JWT bearer authentication.
3. Implement Alpaca paper endpoints and order fill synchronization.
4. Add a real market calendar and holiday-aware scheduler.
5. Build ingestion jobs for RSS/Yahoo-compatible news feeds with deduplication.
6. Wire a real local LLM adapter into the AI service abstraction.
7. Add portfolio analytics, charts, and report tables on the frontend.

## Example API surface

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/dashboard`
- `GET /api/v1/portfolios`
- `POST /api/v1/portfolios`
- `GET /api/v1/portfolios/{portfolio_id}`
- `PUT /api/v1/portfolios/{portfolio_id}/rules`
- `GET /api/v1/settings/risk-profile-defaults`
- `GET /api/v1/trades/orders`
- `POST /api/v1/trades/orders`
- `GET /api/v1/trades/queued`
- `GET /api/v1/trades`
- `GET /api/v1/reports`
- `GET /api/v1/reports/{report_id}`
- `POST /api/v1/reports/generate?portfolio_id=1`
