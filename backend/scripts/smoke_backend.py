"""Run local backend API smoke checks without starting a network server."""

import asyncio

import httpx

from app.db.init_db import create_database_schema, seed_demo_data
from app.db.session import SessionLocal
from app.main import app
from app.core.security import create_access_token


SMOKE_GET_PATHS = [
    "/health",
    "/api/v1/dashboard",
    "/api/v1/portfolios",
    "/api/v1/portfolios/1",
    "/api/v1/portfolios/1/rules",
    "/api/v1/trades/orders",
    "/api/v1/trades/queued",
    "/api/v1/trades",
    "/api/v1/ai/decisions",
    "/api/v1/ai/status",
    "/api/v1/trades/broker/status",
    "/api/v1/settings/system-status",
    "/api/v1/reports",
    "/api/v1/settings/risk-profile-defaults",
]


async def run() -> None:
    create_database_schema()
    with SessionLocal() as db:
        seed_demo_data(db)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers = {"Authorization": f"Bearer {create_access_token('1')}"}
        for path in SMOKE_GET_PATHS:
            response = await client.get(path, headers=headers)
            response.raise_for_status()
            print(f"GET {path}: {response.status_code}")

        posts = [
            "/api/v1/ai/debug-sample",
            "/api/v1/trades/orders/sync",
            "/api/v1/portfolios/1/run-analysis",
            "/api/v1/portfolios/1/rebalance",
            "/api/v1/portfolios/1/generate-report",
            "/api/v1/portfolios/1/pause",
            "/api/v1/portfolios/1/resume",
            "/api/v1/reports/generate?portfolio_id=1",
            "/api/v1/jobs/daily-reports",
        ]
        for path in posts:
            response = await client.post(path, headers=headers)
            response.raise_for_status()
            print(f"POST {path}: {response.status_code}")

        response = await client.delete("/api/v1/portfolios/1/queued-trades", headers=headers)
        response.raise_for_status()
        print(f"DELETE /api/v1/portfolios/1/queued-trades: {response.status_code}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
