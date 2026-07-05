from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Callable

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from bedtime_guard.events import append_event_record, build_event_record
from bedtime_guard.platforms import warning_message
from bedtime_guard.schedule import DebugMode, ScheduleConfig, SchedulePhase, ScheduleSnapshot, compute_schedule_snapshot
from bedtime_guard.state import RuntimeState, save_runtime_state
from bedtime_guard.snooze import (
    FixedPhraseSource,
    SnoozeDecision,
    SnoozeTier,
    choose_snooze_decision,
    matches_passphrase,
)


DEFAULT_SNOOZE_TIERS = (
    SnoozeTier(0, 10, 4),
    SnoozeTier(30, 5, 8),
    SnoozeTier(60, 2, 14),
    SnoozeTier(120, 1, 24),
)


@dataclass(frozen=True)
class WarningViewModel:
    title_text: str
    body_text: str
    dismiss_text: str
    debug_text: str


@dataclass(frozen=True)
class GuardViewModel:
    status_text: str
    current_time_text: str
    time_since_bedtime_text: str
    release_time_text: str
    debug_text: str
    escape_hint_text: str
    debug_escape_enabled: bool
    snooze_button_text: str
    snooze_prompt_visible: bool
    snooze_instruction_text: str
    snooze_phrase_text: str
    snooze_feedback_text: str


def format_clock(moment: datetime) -> str:
    return moment.strftime("%I:%M:%S %p").lstrip("0")


def format_duration(delta: timedelta) -> str:
    total_seconds = max(0, int(delta.total_seconds()))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {seconds:02d}s"
    return f"{seconds}s"


