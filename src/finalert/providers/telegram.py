from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from finalert.exceptions import DeliveryError
from finalert.providers.base import Provider


class TelegramProvider(Provider):
    def __init__(self, token: str, chat_id: str, *, timeout: float = 10.0) -> None:
        self.token = token
        self.chat_id = chat_id
        self.timeout = timeout

    def send(self, title: str, message: str) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = urlencode(
            {"chat_id": self.chat_id, "text": f"{title}\n\n{message}"}
        ).encode("utf-8")
        request = Request(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            raise DeliveryError(f"Telegram returned HTTP {exc.code}") from exc
        except URLError as exc:
            raise DeliveryError(f"Telegram request failed: {exc.reason}") from exc

        try:
            result = json.loads(body)
        except json.JSONDecodeError as exc:
            raise DeliveryError("Telegram returned an invalid response") from exc
        if not result.get("ok"):
            description = result.get("description", "unknown Telegram error")
            raise DeliveryError(str(description))
