import logging

import structlog

REDACT = {"password", "new_password", "current_password", "token", "refresh", "access", "temp_password"}


def _redact(_, __, event_dict):
    for k in list(event_dict):
        if k in REDACT:
            event_dict[k] = "***"
    return event_dict


def setup(level: str = "info") -> None:
    logging.basicConfig(level=level.upper(), format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact,
            structlog.processors.JSONRenderer(),
        ],
    )
