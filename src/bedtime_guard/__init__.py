"""Bedtime Guard core package."""

from .events import EventRecord, append_event_record, build_event_record
from .platforms import (
    PlatformAction,
    PlatformActionKind,
    PlatformAdapter,
    RecordedPlatformAdapter,
    plan_phase_actions,
)
from .policy import BedtimeGuardPolicy, load_policy
from .schedule import (
    DebugMode,
    ScheduleConfig,
    SchedulePhase,
    ScheduleSnapshot,
    compute_schedule_snapshot,
)
from .state import RuntimeState, load_runtime_state, save_runtime_state
from .snooze import (
    FixedPhraseSource,
    SnoozeDecision,
    SnoozeTier,
    choose_snooze_decision,
    matches_passphrase,
)

__all__ = [
    "DebugMode",
    "BedtimeGuardPolicy",
    "EventRecord",
    "FixedPhraseSource",
    "PlatformAction",
    "PlatformActionKind",
    "PlatformAdapter",
    "RuntimeState",
    "RecordedPlatformAdapter",
    "ScheduleConfig",
    "SchedulePhase",
    "ScheduleSnapshot",
    "append_event_record",
    "build_event_record",
    "SnoozeDecision",
    "SnoozeTier",
    "choose_snooze_decision",
    "compute_schedule_snapshot",
    "load_policy",
    "load_runtime_state",
    "matches_passphrase",
    "plan_phase_actions",
    "save_runtime_state",
]
