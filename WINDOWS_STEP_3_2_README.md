# Windows Step 3.2

This note is for the current Windows milestone:

- `Step 3.2: Windows Guard Port`

The goal is to run the full guard prototype on a real Windows machine, verify that the shared guard flow still feels usable there, and record the Windows-specific weaknesses we are willing to live with for now.

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
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -e .
```

Use Python `3.13` for now. The current `PySide6` dependency range does not install cleanly with Python `3.14` on Windows.

Single-paste setup command:

```powershell
py -3.13 -m venv .venv; .venv\Scripts\python -m pip install -e .
```

## Run The Guard Prototype

Manual prototype command:

```powershell
.venv\Scripts\python src\bedtime_guard\ui\guard_screen.py --confirm
```

The default debug run should:

- start with a dismissable warning
- transition into the full-screen guard shortly after
- allow snooze with the visible passphrase prompt
- reactivate the guard if focus is lost
- release automatically a few minutes later

Single-paste setup plus prototype run:

```powershell
py -3.13 -m venv .venv; .venv\Scripts\python -m pip install -e .; .venv\Scripts\python src\bedtime_guard\ui\guard_screen.py --confirm
```

## Automated Verification

Focused tests for this milestone:

```powershell
.venv\Scripts\python -m pytest tests\test_guard_screen.py tests\test_platforms.py
```

Single-paste setup plus focused tests:

```powershell
py -3.13 -m venv .venv; .venv\Scripts\python -m pip install -e .; .venv\Scripts\python -m pytest tests\test_guard_screen.py tests\test_platforms.py
```

Full suite:

```powershell
.venv\Scripts\python -m pytest
```

## Runtime Files To Inspect

After a manual run, inspect:

- `.runtime\guard_events.jsonl`
- `.runtime\guard_state.json`

Those files should show the warning, dismissal if used, guard activation, snooze activity if used, and final release.

## What To Verify Manually

Check these on the real Windows machine:

- The warning window shows before the guard.
- The full-screen guard covers every display you actually use.
- The snooze prompt accepts the correct passphrase and rejects an incorrect one without clearing the typed text.
- The guard disappears cleanly during snooze and returns when the snooze expires.
- The guard tries to refocus after app switching and feels annoying enough to be useful.
- Alt+Tab behavior is acceptable.
- Win key behavior is acceptable.
- Virtual desktop behavior is acceptable.
- Lock and unlock behavior is acceptable.
- Wake from sleep behavior is acceptable.
- Multi-monitor behavior is acceptable.
- `Esc` exits immediately in debug mode.

## Known Windows Weaknesses Right Now

These are expected limitations of the current prototype:

- Reactivation is still based on Qt window activation and topmost behavior, not a native kiosk or shell-level lockout.
- A determined user can probably still get around the guard with Windows features such as virtual desktops or secure system UI.
- Lock, unlock, sleep, wake, and fast user switching should be treated as best-effort until the autostart and recovery milestone is done.
- This is still a Python-run prototype, not a polished installed Windows app.

## Files To Inspect

If you want to inspect the current implementation:

- [src/bedtime_guard/ui/guard_screen.py](/Users/user/code2/expr/sleep/src/bedtime_guard/ui/guard_screen.py:1)
- [src/bedtime_guard/platforms.py](/Users/user/code2/expr/sleep/src/bedtime_guard/platforms.py:1)
- [tests/test_guard_screen.py](/Users/user/code2/expr/sleep/tests/test_guard_screen.py:1)
- [tests/test_platforms.py](/Users/user/code2/expr/sleep/tests/test_platforms.py:1)
