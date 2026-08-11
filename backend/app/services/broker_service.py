"""Paper broker abstraction for Alpaca."""

import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class BrokerOrderResult:
    status: str
    broker_order_id: str | None = None
    message: str | None = None
    filled_quantity: float = 0
    filled_average_price: float | None = None
    simulated: bool = False
    raw_status: str | None = None


class BaseBrokerService:
    def submit_market_order(self, *, ticker: str, side: str, quantity: float) -> BrokerOrderResult:
        raise NotImplementedError

    def latest_price(self, ticker: str) -> float | None:
        raise NotImplementedError

    def get_order(self, broker_order_id: str) -> BrokerOrderResult:
        raise NotImplementedError

    def is_configured(self) -> bool:
        raise NotImplementedError

    def account_snapshot(self) -> dict:
        raise NotImplementedError

    def average_daily_volume(self, ticker: str) -> int:
        raise NotImplementedError

    def asset_is_tradable_us_equity_or_etf(self, ticker: str) -> tuple[bool, str | None, str | None]:
        raise NotImplementedError


class AlpacaPaperBrokerService(BaseBrokerService):
    """Alpaca adapter that refuses non-paper trading endpoints."""

    def __init__(self) -> None:
        self.base_url = settings.alpaca_base_url.rstrip("/")
        self.data_url = settings.alpaca_data_url.rstrip("/")
        self.headers = {
            "APCA-API-KEY-ID": settings.alpaca_api_key,
            "APCA-API-SECRET-KEY": settings.alpaca_api_secret,
        }

    def is_configured(self) -> bool:
        return settings.alpaca_api_key != "paper-key" and settings.alpaca_api_secret != "paper-secret"

    def _assert_paper_only(self) -> None:
        if "paper-api.alpaca.markets" not in self.base_url:
            raise RuntimeError("Refusing to use a non-paper Alpaca trading endpoint.")

    def account_snapshot(self) -> dict:
        self._assert_paper_only()
        if not self.is_configured():
            return {
                "status": "demo", "connected": False, "mode": "demo-simulation",
                "buying_power": None, "cash": None, "portfolio_value": None,
                "positions": [], "orders": [], "fills": [],
            }
        try:
            account_response = httpx.get(f"{self.base_url}/v2/account", headers=self.headers, timeout=20)
            account_response.raise_for_status()
            positions_response = httpx.get(f"{self.base_url}/v2/positions", headers=self.headers, timeout=20)
            positions_response.raise_for_status()
            orders_response = httpx.get(
                f"{self.base_url}/v2/orders", headers=self.headers,
                params={"status": "all", "limit": 100, "direction": "desc"}, timeout=20,
            )
            orders_response.raise_for_status()
            account = account_response.json()
            positions = positions_response.json()
            orders = orders_response.json()
            safe_orders = [{
                "id": item.get("id"), "symbol": item.get("symbol"), "side": item.get("side"),
                "qty": item.get("qty"), "filled_qty": item.get("filled_qty"),
                "filled_avg_price": item.get("filled_avg_price"), "status": item.get("status"),
                "submitted_at": item.get("submitted_at"), "filled_at": item.get("filled_at"),
            } for item in orders]
            return {
                "status": "connected", "connected": True, "mode": "alpaca-paper",
                "buying_power": float(account.get("buying_power") or 0),
                "cash": float(account.get("cash") or 0),
                "portfolio_value": float(account.get("portfolio_value") or 0),
                "positions": [{
                    "symbol": item.get("symbol"), "qty": item.get("qty"),
                    "market_value": item.get("market_value"), "current_price": item.get("current_price"),
                    "unrealized_pl": item.get("unrealized_pl"),
                } for item in positions],
                "orders": safe_orders,
                "fills": [item for item in safe_orders if item["status"] == "filled"],
            }
        except httpx.HTTPStatusError as exc:
            logger.warning("Alpaca paper account check failed with HTTP %s.", exc.response.status_code)
            return {"status": "disconnected", "connected": False, "mode": "alpaca-paper", "failure_category": "http_error"}
        except httpx.HTTPError as exc:
            logger.warning("Alpaca paper account check failed: %s", type(exc).__name__)
            return {"status": "disconnected", "connected": False, "mode": "alpaca-paper", "failure_category": "unavailable"}

    def submit_market_order(self, *, ticker: str, side: str, quantity: float) -> BrokerOrderResult:
        self._assert_paper_only()
        if not self.is_configured():
            logger.info("Alpaca paper credentials not configured; simulating paper order for %s.", ticker)
            return BrokerOrderResult(
                status="filled",
                broker_order_id=f"simulated-paper-{ticker.lower()}-{side}",
                message="Local simulated paper order. Configure Alpaca paper keys for API submission.",
                filled_quantity=quantity,
                simulated=True,
                raw_status="simulated_fill",
            )

        try:
            response = httpx.post(
                f"{self.base_url}/v2/orders",
                headers=self.headers,
                json={
                    "symbol": ticker.upper(),
                    "qty": str(quantity),
                    "side": side,
                    "type": "market",
                    "time_in_force": "day",
                },
                timeout=20,
            )
            payload = response.json()
            if response.status_code >= 400:
                return BrokerOrderResult(status="rejected", message=str(payload))
            return self._parse_order(payload)
        except Exception as exc:
            logger.warning("Alpaca paper order failed: %s", exc)
            return BrokerOrderResult(status="rejected", message=str(exc))

    def get_order(self, broker_order_id: str) -> BrokerOrderResult:
        self._assert_paper_only()
        if not self.is_configured():
            return BrokerOrderResult(status="unavailable", message="Alpaca paper credentials are not configured.")
        try:
            response = httpx.get(
                f"{self.base_url}/v2/orders/{broker_order_id}", headers=self.headers, timeout=20
            )
            payload = response.json()
            if response.status_code >= 400:
                return BrokerOrderResult(status="unavailable", broker_order_id=broker_order_id, message=str(payload))
            return self._parse_order(payload)
        except Exception as exc:
            logger.warning("Unable to synchronize Alpaca paper order %s: %s", broker_order_id, exc)
            return BrokerOrderResult(status="unavailable", broker_order_id=broker_order_id, message=str(exc))

    def _parse_order(self, payload: dict) -> BrokerOrderResult:
        raw_status = str(payload.get("status") or "unknown").lower()
        if raw_status == "filled":
            status = "filled"
        elif raw_status in {"canceled", "expired", "replaced"}:
            status = "canceled"
        elif raw_status in {"rejected", "stopped"}:
            status = "rejected"
        else:
            status = "submitted"
        filled_quantity = float(payload.get("filled_qty") or 0)
        filled_price = payload.get("filled_avg_price")
        return BrokerOrderResult(
            status=status,
            broker_order_id=payload.get("id"),
            message=str(payload.get("reject_reason") or raw_status),
            filled_quantity=filled_quantity,
            filled_average_price=float(filled_price) if filled_price not in (None, "") else None,
            raw_status=raw_status,
        )

    def latest_price(self, ticker: str) -> float | None:
        if not self.is_configured():
            return None
        try:
            response = httpx.get(
                f"{self.data_url}/v2/stocks/{ticker.upper()}/trades/latest",
                headers=self.headers,
                timeout=15,
            )
            response.raise_for_status()
            price = response.json().get("trade", {}).get("p")
            return float(price) if price is not None else None
        except Exception as exc:
            logger.info("Unable to fetch latest price for %s: %s", ticker, exc)
            return None

    def average_daily_volume(self, ticker: str) -> int:
        if not self.is_configured():
            return 1_000_000
        try:
            response = httpx.get(
                f"{self.data_url}/v2/stocks/{ticker.upper()}/bars",
                headers=self.headers,
                params={"timeframe": "1Day", "limit": 10, "adjustment": "raw"},
                timeout=15,
            )
            response.raise_for_status()
            bars = response.json().get("bars", [])
            if not bars:
                return 0
            return int(sum(float(bar.get("v", 0)) for bar in bars) / len(bars))
        except Exception as exc:
            logger.info("Unable to fetch volume for %s: %s", ticker, exc)
            return 1_000_000

    def asset_is_tradable_us_equity_or_etf(self, ticker: str) -> tuple[bool, str | None, str | None]:
        if not self.is_configured():
            return True, None, "stock"
        try:
            response = httpx.get(f"{self.base_url}/v2/assets/{ticker.upper()}", headers=self.headers, timeout=15)
            response.raise_for_status()
            asset = response.json()
            asset_class = str(asset.get("class", ""))
            exchange = str(asset.get("exchange", ""))
            tradable = bool(asset.get("tradable"))
            valid = tradable and asset_class == "us_equity" and exchange in {"NYSE", "NASDAQ", "AMEX", "ARCA", "BATS"}
            return valid, asset.get("name"), "etf" if exchange == "ARCA" else "stock"
        except Exception as exc:
            logger.info("Unable to verify asset %s: %s", ticker, exc)
            return False, None, None


broker_service: BaseBrokerService = AlpacaPaperBrokerService()
