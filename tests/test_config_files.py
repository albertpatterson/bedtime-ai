from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.bedtime_guard.config_files import (
    default_app_paths,
    ensure_default_policy,
    main,
    render_default_policy,
)
from src.bedtime_guard.policy import load_policy


class ConfigFilesTests(unittest.TestCase):
    def test_default_app_paths_for_macos(self) -> None:
        home = Path("/Users/tester")

        paths = default_app_paths(platform="darwin", home=home)

        self.assertEqual(
            paths.config_path,
            home / "Library" / "Application Support" / "BedtimeGuard" / "config.toml",
        )
        self.assertEqual(
            paths.state_path,
            home / "Library" / "Application Support" / "BedtimeGuard" / "state.json",
        )
        self.assertEqual(
            paths.event_log_path,
            home / "Library" / "Logs" / "BedtimeGuard" / "guard_events.jsonl",
        )
        self.assertEqual(
            paths.recovery_instructions_path,
            home / "Library" / "Application Support" / "BedtimeGuard" / "RECOVERY.txt",
        )

    def test_default_app_paths_for_windows(self) -> None:
        home = Path("C:/Users/tester")
        appdata = Path("C:/Users/tester/AppData/Roaming")
        localappdata = Path("C:/Users/tester/AppData/Local")

        paths = default_app_paths(
            platform="win32",
            home=home,
            appdata=appdata,
            localappdata=localappdata,
        )

        self.assertEqual(paths.config_path, appdata / "BedtimeGuard" / "config.toml")
        self.assertEqual(paths.state_path, appdata / "BedtimeGuard" / "state.json")
        self.assertEqual(
            paths.event_log_path,
            localappdata / "BedtimeGuard" / "Logs" / "guard_events.jsonl",
        )
        self.assertEqual(
            paths.recovery_instructions_path,
            appdata / "BedtimeGuard" / "RECOVERY.txt",
        )

    def test_default_policy_is_parseable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "config.toml"
            policy_path.write_text(render_default_policy(), encoding="utf-8")

            policy = load_policy(policy_path)

        self.assertEqual(policy.schedule.bedtime.hour, 22)
        self.assertEqual(len(policy.snooze_tiers), 4)

    def test_ensure_default_policy_writes_once_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "config.toml"

            wrote_first = ensure_default_policy(policy_path)
            wrote_second = ensure_default_policy(policy_path)

        self.assertTrue(wrote_first)
        self.assertFalse(wrote_second)

    def test_main_can_write_default_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "--platform",
                        "darwin",
                        "--home-dir",
                        tmpdir,
                        "--write-default-config",
                    ]
                )

            expected_paths = default_app_paths(platform="darwin", home=Path(tmpdir))
            self.assertEqual(result, 0)
            self.assertTrue(expected_paths.config_path.exists())


if __name__ == "__main__":
    unittest.main()
