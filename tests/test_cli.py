from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

from finalert.cli import main


class CliTests(unittest.TestCase):
    def test_version_command_reports_package_version(self) -> None:
        output = StringIO()

        with redirect_stdout(output), self.assertRaises(SystemExit) as raised:
            main(["--version"])

        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(output.getvalue().strip(), "finalert 0.3.0")

    @patch("finalert.cli.provider_from_env")
    def test_test_command_succeeds(self, provider_from_env: MagicMock) -> None:
        output = StringIO()

        with redirect_stdout(output):
            result = main(["test", "--provider", "pushplus"])

        self.assertEqual(result, 0)
        self.assertIn("Test notification sent", output.getvalue())
        provider_from_env.assert_called_once_with("pushplus")

    @patch("finalert.cli.provider_from_env", side_effect=RuntimeError("offline"))
    def test_test_command_reports_failure(self, provider_from_env: MagicMock) -> None:
        error = StringIO()

        with redirect_stderr(error):
            result = main(["test"])

        self.assertEqual(result, 1)
        self.assertIn("offline", error.getvalue())


if __name__ == "__main__":
    unittest.main()
