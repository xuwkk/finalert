# Using Finalert with PushPlus and personal WeChat

Finalert can send completion, failure, and tqdm milestone notifications to a
personal WeChat account through PushPlus.

PushPlus is an independent third-party service. It is not operated by Finalert
or WeChat, and its availability, quotas, and delivery behaviour are controlled
by PushPlus and WeChat.

## 1. Create a PushPlus account

Open the [PushPlus website](https://www.pushplus.plus/) and follow its current
instructions to sign in and connect the WeChat account that should receive
notifications.

PushPlus requires the sending account to complete identity verification before
its message API can be used. An unverified account returns error code `905`.
Follow the current instructions in the
[PushPlus identity-verification guide](https://www.pushplus.plus/doc/help/verify.html).

PushPlus currently charges a service fee for identity verification. Registration and identity
verification are separate, and the pricing and requirements are controlled by
PushPlus, so check its current terms before proceeding.

## 2. Obtain a message token

In PushPlus, create or copy a personal message token. A message token allows its
holder to send notifications to the connected recipient, so treat it like a
password.

Do not paste a real token into source code, documentation, an issue, or a Git
commit.

## 3. Configure Finalert

Set the provider and message token in the shell that will run the Python job:

```bash
export FINALERT_PROVIDER="pushplus"
export FINALERT_PUSHPLUS_TOKEN="your-message-token"
```

Finalert does not automatically load `.env` files. If the values are stored in
`.finalert.env`, load them first:

```bash
source .finalert.env
```

Keep `.finalert.env` out of version control and restrict it on macOS or Linux:

```bash
chmod 600 .finalert.env
```

## 4. Send a test notification

```bash
finalert test --provider pushplus
```

A successful request prints:

```text
✓ Test notification sent
```

Check the connected WeChat account for the test message. PushPlus may accept a
request before the downstream WeChat notification is displayed, so a short
delivery delay does not necessarily indicate a Finalert error.

## 5. Use PushPlus from Python

Use the configured provider:

```python
from finalert import notify

run_analysis()
notify("The analysis results have been saved.")
```

Or select PushPlus for one call while keeping another default provider:

```python
notify("Backup complete", provider="pushplus")
```

Monitor both successful completion and failure:

```python
from finalert import watch

with watch("Model training", provider="pushplus"):
    train_model()
```

Use personal WeChat for tqdm milestones:

```python
from finalert.tqdm import tqdm

for item in tqdm(
    dataset,
    desc="Dataset processing",
    notify_at=(25, 50, 75, 100),
    notify_provider="pushplus",
):
    process(item)
```

Keep milestone counts low to avoid unnecessary messages and service limits.

## Security and privacy

- Finalert sends the PushPlus token in an HTTPS request body, not in the URL.
- Finalert does not include the token in its delivery error messages.
- Rotate the token in PushPlus if it is exposed.
- Notification titles and content pass through PushPlus and WeChat. Do not send
  secrets, passwords, access tokens, or sensitive research data.

For current API details and service behaviour, see the
[PushPlus message API documentation](https://www.pushplus.plus/doc/guide/api.html).

## Troubleshooting

### Missing token

If Finalert reports that `FINALERT_PUSHPLUS_TOKEN` is missing, confirm that the
variable is available in the current shell:

```bash
test -n "$FINALERT_PUSHPLUS_TOKEN" && echo "token is set"
```

This checks whether a value exists without printing the token.

### PushPlus returns an error code

Confirm that the token is active, the recipient is still connected, and the
account has not reached a PushPlus or WeChat delivery limit. Run `finalert test`
again after correcting the PushPlus configuration.

Common codes include:

- `903`: the message token is invalid.
- `905`: the sending account has not completed PushPlus identity verification.
- `900`: the account is temporarily restricted, commonly because of excessive
  requests.

### The request succeeds but no WeChat message appears

Check the PushPlus message history and channel configuration, then confirm that
the intended WeChat account is connected. Delivery after PushPlus accepts the
request is handled by PushPlus and WeChat rather than Finalert.
