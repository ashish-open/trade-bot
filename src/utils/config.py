"""
Configuration management for the trading bot.
Loads settings from .env file and provides typed access.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class PolymarketConfig(BaseSettings):
    """Polymarket-specific configuration."""

    private_key: str = Field(
        default="",
        alias="POLYMARKET_PRIVATE_KEY",
        description="Your Ethereum private key for signing transactions",
    )
    wallet_address: str = Field(
        default="",
        alias="POLYMARKET_WALLET_ADDRESS",
        description="Your public wallet address",
    )
    clob_url: str = Field(
        default="https://clob.polymarket.com",
        alias="POLYMARKET_CLOB_URL",
    )
    gamma_url: str = Field(
        default="https://gamma-api.polymarket.com",
        alias="POLYMARKET_GAMMA_URL",
    )
    data_url: str = Field(
        default="https://data-api.polymarket.com",
        alias="POLYMARKET_DATA_URL",
    )
    chain_id: int = Field(
        default=137,
        alias="POLYMARKET_CHAIN_ID",
        description="137 = Polygon mainnet",
    )

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def has_credentials(self) -> bool:
        """Check if private key and wallet address are configured."""
        return bool(self.private_key) and bool(self.wallet_address)


class BotConfig(BaseSettings):
    """Top-level bot configuration."""

    trading_mode: str = Field(
        default="paper",
        alias="TRADING_MODE",
        description="'paper' for simulated trading, 'live' for real money",
    )
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def is_paper_mode(self) -> bool:
        return self.trading_mode.lower() == "paper"


# Singleton instances — import these directly
polymarket_config = PolymarketConfig()
bot_config = BotConfig()
