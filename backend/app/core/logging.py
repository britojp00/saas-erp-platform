import json
import logging
import sys
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.core.request_context import get_request_context


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "timestamp": datetime.now(UTC)
            .astimezone(ZoneInfo("America/Sao_Paulo"))
            .isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        ctx = get_request_context()
        if ctx.request_id:
            log_entry["request_id"] = ctx.request_id
        if ctx.tenant_id is not None:
            log_entry["tenant_id"] = ctx.tenant_id
        if ctx.user_id is not None:
            log_entry["user_id"] = ctx.user_id

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        for key in ("event", "method", "path", "status_code", "duration_ms"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = (
            datetime.now(UTC).astimezone(ZoneInfo("America/Sao_Paulo")).isoformat()
        )
        ctx = get_request_context()
        parts = [
            timestamp,
            record.levelname.ljust(8),
            record.name,
            record.getMessage(),
        ]
        if ctx.request_id:
            parts.append(f"request_id={ctx.request_id}")
        if ctx.tenant_id is not None:
            parts.append(f"tenant_id={ctx.tenant_id}")
        if ctx.user_id is not None:
            parts.append(f"user_id={ctx.user_id}")
        if record.exc_info and record.exc_info[0] is not None:
            parts.append(self.formatException(record.exc_info))
        return " ".join(parts)


def setup_logging(level: str = "INFO", json_format: bool = True) -> None:
    log_level = getattr(logging, level.upper(), logging.INFO)

    if json_format:
        formatter: logging.Formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).propagate = True

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
