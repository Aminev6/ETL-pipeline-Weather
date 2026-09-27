"""Configure logging once for a command-line entry point."""

import logging

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging() -> None:
    """Attach a stream handler to the root logger if none exists yet."""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
