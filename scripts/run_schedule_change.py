from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from bedtime_guard.config_files import default_app_paths, ensure_default_policy
from bedtime_guard.policy import load_policy
from bedtime_guard.set_schedule import main as set_schedule_main


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOME_DIR = ROOT / ".tmp-settings-home"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convenience wrapper for guarded-hours schedule-change verification."
        )
    )
    parser.add_argument(
        "--bedtime",
        help="Bedtime in HH:MM 24-hour format.",
    )
    parser.add_argument(
        "--wind-down-minutes",
        type=int,
        help="Optional new wind-down lead time in minutes.",
    )
    parser.add_argument(
        "--now",
        help="Optional ISO timestamp override used for event logging.",
    )
    parser.add_argument(
        "--home-dir",
        default=str(DEFAULT_HOME_DIR),
        help="Throwaway home directory used to compute config, state, and log paths.",
    )
    return parser


def _prompt_or_default(
    *,
    label: str,
    default: str,
    interactive: bool,
    prompt,
) -> str:
    if not interactive:
        return default
    entered = prompt(f"{label} [{default}]: ").strip()
    return entered or default


def main(
    argv: list[str] | None = None,
    *,
    prompt=input,
    interactive: bool | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    home_dir = Path(args.home_dir).expanduser().resolve()
    paths = default_app_paths(platform="darwin", home=home_dir)
    ensure_default_policy(paths.config_path)
    interactive = sys.stdin.isatty() if interactive is None else interactive
    current_policy = load_policy(paths.config_path)

    bedtime = args.bedtime or _prompt_or_default(
        label="Bedtime",
        default=current_policy.schedule.bedtime.isoformat(timespec="minutes"),
        interactive=interactive,
        prompt=prompt,
    )
    wind_down_text = (
        str(args.wind_down_minutes)
        if args.wind_down_minutes is not None
        else _prompt_or_default(
            label="Wind-down minutes",
            default=str(current_policy.schedule.wind_down_minutes),
            interactive=interactive,
            prompt=prompt,
        )
    )
    now_text = args.now or _prompt_or_default(
        label="Verification time",
        default=datetime.now().astimezone().isoformat(timespec="seconds"),
        interactive=interactive,
        prompt=prompt,
    )

    forwarded_args = [
        "--config-path",
        str(paths.config_path),
        "--event-log",
        str(paths.event_log_path),
        "--bedtime",
        bedtime,
        "--now",
        now_text,
    ]

    if wind_down_text != str(current_policy.schedule.wind_down_minutes):
        forwarded_args.extend(["--wind-down-minutes", wind_down_text])

    print(f"Home dir: {home_dir}")
    print(f"Config path: {paths.config_path}")
    print(f"Event log path: {paths.event_log_path}")

    return set_schedule_main(forwarded_args)


if __name__ == "__main__":
    raise SystemExit(main())
