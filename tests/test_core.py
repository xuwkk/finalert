from __future__ import annotations

import logging
import unittest
from unittest.mock import patch

from finalert import notify, watch
from finalert.providers import Provider


class RecordingProvider(Provider):
    def __init__(self, error: Exception | None = None) -> None:
        self.notifications: list[tuple[str, str]] = []
        self.error = error

    def send(self, title: str, message: str) -> None:
        if self.error:
            raise self.error
        self.notifications.append((title, message))


class CoreTests(unittest.TestCase):
    def test_notify_sends_custom_content(self) -> None:
        provider = RecordingProvider()

        delivered = notify("Saved results", title="Finished", provider=provider)

        self.assertTrue(delivered)
        self.assertEqual(provider.notifications, [("Finished", "Saved results")])

    def test_notify_uses_script_name_for_defaults(self) -> None:
        provider = RecordingProvider()

        with patch("sys.argv", ["/tmp/analysis.py"]):
            notify(provider=provider)

        title, message = provider.notifications[0]
        self.assertEqual(title, "✅ analysis.py completed")
        self.assertIn("analysis.py", message)

    def test_notify_is_best_effort(self) -> None:
        provider = RecordingProvider(RuntimeError("network unavailable"))

        with self.assertLogs("finalert", logging.WARNING):
            delivered = notify("Done", provider=provider)

        self.assertFalse(delivered)

    def test_watch_notifies_on_success(self) -> None:
        provider = RecordingProvider()

        with patch("finalert.core.time.monotonic", side_effect=[10.0, 75.0]):
            with watch("Training", provider=provider):
                pass

        title, message = provider.notifications[0]
        self.assertEqual(title, "✅ Training completed")
        self.assertEqual(message, "Duration: 1m 5s")

    def test_watch_notifies_and_reraises_on_failure(self) -> None:
        provider = RecordingProvider()

        with patch("finalert.core.time.monotonic", side_effect=[10.0, 12.0]):
            with self.assertRaisesRegex(ValueError, "bad input"):
                with watch("Training", provider=provider):
                    raise ValueError("bad input")

        title, message = provider.notifications[0]
        self.assertEqual(title, "❌ Training failed")
        self.assertIn("Duration: 2s", message)
        self.assertIn("ValueError: bad input", message)


if __name__ == "__main__":
    unittest.main()