def minutes_since_bedtime(snapshot: ScheduleSnapshot) -> int:
    return max(0, int(snapshot.time_since_bedtime.total_seconds() // 60))


def build_warning_view_model(
    *, snapshot: ScheduleSnapshot, dismissed: bool = False
) -> WarningViewModel:
    debug_text = "Debug schedule active" if snapshot.debug_enabled else ""
    return WarningViewModel(
        title_text="Bedtime is approaching",
        body_text=warning_message(snapshot),
        dismiss_text="Dismiss",
        debug_text=debug_text if not dismissed else "",
    )


def build_guard_view_model(
    *,
    now: datetime,
    snapshot: ScheduleSnapshot,
    snooze_decision: SnoozeDecision,
    snooze_prompt_visible: bool = False,
    snooze_feedback_text: str = "",
) -> GuardViewModel:
    debug_text = "Debug schedule active" if snapshot.debug_enabled else ""
    return GuardViewModel(
        status_text="Bedtime guard active",
        current_time_text=f"Current time: {format_clock(now)}",
        time_since_bedtime_text=(
            f"Time since bedtime: {format_duration(snapshot.time_since_bedtime)}"
        ),
        release_time_text=f"Automatic release: {format_clock(snapshot.release_at)}",
        debug_text=debug_text,
        escape_hint_text=(
            "Esc exits immediately in debug mode." if snapshot.debug_enabled else ""
        ),
        debug_escape_enabled=snapshot.debug_enabled,
        snooze_button_text="Snooze",
        snooze_prompt_visible=snooze_prompt_visible,
        snooze_instruction_text=(
            f"Type the current passphrase to snooze for "
            f"{snooze_decision.tier.duration_minutes} minute"
            f"{'' if snooze_decision.tier.duration_minutes == 1 else 's'}."
        ),
        snooze_phrase_text=snooze_decision.passphrase,
        snooze_feedback_text=snooze_feedback_text,
    )


def compute_guard_view_model(
    *,
    now: datetime,
    config: ScheduleConfig,
    tiers: tuple[SnoozeTier, ...] = DEFAULT_SNOOZE_TIERS,
    phrase_source: FixedPhraseSource | None = None,
    last_snooze_at: datetime | None = None,
    active_snooze_expires_at: datetime | None = None,
    bedtime_at_override: datetime | None = None,
    snooze_prompt_visible: bool = False,
    snooze_feedback_text: str = "",
) -> tuple[ScheduleSnapshot, SnoozeDecision, GuardViewModel]:
    snapshot = compute_schedule_snapshot(
        now=now,
        config=config,
        last_snooze_at=last_snooze_at,
        active_snooze_expires_at=active_snooze_expires_at,
        bedtime_at_override=bedtime_at_override,
    )
    snooze_decision = choose_snooze_decision(
        minutes_since_bedtime=minutes_since_bedtime(snapshot),
        tiers=tiers,
        phrase_source=phrase_source,
        time_scale=config.time_scale,
    )
    return snapshot, snooze_decision, build_guard_view_model(
        now=now,
        snapshot=snapshot,
        snooze_decision=snooze_decision,
        snooze_prompt_visible=snooze_prompt_visible,
        snooze_feedback_text=snooze_feedback_text,
    )


class WarningWindow(QWidget):
    def __init__(self, *, on_dismissed: Callable[[], None]) -> None:
        super().__init__()
        self.setWindowTitle("Bedtime Warning")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setStyleSheet(
            "background-color: rgba(250, 245, 235, 248);"
            "color: #1d252d;"
        )
        self.resize(420, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        self._title_label = QLabel()
        self._title_label.setFont(QFont("Helvetica Neue", 24, QFont.Weight.DemiBold))
        layout.addWidget(self._title_label)

        self._body_label = QLabel()
        self._body_label.setWordWrap(True)
        self._body_label.setFont(QFont("Helvetica Neue", 16))
        layout.addWidget(self._body_label)

        self._debug_label = QLabel()
        self._debug_label.setFont(QFont("Helvetica Neue", 13))
        self._debug_label.setStyleSheet("color: #8f5f2e;")
        layout.addWidget(self._debug_label)

        self._dismiss_button = QPushButton("Dismiss")
        self._dismiss_button.setFixedHeight(42)
        self._dismiss_button.setStyleSheet(
            "QPushButton {"
            "background-color: #1d252d;"
            "color: #f5f0e7;"
            "border: none;"
            "border-radius: 6px;"
            "padding: 8px 14px;"
            "font-size: 16px;"
            "font-weight: 600;"
            "}"
        )
        self._dismiss_button.clicked.connect(on_dismissed)
        layout.addWidget(self._dismiss_button)

    def show_warning(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def set_view_model(self, model: WarningViewModel) -> None:
        self._title_label.setText(model.title_text)
        self._body_label.setText(model.body_text)
        self._dismiss_button.setText(model.dismiss_text)
        self._debug_label.setText(model.debug_text)
        self._debug_label.setVisible(bool(model.debug_text))


class GuardWindow(QWidget):
    def __init__(
        self,
        screen_name: str,
        *,
        on_snooze_requested: Callable[[], None],
        on_passphrase_submitted: Callable[[str], None],
    ) -> None:
        super().__init__()
        self.setWindowTitle(f"Bedtime Guard - {screen_name}")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setStyleSheet(
            "background-color: rgba(12, 18, 24, 238);"
            "color: #f4f2ea;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(16)
        layout.addStretch()

        self._status_label = QLabel()
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setFont(QFont("Helvetica Neue", 32, QFont.Weight.DemiBold))
        layout.addWidget(self._status_label)

        self._details_label = QLabel()
        self._details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._details_label.setWordWrap(True)
        self._details_label.setFont(QFont("Helvetica Neue", 22))
        layout.addWidget(self._details_label)

        self._debug_label = QLabel()
        self._debug_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._debug_label.setFont(QFont("Helvetica Neue", 16))
        self._debug_label.setStyleSheet("color: #d3b970;")
        layout.addWidget(self._debug_label)

        self._snooze_button = QPushButton("Snooze")
        self._snooze_button.setFixedHeight(52)
        self._snooze_button.setStyleSheet(
            "QPushButton {"
            "background-color: #f4f2ea;"
            "color: #0c1218;"
            "border: none;"
            "border-radius: 6px;"
            "padding: 10px 18px;"
            "font-size: 18px;"
            "font-weight: 600;"
            "}"
            "QPushButton:pressed { background-color: #ddd8ca; }"
        )
        self._snooze_button.clicked.connect(on_snooze_requested)
        layout.addWidget(self._snooze_button)

        self._snooze_instruction_label = QLabel()
        self._snooze_instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._snooze_instruction_label.setWordWrap(True)
        self._snooze_instruction_label.setFont(QFont("Helvetica Neue", 18))
        layout.addWidget(self._snooze_instruction_label)

        self._snooze_phrase_label = QLabel()
        self._snooze_phrase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._snooze_phrase_label.setWordWrap(True)
        self._snooze_phrase_label.setFont(QFont("Helvetica Neue", 18, QFont.Weight.Medium))
        self._snooze_phrase_label.setStyleSheet("color: #f0db92;")
        layout.addWidget(self._snooze_phrase_label)

        self._passphrase_input = QLineEdit()
        self._passphrase_input.setMinimumHeight(46)
        self._passphrase_input.setStyleSheet(
            "QLineEdit {"
            "background-color: rgba(244, 242, 234, 0.08);"
            "color: #f4f2ea;"
            "border: 1px solid rgba(244, 242, 234, 0.24);"
            "border-radius: 6px;"
            "padding: 10px 12px;"
            "font-size: 18px;"
            "}"
        )
        self._passphrase_input.returnPressed.connect(self._submit_passphrase)
        layout.addWidget(self._passphrase_input)

        self._submit_button = QPushButton("Submit passphrase")
        self._submit_button.setFixedHeight(48)
        self._submit_button.setStyleSheet(
            "QPushButton {"
            "background-color: rgba(244, 242, 234, 0.12);"
            "color: #f4f2ea;"
            "border: 1px solid rgba(244, 242, 234, 0.28);"
            "border-radius: 6px;"
            "padding: 10px 18px;"
            "font-size: 17px;"
            "}"
        )
        self._submit_button.clicked.connect(self._submit_passphrase)
        layout.addWidget(self._submit_button)

        self._snooze_feedback_label = QLabel()
        self._snooze_feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._snooze_feedback_label.setWordWrap(True)
        self._snooze_feedback_label.setFont(QFont("Helvetica Neue", 16))
        self._snooze_feedback_label.setStyleSheet("color: #efb39b;")
        layout.addWidget(self._snooze_feedback_label)

        self._exit_label = QLabel()
        self._exit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._exit_label.setFont(QFont("Helvetica Neue", 16))
        self._exit_label.setStyleSheet("color: #a6adbb;")
        layout.addWidget(self._exit_label)
        layout.addStretch()

        self._prompt_widgets = (
            self._snooze_instruction_label,
            self._snooze_phrase_label,
            self._passphrase_input,
            self._submit_button,
            self._snooze_feedback_label,
        )
        self._on_passphrase_submitted = on_passphrase_submitted
        self._set_prompt_visible(False)
        self._escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self._escape_shortcut.activated.connect(QApplication.instance().quit)
        self._escape_shortcut.setEnabled(False)

    def _submit_passphrase(self) -> None:
        self._on_passphrase_submitted(self._passphrase_input.text())

    def _set_prompt_visible(self, visible: bool) -> None:
        for widget in self._prompt_widgets:
            widget.setVisible(visible)

    def clear_prompt_input(self) -> None:
        self._passphrase_input.clear()

    def focus_prompt_input(self) -> None:
        self._passphrase_input.setFocus(Qt.FocusReason.OtherFocusReason)

    def show_guard(self) -> None:
        self.showFullScreen()

    def set_view_model(self, model: GuardViewModel) -> None:
        self._status_label.setText(model.status_text)
        self._details_label.setText(
            "\n".join(
                (
                    model.current_time_text,
                    model.time_since_bedtime_text,
                    model.release_time_text,
                )
            )
        )
        self._debug_label.setText(model.debug_text)
        self._debug_label.setVisible(bool(model.debug_text))
        self._snooze_button.setText(model.snooze_button_text)
        self._snooze_button.setVisible(not model.snooze_prompt_visible)
        self._snooze_instruction_label.setText(model.snooze_instruction_text)
        self._snooze_phrase_label.setText(model.snooze_phrase_text)
        self._snooze_feedback_label.setText(model.snooze_feedback_text)
        self._snooze_feedback_label.setVisible(bool(model.snooze_feedback_text))
        self._set_prompt_visible(model.snooze_prompt_visible)
        self._exit_label.setText(model.escape_hint_text)
        self._exit_label.setVisible(bool(model.escape_hint_text))
        self._escape_shortcut.setEnabled(model.debug_escape_enabled)


def reactivate_windows(windows: list[GuardWindow]) -> None:
    for window in windows:
        if not window.isVisible():
            continue
        window.showFullScreen()
        window.raise_()
        window.activateWindow()


class ReactivationController:
    def __init__(self, app: QApplication, windows: list[GuardWindow]) -> None:
        self._windows = windows
        self._enabled = True
        self._timer = QTimer(app)
        self._timer.setInterval(1500)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._reactivate)
        app.applicationStateChanged.connect(self._handle_application_state_changed)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self._timer.stop()

    def _handle_application_state_changed(self, state: Qt.ApplicationState) -> None:
        if not self._enabled:
            return
        if state == Qt.ApplicationState.ApplicationActive:
            self._timer.stop()
            return
        self._timer.start()

    def _reactivate(self) -> None:
        if not self._enabled:
            return
        reactivate_windows(self._windows)


class GuardAppController:
    def __init__(
        self,
        *,
        app: QApplication,
        config: ScheduleConfig,
        tiers: tuple[SnoozeTier, ...] = DEFAULT_SNOOZE_TIERS,
        phrase_source: FixedPhraseSource | None = None,
        now_provider: Callable[[], datetime] | None = None,
        last_snooze_at: datetime | None = None,
        active_snooze_expires_at: datetime | None = None,
        event_log_path: Path | None = None,
        state_path: Path | None = None,
    ) -> None:
        self._app = app
        self._config = config
        self._tiers = tiers
        self._phrase_source = phrase_source
        self._now_provider = now_provider or datetime.now
        self._event_log_path = event_log_path
        self._state_path = state_path
        self._last_snooze_at = last_snooze_at
        self._active_snooze_expires_at = active_snooze_expires_at
        self._snooze_prompt_visible = False
        self._snooze_feedback_text = ""
        self._warning_dismissed = False
        self._warning_window: WarningWindow | None = None
        self._previous_phase: SchedulePhase | None = None
        self._bedtime_at_override = compute_schedule_snapshot(
            now=self._now_provider(),
            config=config,
            last_snooze_at=last_snooze_at,
            active_snooze_expires_at=active_snooze_expires_at,
        ).bedtime_at
        self._windows: list[GuardWindow] = []
        self._reactivation_controller = ReactivationController(app, self._windows)
        self._refresh_timer = QTimer(app)
        self._refresh_timer.setInterval(1000)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start()
        self.refresh()

    @property
    def windows(self) -> list[GuardWindow]:
        return self._windows

    @property
    def has_visible_ui(self) -> bool:
        return bool(self._windows) or self._warning_window is not None

    def _build_windows(self) -> list[GuardWindow]:
        windows: list[GuardWindow] = []
        for screen in QGuiApplication.screens():
            window = GuardWindow(
                screen.name(),
                on_snooze_requested=self.open_snooze_prompt,
                on_passphrase_submitted=self.submit_passphrase,
            )
            window.setGeometry(screen.geometry())
            window.show_guard()
            windows.append(window)
        return windows

    def _build_warning_window(self) -> WarningWindow:
        window = WarningWindow(on_dismissed=self.dismiss_warning)
        primary_screen = QGuiApplication.primaryScreen()
        if primary_screen is not None:
            available = primary_screen.availableGeometry()
            x = available.x() + available.width() - window.width() - 24
            y = available.y() + 24
            window.move(x, y)
        return window

    def _ensure_warning_window(self) -> WarningWindow:
        if self._warning_window is None:
            self._warning_window = self._build_warning_window()
        return self._warning_window

    def _close_warning_window(self) -> None:
        if self._warning_window is None:
            return
        self._warning_window.close()
        self._warning_window = None

    def _save_runtime_state(self, phase: SchedulePhase) -> None:
        if self._state_path is None:
            return
        save_runtime_state(
            self._state_path,
            RuntimeState(
                last_snooze_at=self._last_snooze_at,
                active_snooze_expires_at=self._active_snooze_expires_at,
                last_known_phase=phase.value,
            ),
        )

    def _append_event(
        self, *, event_type: str, occurred_at: datetime, details: dict[str, object]
    ) -> None:
        if self._event_log_path is None:
            return
        append_event_record(
            self._event_log_path,
            build_event_record(
                event_type=event_type,
                occurred_at=occurred_at,
                details=details,
            ),
        )

    def _close_windows(self) -> None:
        for window in self._windows:
            window.close()
        self._windows = []

    def _ensure_windows(self) -> None:
        if self._windows:
            return
        self._windows = self._build_windows()
        self._reactivation_controller._windows = self._windows

    def dismiss_warning(self) -> None:
        self._warning_dismissed = True
        self._append_event(
            event_type="warning_dismissed",
            occurred_at=self._now_provider(),
            details={"phase": SchedulePhase.WIND_DOWN.value},
        )
        self._close_warning_window()

    def open_snooze_prompt(self) -> None:
        self._snooze_prompt_visible = True
        self._snooze_feedback_text = ""
        self.refresh()
        for window in self._windows:
            window.clear_prompt_input()
            window.focus_prompt_input()

    def submit_passphrase(self, entered: str) -> bool:
        now = self._now_provider()
        snapshot, decision, _ = compute_guard_view_model(
            now=now,
            config=self._config,
            tiers=self._tiers,
            phrase_source=self._phrase_source,
            last_snooze_at=self._last_snooze_at,
            active_snooze_expires_at=self._active_snooze_expires_at,
            bedtime_at_override=self._bedtime_at_override,
            snooze_prompt_visible=self._snooze_prompt_visible,
            snooze_feedback_text=self._snooze_feedback_text,
        )
        if not matches_passphrase(expected=decision.passphrase, entered=entered):
            self._snooze_prompt_visible = True
            self._snooze_feedback_text = "Passphrase did not match. Try again."
            self.refresh()
            for window in self._windows:
                window.focus_prompt_input()
            return False

        self._last_snooze_at = now
        self._active_snooze_expires_at = now + timedelta(
            minutes=decision.tier.duration_minutes
        )
        self._append_event(
            event_type="snooze_started",
            occurred_at=now,
            details={
                "phase": SchedulePhase.SNOOZED.value,
                "duration_minutes": decision.tier.duration_minutes,
                "snooze_expires_at": self._active_snooze_expires_at.isoformat(),
                "tier_index": decision.tier_index,
            },
        )
        self._snooze_prompt_visible = False
        self._snooze_feedback_text = ""
        for window in self._windows:
            window.clear_prompt_input()
        self.refresh()
        return True

    def refresh(self) -> None:
        now = self._now_provider()
        snapshot, _, model = compute_guard_view_model(
            now=now,
            config=self._config,
            tiers=self._tiers,
            phrase_source=self._phrase_source,
            last_snooze_at=self._last_snooze_at,
            active_snooze_expires_at=self._active_snooze_expires_at,
            bedtime_at_override=self._bedtime_at_override,
            snooze_prompt_visible=self._snooze_prompt_visible,
            snooze_feedback_text=self._snooze_feedback_text,
        )
        if snapshot.phase != self._previous_phase:
            event_type = {
                SchedulePhase.WIND_DOWN: "warning_shown",
                SchedulePhase.GUARDED: "guard_activated",
                SchedulePhase.RELEASED: "released",
            }.get(snapshot.phase)
            if event_type is not None:
                self._append_event(
                    event_type=event_type,
                    occurred_at=now,
                    details={
                        "phase": snapshot.phase.value,
                        "bedtime_at": snapshot.bedtime_at.isoformat(),
                        "release_at": snapshot.release_at.isoformat(),
                        "debug_enabled": snapshot.debug_enabled,
                    },
                )
            self._save_runtime_state(snapshot.phase)
            if snapshot.phase == SchedulePhase.WIND_DOWN:
                self._warning_dismissed = False
            self._previous_phase = snapshot.phase
        if snapshot.phase == SchedulePhase.RELEASED:
            self._refresh_timer.stop()
            self._close_warning_window()
            self._close_windows()
            self._app.quit()
            return
        if snapshot.phase == SchedulePhase.WIND_DOWN:
            self._reactivation_controller.set_enabled(False)
            self._close_windows()
            if not self._warning_dismissed:
                warning_window = self._ensure_warning_window()
                warning_window.set_view_model(build_warning_view_model(snapshot=snapshot))
                warning_window.show_warning()
            return
        if snapshot.phase == SchedulePhase.SNOOZED:
            self._reactivation_controller.set_enabled(False)
            self._close_windows()
            return
        if snapshot.phase != SchedulePhase.GUARDED:
            self._refresh_timer.stop()
            self._close_warning_window()
            self._close_windows()
            self._app.quit()
            return
        self._close_warning_window()
        self._ensure_windows()
        self._reactivation_controller.set_enabled(True)
        for window in self._windows:
            window.set_view_model(model)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required safety flag so the guard prototype is not launched by accident.",
    )
    parser.add_argument(
        "--debug-mode",
        choices=[mode.value for mode in DebugMode],
        default=DebugMode.BEDTIME_IN_10_MINUTES.value,
        help="Schedule mode to use for the prototype run.",
    )
    parser.add_argument(
        "--time-scale",
        type=float,
        default=1 / 60,
        help="Multiplier applied to schedule and snooze timing.",
    )
    parser.add_argument(
        "--bedtime",
        default="22:30",
        help="Bedtime in HH:MM 24-hour format.",
    )
    parser.add_argument(
        "--wind-down-minutes",
        type=int,
        default=30,
        help="Minutes before bedtime when wind-down starts.",
    )
    parser.add_argument(
        "--wakeup-hours-after-last-snooze",
        type=float,
        default=5.0,
        help="Hours after bedtime or last snooze when the guard releases.",
    )
    parser.add_argument(
        "--event-log",
        default=".runtime/guard_events.jsonl",
        help="Path to the JSONL event log for the prototype run.",
    )
    parser.add_argument(
        "--state-path",
        default=".runtime/guard_state.json",
        help="Path to the runtime state file for the prototype run.",
    )
    args = parser.parse_args(argv)
    if not args.confirm:
        parser.error("pass --confirm to launch the guard prototype")
    return args


def build_config_from_args(args: argparse.Namespace) -> ScheduleConfig:
    return ScheduleConfig(
        bedtime=time.fromisoformat(args.bedtime),
        wind_down_minutes=args.wind_down_minutes,
        wakeup_hours_after_last_snooze=args.wakeup_hours_after_last_snooze,
        debug_mode=DebugMode(args.debug_mode),
        time_scale=args.time_scale,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    app = QApplication(sys.argv)
    app.setApplicationName("Bedtime Guard Prototype")
    app.setOrganizationName("BedtimeGuard")
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(12, 18, 24, 238))
    app.setPalette(palette)

    controller = GuardAppController(
        app=app,
        config=build_config_from_args(args),
        event_log_path=Path(args.event_log),
        state_path=Path(args.state_path),
    )
    if not controller.has_visible_ui:
        print("No screens detected; guard prototype did not launch.", file=sys.stderr)
        return 1
    app._guard_controller = controller
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
