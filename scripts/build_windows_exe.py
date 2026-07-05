from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"


@dataclass(frozen=True)
class BuildTarget:
    key: str
    name: str
    script_path: Path
    description: str


TARGETS = {
    "guard_screen": BuildTarget(
        key="guard_screen",
        name="bedtime_guard_prototype",
        script_path=SRC_DIR / "bedtime_guard" / "ui" / "guard_screen.py",
        description="Full warning/guard/snooze prototype.",
    ),
    "windows_overlay_spike": BuildTarget(
        key="windows_overlay_spike",
        name="bedtime_guard_windows_overlay_spike",
        script_path=SRC_DIR / "bedtime_guard" / "ui" / "windows_overlay_spike.py",
        description="Windows overlay feasibility spike.",
    ),
}


def build_pyinstaller_args(
    *,
    target: BuildTarget,
    onefile: bool = True,
    clean: bool = True,
) -> list[str]:
    args = [
        "--noconfirm",
        "--windowed",
        "--name",
        target.name,
        "--distpath",
        str(ROOT / "dist"),
        "--workpath",
        str(ROOT / "build" / "pyinstaller"),
        "--specpath",
        str(ROOT / "build" / "spec"),
        "--paths",
        str(SRC_DIR),
    ]
    if clean:
        args.append("--clean")
    if onefile:
        args.append("--onefile")
    args.append(str(target.script_path))
    return args


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Windows .exe files for Bedtime Guard entrypoints."
    )
    parser.add_argument(
        "target",
        choices=sorted(TARGETS),
        help="Which executable target to build.",
    )
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="Build an unpacked directory instead of a single-file executable.",
    )
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Skip PyInstaller's clean step for faster repeated builds.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = TARGETS[args.target]

    try:
        import PyInstaller.__main__
    except ImportError as exc:  # pragma: no cover - depends on local environment
        raise SystemExit(
            "PyInstaller is not installed. Run `pip install -e .[windows-build]` first."
        ) from exc

    pyinstaller_args = build_pyinstaller_args(
        target=target,
        onefile=not args.onedir,
        clean=not args.skip_clean,
    )
    PyInstaller.__main__.run(pyinstaller_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
