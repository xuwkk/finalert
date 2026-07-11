# Finalert

> **Finally, an alert when your code is done.**

Finalert sends progress, completion, and failure notifications for Python jobs.
Its tqdm integration can notify you at selected percentages, while Telegram,
SMTP email, and generic JSON webhooks provide flexible delivery. The core
package has no third-party runtime dependencies; tqdm support is optional.

1. Use `notify()` at the end of an existing script for the simplest integration:

```python
from finalert import notify

run_analysis()
save_results()

notify("The analysis results have been saved.")
```

2. Use `watch()` when you also want failure notifications and elapsed time:

```python
from finalert import watch

with watch("Model training"):
    train_model()
    save_model()
```

3. Install the tqdm integration and add milestone notifications to an existing
progress loop:

```bash
python -m pip install "finalert[tqdm]"
```

```python
from finalert import watch
from finalert.tqdm import tqdm

with watch("Model training"):
    for batch in tqdm(
        batches,
        desc="Model training",
        notify_at=(25, 50, 75),
    ):
        train_batch(batch)
```

This sends progress messages at 25%, 50%, and 75%, followed by one final success
or failure notification.

## Features

- Send a notification from the final line of a Python program.
- Report successful completion, failure, elapsed time, and an exception summary.
- Deliver notifications through Telegram, SMTP email, or a JSON webhook.
- Preserve the original program result if notification delivery fails.
- Configure credentials through environment variables.
- Send low-frequency tqdm progress notifications at selected percentages.

## Installation

Install from PyPI:

```bash
python -m pip install finalert
```

Install the optional tqdm integration with:

```bash
python -m pip install "finalert[tqdm]"
```

Confirm the installation:

```bash
finalert --version
```

## Configuration

Finalert reads configuration from environment variables. Select one provider by
setting `FINALERT_PROVIDER` to `telegram`, `email`, or `webhook`.

Finalert does not automatically load `.env` files. If you keep the
variables in a shell file such as `.finalert.env`, load it before running a job:

```bash
source .finalert.env
```

Do not commit tokens or passwords to version control. Add `.finalert.env` to
`.gitignore` and restrict its permissions with `chmod 600 .finalert.env`.

### Telegram

Create a bot with Telegram's `@BotFather`, send the bot at least one message,
and obtain the bot token and destination chat ID to compete the following in the `.finalert.env` file:
```bash
export FINALERT_PROVIDER="telegram"
export FINALERT_TELEGRAM_TOKEN="your-bot-token"
export FINALERT_TELEGRAM_CHAT_ID="your-chat-id"
```

For a complete walkthrough, see the
[Telegram setup guide](https://github.com/xuwkk/finalert/blob/master/telegram.md).



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
that line, so it cannot report an earlier crash; use `watch()` instead.

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

The selected provider's credentials still come from environment variables. *You can add multiple providers to the `.finalert.env` file.*

### Report tqdm progress milestones

Install the optional integration and import Finalert's tqdm wrapper:

```bash
python -m pip install "finalert[tqdm]"
```

```python
from finalert.tqdm import tqdm

for item in tqdm(
    dataset,
    desc="Dataset processing",
    notify_at=(25, 50, 75, 100),
):
    process(item)
```

Each percentage is notified at most once. If one update crosses several
milestones, Finalert sends only the latest milestone by default to avoid a burst
of messages. Use `catch_up="all"` to send every crossed milestone.

Combine progress milestones with `watch()` for a final success or failure
notification:

```python
from finalert import watch
from finalert.tqdm import tqdm

with watch("Dataset processing"):
    for item in tqdm(
        dataset,
        desc="Dataset processing",
        notify_at=(25, 50, 75),
    ):
        process(item)
```

Percentage notifications require an iterable with a known length or an explicit
`total=...`. It also supports manual progress updates and `trange` shortcut. 
For complete options and behaviour, see the
[tqdm integration guide](https://github.com/xuwkk/finalert/blob/master/tqdm.md).

## Limitations

- Finalert cannot notify event that prevents Python from executing notification
code.
- Finalert sends notifications synchronously and does not retry failures.
- Finalert does not automatically read `.env` or other configuration files.
- tqdm percentage notifications require a known positive total.

## Development

Run the test suite after installing the package with its tqdm extra:

```bash
python -m pip install -e ".[tqdm]"
python -m unittest discover -s tests -v
```

The tests mock external services and do not send real Telegram messages, emails,
or webhook requests. Use `finalert test` with real credentials for an integration
check.

## Project layout

```text
src/finalert/           Package source
src/finalert/providers/ Notification providers
src/finalert/tqdm.py    Optional tqdm integration
tests/                 Unit tests
tqdm.md                tqdm integration guide
dist/                  Built wheel
```

## License

Finalert is distributed under the MIT License. See `LICENSE` for details.