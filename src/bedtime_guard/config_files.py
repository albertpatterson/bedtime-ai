from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_POLICY_TEXT = """\
[schedule]
bedtime = "22:30"
wind_down_minutes = 30
wakeup_hours_after_last_snooze = 5

[debug]
mode = "off"
time_scale = 1.0
debug_target_cycle_minutes = 5

[snooze]
enabled = true
uses_per_night = "unlimited"
require_passphrase = true
match_case_sensitive = true
allow_paste = true
phrase_source = "fixed_messages"

[[snooze.ladder]]
minutes_after_bedtime = 0
duration_minutes = 10
passphrase_words = 4

[[snooze.ladder]]
minutes_after_bedtime = 30
duration_minutes = 5
passphrase_words = 8

[[snooze.ladder]]
minutes_after_bedtime = 60
duration_minutes = 2
passphrase_words = 14

[[snooze.ladder]]
minutes_after_bedtime = 120
duration_minutes = 1
passphrase_words = 24

[guard]
mode = "full_screen"
cover_all_displays = true
require_snooze_for_desktop = true
close_apps = false

[settings]
require_extra_friction_during_guarded_hours = true
settings_change_friction = "current_snooze_passphrase"
"""


@dataclass(frozen=True)
class AppPaths:
    config_path: Path
    state_path: Path
    event_log_path: Path
    recovery_instructions_path: Path


def _normalize_platform(platform: str | None = None) -> str:
    name = platform or sys.platform
    if name.startswith("darwin"):
        return "darwin"
    if name.startswith("win"):
        return "win32"
    return name


def default_app_paths(
    *,
    platform: str | None = None,
    home: Path | None = None,
    appdata: Path | None = None,
    localappdata: Path | None = None,
) -> AppPaths:
    normalized = _normalize_platform(platform)
    resolved_home = home or Path.home()

    if normalized == "darwin":
        support_dir = resolved_home / "Library" / "Application Support" / "BedtimeGuard"
        log_dir = resolved_home / "Library" / "Logs" / "BedtimeGuard"
    elif normalized == "win32":
        roaming_base = appdata or Path(
            os.environ.get("APPDATA", resolved_home / "AppData" / "Roaming")
        )
        local_base = localappdata or Path(
            os.environ.get("LOCALAPPDATA", resolved_home / "AppData" / "Local")
        )
        support_dir = roaming_base / "BedtimeGuard"
        log_dir = local_base / "BedtimeGuard" / "Logs"
    else:
        support_dir = resolved_home / ".config" / "BedtimeGuard"
        log_dir = resolved_home / ".local" / "state" / "BedtimeGuard" / "logs"

    return AppPaths(
        config_path=support_dir / "config.toml",
        state_path=support_dir / "state.json",
        event_log_path=log_dir / "guard_events.jsonl",
        recovery_instructions_path=support_dir / "RECOVERY.txt",
    )


def render_default_policy() -> str:
    return DEFAULT_POLICY_TEXT


def ensure_default_policy(path: Path, *, overwrite: bool = False) -> bool:
    if path.exists() and not overwrite:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_default_policy(), encoding="utf-8")
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Show or create default Bedtime Guard config files."
    )
    parser.add_argument(
        "--platform",
        choices=("darwin", "win32"),
        help="Compute paths for a specific platform instead of the current one.",
    )
    parser.add_argument(
        "--home-dir",
        help="Override the home directory used for path computation.",
    )
    parser.add_argument(
        "--appdata",
        help="Override %%APPDATA%% when computing Windows paths.",
    )
    parser.add_argument(
        "--localappdata",
        help="Override %%LOCALAPPDATA%% when computing Windows paths.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the default config TOML to stdout.",
    )
    parser.add_argument(
        "--write-default-config",
        action="store_true",
        help="Write the default config TOML to the default config path.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing config file when used with --write-default-config.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = default_app_paths(
        platform=args.platform,
        home=Path(args.home_dir).expanduser() if args.home_dir else None,
        appdata=Path(args.appdata).expanduser() if args.appdata else None,
        localappdata=Path(args.localappdata).expanduser()
        if args.localappdata
        else None,
    )

    if args.stdout:
        print(render_default_policy(), end="")

    if args.write_default_config:
        wrote = ensure_default_policy(paths.config_path, overwrite=args.force)
        if wrote:
            print(f"Wrote default config: {paths.config_path}")
        else:
            print(f"Config already exists: {paths.config_path}")

    print(f"Config path: {paths.config_path}")
    print(f"State path: {paths.state_path}")
    print(f"Event log path: {paths.event_log_path}")
    print(f"Recovery notes path: {paths.recovery_instructions_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
