# Finalert

> **Finally, an alert when your code is done.**

Finalert sends a notification when a Python job completes or fails. It supports
Telegram, SMTP email, and generic JSON webhooks through a small synchronous API
with no third-party runtime dependencies.

Use `notify()` at the end of an existing script for the simplest integration:

```python
from finalert import notify

run_analysis()
save_results()

notify("The analysis results have been saved.")
```

Use `watch()` when you also want failure notifications and elapsed time:

```python
from finalert import watch

with watch("Model training"):
    train_model()
    save_model()
```

## Features

- Send a notification from the final line of a Python program.
- Report successful completion, failure, elapsed time, and an exception summary.
- Deliver notifications through Telegram, SMTP email, or a JSON webhook.
- Test provider configuration from the command line.
- Preserve the original program result if notification delivery fails.
- Configure credentials through environment variables instead of source code.
- Run on Python 3.10 or later without third-party runtime dependencies.

## Installation

Install from the project directory:

```bash
python -m pip install .
```

For development, use an editable installation:

```bash
python -m pip install -e .
```

You can also install the prebuilt wheel:

```bash
python -m pip install dist/finalert-0.1.0-py3-none-any.whl
```

Confirm the installation:

```bash
finalert --version
```

## Configuration

Finalert reads configuration from environment variables. Select one provider by
setting `FINALERT_PROVIDER` to `telegram`, `email`, or `webhook`.

Finalert does not automatically load `.env` files in version 0.1. If you keep the
variables in a shell file such as `.finalert.env`, load it before running a job:

```bash
source .finalert.env
```

Do not commit tokens or passwords to version control. Add `.finalert.env` to
`.gitignore` and restrict its permissions with `chmod 600 .finalert.env`.

### Telegram

Create a bot with Telegram's `@BotFather`, send the bot at least one message,
and obtain the bot token and destination chat ID.

For a complete walkthrough, see [telegram.md](telegram.md).

```bash
export FINALERT_PROVIDER="telegram"
export FINALERT_TELEGRAM_TOKEN="your-bot-token"
export FINALERT_TELEGRAM_CHAT_ID="your-chat-id"
```

### SMTP email

The following example uses STARTTLS on port 587:

```bash
export FINALERT_PROVIDER="email"
export FINALERT_SMTP_HOST="smtp.example.com"
export FINALERT_SMTP_PORT="587"
export FINALERT_SMTP_USERNAME="sender@example.com"
export FINALERT_SMTP_PASSWORD="your-app-password"
export FINALERT_EMAIL_TO="receiver@example.com"
```

Separate multiple recipients with commas:

```bash
export FINALERT_EMAIL_TO="first@example.com,second@example.com"
```

If the sender address differs from the SMTP username, set it explicitly:

```bash
export FINALERT_EMAIL_FROM="notifications@example.com"
```

For implicit SMTP SSL, commonly used on port 465:

```bash
export FINALERT_SMTP_PORT="465"
export FINALERT_SMTP_SSL="true"
export FINALERT_SMTP_STARTTLS="false"
```

### JSON webhook

```bash
export FINALERT_PROVIDER="webhook"
export FINALERT_WEBHOOK_URL="https://example.com/hooks/finalert"
```

Finalert sends an HTTP `POST` request with a JSON body:

```json
{
  "title": "✅ analysis.py completed",
  "message": "The analysis results have been saved."
}
```

Optional HTTP headers can be supplied as a JSON object:

```bash
export FINALERT_WEBHOOK_HEADERS='{"Authorization":"Bearer secret"}'
```

### Network timeout

All providers use a 10-second timeout by default. Override it when needed:

```bash
export FINALERT_TIMEOUT="5"
```

## Test the configuration

Send a test notification using the configured provider:

```bash
finalert test
```

Override `FINALERT_PROVIDER` for one test while still reading that provider's
credentials from the environment:

```bash
finalert test --provider telegram
```

A successful request prints:

```text
✓ Test notification sent
```

## Usage

### Notify at the end of a script

```python
from finalert import notify

perform_analysis()

notify("Results were written to output.csv")
```

Customize the notification title:

```python
notify(
    "Results were written to output.csv",
    title="Daily analysis completed",
)
```

If no arguments are provided, Finalert uses the current script name:

```python
notify()
```

`notify()` returns `True` when the provider accepts the notification and `False`
when configuration or delivery fails:

```python
if not notify("The export has completed"):
    print("The job succeeded, but its notification could not be sent.")
```

Delivery errors are logged as warnings. They do not turn a successful job into a
failed job. A final-line `notify()` call only runs if program execution reaches
that line, so it cannot report an earlier crash.

### Monitor success and failure

Wrap a block with `watch()` to report either outcome:

```python
from finalert import watch

with watch("Dataset export"):
    build_dataset()
    export_dataset()
```

On success, the notification includes elapsed time. On failure, it includes
elapsed time plus the exception type and message. Finalert then re-raises the
original exception so the program keeps its normal failure behaviour.

### Override the provider in Python

The provider can be selected for an individual call:

```python
notify("Backup complete", provider="email")

with watch("Model training", provider="telegram"):
    train_model()
```

The selected provider's credentials still come from environment variables.

## Limitations

- Finalert cannot notify after `kill -9`, loss of power, a fatal interpreter
  failure, or another event that prevents Python from executing notification
  code.
- Version 0.1 sends notifications synchronously and does not retry failures.
- Version 0.1 does not automatically read `.env` or other configuration files.
- Email providers may require an application-specific password.
- Telegram bots cannot initiate a conversation; the recipient must contact the
  bot first.

## Development

Run the test suite after installing the package in editable mode:

```bash
python -m unittest discover -s tests -v
```

The tests mock external services and do not send real Telegram messages, emails,
or webhook requests. Use `finalert test` with real credentials for an integration
check.

## Project layout

```text
src/finalert/           Package source
src/finalert/providers/ Notification providers
tests/                 Unit tests
dist/                  Built wheel
```

## License

Finalert is distributed under the MIT License. See `LICENSE` for details.
