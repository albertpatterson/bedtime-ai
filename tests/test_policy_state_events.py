from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.bedtime_guard.events import append_event_record, build_event_record
from src.bedtime_guard.policy import load_policy
from src.bedtime_guard.schedule import DebugMode
from src.bedtime_guard.state import RuntimeState, load_runtime_state, save_runtime_state


TZ = ZoneInfo("America/Chicago")


POLICY_TEXT = """\
[schedule]
bedtime = "22:30"
wind_down_minutes = 30
wakeup_hours_after_last_snooze = 5

[debug]
mode = "off"
time_scale = 1.0
debug_target_cycle_minutes = 5

[snooze]
enabled = true
uses_per_night = "unlimited"
require_passphrase = true
match_case_sensitive = true
allow_paste = true
phrase_source = "fixed_messages"

[[snooze.ladder]]
minutes_after_bedtime = 0
duration_minutes = 10
passphrase_words = 4

[[snooze.ladder]]
minutes_after_bedtime = 30
duration_minutes = 5
passphrase_words = 8

[guard]
mode = "full_screen"
cover_all_displays = true
require_snooze_for_desktop = true
close_apps = false

[settings]
require_extra_friction_during_guarded_hours = true
settings_change_friction = "current_snooze_passphrase"
"""


class PolicyStateEventsTests(unittest.TestCase):
    def test_load_policy_reads_expected_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "config.toml"
            policy_path.write_text(POLICY_TEXT, encoding="utf-8")

            policy = load_policy(policy_path)

        self.assertEqual(policy.schedule.bedtime.hour, 22)
        self.assertEqual(policy.schedule.debug_mode, DebugMode.OFF)
        self.assertEqual(policy.debug_target_cycle_minutes, 5)
        self.assertEqual(len(policy.snooze_tiers), 2)
        self.assertTrue(policy.match_case_sensitive)
        self.assertEqual(policy.settings_change_friction, "current_snooze_passphrase")

    def test_load_policy_rejects_missing_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "config.toml"
            policy_path.write_text("[schedule]\nbedtime = \"22:30\"\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_policy(policy_path)

    def test_runtime_state_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "state.json"
            state = RuntimeState(
                last_snooze_at=datetime(2026, 7, 4, 23, 0, tzinfo=TZ),
                active_snooze_expires_at=datetime(2026, 7, 4, 23, 10, tzinfo=TZ),
                last_known_phase="snoozed",
            )

            save_runtime_state(state_path, state)
            loaded = load_runtime_state(state_path)

        self.assertEqual(loaded, state)

    def test_load_runtime_state_defaults_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "missing.json"

            loaded = load_runtime_state(state_path)

        self.assertEqual(loaded, RuntimeState())

    def test_event_log_is_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "events.jsonl"
            record = build_event_record(
                event_type="guard_activated",
                occurred_at=datetime(2026, 7, 4, 22, 30, tzinfo=TZ),
                details={"phase": "guarded", "debug": False},
            )

            append_event_record(log_path, record)
            lines = log_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(lines), 1)
        self.assertIn('"event_type": "guard_activated"', lines[0])
        self.assertIn('"phase": "guarded"', lines[0])


if __name__ == "__main__":
    unittest.main()
