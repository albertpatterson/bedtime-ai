from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, time, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from src.bedtime_guard.schedule import DebugMode, ScheduleConfig, SchedulePhase
from src.bedtime_guard.state import load_runtime_state
from src.bedtime_guard.ui.guard_screen import (
    GuardAppController,
    build_config_from_args,
    compute_guard_view_model,
    format_duration,
    main,
)


TZ = ZoneInfo("America/Chicago")


class GuardScreenTests(unittest.TestCase):
    def test_format_duration_handles_hours_minutes_and_seconds(self) -> None:
        self.assertEqual(format_duration(timedelta(hours=2, minutes=5)), "2h 05m")
        self.assertEqual(format_duration(timedelta(minutes=7, seconds=4)), "7m 04s")
        self.assertEqual(format_duration(timedelta(seconds=9)), "9s")

    def test_compute_guard_view_model_exposes_guard_details(self) -> None:
        config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
            debug_mode=DebugMode.BEDTIME_NOW,
            time_scale=1 / 60,
        )
        now = datetime(2026, 7, 4, 12, 0, tzinfo=TZ)

        snapshot, decision, model = compute_guard_view_model(now=now, config=config)

        self.assertEqual(snapshot.phase.value, "guarded")
        self.assertEqual(decision.tier.duration_minutes, 1)
        self.assertIn("Current time:", model.current_time_text)
        self.assertIn("Time since bedtime: 0s", model.time_since_bedtime_text)
        self.assertIn("Automatic release:", model.release_time_text)
        self.assertEqual(model.debug_text, "Debug schedule active")
        self.assertEqual(model.escape_hint_text, "Esc exits immediately in debug mode.")
        self.assertTrue(model.debug_escape_enabled)
        self.assertEqual(model.snooze_button_text, "Snooze")
        self.assertFalse(model.snooze_prompt_visible)
        self.assertIn("Type the current passphrase", model.snooze_instruction_text)
        self.assertEqual(model.snooze_phrase_text, "Sleep!")
        self.assertEqual(model.snooze_feedback_text, "")

    def test_compute_guard_view_model_disables_escape_hint_outside_debug(self) -> None:
        config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
        )
        now = datetime(2026, 7, 4, 22, 45, tzinfo=TZ)

        _, _, model = compute_guard_view_model(now=now, config=config)

        self.assertEqual(model.debug_text, "")
        self.assertEqual(model.escape_hint_text, "")
        self.assertFalse(model.debug_escape_enabled)

    def test_compute_guard_view_model_can_show_snooze_prompt_feedback(self) -> None:
        config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
            debug_mode=DebugMode.BEDTIME_NOW,
            time_scale=1 / 60,
        )
        now = datetime(2026, 7, 4, 12, 0, tzinfo=TZ)

        _, _, model = compute_guard_view_model(
            now=now,
            config=config,
            snooze_prompt_visible=True,
            snooze_feedback_text="Passphrase did not match. Try again.",
        )

        self.assertTrue(model.snooze_prompt_visible)
        self.assertEqual(
            model.snooze_feedback_text, "Passphrase did not match. Try again."
        )

    def test_debug_release_time_stays_fixed_without_snooze(self) -> None:
        config = ScheduleConfig(
            bedtime=time(22, 30),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
            debug_mode=DebugMode.BEDTIME_NOW,
            time_scale=1 / 60,
        )
        start = datetime(2026, 7, 4, 12, 0, tzinfo=TZ)
        fixed_bedtime = start

        first_snapshot, _, _ = compute_guard_view_model(
            now=start,
            config=config,
            bedtime_at_override=fixed_bedtime,
        )
        later_snapshot, _, _ = compute_guard_view_model(
            now=datetime(2026, 7, 4, 12, 2, tzinfo=TZ),
            config=config,
            bedtime_at_override=fixed_bedtime,
        )

        self.assertEqual(first_snapshot.release_at, later_snapshot.release_at)
        self.assertEqual(later_snapshot.time_since_bedtime, timedelta(minutes=2))

    def test_default_debug_mode_starts_in_wind_down(self) -> None:
        args = Mock(
            bedtime="21:45",
            wind_down_minutes=20,
            wakeup_hours_after_last_snooze=4.5,
            debug_mode="bedtime_in_10_minutes",
            time_scale=1 / 60,
        )

        config = build_config_from_args(args)
        snapshot, _, _ = compute_guard_view_model(
            now=datetime(2026, 7, 4, 12, 0, tzinfo=TZ),
            config=config,
        )

        self.assertEqual(snapshot.phase, SchedulePhase.WIND_DOWN)

    def test_build_config_from_args_uses_cli_values(self) -> None:
        args = Mock(
            bedtime="21:45",
            wind_down_minutes=20,
            wakeup_hours_after_last_snooze=4.5,
            debug_mode="bedtime_in_10_minutes",
            time_scale=0.5,
        )

        config = build_config_from_args(args)

        self.assertEqual(config.bedtime, time(21, 45))
        self.assertEqual(config.wind_down_minutes, 20)
        self.assertEqual(config.wakeup_hours_after_last_snooze, 4.5)
        self.assertEqual(config.debug_mode, DebugMode.BEDTIME_IN_10_MINUTES)
        self.assertEqual(config.time_scale, 0.5)

    def test_guard_controller_quits_when_schedule_releases(self) -> None:
        app = Mock()
        timer = Mock()
        windows = [Mock(), Mock()]
        config = ScheduleConfig(
            bedtime=time(12, 0),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
            debug_mode=DebugMode.OFF,
            time_scale=1 / 60,
        )
        times = iter(
            (
                datetime(2026, 7, 4, 12, 0, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 0, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 6, tzinfo=TZ),
            )
        )

        with (
            patch("src.bedtime_guard.ui.guard_screen.QTimer", return_value=timer),
            patch.object(GuardAppController, "_build_windows", return_value=windows),
            patch("src.bedtime_guard.ui.guard_screen.ReactivationController"),
        ):
            controller = GuardAppController(
                app=app,
                config=config,
                now_provider=lambda: next(times),
            )

        self.assertEqual(controller.windows, windows)
        for window in windows:
            window.set_view_model.assert_called_once()

        controller.refresh()

        timer.stop.assert_called()
        for window in windows:
            window.close.assert_called_once()
        app.quit.assert_called()

    def test_wind_down_shows_warning_and_bedtime_transition_shows_guard(self) -> None:
        app = Mock()
        timer = Mock()
        warning_window = Mock()
        guard_window = Mock()
        config = ScheduleConfig(
            bedtime=time(12, 0),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
            debug_mode=DebugMode.OFF,
            time_scale=1 / 60,
        )
        times = iter(
            (
                datetime(2026, 7, 4, 11, 59, 45, tzinfo=TZ),
                datetime(2026, 7, 4, 11, 59, 45, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 0, 0, tzinfo=TZ),
            )
        )

        with (
            patch("src.bedtime_guard.ui.guard_screen.QTimer", return_value=timer),
            patch.object(
                GuardAppController, "_build_warning_window", return_value=warning_window
            ),
            patch.object(GuardAppController, "_build_windows", return_value=[guard_window]),
            patch("src.bedtime_guard.ui.guard_screen.ReactivationController"),
        ):
            controller = GuardAppController(
                app=app,
                config=config,
                now_provider=lambda: next(times),
            )
            warning_window.set_view_model.assert_called_once()
            warning_window.show_warning.assert_called_once()

            controller.refresh()

            warning_window.close.assert_called_once()
            guard_window.set_view_model.assert_called_once()

    def test_logging_captures_warning_guard_and_release_flow(self) -> None:
        app = Mock()
        timer = Mock()
        warning_window = Mock()
        guard_window = Mock()
        config = ScheduleConfig(
            bedtime=time(12, 0),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
            debug_mode=DebugMode.OFF,
            time_scale=1 / 60,
        )
        times = iter(
            (
                datetime(2026, 7, 4, 11, 59, 45, tzinfo=TZ),
                datetime(2026, 7, 4, 11, 59, 45, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 0, 0, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 6, 0, tzinfo=TZ),
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "events.jsonl"
            state_path = Path(tmpdir) / "state.json"

            with (
                patch("src.bedtime_guard.ui.guard_screen.QTimer", return_value=timer),
                patch.object(
                    GuardAppController,
                    "_build_warning_window",
                    return_value=warning_window,
                ),
                patch.object(
                    GuardAppController, "_build_windows", return_value=[guard_window]
                ),
                patch("src.bedtime_guard.ui.guard_screen.ReactivationController"),
            ):
                controller = GuardAppController(
                    app=app,
                    config=config,
                    now_provider=lambda: next(times),
                    event_log_path=log_path,
                    state_path=state_path,
                )
                controller.refresh()
                controller.refresh()

            event_types = [
                json.loads(line)["event_type"]
                for line in log_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                event_types,
                ["warning_shown", "guard_activated", "released"],
            )
            state = load_runtime_state(state_path)
            self.assertEqual(state.last_known_phase, SchedulePhase.RELEASED.value)

    def test_incorrect_passphrase_does_not_activate_snooze(self) -> None:
        app = Mock()
        timer = Mock()
        window = Mock()
        window.isVisible.return_value = True
        config = ScheduleConfig(
            bedtime=time(12, 0),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
            debug_mode=DebugMode.OFF,
            time_scale=1 / 60,
        )
        now = datetime(2026, 7, 4, 12, 0, tzinfo=TZ)

        with (
            patch("src.bedtime_guard.ui.guard_screen.QTimer", return_value=timer),
            patch.object(GuardAppController, "_build_windows", return_value=[window]),
            patch("src.bedtime_guard.ui.guard_screen.ReactivationController"),
        ):
            controller = GuardAppController(
                app=app,
                config=config,
                now_provider=lambda: now,
            )

        controller.open_snooze_prompt()
        clear_calls_before_submit = window.clear_prompt_input.call_count
        result = controller.submit_passphrase("nope")

        self.assertFalse(result)
        self.assertTrue(controller._snooze_prompt_visible)
        self.assertEqual(
            controller._snooze_feedback_text, "Passphrase did not match. Try again."
        )
        self.assertIsNone(controller._active_snooze_expires_at)
        window.close.assert_not_called()
        self.assertEqual(window.clear_prompt_input.call_count, clear_calls_before_submit)
        window.focus_prompt_input.assert_called()

    def test_correct_passphrase_activates_snooze_and_expiry_returns_to_guarded(self) -> None:
        app = Mock()
        timer = Mock()
        window = Mock()
        window.isVisible.side_effect = [True, True, False]
        config = ScheduleConfig(
            bedtime=time(12, 0),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
            debug_mode=DebugMode.OFF,
            time_scale=0.2,
        )
        times = iter(
            (
                datetime(2026, 7, 4, 12, 0, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 0, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 0, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 1, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 2, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 4, tzinfo=TZ),
            )
        )

        with (
            patch("src.bedtime_guard.ui.guard_screen.QTimer", return_value=timer),
            patch.object(GuardAppController, "_build_windows", return_value=[window]),
            patch("src.bedtime_guard.ui.guard_screen.ReactivationController"),
        ):
            controller = GuardAppController(
                app=app,
                config=config,
                now_provider=lambda: next(times),
            )

        controller.open_snooze_prompt()
        result = controller.submit_passphrase("Sleep!")

        self.assertTrue(result)
        self.assertEqual(
            controller._active_snooze_expires_at,
            datetime(2026, 7, 4, 12, 3, tzinfo=TZ),
        )
        window.close.assert_called_once()
        self.assertEqual(controller.windows, [])

        replacement_window = Mock()
        replacement_window.isVisible.return_value = True
        with patch.object(
            GuardAppController, "_build_windows", return_value=[replacement_window]
        ):
            controller.refresh()

        self.assertEqual(controller.windows, [replacement_window])
        replacement_window.set_view_model.assert_called_once()

    def test_snooze_submission_logs_event_and_saves_runtime_state(self) -> None:
        app = Mock()
        timer = Mock()
        window = Mock()
        config = ScheduleConfig(
            bedtime=time(12, 0),
            wind_down_minutes=30,
            wakeup_hours_after_last_snooze=5,
            debug_mode=DebugMode.OFF,
            time_scale=0.2,
        )
        times = iter(
            (
                datetime(2026, 7, 4, 12, 0, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 0, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 0, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 1, tzinfo=TZ),
                datetime(2026, 7, 4, 12, 2, tzinfo=TZ),
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "events.jsonl"
            state_path = Path(tmpdir) / "state.json"

            with (
                patch("src.bedtime_guard.ui.guard_screen.QTimer", return_value=timer),
                patch.object(GuardAppController, "_build_windows", return_value=[window]),
                patch("src.bedtime_guard.ui.guard_screen.ReactivationController"),
            ):
                controller = GuardAppController(
                    app=app,
                    config=config,
                    now_provider=lambda: next(times),
                    event_log_path=log_path,
                    state_path=state_path,
                )

            controller.open_snooze_prompt()
            result = controller.submit_passphrase("Sleep!")

            self.assertTrue(result)
            event_types = [
                json.loads(line)["event_type"]
                for line in log_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(event_types, ["guard_activated", "snooze_started"])
            state = load_runtime_state(state_path)
            self.assertEqual(state.last_known_phase, SchedulePhase.SNOOZED.value)
            self.assertEqual(
                state.active_snooze_expires_at,
                datetime(2026, 7, 4, 12, 3, tzinfo=TZ),
            )

    def test_confirm_flag_is_required(self) -> None:
        with self.assertRaises(SystemExit) as context:
            main([])

        self.assertNotEqual(context.exception.code, 0)

    def test_main_returns_error_when_no_screens_detected(self) -> None:
        with (
            patch("src.bedtime_guard.ui.guard_screen.QApplication") as app_class,
            patch("src.bedtime_guard.ui.guard_screen.GuardAppController") as controller_class,
        ):
            app = app_class.return_value
            palette = Mock()
            app.palette.return_value = palette
            controller_class.return_value.has_visible_ui = False

            result = main(["--confirm"])

        self.assertEqual(result, 1)
        app.setPalette.assert_called_once()
        palette.setColor.assert_called_once()

    def test_main_allows_warning_first_debug_startup(self) -> None:
        with (
            patch("src.bedtime_guard.ui.guard_screen.QApplication") as app_class,
            patch("src.bedtime_guard.ui.guard_screen.GuardAppController") as controller_class,
        ):
            app = app_class.return_value
            palette = Mock()
            app.palette.return_value = palette
            app.exec.return_value = 0
            controller_class.return_value.has_visible_ui = True

            result = main(["--confirm"])

        self.assertEqual(result, 0)
        app.exec.assert_called_once()


if __name__ == "__main__":
    unittest.main()
