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
- Database: SQLAlchemy with SQLite for local demo mode and PostgreSQL-ready configuration
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
- Next.js dashboard, portfolio management, portfolio tuning, rules, trades, AI decisions, benchmark comparison, and reports pages
- Local database initializer with demo user, portfolio, positions, news, AI decision, and benchmarks
- Manual local job endpoints for intraday analysis, evening scans, queued orders, and reports
- Built-in backend smoke tests using `unittest` and in-process ASGI requests

Stubbed on purpose:

- Real JWT request auth middleware
- Alembic migrations for production-grade schema upgrades
- Full charting-library integration
- Market calendar holiday awareness

## Assumptions

- Scheduling and display should use Central Time where relevant.
- Market hours are approximated as 8:30 AM to 3:00 PM Central for the MVP.
- The app will run on a home server behind the user’s own network, reverse proxy, or VPN.
- Commission-free enforcement will depend on the broker/account capabilities and should be verified at integration time.
- The initial version uses APScheduler for simplicity, though Celery + Redis can be swapped in later if workload grows.
- Auth routes currently issue tokens, but authenticated API access is temporarily stubbed with the `X-User-Id` header to keep the scaffold runnable while the rest of the system is wired up.

## Local setup

The local demo path uses SQLite and does not require real Alpaca credentials. API calls use the temporary demo auth header `X-User-Id: 1`; CSV report downloads can also use `?user_id=1`.

### Backend install

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

4. For local demo mode, keep:

```bash
DATABASE_URL=sqlite:///./paper_hedge_fund.sqlite3
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_API_KEY=paper-key
ALPACA_API_SECRET=paper-secret
OLLAMA_MODEL=qwen3:8b
```

5. Initialize the database and seed demo data:

```bash
PYTHONPATH=. python scripts/init_db.py
```

6. Optional: start Ollama and pull the local model:

```bash
ollama pull qwen3:8b
ollama serve
```

If Ollama is not running, the backend logs a warning and returns deterministic fallback AI suggestions.

7. Start the backend:

```bash
uvicorn app.main:app --reload
```

The backend will also create tables and seed demo data at startup when needed.

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

### Frontend install

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

Open `http://localhost:3000/dashboard`.

### Local network access

Use your machine's LAN IP address in place of `YOUR_LAN_IP`.

Backend:

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```bash
cd frontend
echo 'NEXT_PUBLIC_API_BASE_URL=http://YOUR_LAN_IP:8000/api/v1' > .env.local
npm run dev -- --hostname 0.0.0.0 --port 3000
```

Then open `http://YOUR_LAN_IP:3000/dashboard` from another device on the same network.

## Portfolio management

- Use `/dashboard` to switch into a portfolio from the selector.
- Use `/portfolios` to view all paper portfolios for the current `X-User-Id: 1` account and create new ones.
- Portfolio cards show risk profile, initial paper investment, current value, daily gain/loss, total return, benchmark comparison when available, and active/paused status.
- Use `/portfolios/{id}` for holdings, allocation bars, queued trades, recent trades, AI decisions with reasoning, benchmark performance, matching news, latest report link, and action buttons.
- Use `/portfolios/{id}/settings` or the Tuning section on the detail page to edit risk profile, trade limits, cash reserve, concentration, ticker allow/block lists, ETF permission, after-hours scanning, queueing behavior, aggressiveness, and active/paused state.

Create portfolio validation is handled in the frontend for required names, positive initial paper investment, percentage ranges, non-negative trade limits, and uppercase ticker normalization.

## Demo mode

The app works without real Alpaca credentials or Ollama running.

- Missing Alpaca credentials keep the app in local paper/demo mode.
- Missing Ollama produces deterministic fallback AI suggestions and a backend warning.
- Demo seed data includes a user, a balanced paper portfolio, positions, news, an AI decision, reports, and benchmark snapshots.
- Portfolio action buttons return useful demo results and never submit live trades.

Buttons that benefit from real services:

- `Run AI analysis now`: uses Ollama when available; otherwise fallback suggestions.
- `Generate daily report now`: works locally and includes demo benchmark/news data when live feeds are unavailable.
- `Rebalance now`: currently queues a demo paper trade for next open.
- `Pause portfolio`, `Resume portfolio`, and `Clear queued trades`: work locally.
- Benchmark refresh uses local/mock-compatible benchmark logic when live market data is unavailable.

