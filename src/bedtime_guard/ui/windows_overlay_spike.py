from __future__ import annotations

import argparse
import sys

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget


OVERLAY_TEXT = (
    "Bedtime Guard Windows Overlay Spike\n"
    "Esc closes this spike.\n"
    "This is a feasibility check for full-screen coverage, topmost behavior,\n"
    "and reactivation after app switching on Windows."
)


class OverlayWindow(QWidget):
    def __init__(self, screen_name: str) -> None:
        super().__init__()
        self.setWindowTitle(f"Bedtime Guard Windows Overlay Spike - {screen_name}")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setStyleSheet(
            "background-color: rgba(12, 18, 24, 244);"
            "color: #f4f2ea;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addStretch()

        label = QLabel(OVERLAY_TEXT)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setFont(QFont("Segoe UI", 26))
        layout.addWidget(label)
        layout.addStretch()

        shortcut = QShortcut(QKeySequence("Escape"), self)
        shortcut.activated.connect(QApplication.instance().quit)


def reactivate_windows(windows: list[OverlayWindow]) -> None:
    for window in windows:
        if not window.isVisible():
            continue
        window.showFullScreen()
        window.raise_()
        window.activateWindow()


class ReactivationController:
    def __init__(self, app: QApplication, windows: list[OverlayWindow]) -> None:
        self._windows = windows
        self._timer = QTimer(app)
        self._timer.setInterval(1500)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._reactivate)
        app.applicationStateChanged.connect(self._handle_application_state_changed)

    def _handle_application_state_changed(self, state: Qt.ApplicationState) -> None:
        if state == Qt.ApplicationState.ApplicationActive:
            self._timer.stop()
            return
        self._timer.start()

    def _reactivate(self) -> None:
        reactivate_windows(self._windows)


def build_windows() -> list[OverlayWindow]:
    windows: list[OverlayWindow] = []
    for screen in QGuiApplication.screens():
        geometry = screen.geometry()
        window = OverlayWindow(screen.name())
        window.setGeometry(geometry)
        window.showFullScreen()
        windows.append(window)
    return windows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required safety flag so the spike is not launched by accident.",
    )
    args = parser.parse_args(argv)
    if not args.confirm:
        parser.error("pass --confirm to launch the Windows overlay spike")

    app = QApplication(sys.argv)
    app.setApplicationName("Bedtime Guard Windows Overlay Spike")
    app.setOrganizationName("BedtimeGuard")
    app.setQuitOnLastWindowClosed(True)
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(12, 18, 24, 244))
    app.setPalette(palette)

    windows = build_windows()
    if not windows:
        print("No screens detected; Windows overlay spike did not launch.", file=sys.stderr)
        return 1
    app._reactivation_controller = ReactivationController(app, windows)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
