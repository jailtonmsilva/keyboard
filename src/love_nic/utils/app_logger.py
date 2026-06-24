"""Logging de runtime para o Love Nic."""

from __future__ import annotations

import logging
import re
import sys
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_NAME = "love_nic"


class _LoveNicFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created)
        record.log_datetime = timestamp.strftime("%d/%m/%Y %H:%M:%S")
        record.level_padded = f"{record.levelname:<7}"

        if not hasattr(record, "source"):
            record.source = "APP"
        source_name = str(record.source)
        record.source_field = f"[{source_name}]"
        record.source_padding = " " * max(0, 8 - len(source_name))

        if not hasattr(record, "message_text"):
            record.message_text = record.getMessage()
        if not hasattr(record, "context_text"):
            record.context_text = ""

        return super().format(record)


def _logs_dir() -> Path:
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parents[3]

    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def _build_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_filename = datetime.now().strftime("%Y-%m-%d-love_nic.log")
    log_path = _logs_dir() / log_filename
    handler = RotatingFileHandler(log_path, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    formatter = _LoveNicFormatter(
        "%(log_datetime)s [%(level_padded)s] %(source_field)s%(source_padding)s -> %(message_text)s%(context_text)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def get_logger() -> logging.Logger:
    return _build_logger()


def _format_context_value(value) -> str:
    text = str(value)
    if re.fullmatch(r"[A-Za-z0-9_.-]+", text):
        return text
    return f'"{text}"'


def _serialize_context(context: dict[str, object] | None) -> str:
    if not context:
        return ""

    parts = [f"{key}={_format_context_value(value)}" for key, value in context.items()]
    return " | " + " ".join(parts)


def log_event(
    *,
    source: str,
    message: str,
    level: int = logging.INFO,
    context: dict[str, object] | None = None,
    exc_info=None,
) -> None:
    logger = get_logger()
    logger.log(
        level,
        message,
        exc_info=exc_info,
        extra={
            "source": source,
            "message_text": message,
            "context_text": _serialize_context(context),
        },
    )


def install_global_exception_logging() -> None:
    previous_hook = sys.excepthook

    def _excepthook(exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            previous_hook(exc_type, exc_value, exc_traceback)
            return

        log_event(
            source="APP",
            message="Excecao nao tratada durante execucao.",
            level=logging.ERROR,
            context={
                "status": "UNKNOWN",
                "erro": f"{exc_type.__name__}: {exc_value}",
            },
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        previous_hook(exc_type, exc_value, exc_traceback)

    sys.excepthook = _excepthook

    if hasattr(threading, "excepthook"):
        previous_thread_hook = threading.excepthook

        def _threading_excepthook(args) -> None:
            log_event(
                source="APP",
                message="Excecao nao tratada em thread.",
                level=logging.ERROR,
                context={
                    "status": "UNKNOWN",
                    "erro": f"{args.exc_type.__name__}: {args.exc_value}",
                },
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )
            previous_thread_hook(args)

        threading.excepthook = _threading_excepthook
