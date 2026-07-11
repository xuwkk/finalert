# Configuring Telegram for Finalert

This guide configures Finalert to send notifications to a private Telegram chat.
The process normally takes about five minutes.

## 1. Create a Telegram bot

Open Telegram and start a conversation with the official
[`@BotFather`](https://t.me/BotFather) account. Send:

```text
/newbot
```

Follow the prompts to choose:

1. A display name, such as `Finalert`.
2. A unique username, such as `my_finalert_bot`.

Bot usernames normally end in `bot`. When creation is complete, BotFather will
return a token resembling:

```text
1234567890:AAExampleToken...
```

The token is your bot's password. Anyone who has it can control the bot. Never
commit it to Git, paste it into an issue, or share it publicly. If it is exposed,
revoke it through BotFather and generate a replacement. See Telegram's official
[Introduction to Bots](https://core.telegram.org/bots) for more information.

## 2. Start the conversation

Open the bot you just created and select **Start**, or send it a message such as:

```text
hello
```

This step is required. Telegram bots cannot initiate a private conversation;
the user must contact the bot first.

## 3. Find your Chat ID

Temporarily place the token in an environment variable:

```bash
export FINALERT_TELEGRAM_TOKEN="your-bot-token"
```

Ask Telegram for the bot's latest updates:

```bash
curl -s \
  "https://api.telegram.org/bot${FINALERT_TELEGRAM_TOKEN}/getUpdates" \
  | python -m json.tool
```

The response should contain an object similar to:

```json
{
  "ok": true,
  "result": [
    {
      "message": {
        "chat": {
          "id": 123456789,
          "first_name": "Your name",
          "type": "private"
        }
      }
    }
  ]
}
```

The value of `message.chat.id`, `123456789` in this example, is your Chat ID.
The [`getUpdates` method](https://core.telegram.org/bots/api#getupdates) is part
of Telegram's official Bot API.

If `result` is empty, send the bot another message and repeat the command. An
existing outgoing webhook also prevents `getUpdates` from working, although a
newly created bot normally has no webhook configured.

## 4. Create the Finalert environment file

Create a file named `.finalert.env` in the project where you run your Python
program:

```bash
export FINALERT_PROVIDER="telegram"
export FINALERT_TELEGRAM_TOKEN="1234567890:AAExampleToken"
export FINALERT_TELEGRAM_CHAT_ID="123456789"
```

Restrict access to the file:

```bash
chmod 600 .finalert.env
```

Add it to your project's `.gitignore`:

```gitignore
.finalert.env
```

Finalert does not automatically load environment files. Load the file in
each new terminal session before running a job:

```bash
source .finalert.env
```

## 5. Install Finalert

From the Finalert source directory:

```bash
python -m pip install .
```

Confirm the installation:

```bash
finalert --version
```

The expected output is:

```text
finalert 0.3.1
```

## 6. Send a test notification

Load the configuration and run the test command:

```bash
source .finalert.env
finalert test
```

The terminal should display:

```text
✓ Test notification sent
```

Your Telegram chat should receive:

```text
🧪 Finalert test

Your configuration works. Finalert can send notifications.
```

If the `finalert` executable is not available on your shell path, use:

```bash
python -m finalert test
```

## 7. Notify at the end of a Python program

Add `notify()` after the work that must finish:

```python
import time

print("Starting...")
time.sleep(10)
print("Finished")

from finalert import notify

notify("The Python program has finished.")
```

Run it after loading the environment:

```bash
source .finalert.env
python example.py
```

Telegram will receive a message similar to:

```text
✅ example.py completed

The Python program has finished.
```

This approach only sends a notification if execution reaches the final call.

## 8. Monitor both success and failure

Use `watch()` when you also want failure and duration notifications:

```python
from finalert import watch

with watch("Model training"):
    train_model()
    save_model()
```

A successful job produces a message similar to:

```text
✅ Model training completed

Duration: 1h 20m 5s
```

A failed job produces a message similar to:

```text
❌ Model training failed

Duration: 12s
Error: ValueError: invalid input shape
```

Finalert re-raises the original exception after attempting the notification, so
it does not change the program's normal failure behaviour.

## Group chats

To send notifications to a group:

1. Add the bot to the group.
2. Send a message or command in the group.
3. Call `getUpdates` again.
4. Use the group's `message.chat.id` as `FINALERT_TELEGRAM_CHAT_ID`.

Group Chat IDs are commonly negative numbers. Telegram's Privacy Mode may limit
which group messages a bot can see, but a direct command to the bot is generally
sufficient for discovering the chat.

## Troubleshooting

### `Unauthorized` or HTTP 401

The bot token is invalid or has been revoked. Copy the current token from
BotFather and update `FINALERT_TELEGRAM_TOKEN`.

### `chat not found`

The Chat ID is incorrect, or the user has not started a conversation with the
bot. Contact the bot, repeat `getUpdates`, and copy `message.chat.id` exactly.

### An empty `result` array

Send the bot a new message and run `getUpdates` again. If the bot already uses a
webhook, Telegram does not allow `getUpdates` at the same time.

### `finalert: command not found`

The package may have been installed into a different Python environment. Try:

```bash
python -m finalert test
```

### A leaked token

Revoke it immediately through BotFather, generate a new token, update your
environment file, and restart any process that used the old value.
