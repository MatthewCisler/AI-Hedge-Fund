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


class BaseBrokerService:
    def submit_market_order(self, *, ticker: str, side: str, quantity: float) -> BrokerOrderResult:
        raise NotImplementedError

    def latest_price(self, ticker: str) -> float | None:
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

    def _configured(self) -> bool:
        return settings.alpaca_api_key != "paper-key" and settings.alpaca_api_secret != "paper-secret"

    def _assert_paper_only(self) -> None:
        if "paper-api.alpaca.markets" not in self.base_url:
            raise RuntimeError("Refusing to use a non-paper Alpaca trading endpoint.")

    def submit_market_order(self, *, ticker: str, side: str, quantity: float) -> BrokerOrderResult:
        self._assert_paper_only()
        if not self._configured():
            logger.info("Alpaca paper credentials not configured; simulating paper order for %s.", ticker)
            return BrokerOrderResult(
                status="submitted",
                broker_order_id=f"simulated-paper-{ticker.lower()}-{side}",
                message="Local simulated paper order. Configure Alpaca paper keys for API submission.",
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
            return BrokerOrderResult(status="submitted", broker_order_id=payload.get("id"), message="Submitted.")
        except Exception as exc:
            logger.warning("Alpaca paper order failed: %s", exc)
            return BrokerOrderResult(status="rejected", message=str(exc))

    def latest_price(self, ticker: str) -> float | None:
        if not self._configured():
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
        if not self._configured():
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
        if not self._configured():
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
