from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.run_schedule_change import main
from src.bedtime_guard.policy import load_policy


class RunScheduleChangeTests(unittest.TestCase):
    def test_wrapper_updates_bedtime_with_default_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "--home-dir",
                        tmpdir,
                        "--bedtime",
                        "21:40",
                    ]
                , interactive=False)

            policy = load_policy(
                Path(tmpdir)
                / "Library"
                / "Application Support"
                / "BedtimeGuard"
                / "config.toml"
            )

        self.assertEqual(result, 0)
        self.assertEqual(policy.schedule.bedtime.isoformat(timespec="minutes"), "21:40")

    def test_wrapper_can_use_current_passphrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "--home-dir",
                        tmpdir,
                        "--bedtime",
                        "21:00",
                        "--now",
                        "2026-07-05T22:45:00-05:00",
                    ],
                    interactive=False,
                )

            policy = load_policy(
                Path(tmpdir)
                / "Library"
                / "Application Support"
                / "BedtimeGuard"
                / "config.toml"
            )

        self.assertEqual(result, 0)
        self.assertEqual(policy.schedule.bedtime.isoformat(timespec="minutes"), "21:00")

    def test_wrapper_prompts_and_keeps_existing_values_on_blank_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            prompts = iter(["", "", ""])
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    ["--home-dir", tmpdir],
                    prompt=lambda _: next(prompts),
                    interactive=True,
                )

            policy = load_policy(
                Path(tmpdir)
                / "Library"
                / "Application Support"
                / "BedtimeGuard"
                / "config.toml"
            )

        self.assertEqual(result, 0)
        self.assertEqual(policy.schedule.bedtime.isoformat(timespec="minutes"), "22:30")
        self.assertEqual(policy.schedule.wind_down_minutes, 30)

    def test_wrapper_prompts_for_new_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            prompts = iter(["21:55", "25", ""])
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    ["--home-dir", tmpdir],
                    prompt=lambda _: next(prompts),
                    interactive=True,
                )

            policy = load_policy(
                Path(tmpdir)
                / "Library"
                / "Application Support"
                / "BedtimeGuard"
                / "config.toml"
            )

        self.assertEqual(result, 0)
        self.assertEqual(policy.schedule.bedtime.isoformat(timespec="minutes"), "21:55")
        self.assertEqual(policy.schedule.wind_down_minutes, 25)

    def test_wrapper_can_prompt_for_current_time_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            prompts = iter(["21:00", "30", ""])
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    ["--home-dir", tmpdir],
                    prompt=lambda _: next(prompts),
                    interactive=True,
                )

            output = stdout.getvalue()
            policy = load_policy(
                Path(tmpdir)
                / "Library"
                / "Application Support"
                / "BedtimeGuard"
                / "config.toml"
            )

        self.assertEqual(result, 0)
        self.assertIn("Event log path:", output)
        self.assertEqual(policy.schedule.bedtime.isoformat(timespec="minutes"), "21:00")


if __name__ == "__main__":
    unittest.main()
