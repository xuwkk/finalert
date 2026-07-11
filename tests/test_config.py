from __future__ import annotations

import unittest

from finalert.config import provider_from_env
from finalert.exceptions import ConfigurationError
from finalert.providers import EmailProvider, TelegramProvider, WebhookProvider


class ConfigTests(unittest.TestCase):
    def test_telegram_configuration(self) -> None:
        provider = provider_from_env(
            env={
                "FINALERT_PROVIDER": "telegram",
                "FINALERT_TELEGRAM_TOKEN": "token",
                "FINALERT_TELEGRAM_CHAT_ID": "123",
            }
        )

        self.assertIsInstance(provider, TelegramProvider)
        self.assertEqual(provider.chat_id, "123")

    def test_webhook_configuration_with_headers(self) -> None:
        provider = provider_from_env(
            env={
                "FINALERT_PROVIDER": "webhook",
                "FINALERT_WEBHOOK_URL": "https://example.test/hooks/1",
                "FINALERT_WEBHOOK_HEADERS": '{"Authorization": "Bearer secret"}',
            }
        )

        self.assertIsInstance(provider, WebhookProvider)
        self.assertEqual(provider.headers["Authorization"], "Bearer secret")

    def test_email_configuration(self) -> None:
        provider = provider_from_env(
            env={
                "FINALERT_PROVIDER": "email",
                "FINALERT_SMTP_HOST": "smtp.example.test",
                "FINALERT_SMTP_USERNAME": "sender@example.test",
                "FINALERT_SMTP_PASSWORD": "secret",
                "FINALERT_EMAIL_TO": "one@example.test, two@example.test",
            }
        )

        self.assertIsInstance(provider, EmailProvider)
        self.assertEqual(
            provider.recipients, ["one@example.test", "two@example.test"]
        )
        self.assertTrue(provider.starttls)

    def test_provider_argument_overrides_environment(self) -> None:
        provider = provider_from_env(
            "webhook",
            env={
                "FINALERT_PROVIDER": "telegram",
                "FINALERT_WEBHOOK_URL": "https://example.test/hook",
            },
        )

        self.assertIsInstance(provider, WebhookProvider)

    def test_missing_provider_is_explained(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "No provider selected"):
            provider_from_env(env={})

    def test_invalid_timeout_is_rejected(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "greater than zero"):
            provider_from_env(
                env={
                    "FINALERT_PROVIDER": "webhook",
                    "FINALERT_WEBHOOK_URL": "https://example.test/hook",
                    "FINALERT_TIMEOUT": "0",
                }
            )


if __name__ == "__main__":
    unittest.main()

