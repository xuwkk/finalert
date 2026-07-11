from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.parse import parse_qs

from finalert.providers import (
    EmailProvider,
    PushPlusProvider,
    TelegramProvider,
    WebhookProvider,
)
from finalert.exceptions import DeliveryError


class Response:
    def __init__(self, body: bytes = b"", status: int = 200) -> None:
        self.body = body
        self.status = status

    def read(self) -> bytes:
        return self.body

    def __enter__(self) -> "Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class ProviderTests(unittest.TestCase):
    @patch("finalert.providers.webhook.urlopen")
    def test_webhook_posts_json(self, urlopen: MagicMock) -> None:
        urlopen.return_value = Response(status=204)
        provider = WebhookProvider("https://example.test/hook")

        provider.send("Done", "The job completed")

        request = urlopen.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(
            json.loads(request.data),
            {"title": "Done", "message": "The job completed"},
        )

    @patch("finalert.providers.telegram.urlopen")
    def test_telegram_posts_message(self, urlopen: MagicMock) -> None:
        urlopen.return_value = Response(b'{"ok": true}')
        provider = TelegramProvider("token", "123")

        provider.send("Done", "The job completed")

        request = urlopen.call_args.args[0]
        params = parse_qs(request.data.decode("utf-8"))
        self.assertEqual(params["chat_id"], ["123"])
        self.assertEqual(params["text"], ["Done\n\nThe job completed"])

    @patch("finalert.providers.telegram.urlopen")
    def test_telegram_http_error_does_not_expose_token(
        self, urlopen: MagicMock
    ) -> None:
        urlopen.side_effect = HTTPError(
            "https://api.telegram.org/botSECRET/sendMessage",
            401,
            "Unauthorized",
            {},
            None,
        )
        provider = TelegramProvider("SECRET", "123")

        with self.assertRaises(DeliveryError) as raised:
            provider.send("Done", "The job completed")

        self.assertEqual(str(raised.exception), "Telegram returned HTTP 401")
        self.assertNotIn("SECRET", str(raised.exception))

    @patch("finalert.providers.pushplus.urlopen")
    def test_pushplus_posts_personal_wechat_message(
        self, urlopen: MagicMock
    ) -> None:
        urlopen.return_value = Response(b'{"code": 200, "msg": "success"}')
        provider = PushPlusProvider("SECRET")

        provider.send("Done", "The job completed")

        request = urlopen.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.full_url, "https://www.pushplus.plus/send")
        self.assertEqual(
            json.loads(request.data),
            {
                "token": "SECRET",
                "title": "Done",
                "content": "The job completed",
                "template": "txt",
                "channel": "wechat",
            },
        )

    @patch("finalert.providers.pushplus.urlopen")
    def test_pushplus_api_error_does_not_expose_token(
        self, urlopen: MagicMock
    ) -> None:
        urlopen.return_value = Response(b'{"code": 500, "msg": "invalid token"}')
        provider = PushPlusProvider("SECRET")

        with self.assertRaises(DeliveryError) as raised:
            provider.send("Done", "The job completed")

        self.assertEqual(str(raised.exception), "PushPlus returned error code 500")
        self.assertNotIn("SECRET", str(raised.exception))

    @patch("finalert.providers.pushplus.urlopen")
    def test_pushplus_explains_required_identity_verification(
        self, urlopen: MagicMock
    ) -> None:
        urlopen.return_value = Response(b'{"code": 905, "msg": "not verified"}')
        provider = PushPlusProvider("SECRET")

        with self.assertRaises(DeliveryError) as raised:
            provider.send("Done", "The job completed")

        self.assertIn("identity verification", str(raised.exception))
        self.assertNotIn("SECRET", str(raised.exception))

    @patch("finalert.providers.pushplus.urlopen")
    def test_pushplus_rejects_invalid_response(self, urlopen: MagicMock) -> None:
        urlopen.return_value = Response(b"not json")
        provider = PushPlusProvider("SECRET")

        with self.assertRaisesRegex(DeliveryError, "invalid response"):
            provider.send("Done", "The job completed")

    @patch("finalert.providers.email.smtplib.SMTP")
    def test_email_uses_starttls_and_login(self, smtp_class: MagicMock) -> None:
        smtp = smtp_class.return_value.__enter__.return_value
        provider = EmailProvider(
            "smtp.example.test",
            587,
            "sender@example.test",
            ["receiver@example.test"],
            username="sender@example.test",
            password="secret",
        )

        provider.send("Done", "The job completed")

        smtp.starttls.assert_called_once_with()
        smtp.login.assert_called_once_with("sender@example.test", "secret")
        email = smtp.send_message.call_args.args[0]
        self.assertEqual(email["Subject"], "Done")


if __name__ == "__main__":
    unittest.main()
