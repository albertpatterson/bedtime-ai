# Windows Step 3.1

This note is for the current Windows milestone:

- `Step 3.1: Windows Overlay Spike`

The goal is to run the Windows overlay spike on a real Windows machine and decide whether the overlay behavior is good enough to proceed with the Windows port.

## Copy To Windows

Copy the full repository to the Windows machine.

You do not need to copy:

- `.venv`
- `.runtime`
- `__pycache__`
- `.pytest_cache`
- `build`
- `dist`

## Windows Setup

From PowerShell in the repo root:

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -e .
```

Optional packaging tools, only if you later want `.exe` builds:

```powershell
.venv\Scripts\python -m pip install -e .[windows-build]
```

## Run The Spike

Manual spike command:

```powershell
.venv\Scripts\python src\bedtime_guard\ui\windows_overlay_spike.py --confirm
```

Focused automated verification:

```powershell
.venv\Scripts\python -m pytest tests\test_windows_overlay_spike.py
```

Full test suite:

```powershell
.venv\Scripts\python -m pytest
```

## What To Verify Manually

Check these on the real Windows machine:

- The overlay covers every display.
- The overlay stays topmost enough to be useful.
- `Esc` exits the spike cleanly.
- Alt+Tab behavior is acceptable.
- Win key behavior is acceptable.
- Virtual desktop behavior is acceptable.
- Lock and unlock behavior is acceptable.
- Wake from sleep behavior is acceptable.
- Fast user switching behavior is acceptable.
- Multi-monitor behavior is acceptable.

## Files To Inspect

If you want to inspect the current implementation:

- [src/bedtime_guard/ui/windows_overlay_spike.py](/Users/user/code2/expr/sleep/src/bedtime_guard/ui/windows_overlay_spike.py:1)
- [tests/test_windows_overlay_spike.py](/Users/user/code2/expr/sleep/tests/test_windows_overlay_spike.py:1)
- [scripts/build_windows_exe.py](/Users/user/code2/expr/sleep/scripts/build_windows_exe.py:1)

## Optional Packaging

If you later want a Windows `.exe`, run on the Windows machine:

```powershell
.venv\Scripts\python scripts\build_windows_exe.py windows_overlay_spike
.venv\Scripts\python scripts\build_windows_exe.py guard_screen
```
