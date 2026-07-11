from __future__ import annotations

import logging
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from finalert.config import provider_from_env
from finalert.providers import Provider

logger = logging.getLogger("finalert")


def _script_name() -> str:
    if not sys.argv or not sys.argv[0]:
        return "Python job"
    return Path(sys.argv[0]).name or "Python job"


def _format_duration(seconds: float) -> str:
    total = max(0, round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _resolve_provider(provider: str | Provider | None) -> Provider:
    if isinstance(provider, Provider):
        return provider
    return provider_from_env(provider)


def notify(
    message: str | None = None,
    *,
    title: str | None = None,
    provider: str | Provider | None = None,
) -> bool:
    """Send a best-effort notification and return whether it was delivered."""
    job = _script_name()
    final_title = title or f"✅ {job} completed"
    final_message = message or f"{job} reached the end of the program."
    try:
        _resolve_provider(provider).send(final_title, final_message)
    except Exception as exc:
        logger.warning("Notification could not be sent: %s", exc)
        return False
    return True


@contextmanager
def watch(
    name: str | None = None,
    *,
    provider: str | Provider | None = None,
) -> Iterator[None]:
    """Notify when the wrapped block succeeds or raises an exception."""
    job = name or _script_name()
    started = time.monotonic()
    try:
        yield
    except BaseException as exc:
        elapsed = _format_duration(time.monotonic() - started)
        notify(
            f"Duration: {elapsed}\nError: {type(exc).__name__}: {exc}",
            title=f"❌ {job} failed",
            provider=provider,
        )
        raise
    else:
        elapsed = _format_duration(time.monotonic() - started)
        notify(
            f"Duration: {elapsed}",
            title=f"✅ {job} completed",
            provider=provider,
        )
