from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .schedule import SchedulePhase, ScheduleSnapshot


class PlatformActionKind(str, Enum):
    SHOW_WARNING = "show_warning"
    SHOW_GUARD = "show_guard"
    ENABLE_GUARD_REACTIVATION = "enable_guard_reactivation"
    HIDE_GUARD = "hide_guard"
    DISABLE_GUARD_REACTIVATION = "disable_guard_reactivation"
    CLEAR_WARNING = "clear_warning"


@dataclass(frozen=True)
class PlatformAction:
    kind: PlatformActionKind
    message: str


class PlatformAdapter(Protocol):
    def show_warning(self, message: str) -> None: ...

    def clear_warning(self) -> None: ...

    def show_guard(self, message: str) -> None: ...

    def enable_guard_reactivation(self) -> None: ...

    def disable_guard_reactivation(self) -> None: ...

    def hide_guard(self) -> None: ...

    def enable_autostart(self) -> None: ...

    def disable_autostart(self) -> None: ...

    def write_recovery_instructions(self, message: str) -> None: ...


@dataclass
class RecordedPlatformAdapter:
    """Simple recorder for boundary tests before any real UI exists."""

    actions: list[PlatformAction]

    def show_warning(self, message: str) -> None:
        self.actions.append(PlatformAction(PlatformActionKind.SHOW_WARNING, message))

    def clear_warning(self) -> None:
        self.actions.append(PlatformAction(PlatformActionKind.CLEAR_WARNING, ""))

    def show_guard(self, message: str) -> None:
        self.actions.append(PlatformAction(PlatformActionKind.SHOW_GUARD, message))

    def enable_guard_reactivation(self) -> None:
        self.actions.append(
            PlatformAction(PlatformActionKind.ENABLE_GUARD_REACTIVATION, "")
        )

    def disable_guard_reactivation(self) -> None:
        self.actions.append(
            PlatformAction(PlatformActionKind.DISABLE_GUARD_REACTIVATION, "")
        )

    def hide_guard(self) -> None:
        self.actions.append(PlatformAction(PlatformActionKind.HIDE_GUARD, ""))

    def enable_autostart(self) -> None:  # pragma: no cover - boundary placeholder
        return None

    def disable_autostart(self) -> None:  # pragma: no cover - boundary placeholder
        return None

    def write_recovery_instructions(
        self, message: str
    ) -> None:  # pragma: no cover - boundary placeholder
        return None


def guard_message(snapshot: ScheduleSnapshot) -> str:
    return (
        f"Bedtime guard active. "
        f"Release at {snapshot.release_at.isoformat()}. "
        f"Time since bedtime: {snapshot.time_since_bedtime}."
    )


def warning_message(snapshot: ScheduleSnapshot) -> str:
    remaining = snapshot.bedtime_at - snapshot.wind_down_starts_at - snapshot.time_since_bedtime
    return f"Bedtime is coming up. Remaining wind-down window: {remaining}."


def plan_phase_actions(
    *,
    previous_phase: SchedulePhase | None,
    snapshot: ScheduleSnapshot,
) -> tuple[PlatformAction, ...]:
    current_phase = snapshot.phase
    actions: list[PlatformAction] = []

    if current_phase == SchedulePhase.WIND_DOWN and previous_phase != SchedulePhase.WIND_DOWN:
        actions.append(
            PlatformAction(PlatformActionKind.SHOW_WARNING, warning_message(snapshot))
        )

    if current_phase == SchedulePhase.GUARDED and previous_phase != SchedulePhase.GUARDED:
        actions.append(PlatformAction(PlatformActionKind.CLEAR_WARNING, ""))
        actions.append(
            PlatformAction(PlatformActionKind.SHOW_GUARD, guard_message(snapshot))
        )
        actions.append(
            PlatformAction(PlatformActionKind.ENABLE_GUARD_REACTIVATION, "")
        )

    if current_phase == SchedulePhase.SNOOZED and previous_phase == SchedulePhase.GUARDED:
        actions.append(
            PlatformAction(PlatformActionKind.DISABLE_GUARD_REACTIVATION, "")
        )
        actions.append(PlatformAction(PlatformActionKind.HIDE_GUARD, ""))

    if current_phase == SchedulePhase.RELEASED and previous_phase != SchedulePhase.RELEASED:
        actions.append(PlatformAction(PlatformActionKind.CLEAR_WARNING, ""))
        actions.append(
            PlatformAction(PlatformActionKind.DISABLE_GUARD_REACTIVATION, "")
        )
        actions.append(PlatformAction(PlatformActionKind.HIDE_GUARD, ""))

    return tuple(actions)
