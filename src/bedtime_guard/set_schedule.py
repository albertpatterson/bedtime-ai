from __future__ import annotations

import argparse
from datetime import datetime, time
from pathlib import Path

from .config_files import default_app_paths, ensure_default_policy
from .events import append_event_record, build_event_record
from .policy import load_policy, save_policy, update_policy_schedule


def build_parser() -> argparse.ArgumentParser:
    app_paths = default_app_paths()
    parser = argparse.ArgumentParser(
        description="Update the Bedtime Guard bedtime and optional wind-down minutes."
    )
    parser.add_argument(
        "--bedtime",
        required=True,
        help="Bedtime in HH:MM 24-hour format.",
    )
    parser.add_argument(
        "--wind-down-minutes",
        type=int,
        help="Optional new wind-down lead time in minutes. Omit to keep the current setting.",
    )
    parser.add_argument(
        "--config-path",
        default=str(app_paths.config_path),
        help="Path to the TOML policy file to update.",
    )
    parser.add_argument(
        "--event-log",
        default=str(app_paths.event_log_path),
        help="Path to the JSONL event log for config-change events.",
    )
    parser.add_argument(
        "--now",
        help="Optional ISO timestamp override for verification and tests.",
    )
    return parser


def _append_change_event(
    *,
    event_log_path: Path,
    event_type: str,
    occurred_at: datetime,
    details: dict[str, object],
) -> None:
    append_event_record(
        event_log_path,
        build_event_record(
            event_type=event_type,
            occurred_at=occurred_at,
            details=details,
        ),
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bedtime = time.fromisoformat(args.bedtime)
    config_path = Path(args.config_path)
    event_log_path = Path(args.event_log)
    now = datetime.fromisoformat(args.now) if args.now else datetime.now().astimezone()

    if args.wind_down_minutes is not None and args.wind_down_minutes < 0:
        raise SystemExit("wind_down_minutes must be non-negative")

    if not config_path.exists():
        ensure_default_policy(config_path)

    policy = load_policy(config_path)
    old_bedtime = policy.schedule.bedtime.isoformat(timespec="minutes")
    old_wind_down = policy.schedule.wind_down_minutes
    attempted_changes = {
        "old_bedtime": old_bedtime,
        "new_bedtime": bedtime.isoformat(timespec="minutes"),
        "old_wind_down_minutes": old_wind_down,
        "new_wind_down_minutes": (
            old_wind_down if args.wind_down_minutes is None else args.wind_down_minutes
        ),
    }
    _append_change_event(
        event_log_path=event_log_path,
        event_type="schedule_change_attempted",
        occurred_at=now,
        details=attempted_changes,
    )

    updated = update_policy_schedule(
        policy,
        bedtime=bedtime,
        wind_down_minutes=args.wind_down_minutes,
    )
    save_policy(config_path, updated)
    _append_change_event(
        event_log_path=event_log_path,
        event_type="schedule_change_applied",
        occurred_at=now,
        details={
            **attempted_changes,
            "applied_bedtime": updated.schedule.bedtime.isoformat(timespec="minutes"),
            "applied_wind_down_minutes": updated.schedule.wind_down_minutes,
        },
    )

    print(f"Updated config: {config_path}")
    print(f"Bedtime: {updated.schedule.bedtime.isoformat(timespec='minutes')}")
    print(f"Wind-down minutes: {updated.schedule.wind_down_minutes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
