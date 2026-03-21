"""
Logging setup using loguru.
Provides structured, readable logs for the trading bot.
"""

import sys
from loguru import logger
from src.utils.config import bot_config


def setup_logger():
    """Configure the global logger."""
    # Remove default handler
    logger.remove()

    # Console output — human-readable format
    logger.add(
        sys.stdout,
        level=bot_config.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File output — for audit trail (rotates at 10MB, keeps 7 days)
    logger.add(
        "data/logs/trade_bot_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="7 days",
        compression="gz",
    )

    return logger


# Initialize on import
setup_logger()
