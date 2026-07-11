from __future__ import annotations

import json
import os
from collections.abc import Mapping

from finalert.exceptions import ConfigurationError
from finalert.providers import (
    EmailProvider,
    Provider,
    PushPlusProvider,
    TelegramProvider,
    WebhookProvider,
)


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise ConfigurationError(f"Missing required environment variable: {name}")
    return value


def _boolean(env: Mapping[str, str], name: str, default: bool) -> bool:
    raw = env.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"{name} must be true or false")


def _timeout(env: Mapping[str, str]) -> float:
    raw = env.get("FINALERT_TIMEOUT", "10")
    try:
        timeout = float(raw)
    except ValueError as exc:
        raise ConfigurationError("FINALERT_TIMEOUT must be a number") from exc
    if timeout <= 0:
        raise ConfigurationError("FINALERT_TIMEOUT must be greater than zero")
    return timeout


def provider_from_env(
    provider_name: str | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Provider:
    values = os.environ if env is None else env
    name = (provider_name or values.get("FINALERT_PROVIDER", "")).strip().lower()
    if not name:
        raise ConfigurationError(
            "No provider selected. Set FINALERT_PROVIDER to telegram, email, "
            "webhook, or pushplus."
        )

    timeout = _timeout(values)

    if name == "telegram":
        return TelegramProvider(
            _required(values, "FINALERT_TELEGRAM_TOKEN"),
            _required(values, "FINALERT_TELEGRAM_CHAT_ID"),
            timeout=timeout,
        )

    if name == "pushplus":
        return PushPlusProvider(
            _required(values, "FINALERT_PUSHPLUS_TOKEN"),
            timeout=timeout,
        )

    if name == "webhook":
        url = _required(values, "FINALERT_WEBHOOK_URL")
        if not url.startswith(("http://", "https://")):
            raise ConfigurationError("FINALERT_WEBHOOK_URL must use http:// or https://")
        raw_headers = values.get("FINALERT_WEBHOOK_HEADERS", "{}").strip() or "{}"
        try:
            headers = json.loads(raw_headers)
        except json.JSONDecodeError as exc:
            raise ConfigurationError("FINALERT_WEBHOOK_HEADERS must be valid JSON") from exc
        if not isinstance(headers, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in headers.items()
        ):
            raise ConfigurationError(
                "FINALERT_WEBHOOK_HEADERS must be a JSON object of string values"
            )
        return WebhookProvider(url, headers=headers, timeout=timeout)

    if name == "email":
        host = _required(values, "FINALERT_SMTP_HOST")
        try:
            port = int(values.get("FINALERT_SMTP_PORT", "587"))
        except ValueError as exc:
            raise ConfigurationError("FINALERT_SMTP_PORT must be an integer") from exc
        recipients = [
            address.strip()
            for address in _required(values, "FINALERT_EMAIL_TO").split(",")
            if address.strip()
        ]
        if not recipients:
            raise ConfigurationError("FINALERT_EMAIL_TO must contain an email address")
        username = values.get("FINALERT_SMTP_USERNAME", "").strip() or None
        sender = values.get("FINALERT_EMAIL_FROM", "").strip() or username
        if not sender:
            raise ConfigurationError(
                "Set FINALERT_EMAIL_FROM or FINALERT_SMTP_USERNAME"
            )
        use_ssl = _boolean(values, "FINALERT_SMTP_SSL", False)
        starttls = _boolean(values, "FINALERT_SMTP_STARTTLS", not use_ssl)
        return EmailProvider(
            host,
            port,
            sender,
            recipients,
            username=username,
            password=values.get("FINALERT_SMTP_PASSWORD"),
            use_ssl=use_ssl,
            starttls=starttls,
            timeout=timeout,
        )

    raise ConfigurationError(
        f"Unsupported provider {name!r}. Choose telegram, email, webhook, or "
        "pushplus."
    )
