"""Logger configuration for the Cloud SQL CRUD application."""

import logging
import os


def get_logger(name=__name__):
    """
    Configures and returns a named logger instance.

    Sets the log level based on the LOG_LEVEL environment variable (defaulting to INFO).
    Adds a StreamHandler if the logger doesn't have any handlers yet.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    return logger
