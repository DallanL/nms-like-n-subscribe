import logging
import sys

from colorlog import ColoredFormatter
from .config import Config


def setup_logging():
    """
    Configures logging with structured JSON output.

    Expected Config variables:
      - LOG_LEVEL: Logging level (e.g., "INFO", "DEBUG")
      - LOG_FILE: (Optional) File path to log to. If empty or not set, only stdout is used.
    """
    # Get log level and file path from Config
    log_level = (Config.LOG_LEVEL or "INFO").upper()
    log_file = Config.LOG_FILE if hasattr(Config, "LOG_FILE") else None

    # Get the root logger and set its log level
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove any existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create a StreamHandler for stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)

    # Create a formatter for structured logs
    formatter = ColoredFormatter(
        fmt="%(asctime)s - %(name)s - %(log_color)s%(levelname)s%(reset)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "blue",
            "INFO": "green",
            "WARNING": "bold_yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Optionally add a FileHandler if LOG_FILE is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.info(
        "Logging configuration complete",
        extra={"log_level": log_level, "log_file": log_file},
    )


if __name__ == "__main__":
    setup_logging()
    logging.info("This is a test log message")
