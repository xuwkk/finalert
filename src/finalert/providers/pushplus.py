from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from finalert.exceptions import DeliveryError
from finalert.providers.base import Provider


_ERROR_MESSAGES = {
    900: "PushPlus account is temporarily restricted",
    903: "PushPlus message token is invalid",
    905: (
        "PushPlus account is not verified; complete PushPlus identity "
        "verification before sending messages"
    ),
}


class PushPlusProvider(Provider):
    """Send personal WeChat notifications through PushPlus."""

    endpoint = "https://www.pushplus.plus/send"

    def __init__(self, token: str, *, timeout: float = 10.0) -> None:
        self.token = token
        self.timeout = timeout

    def send(self, title: str, message: str) -> None:
        payload = json.dumps(
            {
                "token": self.token,
                "title": title,
                "content": message,
                "template": "txt",
                "channel": "wechat",
            }
        ).encode("utf-8")
        request = Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            raise DeliveryError(f"PushPlus returned HTTP {exc.code}") from exc
        except URLError as exc:
            raise DeliveryError(f"PushPlus request failed: {exc.reason}") from exc

        try:
            result = json.loads(body)
        except json.JSONDecodeError as exc:
            raise DeliveryError("PushPlus returned an invalid response") from exc
        if not isinstance(result, dict) or "code" not in result:
            raise DeliveryError("PushPlus returned an invalid response")
        if result["code"] != 200:
            detail = _ERROR_MESSAGES.get(result["code"])
            if detail is not None:
                raise DeliveryError(detail)
            raise DeliveryError(f"PushPlus returned error code {result['code']!r}")
