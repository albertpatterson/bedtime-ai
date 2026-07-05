from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import time
from pathlib import Path

from src.bedtime_guard.config_files import render_default_policy
from src.bedtime_guard.policy import load_policy, update_policy_schedule
from src.bedtime_guard.set_schedule import main


class SetScheduleTests(unittest.TestCase):
    def test_update_policy_schedule_can_preserve_existing_wind_down_minutes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text(render_default_policy(), encoding="utf-8")
            policy = load_policy(config_path)

        updated = update_policy_schedule(policy, bedtime=time(21, 45))

        self.assertEqual(updated.schedule.bedtime.hour, 21)
        self.assertEqual(updated.schedule.bedtime.minute, 45)
        self.assertEqual(
            updated.schedule.wind_down_minutes,
            policy.schedule.wind_down_minutes,
        )

    def test_main_updates_bedtime_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            event_log_path = Path(tmpdir) / "events.jsonl"
            config_path.write_text(render_default_policy(), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "--config-path",
                        str(config_path),
                        "--event-log",
                        str(event_log_path),
                        "--bedtime",
                        "21:15",
                    ]
                )

            policy = load_policy(config_path)

        self.assertEqual(result, 0)
        self.assertEqual(policy.schedule.bedtime.isoformat(timespec="minutes"), "21:15")
        self.assertEqual(policy.schedule.wind_down_minutes, 30)

    def test_main_updates_bedtime_and_wind_down_minutes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            event_log_path = Path(tmpdir) / "events.jsonl"
            config_path.write_text(render_default_policy(), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "--config-path",
                        str(config_path),
                        "--event-log",
                        str(event_log_path),
                        "--bedtime",
                        "23:05",
                        "--wind-down-minutes",
                        "45",
                    ]
                )

            policy = load_policy(config_path)

        self.assertEqual(result, 0)
        self.assertEqual(policy.schedule.bedtime.isoformat(timespec="minutes"), "23:05")
        self.assertEqual(policy.schedule.wind_down_minutes, 45)

    def test_main_bootstraps_missing_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            event_log_path = Path(tmpdir) / "events.jsonl"

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "--config-path",
                        str(config_path),
                        "--event-log",
                        str(event_log_path),
                        "--bedtime",
                        "22:10",
                    ]
                )

            policy = load_policy(config_path)
            exists = config_path.exists()

        self.assertEqual(result, 0)
        self.assertTrue(exists)
        self.assertEqual(policy.schedule.bedtime.isoformat(timespec="minutes"), "22:10")

    def test_main_logs_attempt_and_apply_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            event_log_path = Path(tmpdir) / "events.jsonl"
            config_path.write_text(render_default_policy(), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "--config-path",
                        str(config_path),
                        "--event-log",
                        str(event_log_path),
                        "--bedtime",
                        "21:00",
                    ]
                )

            policy = load_policy(config_path)
            events = [
                json.loads(line)
                for line in event_log_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(result, 0)
        self.assertEqual(policy.schedule.bedtime.isoformat(timespec="minutes"), "21:00")
        self.assertEqual(
            [event["event_type"] for event in events],
            ["schedule_change_attempted", "schedule_change_applied"],
        )


if __name__ == "__main__":
    unittest.main()
