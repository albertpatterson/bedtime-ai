from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum


class DebugMode(str, Enum):
    OFF = "off"
    BEDTIME_NOW = "bedtime_now"
    BEDTIME_IN_10_MINUTES = "bedtime_in_10_minutes"


class SchedulePhase(str, Enum):
    INACTIVE = "inactive"
    WIND_DOWN = "wind_down"
    GUARDED = "guarded"
    SNOOZED = "snoozed"
    RELEASED = "released"


@dataclass(frozen=True)
class ScheduleConfig:
    bedtime: time
    wind_down_minutes: int
    wakeup_hours_after_last_snooze: float
    debug_mode: DebugMode = DebugMode.OFF
    time_scale: float = 1.0

    def __post_init__(self) -> None:
        if self.wind_down_minutes < 0:
            raise ValueError("wind_down_minutes must be non-negative")
        if self.wakeup_hours_after_last_snooze <= 0:
            raise ValueError("wakeup_hours_after_last_snooze must be positive")
        if self.time_scale <= 0:
            raise ValueError("time_scale must be positive")


@dataclass(frozen=True)
class ScheduleSnapshot:
    phase: SchedulePhase
    bedtime_at: datetime
    wind_down_starts_at: datetime
    release_at: datetime
    snooze_expires_at: datetime | None
    time_since_bedtime: timedelta
    debug_enabled: bool


def _scaled_minutes(minutes: float, time_scale: float) -> timedelta:
    return timedelta(minutes=minutes * time_scale)


def _scaled_hours(hours: float, time_scale: float) -> timedelta:
    return timedelta(hours=hours * time_scale)


def _combine_today(now: datetime, bedtime: time) -> datetime:
    return datetime.combine(now.date(), bedtime, tzinfo=now.tzinfo)


def _effective_bedtime(now: datetime, config: ScheduleConfig) -> datetime:
    if config.debug_mode == DebugMode.BEDTIME_NOW:
        return now
    if config.debug_mode == DebugMode.BEDTIME_IN_10_MINUTES:
        return now + _scaled_minutes(10, config.time_scale)

    bedtime_today = _combine_today(now, config.bedtime)
    if now < bedtime_today:
        return bedtime_today
    return bedtime_today


def compute_schedule_snapshot(
    *,
    now: datetime,
    config: ScheduleConfig,
    last_snooze_at: datetime | None = None,
    active_snooze_expires_at: datetime | None = None,
    bedtime_at_override: datetime | None = None,
) -> ScheduleSnapshot:
    bedtime_at = bedtime_at_override or _effective_bedtime(now, config)
    wind_down_starts_at = bedtime_at - _scaled_minutes(
        config.wind_down_minutes, config.time_scale
    )

    wake_anchor = last_snooze_at or bedtime_at
    release_at = wake_anchor + _scaled_hours(
        config.wakeup_hours_after_last_snooze, config.time_scale
    )

    if now >= release_at:
        phase = SchedulePhase.RELEASED
    elif active_snooze_expires_at is not None and now < active_snooze_expires_at:
        phase = SchedulePhase.SNOOZED
    elif now >= bedtime_at:
        phase = SchedulePhase.GUARDED
    elif now >= wind_down_starts_at:
        phase = SchedulePhase.WIND_DOWN
    else:
        phase = SchedulePhase.INACTIVE

    if now >= bedtime_at:
        time_since_bedtime = now - bedtime_at
    else:
        time_since_bedtime = timedelta(0)

    return ScheduleSnapshot(
        phase=phase,
        bedtime_at=bedtime_at,
        wind_down_starts_at=wind_down_starts_at,
        release_at=release_at,
        snooze_expires_at=active_snooze_expires_at,
        time_since_bedtime=time_since_bedtime,
        debug_enabled=config.debug_mode != DebugMode.OFF,
    )
