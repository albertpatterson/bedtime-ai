# Config Step 4.1

This note is for the current configuration milestone:

- `Step 4.1: Config File Defaults And Locations`

The goal is to make the default config, runtime state, event log, and recovery-note locations concrete, and to provide a small command that can generate a readable starter config.

## Current Default Locations

### macOS

- Config: `~/Library/Application Support/BedtimeGuard/config.toml`
- Runtime state: `~/Library/Application Support/BedtimeGuard/state.json`
- Recovery notes: `~/Library/Application Support/BedtimeGuard/RECOVERY.txt`
- Event log: `~/Library/Logs/BedtimeGuard/guard_events.jsonl`

### Windows

- Config: `%APPDATA%\BedtimeGuard\config.toml`
- Runtime state: `%APPDATA%\BedtimeGuard\state.json`
- Recovery notes: `%APPDATA%\BedtimeGuard\RECOVERY.txt`
- Event log: `%LOCALAPPDATA%\BedtimeGuard\Logs\guard_events.jsonl`

## Inspect The Generated Default Config

From the repo root on macOS:

```bash
.venv/bin/python -m bedtime_guard.config_files --platform darwin --stdout
```

From PowerShell on Windows:

```powershell
.venv\Scripts\python -m bedtime_guard.config_files --platform win32 --stdout
```

## Write A Safe Throwaway Config For Verification

This writes into a repo-local temporary home directory instead of your real home directory.

macOS:

```bash
.venv/bin/python -m bedtime_guard.config_files --platform darwin --home-dir "$PWD/.tmp-config-home" --write-default-config
```

Windows PowerShell:

```powershell
.venv\Scripts\python -m bedtime_guard.config_files --platform win32 --home-dir "$PWD\.tmp-config-home" --appdata "$PWD\.tmp-config-home\AppData\Roaming" --localappdata "$PWD\.tmp-config-home\AppData\Local" --write-default-config
```

## Inspect Windows-Style Paths Without Writing

From macOS or Linux, if you just want to see the Windows path computation:

```bash
.venv/bin/python -m bedtime_guard.config_files --platform win32 --home-dir "$PWD/.tmp-config-home" --appdata "$PWD/.tmp-config-home/AppData/Roaming" --localappdata "$PWD/.tmp-config-home/AppData/Local"
```

## Automated Verification

Focused tests:

```bash
.venv/bin/python -m pytest tests/test_config_files.py tests/test_policy_state_events.py
```

Full suite:

```bash
.venv/bin/python -m pytest
```

## What To Verify Manually

- The generated default config is readable and unsurprising.
- The generated config loads cleanly through the policy loader.
- The macOS default paths feel like the places you would naturally look later.
- The Windows default paths feel reasonable for a normal desktop app.
- The guard prototype now defaults its runtime state and event log paths to these platform locations rather than `.runtime`.

## Files To Inspect

- [src/bedtime_guard/config_files.py](/Users/user/code2/expr/sleep/src/bedtime_guard/config_files.py:1)
- [src/bedtime_guard/policy.py](/Users/user/code2/expr/sleep/src/bedtime_guard/policy.py:1)
- [src/bedtime_guard/ui/guard_screen.py](/Users/user/code2/expr/sleep/src/bedtime_guard/ui/guard_screen.py:685)
- [tests/test_config_files.py](/Users/user/code2/expr/sleep/tests/test_config_files.py:1)
- [tests/test_policy_state_events.py](/Users/user/code2/expr/sleep/tests/test_policy_state_events.py:1)
