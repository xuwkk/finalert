# Using Finalert with tqdm

Finalert can wrap tqdm and send progress notifications through the same
Telegram, email, or webhook provider used by `notify()` and `watch()`.

Unlike `tqdm.contrib.telegram`, which mirrors a progress bar to Telegram,
Finalert sends low-frequency milestone messages and remains provider-agnostic.

## Installation

tqdm is an optional dependency. Install the integration with:

```bash
python -m pip install "finalert[tqdm]"
```

The base `finalert` installation does not install tqdm.

## Basic usage

Replace the usual tqdm import with Finalert's wrapper:

```python
from finalert.tqdm import tqdm

for item in tqdm(
    range(100),
    desc="Data processing",
    notify_at=(25, 50, 75, 100),
):
    process(item)
```

The wrapper uses `tqdm.auto`, so tqdm can select an appropriate terminal or
notebook progress bar.

At 50%, a notification resembles:

```text
🔄 Data processing reached 50%

Progress: 50 / 100 it
Elapsed: 00:12
```

## Configuration

The wrapper uses the existing Finalert environment variables. For Telegram:

```bash
export FINALERT_PROVIDER="telegram"
export FINALERT_TELEGRAM_TOKEN="your-bot-token"
export FINALERT_TELEGRAM_CHAT_ID="your-chat-id"
```

It works in the same way with `FINALERT_PROVIDER=email` or
`FINALERT_PROVIDER=webhook`.

## Choosing milestones

Use `notify_at` to choose percentages:

```python
tqdm(items, notify_at=(10, 50, 90, 100))
```

Milestones are sorted and duplicate values are removed. Every value must be a
finite number greater than 0 and at most 100.

Finalert detects threshold crossings, so a progress update that jumps from 45%
to 60% still triggers the 50% milestone.

## Large progress jumps

If one update crosses several milestones, the default `catch_up="latest"`
sends only the latest one:

```python
bar = tqdm(
    total=100,
    notify_at=(25, 50, 75),
    catch_up="latest",
)
bar.update(80)  # sends only the 75% notification
```

To send every crossed milestone instead:

```python
bar = tqdm(
    total=100,
    notify_at=(25, 50, 75),
    catch_up="all",
)
bar.update(80)  # sends 25%, 50%, and 75%
```

## Custom notification name and provider

By default, the tqdm `desc` is used as the notification name. Override it with
`notify_name`:

```python
for item in tqdm(
    items,
    desc="Processing",
    notify_name="Daily customer export",
    notify_at=(50, 100),
):
    process(item)
```

Override the configured provider for one progress bar with `notify_provider`:

```python
tqdm(
    items,
    notify_at=(50, 100),
    notify_provider="email",
)
```

Provider credentials still come from the corresponding `FINALERT_*`
environment variables.

## Combining milestones with success and failure notifications

Use `watch()` around the loop and omit 100% from `notify_at` to avoid two final
success messages:

```python
from finalert import watch
from finalert.tqdm import tqdm

with watch("Model inference"):
    for batch in tqdm(
        batches,
        desc="Model inference",
        notify_at=(25, 50, 75),
    ):
        run_inference(batch)
```

This produces progress messages at 25%, 50%, and 75%, followed by one success or
failure message from `watch()`.

## Manual progress updates

Finalert supports tqdm's manual mode:

```python
from finalert.tqdm import tqdm

with tqdm(total=100, notify_at=(25, 50, 75, 100)) as bar:
    for chunk in chunks:
        process(chunk)
        bar.update(chunk.size)
```

The `trange` shortcut is also available:

```python
from finalert.tqdm import trange

for index in trange(100, notify_at=(50, 100)):
    process(index)
```

## Unknown totals

Percentage milestones require a known positive total. Lists, ranges, and other
sized iterables normally provide this automatically. For a generator, pass the
total explicitly:

```python
for item in tqdm(
    generate_items(),
    total=10_000,
    notify_at=(25, 50, 75, 100),
):
    process(item)
```

Without a known total, Finalert raises a clear `ValueError`. To use Finalert's
tqdm wrapper without milestone notifications, pass `notify_at=()`.

## Delivery behaviour

- Each milestone is processed at most once per progress-bar run.
- Notification failures are logged and do not stop the loop.
- A failed milestone is marked as processed to avoid retrying on every update.
- Notifications are synchronous and may briefly pause the loop at a milestone.
- `reset()` clears the sent milestones for a new run.
- `disable=True` hides the visual progress bar but milestone tracking continues.

Nested bars, multiprocessing worker coordination, unknown-total interval
notifications, and `tqdm.asyncio` are not handled specially in Finalert 0.2.
