"""Risk profile defaults."""

RISK_PROFILE_DEFAULTS = {
    "safe": {
        "max_position_size_pct": 8.0,
        "max_daily_trades": 2,
        "etf_allowed": True,
        "rebalance_threshold": 4.0,
        "sector_concentration_limit": 20.0,
        "minimum_liquidity_volume": 1_000_000,
        "allow_queued_after_hours": True,
        "cooldown_minutes_per_ticker": 120,
    },
    "balanced": {
        "max_position_size_pct": 12.0,
        "max_daily_trades": 4,
        "etf_allowed": True,
        "rebalance_threshold": 5.0,
        "sector_concentration_limit": 25.0,
        "minimum_liquidity_volume": 750_000,
        "allow_queued_after_hours": True,
        "cooldown_minutes_per_ticker": 90,
    },
    "risky": {
        "max_position_size_pct": 18.0,
        "max_daily_trades": 6,
        "etf_allowed": True,
        "rebalance_threshold": 7.5,
        "sector_concentration_limit": 35.0,
        "minimum_liquidity_volume": 300_000,
        "allow_queued_after_hours": True,
        "cooldown_minutes_per_ticker": 45,
    },
}