## Smoke tests

Run backend smoke checks:

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. python scripts/smoke_backend.py
PYTHONPATH=. python -m unittest discover -s tests
```

Run compile and frontend build checks:

```bash
cd backend
source .venv/bin/activate
python -m compileall app scripts tests

cd ../frontend
npm run build
```

## Manual local actions

The frontend includes buttons for common demo actions:

- AI Decisions: `Run AI Analysis`, `Debug Sample`
- Benchmarks: `Refresh Benchmarks`
- Reports: `Generate Report`
- Trades: `Run Queued Orders`
- Settings: `Run Intraday Analysis`, `Run Evening Scan`, `Daily Reports`

Equivalent API calls:

```bash
curl -H 'X-User-Id: 1' http://localhost:8000/api/v1/dashboard
curl -X POST -H 'X-User-Id: 1' 'http://localhost:8000/api/v1/ai/analyze?portfolio_id=1'
curl -X POST -H 'X-User-Id: 1' 'http://localhost:8000/api/v1/ai/debug-sample'
curl -X POST -H 'X-User-Id: 1' 'http://localhost:8000/api/v1/portfolios/1/benchmarks/refresh'
curl -X PATCH -H 'Content-Type: application/json' -H 'X-User-Id: 1' -d '{"risk_profile":"balanced"}' 'http://localhost:8000/api/v1/portfolios/1'
curl -X POST -H 'X-User-Id: 1' 'http://localhost:8000/api/v1/portfolios/1/run-analysis'
curl -X POST -H 'X-User-Id: 1' 'http://localhost:8000/api/v1/portfolios/1/rebalance'
curl -X POST -H 'X-User-Id: 1' 'http://localhost:8000/api/v1/portfolios/1/generate-report'
curl -X POST -H 'X-User-Id: 1' 'http://localhost:8000/api/v1/portfolios/1/pause'
curl -X POST -H 'X-User-Id: 1' 'http://localhost:8000/api/v1/portfolios/1/resume'
curl -X DELETE -H 'X-User-Id: 1' 'http://localhost:8000/api/v1/portfolios/1/queued-trades'
curl -X POST -H 'X-User-Id: 1' 'http://localhost:8000/api/v1/reports/generate?portfolio_id=1'
curl -X POST -H 'X-User-Id: 1' 'http://localhost:8000/api/v1/jobs/intraday-analysis'
curl -X POST -H 'X-User-Id: 1' 'http://localhost:8000/api/v1/jobs/evening-scan'
curl -X POST -H 'X-User-Id: 1' 'http://localhost:8000/api/v1/jobs/queued-orders'
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
5. Add richer charts and historical performance curves.
6. Add Alembic migrations for production database upgrades.

## Example API surface

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/dashboard`
- `GET /api/v1/ai/decisions`
- `POST /api/v1/ai/analyze?portfolio_id=1`
- `POST /api/v1/ai/debug-sample`
- `POST /api/v1/jobs/intraday-analysis`
- `POST /api/v1/jobs/evening-scan`
- `POST /api/v1/jobs/queued-orders`
- `POST /api/v1/jobs/daily-reports`
- `GET /api/v1/news`
- `GET /api/v1/portfolios`
- `POST /api/v1/portfolios`
- `GET /api/v1/portfolios/{portfolio_id}`
- `PATCH /api/v1/portfolios/{portfolio_id}`
- `GET /api/v1/portfolios/{portfolio_id}/rules`
- `PATCH /api/v1/portfolios/{portfolio_id}/rules`
- `PUT /api/v1/portfolios/{portfolio_id}/rules`
- `POST /api/v1/portfolios/{portfolio_id}/run-analysis`
- `POST /api/v1/portfolios/{portfolio_id}/rebalance`
- `POST /api/v1/portfolios/{portfolio_id}/generate-report`
- `POST /api/v1/portfolios/{portfolio_id}/pause`
- `POST /api/v1/portfolios/{portfolio_id}/resume`
- `DELETE /api/v1/portfolios/{portfolio_id}/queued-trades`
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
