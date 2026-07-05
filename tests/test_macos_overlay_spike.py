from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import Qt

from src.bedtime_guard.ui.macos_overlay_spike import (
    ReactivationController,
    main,
    reactivate_windows,
)


class MacOSOverlaySpikeTests(unittest.TestCase):
    def test_reactivate_windows_refreshes_visible_windows(self) -> None:
        visible_window = Mock()
        visible_window.isVisible.return_value = True
        hidden_window = Mock()
        hidden_window.isVisible.return_value = False

        reactivate_windows([visible_window, hidden_window])

        visible_window.showFullScreen.assert_called_once()
        visible_window.raise_.assert_called_once()
        visible_window.activateWindow.assert_called_once()
        hidden_window.showFullScreen.assert_not_called()

    def test_reactivation_controller_starts_timer_when_app_loses_activation(self) -> None:
        app = Mock()
        timer = Mock()

        with patch("src.bedtime_guard.ui.macos_overlay_spike.QTimer", return_value=timer):
            ReactivationController(app, [])

        handler = app.applicationStateChanged.connect.call_args.args[0]
        handler(Mock())

        timer.start.assert_called_once()

    def test_reactivation_controller_stops_timer_when_app_is_active(self) -> None:
        app = Mock()
        timer = Mock()

        with patch("src.bedtime_guard.ui.macos_overlay_spike.QTimer", return_value=timer):
            ReactivationController(app, [])

        handler = app.applicationStateChanged.connect.call_args.args[0]
        handler(Qt.ApplicationState.ApplicationActive)

        timer.stop.assert_called_once()

    def test_confirm_flag_is_required(self) -> None:
        with self.assertRaises(SystemExit) as context:
            main([])

        self.assertNotEqual(context.exception.code, 0)

    def test_main_returns_error_when_no_screens_detected(self) -> None:
        with (
            patch("src.bedtime_guard.ui.macos_overlay_spike.QApplication") as app_class,
            patch("src.bedtime_guard.ui.macos_overlay_spike.build_windows", return_value=[]),
        ):
            app = app_class.return_value
            palette = Mock()
            app.palette.return_value = palette

            result = main(["--confirm"])

        self.assertEqual(result, 1)
        app.setPalette.assert_called_once()
        palette.setColor.assert_called_once()


if __name__ == "__main__":
    unittest.main()
