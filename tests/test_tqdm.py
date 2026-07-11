from __future__ import annotations

import logging
import unittest
from io import StringIO

from finalert.providers import Provider
from finalert.tqdm import FinalertTqdm, tqdm, trange


class RecordingProvider(Provider):
    def __init__(self, error: Exception | None = None) -> None:
        self.notifications: list[tuple[str, str]] = []
        self.error = error

    def send(self, title: str, message: str) -> None:
        if self.error is not None:
            raise self.error
        self.notifications.append((title, message))


class TqdmTests(unittest.TestCase):
    def test_iterable_sends_each_reached_milestone_once(self) -> None:
        provider = RecordingProvider()

        result = list(
            tqdm(
                range(4),
                desc="Import",
                notify_at=(25, 50, 75, 100),
                notify_provider=provider,
                file=StringIO(),
            )
        )

        self.assertEqual(result, [0, 1, 2, 3])
        self.assertEqual(
            [title for title, _ in provider.notifications],
            [
                "🔄 Import reached 25%",
                "🔄 Import reached 50%",
                "🔄 Import reached 75%",
                "🔄 Import reached 100%",
            ],
        )

    def test_large_jump_sends_only_latest_crossed_milestone_by_default(self) -> None:
        provider = RecordingProvider()
        bar = FinalertTqdm(
            total=100,
            notify_at=(25, 50, 75, 100),
            notify_provider=provider,
            mininterval=0,
            file=StringIO(),
        )

        bar.update(76)
        bar.update(1)
        bar.close()

        self.assertEqual(
            [title for title, _ in provider.notifications],
            ["🔄 Progress reached 75%"],
        )

    def test_catch_up_all_sends_every_crossed_milestone(self) -> None:
        provider = RecordingProvider()
        bar = FinalertTqdm(
            total=100,
            notify_at=(25, 50, 75),
            notify_provider=provider,
            catch_up="all",
            mininterval=0,
            file=StringIO(),
        )

        bar.update(76)
        bar.close()

        self.assertEqual(
            [title for title, _ in provider.notifications],
            [
                "🔄 Progress reached 25%",
                "🔄 Progress reached 50%",
                "🔄 Progress reached 75%",
            ],
        )

    def test_milestones_are_sorted_and_deduplicated(self) -> None:
        provider = RecordingProvider()
        bar = FinalertTqdm(
            total=100,
            notify_at=(50, 25, 50),
            notify_provider=provider,
            catch_up="all",
            mininterval=0,
            file=StringIO(),
        )

        bar.update(50)
        bar.close()

        self.assertEqual(
            [title for title, _ in provider.notifications],
            ["🔄 Progress reached 25%", "🔄 Progress reached 50%"],
        )

    def test_notification_contains_counts_elapsed_and_unit(self) -> None:
        provider = RecordingProvider()
        bar = FinalertTqdm(
            total=8,
            unit="files",
            notify_at=(50,),
            notify_name="Backup",
            notify_provider=provider,
            mininterval=0,
            file=StringIO(),
        )

        bar.update(4)
        bar.close()

        title, message = provider.notifications[0]
        self.assertEqual(title, "🔄 Backup reached 50%")
        self.assertIn("Progress: 4 / 8 files", message)
        self.assertIn("Elapsed:", message)

    def test_unknown_total_requires_explicit_total(self) -> None:
        with self.assertRaisesRegex(ValueError, "known positive total"):
            FinalertTqdm(
                iter(range(3)),
                notify_provider=RecordingProvider(),
                file=StringIO(),
            )

    def test_empty_milestones_allow_unknown_total(self) -> None:
        provider = RecordingProvider()

        result = list(
            FinalertTqdm(
                iter(range(3)),
                notify_at=(),
                notify_provider=provider,
                file=StringIO(),
            )
        )

        self.assertEqual(result, [0, 1, 2])
        self.assertEqual(provider.notifications, [])

    def test_invalid_milestones_are_rejected(self) -> None:
        invalid_values = [(0,), (101,), (float("nan"),), (True,), ("50",)]

        for notify_at in invalid_values:
            with self.subTest(notify_at=notify_at):
                with self.assertRaises((TypeError, ValueError)):
                    FinalertTqdm(
                        total=100,
                        notify_at=notify_at,
                        file=StringIO(),
                    )

    def test_invalid_catch_up_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "catch_up"):
            FinalertTqdm(total=100, catch_up="sometimes", file=StringIO())

    def test_delivery_failure_does_not_break_progress(self) -> None:
        provider = RecordingProvider(RuntimeError("offline"))
        bar = FinalertTqdm(
            total=2,
            notify_at=(50,),
            notify_provider=provider,
            mininterval=0,
            file=StringIO(),
        )

        with self.assertLogs("finalert", logging.WARNING):
            bar.update(1)
        bar.close()

        self.assertEqual(bar.n, 1)

    def test_disabled_manual_bar_still_tracks_milestones(self) -> None:
        provider = RecordingProvider()
        bar = FinalertTqdm(
            total=4,
            disable=True,
            notify_at=(50,),
            notify_provider=provider,
        )

        bar.update(2)
        bar.close()

        self.assertEqual(bar.n, 2)
        self.assertEqual(
            [title for title, _ in provider.notifications],
            ["🔄 Progress reached 50%"],
        )

    def test_reset_allows_milestones_for_a_new_run(self) -> None:
        provider = RecordingProvider()
        bar = FinalertTqdm(
            total=4,
            notify_at=(50,),
            notify_provider=provider,
            mininterval=0,
            file=StringIO(),
        )

        bar.update(2)
        bar.reset(total=4)
        bar.update(2)
        bar.close()

        self.assertEqual(len(provider.notifications), 2)

    def test_trange_returns_finalert_tqdm(self) -> None:
        bar = trange(2, notify_at=(), file=StringIO())

        self.assertIsInstance(bar, FinalertTqdm)
        bar.close()


if __name__ == "__main__":
    unittest.main()
