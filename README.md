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
- AI: local Ollama adapter, defaulting to `qwen3:8b` at `http://localhost:11434`
- News: pluggable public RSS ingestion with URL deduplication and ticker inference
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
- Order, trade, queued trade, AI decision, news, benchmark, report, and audit log models
- FastAPI routes for auth, dashboard, portfolios, benchmarks, settings, trades, AI decisions, news, and reports
- Ollama-backed AI service abstraction with a deterministic fallback when the local model is unavailable
- RSS news ingestion that stores source, headline, URL, timestamp, summary, and inferred tickers
- Alpaca paper-trading abstraction that refuses non-paper trading endpoints
- Deterministic rules engine for cash, max position size, liquidity, daily trade count, ticker cooldown, ETF permission, and market-hours queueing
- APScheduler jobs for intraday analysis, evening scans, market-open queued orders, and daily reports at about 3:10 PM Central
- Next.js dashboard, rules, trades, AI decisions, benchmark comparison, and reports pages

Stubbed on purpose:

- Real JWT request auth middleware
- Alembic migrations
- Full frontend mutation forms and charts
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

4. Update `.env` with your database, JWT, Ollama, news RSS, and Alpaca paper credentials.
5. Start Ollama and pull the local model:

```bash
ollama pull qwen3:8b
ollama serve
```

6. Create the database if you use PostgreSQL. The local `.env` can point at SQLite for development.
7. Start the backend:

```bash
uvicorn app.main:app --reload
```

Key backend environment variables:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `ALPACA_BASE_URL=https://paper-api.alpaca.markets`
- `ALPACA_DATA_URL=https://data.alpaca.markets`
- `ALPACA_API_KEY`
- `ALPACA_API_SECRET`
- `LOCAL_AI_PROVIDER=ollama`
- `OLLAMA_URL=http://localhost:11434`
- `OLLAMA_MODEL=qwen3:8b`
- `NEWS_RSS_SOURCES=[...]`
- `MARKET_TIMEZONE=America/Chicago`

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
- Keep `ALPACA_BASE_URL` set to `https://paper-api.alpaca.markets`; the broker adapter refuses live endpoints.
- Add backup and log-rotation policies before storing meaningful historical data.

## Suggested next steps

1. Add Alembic migrations and seed data.
2. Replace the header-based auth stub with JWT bearer authentication.
3. Add Alpaca paper order fill synchronization.
4. Add a real market calendar and holiday-aware scheduler.
5. Add frontend mutation forms for report generation, AI analysis, and rules editing.
6. Add Alembic migrations for production database upgrades.

## Example API surface

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/dashboard`
- `GET /api/v1/ai/decisions`
- `POST /api/v1/ai/analyze?portfolio_id=1`
- `GET /api/v1/news`
- `GET /api/v1/portfolios`
- `POST /api/v1/portfolios`
- `GET /api/v1/portfolios/{portfolio_id}`
- `PUT /api/v1/portfolios/{portfolio_id}/rules`
- `GET /api/v1/portfolios/{portfolio_id}/benchmarks`
- `POST /api/v1/portfolios/{portfolio_id}/benchmarks/refresh`
- `GET /api/v1/settings/risk-profile-defaults`
- `GET /api/v1/trades/orders`
- `POST /api/v1/trades/orders`
- `GET /api/v1/trades/queued`
- `GET /api/v1/trades`
- `GET /api/v1/reports`
- `GET /api/v1/reports/{report_id}`
- `GET /api/v1/reports/{report_id}/csv`
- `POST /api/v1/reports/generate?portfolio_id=1`
