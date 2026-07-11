from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from finalert.exceptions import DeliveryError
from finalert.providers.base import Provider


class WebhookProvider(Provider):
    def __init__(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout

    def send(self, title: str, message: str) -> None:
        payload = json.dumps({"title": title, "message": message}).encode("utf-8")
        headers = {"Content-Type": "application/json", **self.headers}
        request = Request(self.url, data=payload, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                status = getattr(response, "status", 200)
                if not 200 <= status < 300:
                    raise DeliveryError(f"Webhook returned HTTP {status}")
        except HTTPError as exc:
            raise DeliveryError(f"Webhook returned HTTP {exc.code}") from exc
        except URLError as exc:
            raise DeliveryError(f"Webhook request failed: {exc.reason}") from exc
