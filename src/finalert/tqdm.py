from __future__ import annotations

import math
import time
from collections.abc import Iterable, Iterator
from numbers import Real

from finalert.core import notify
from finalert.providers import Provider

try:
    from tqdm.auto import tqdm as _StandardTqdm
except ImportError as exc:  # pragma: no cover - exercised without the extra
    raise ImportError(
        'Finalert tqdm support requires tqdm. Install it with '
        '`pip install "finalert[tqdm]"`.'
    ) from exc


def _normalise_milestones(values: Iterable[float]) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("notify_at must be an iterable of percentages")

    try:
        raw_values = tuple(values)
    except TypeError as exc:
        raise TypeError("notify_at must be an iterable of percentages") from exc

    milestones: set[float] = set()
    for value in raw_values:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError("notify_at percentages must be numbers")
        percentage = float(value)
        if not math.isfinite(percentage) or not 0 < percentage <= 100:
            raise ValueError("notify_at percentages must be greater than 0 and at most 100")
        milestones.add(percentage)
    return tuple(sorted(milestones))


def _format_number(value: float) -> str:
    return f"{value:g}"


class FinalertTqdm(_StandardTqdm):
    """A tqdm progress bar that sends milestone notifications through Finalert."""

    def __init__(
        self,
        *args: object,
        notify_at: Iterable[float] = (25, 50, 75, 100),
        notify_name: str | None = None,
        notify_provider: str | Provider | None = None,
        catch_up: str = "latest",
        **kwargs: object,
    ) -> None:
        self._finalert_milestones = _normalise_milestones(notify_at)
        self._finalert_sent: set[float] = set()
        self._finalert_name = notify_name
        self._finalert_provider = notify_provider
        self._finalert_started = time.monotonic()
        if catch_up not in {"latest", "all"}:
            raise ValueError("catch_up must be 'latest' or 'all'")
        self._finalert_catch_up = catch_up

        super().__init__(*args, **kwargs)

        if self._finalert_milestones and (
            self.total is None
            or not math.isfinite(float(self.total))
            or float(self.total) <= 0
        ):
            super().close()
            raise ValueError(
                "Percentage notifications require a known positive total. "
                "Pass total=... to tqdm()."
            )

    def update(self, n: float = 1) -> bool | None:
        if self.disable:
            self.n += n
            self._finalert_check_milestones()
            return None
        displayed = super().update(n)
        self._finalert_check_milestones()
        return displayed

    def __iter__(self) -> Iterator[object]:
        if not self._finalert_milestones:
            yield from super().__iter__()
            return

        # tqdm intentionally batches its own update() calls for speed. Track
        # completed iterable items here as well so fast loops cannot skip
        # intermediate notification thresholds.
        current = float(self.n)
        check_milestones = self._finalert_check_milestones
        for item in super().__iter__():
            yield item
            current += 1
            check_milestones(current=current)

    def close(self) -> None:
        # tqdm's destructor may call close() after validation failed before the
        # base constructor created its attributes.
        if not hasattr(self, "disable"):
            return
        if hasattr(self, "_finalert_milestones") and hasattr(self, "total"):
            self._finalert_check_milestones()
        super().close()

    def reset(self, total: float | None = None) -> None:
        super().reset(total=total)
        self._finalert_sent.clear()
        self._finalert_started = time.monotonic()

    def _finalert_check_milestones(self, *, current: float | None = None) -> None:
        if not self._finalert_milestones or self.total is None:
            return

        progress = float(self.n) if current is None else current
        percentage = min(100.0, max(0.0, progress / float(self.total) * 100))
        crossed = [
            milestone
            for milestone in self._finalert_milestones
            if milestone <= percentage and milestone not in self._finalert_sent
        ]
        if not crossed:
            return

        # Mark every crossed milestone before sending. A failed notification must
        # not be retried on every subsequent iteration.
        self._finalert_sent.update(crossed)
        selected = crossed if self._finalert_catch_up == "all" else crossed[-1:]
        for milestone in selected:
            self._finalert_send_milestone(milestone, progress)

    def _finalert_send_milestone(self, milestone: float, current_progress: float) -> None:
        name = self._finalert_name or getattr(self, "desc", None) or "Progress"
        current = _format_number(current_progress)
        total = _format_number(float(self.total))
        elapsed = self.format_interval(time.monotonic() - self._finalert_started)
        unit = getattr(self, "unit", None) or "it"
        notify(
            f"Progress: {current} / {total} {unit}\nElapsed: {elapsed}",
            title=f"🔄 {name} reached {_format_number(milestone)}%",
            provider=self._finalert_provider,
        )


tqdm = FinalertTqdm


def trange(*args: int, **kwargs: object) -> FinalertTqdm:
    """Shortcut for ``FinalertTqdm(range(*args), **kwargs)``."""
    return FinalertTqdm(range(*args), **kwargs)


__all__ = ["FinalertTqdm", "tqdm", "trange"]
