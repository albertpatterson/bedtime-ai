from __future__ import annotations

import unittest
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from src.bedtime_guard.schedule import (
    DebugMode,
    ScheduleConfig,
    SchedulePhase,
    compute_schedule_snapshot,
)
from src.bedtime_guard.snooze import (
    FixedPhraseSource,
    SnoozeTier,
    choose_snooze_decision,
    matches_passphrase,
)


TZ = ZoneInfo("America/Chicago")


class ScheduleTests(unittest.TestCase):
    def test_inactive_before_wind_down(self) -> None:
        config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
        )
        now = datetime(2026, 7, 4, 21, 30, tzinfo=TZ)

        snapshot = compute_schedule_snapshot(now=now, config=config)

        self.assertEqual(snapshot.phase, SchedulePhase.INACTIVE)

    def test_wind_down_before_bedtime(self) -> None:
        config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
        )
        now = datetime(2026, 7, 4, 22, 10, tzinfo=TZ)

        snapshot = compute_schedule_snapshot(now=now, config=config)

        self.assertEqual(snapshot.phase, SchedulePhase.WIND_DOWN)

    def test_guarded_at_bedtime(self) -> None:
        config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
        )
        now = datetime(2026, 7, 4, 22, 45, tzinfo=TZ)

        snapshot = compute_schedule_snapshot(now=now, config=config)

        self.assertEqual(snapshot.phase, SchedulePhase.GUARDED)
        self.assertEqual(snapshot.time_since_bedtime, timedelta(minutes=15))

    def test_snoozed_when_active_expiry_is_in_future(self) -> None:
        config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
        )
        now = datetime(2026, 7, 4, 23, 0, tzinfo=TZ)

        snapshot = compute_schedule_snapshot(
            now=now,
            config=config,
            last_snooze_at=datetime(2026, 7, 4, 22, 58, tzinfo=TZ),
            active_snooze_expires_at=datetime(2026, 7, 4, 23, 8, tzinfo=TZ),
        )

        self.assertEqual(snapshot.phase, SchedulePhase.SNOOZED)

    def test_released_after_wakeup_rule(self) -> None:
        config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
        )
        last_snooze_at = datetime(2026, 7, 4, 23, 0, tzinfo=TZ)
        now = datetime(2026, 7, 5, 4, 1, tzinfo=TZ)

        snapshot = compute_schedule_snapshot(
            now=now,
            config=config,
            last_snooze_at=last_snooze_at,
        )

        self.assertEqual(snapshot.phase, SchedulePhase.RELEASED)

    def test_debug_bedtime_now_is_immediately_guarded(self) -> None:
        config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
            debug_mode=DebugMode.BEDTIME_NOW,
        )
        now = datetime(2026, 7, 4, 12, 0, tzinfo=TZ)

        snapshot = compute_schedule_snapshot(now=now, config=config)

        self.assertEqual(snapshot.phase, SchedulePhase.GUARDED)
        self.assertEqual(snapshot.bedtime_at, now)

    def test_debug_bedtime_in_ten_minutes_is_pre_bedtime(self) -> None:
        config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
            debug_mode=DebugMode.BEDTIME_IN_10_MINUTES,
        )
        now = datetime(2026, 7, 4, 12, 0, tzinfo=TZ)

        snapshot = compute_schedule_snapshot(now=now, config=config)

        self.assertEqual(snapshot.phase, SchedulePhase.WIND_DOWN)
        self.assertEqual(snapshot.bedtime_at, now + timedelta(minutes=10))

    def test_time_scale_accelerates_release(self) -> None:
        config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
            debug_mode=DebugMode.BEDTIME_NOW,
            time_scale=1 / 60,
        )
        now = datetime(2026, 7, 4, 12, 6, tzinfo=TZ)
        last_snooze_at = datetime(2026, 7, 4, 12, 0, tzinfo=TZ)

        snapshot = compute_schedule_snapshot(
            now=now,
            config=config,
            last_snooze_at=last_snooze_at,
        )

        self.assertEqual(snapshot.phase, SchedulePhase.RELEASED)

    def test_bedtime_override_keeps_release_anchor_stable_in_debug_mode(self) -> None:
        config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
            debug_mode=DebugMode.BEDTIME_NOW,
            time_scale=1 / 60,
        )
        fixed_bedtime = datetime(2026, 7, 4, 12, 0, tzinfo=TZ)

        first_snapshot = compute_schedule_snapshot(
            now=fixed_bedtime,
            config=config,
            bedtime_at_override=fixed_bedtime,
        )
        later_snapshot = compute_schedule_snapshot(
            now=datetime(2026, 7, 4, 12, 2, tzinfo=TZ),
            config=config,
            bedtime_at_override=fixed_bedtime,
        )

        self.assertEqual(first_snapshot.release_at, later_snapshot.release_at)
        self.assertEqual(later_snapshot.time_since_bedtime, timedelta(minutes=2))

    def test_snooze_tier_uses_first_threshold_before_thirty_minutes(self) -> None:
        decision = choose_snooze_decision(
            minutes_since_bedtime=12,
            tiers=(
                SnoozeTier(0, 10, 4),
                SnoozeTier(30, 5, 8),
                SnoozeTier(60, 2, 14),
                SnoozeTier(120, 1, 24),
            ),
            phrase_source=FixedPhraseSource(
                (
                    "Sleep matters more than one more video.",
                    "Tomorrow deserves a rested version of me.",
                    "Staying up later steals energy from the morning I want.",
                    "I will feel better tomorrow if I stop now and let sleep do its job.",
                )
            ),
        )

        self.assertEqual(decision.tier_index, 0)
        self.assertEqual(decision.tier.duration_minutes, 10)
        self.assertEqual(
            decision.passphrase, "Sleep matters more than one more video."
        )

    def test_snooze_tier_advances_with_minutes_since_bedtime(self) -> None:
        decision = choose_snooze_decision(
            minutes_since_bedtime=61,
            tiers=(
                SnoozeTier(0, 10, 4),
                SnoozeTier(30, 5, 8),
                SnoozeTier(60, 2, 14),
                SnoozeTier(120, 1, 24),
            ),
        )

        self.assertEqual(decision.tier_index, 2)
        self.assertEqual(decision.tier.duration_minutes, 2)
        self.assertEqual(decision.tier.passphrase_words, 14)

    def test_snooze_time_scale_accelerates_duration(self) -> None:
        decision = choose_snooze_decision(
            minutes_since_bedtime=5,
            tiers=(SnoozeTier(0, 10, 4),),
            time_scale=0.2,
        )

        self.assertEqual(decision.tier.duration_minutes, 2)

    def test_matches_passphrase_is_case_sensitive(self) -> None:
        self.assertTrue(
            matches_passphrase(
                expected="Tomorrow deserves a rested version of me.",
                entered="Tomorrow deserves a rested version of me.",
            )
        )
        self.assertFalse(
            matches_passphrase(
                expected="Tomorrow deserves a rested version of me.",
                entered="tomorrow deserves a rested version of me.",
            )
        )


if __name__ == "__main__":
    unittest.main()
