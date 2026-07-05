from __future__ import annotations

import unittest
from datetime import datetime, time
from zoneinfo import ZoneInfo

from src.bedtime_guard.platforms import PlatformActionKind, plan_phase_actions
from src.bedtime_guard.schedule import ScheduleConfig, SchedulePhase, compute_schedule_snapshot


TZ = ZoneInfo("America/Chicago")


class PlatformBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
        )

    def test_wind_down_transition_produces_warning_action(self) -> None:
        snapshot = compute_schedule_snapshot(
            now=datetime(2026, 7, 4, 22, 10, tzinfo=TZ),
            config=self.config,
        )

        actions = plan_phase_actions(previous_phase=SchedulePhase.INACTIVE, snapshot=snapshot)

        self.assertEqual([action.kind for action in actions], [PlatformActionKind.SHOW_WARNING])

    def test_guarded_transition_clears_warning_and_shows_guard(self) -> None:
        snapshot = compute_schedule_snapshot(
            now=datetime(2026, 7, 4, 22, 45, tzinfo=TZ),
            config=self.config,
        )

        actions = plan_phase_actions(previous_phase=SchedulePhase.WIND_DOWN, snapshot=snapshot)

        self.assertEqual(
            [action.kind for action in actions],
            [
                PlatformActionKind.CLEAR_WARNING,
                PlatformActionKind.SHOW_GUARD,
                PlatformActionKind.ENABLE_GUARD_REACTIVATION,
            ],
        )

    def test_snoozed_transition_hides_guard(self) -> None:
        snapshot = compute_schedule_snapshot(
            now=datetime(2026, 7, 4, 23, 0, tzinfo=TZ),
            config=self.config,
            last_snooze_at=datetime(2026, 7, 4, 22, 58, tzinfo=TZ),
            active_snooze_expires_at=datetime(2026, 7, 4, 23, 8, tzinfo=TZ),
        )

        actions = plan_phase_actions(previous_phase=SchedulePhase.GUARDED, snapshot=snapshot)

        self.assertEqual(
            [action.kind for action in actions],
            [
                PlatformActionKind.DISABLE_GUARD_REACTIVATION,
                PlatformActionKind.HIDE_GUARD,
            ],
        )

    def test_released_transition_clears_warning_and_hides_guard(self) -> None:
        snapshot = compute_schedule_snapshot(
            now=datetime(2026, 7, 5, 4, 1, tzinfo=TZ),
            config=self.config,
            last_snooze_at=datetime(2026, 7, 4, 23, 0, tzinfo=TZ),
        )

        actions = plan_phase_actions(previous_phase=SchedulePhase.SNOOZED, snapshot=snapshot)

        self.assertEqual(
            [action.kind for action in actions],
            [
                PlatformActionKind.CLEAR_WARNING,
                PlatformActionKind.DISABLE_GUARD_REACTIVATION,
                PlatformActionKind.HIDE_GUARD,
            ],
        )

    def test_repeated_phase_has_no_duplicate_action(self) -> None:
        snapshot = compute_schedule_snapshot(
            now=datetime(2026, 7, 4, 22, 12, tzinfo=TZ),
            config=self.config,
        )

        actions = plan_phase_actions(previous_phase=SchedulePhase.WIND_DOWN, snapshot=snapshot)

        self.assertEqual(actions, ())


if __name__ == "__main__":
    unittest.main()
