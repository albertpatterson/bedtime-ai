from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import time
from pathlib import Path
import tomllib

from .schedule import DebugMode, ScheduleConfig
from .snooze import SnoozeTier


@dataclass(frozen=True)
class BedtimeGuardPolicy:
    schedule: ScheduleConfig
    debug_target_cycle_minutes: int
    snooze_enabled: bool
    uses_per_night: str
    require_passphrase: bool
    match_case_sensitive: bool
    allow_paste: bool
    phrase_source: str
    snooze_tiers: tuple[SnoozeTier, ...]
    guard_mode: str
    cover_all_displays: bool
    require_snooze_for_desktop: bool
    close_apps: bool
    require_extra_friction_during_guarded_hours: bool
    settings_change_friction: str


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return str(value)


def _require_table(data: dict, key: str) -> dict:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing or invalid [{key}] table")
    return value


def _require_bool(data: dict, key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"missing or invalid boolean field: {key}")
    return value


def _require_str(data: dict, key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"missing or invalid string field: {key}")
    return value


def _require_int(data: dict, key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise ValueError(f"missing or invalid integer field: {key}")
    return value


def _require_number(data: dict, key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"missing or invalid numeric field: {key}")
    return float(value)


def load_policy(path: Path) -> BedtimeGuardPolicy:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    schedule_table = _require_table(raw, "schedule")
    debug_table = _require_table(raw, "debug")
    snooze_table = _require_table(raw, "snooze")
    guard_table = _require_table(raw, "guard")
    settings_table = _require_table(raw, "settings")

    bedtime = time.fromisoformat(_require_str(schedule_table, "bedtime"))
    schedule = ScheduleConfig(
        bedtime=bedtime,
        wind_down_minutes=_require_int(schedule_table, "wind_down_minutes"),
        wakeup_hours_after_last_snooze=_require_number(
            schedule_table, "wakeup_hours_after_last_snooze"
        ),
        debug_mode=DebugMode(_require_str(debug_table, "mode")),
        time_scale=_require_number(debug_table, "time_scale"),
    )

    ladder = raw.get("snooze", {}).get("ladder")
    if not isinstance(ladder, list) or not ladder:
        raise ValueError("missing or invalid [[snooze.ladder]] entries")
    snooze_tiers = tuple(
        SnoozeTier(
            minutes_after_bedtime=_require_int(entry, "minutes_after_bedtime"),
            duration_minutes=_require_int(entry, "duration_minutes"),
            passphrase_words=_require_int(entry, "passphrase_words"),
        )
        for entry in ladder
    )

    return BedtimeGuardPolicy(
        schedule=schedule,
        debug_target_cycle_minutes=_require_int(debug_table, "debug_target_cycle_minutes"),
        snooze_enabled=_require_bool(snooze_table, "enabled"),
        uses_per_night=_require_str(snooze_table, "uses_per_night"),
        require_passphrase=_require_bool(snooze_table, "require_passphrase"),
        match_case_sensitive=_require_bool(snooze_table, "match_case_sensitive"),
        allow_paste=_require_bool(snooze_table, "allow_paste"),
        phrase_source=_require_str(snooze_table, "phrase_source"),
        snooze_tiers=snooze_tiers,
        guard_mode=_require_str(guard_table, "mode"),
        cover_all_displays=_require_bool(guard_table, "cover_all_displays"),
        require_snooze_for_desktop=_require_bool(
            guard_table, "require_snooze_for_desktop"
        ),
        close_apps=_require_bool(guard_table, "close_apps"),
        require_extra_friction_during_guarded_hours=_require_bool(
            settings_table, "require_extra_friction_during_guarded_hours"
        ),
        settings_change_friction=_require_str(
            settings_table, "settings_change_friction"
        ),
    )


def dump_policy(policy: BedtimeGuardPolicy) -> str:
    lines = [
        "[schedule]",
        f'bedtime = "{policy.schedule.bedtime.isoformat(timespec="minutes")}"',
        f"wind_down_minutes = {policy.schedule.wind_down_minutes}",
        (
            "wakeup_hours_after_last_snooze = "
            f"{_format_number(policy.schedule.wakeup_hours_after_last_snooze)}"
        ),
        "",
        "[debug]",
        f'mode = "{policy.schedule.debug_mode.value}"',
        f"time_scale = {_format_number(policy.schedule.time_scale)}",
        f"debug_target_cycle_minutes = {policy.debug_target_cycle_minutes}",
        "",
        "[snooze]",
        f"enabled = {str(policy.snooze_enabled).lower()}",
        f'uses_per_night = "{policy.uses_per_night}"',
        f"require_passphrase = {str(policy.require_passphrase).lower()}",
        f"match_case_sensitive = {str(policy.match_case_sensitive).lower()}",
        f"allow_paste = {str(policy.allow_paste).lower()}",
        f'phrase_source = "{policy.phrase_source}"',
        "",
    ]
    for tier in policy.snooze_tiers:
        lines.extend(
            (
                "[[snooze.ladder]]",
                f"minutes_after_bedtime = {tier.minutes_after_bedtime}",
                f"duration_minutes = {tier.duration_minutes}",
                f"passphrase_words = {tier.passphrase_words}",
                "",
            )
        )

    lines.extend(
        (
            "[guard]",
            f'mode = "{policy.guard_mode}"',
            f"cover_all_displays = {str(policy.cover_all_displays).lower()}",
            (
                "require_snooze_for_desktop = "
                f"{str(policy.require_snooze_for_desktop).lower()}"
            ),
            f"close_apps = {str(policy.close_apps).lower()}",
            "",
            "[settings]",
            (
                "require_extra_friction_during_guarded_hours = "
                f"{str(policy.require_extra_friction_during_guarded_hours).lower()}"
            ),
            f'settings_change_friction = "{policy.settings_change_friction}"',
            "",
        )
    )
    return "\n".join(lines)


def save_policy(path: Path, policy: BedtimeGuardPolicy) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_policy(policy), encoding="utf-8")


def update_policy_schedule(
    policy: BedtimeGuardPolicy,
    *,
    bedtime: time,
    wind_down_minutes: int | None = None,
) -> BedtimeGuardPolicy:
    schedule = replace(
        policy.schedule,
        bedtime=bedtime,
        wind_down_minutes=(
            policy.schedule.wind_down_minutes
            if wind_down_minutes is None
            else wind_down_minutes
        ),
    )
    return replace(policy, schedule=schedule)
