import sys
import logging
from loguru import logger
from pathlib import Path

MAIN_DIR = Path(__file__).parent.parent.parent


class InterceptHandler(logging.Handler):
    LEVELS_MAP = {
        logging.CRITICAL: "CRITICAL",
        logging.ERROR: "ERROR",
        logging.WARNING: "WARNING",
        logging.INFO: "INFO",
        logging.DEBUG: "DEBUG",
    }

    def _get_level(self, record):
        return self.LEVELS_MAP.get(record.levelno, record.levelno)

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def error_filter(record):
    return record["level"].name in ["ERROR", "CRITICAL"]


def not_error_filter(record):
    return record["level"].name not in ["ERROR", "CRITICAL"]


logger.remove()
format_string = ("<white>{time:YYYY-MM-DD HH:mm:ss}</white> | <level>{level: <8}</level> | "
                 "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.add(sys.stderr, format=format_string)
logger.add(MAIN_DIR / "general.log", filter=not_error_filter, format=format_string)
logger.add(MAIN_DIR / "errors.log", filter=error_filter, format=format_string)

__all__ = [
    "logger",
    "InterceptHandler"
]
