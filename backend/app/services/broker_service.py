"""Paper broker abstraction for Alpaca."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BrokerOrderResult:
    status: str
    broker_order_id: str | None = None
    message: str | None = None


class BaseBrokerService:
    def submit_market_order(self, *, ticker: str, side: str, quantity: float) -> BrokerOrderResult:
        raise NotImplementedError


class AlpacaPaperBrokerService(BaseBrokerService):
    """Intentionally stubbed to keep the scaffold safe and paper-only."""

    def submit_market_order(self, *, ticker: str, side: str, quantity: float) -> BrokerOrderResult:
        logger.info("Paper broker stub called for %s %s x %s", side, ticker, quantity)
        return BrokerOrderResult(
            status="submitted",
            broker_order_id=f"paper-{ticker.lower()}-{side}",
            message="Stubbed Alpaca paper order accepted.",
        )


broker_service: BaseBrokerService = AlpacaPaperBrokerService()
