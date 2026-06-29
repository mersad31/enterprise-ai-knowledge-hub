import json
import logging
import sys
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON for production tooling."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)


        # Attach any extra fields passed via logger.info(..., extra={...})
        for key, value in record.__dict__.items():
            if key not in _RESERVED_KEYS:
                log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False)


_RESERVED_KEYS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
}

def setup_logging(debug: bool = False) -> None:
    """Configure the root logger once at application startup."""
    log_level = logging.DEBUG if debug else logging.INFO

    # Console handler with JSON output
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear() # avoid duplicate handlers on reload
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    # Silence overly chatty third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)