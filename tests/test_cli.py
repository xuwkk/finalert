from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

from finalert.cli import main


class CliTests(unittest.TestCase):
    @patch("finalert.cli.provider_from_env")
    def test_test_command_succeeds(self, provider_from_env: MagicMock) -> None:
        output = StringIO()

        with redirect_stdout(output):
            result = main(["test", "--provider", "webhook"])

        self.assertEqual(result, 0)
        self.assertIn("Test notification sent", output.getvalue())
        provider_from_env.assert_called_once_with("webhook")

    @patch("finalert.cli.provider_from_env", side_effect=RuntimeError("offline"))
    def test_test_command_reports_failure(self, provider_from_env: MagicMock) -> None:
        error = StringIO()

        with redirect_stderr(error):
            result = main(["test"])

        self.assertEqual(result, 1)
        self.assertIn("offline", error.getvalue())


if __name__ == "__main__":
    unittest.main()

