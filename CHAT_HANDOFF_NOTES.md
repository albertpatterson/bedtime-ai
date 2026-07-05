# Bedtime Guard Chat Handoff Notes

This file captures practical context from the current chat that is useful for the next chat, especially things that are only partly represented in `BEDTIME_APP_DESIGN.md`.

## Current Repo State

The project has moved from pure design into early implementation.

Implemented so far:

- `Step 1.1: Core Schedule Model [Complete]`
- `Step 1.2: Snooze And Passphrase Model [Complete]`
- `Step 1.3: Policy, State, And Event Files [Complete]`
- `Step 1.4: Platform Adapter Boundary [Complete]`
- `Step 2.1: macOS Overlay Spike [Complete]`
- `Step 2.2: Guard Screen UI [Complete]`
- `Step 2.3: Snooze Prompt UI [Complete]`
- `Step 2.4: Wind-Down Warning UI [Complete]`

The implementation is still intentionally early-stage and prototype-oriented.

## Important Files Already Created

- `src/bedtime_guard/schedule.py`
- `src/bedtime_guard/snooze.py`
- `src/bedtime_guard/policy.py`
- `src/bedtime_guard/state.py`
- `src/bedtime_guard/events.py`
- `src/bedtime_guard/platforms.py`
- `src/bedtime_guard/ui/macos_overlay_spike.py`
- `src/bedtime_guard/ui/guard_screen.py`
- `tests/test_schedule.py`
- `tests/test_policy_state_events.py`
- `tests/test_platforms.py`
- `tests/test_macos_overlay_spike.py`
- `tests/test_guard_screen.py`
- `pyproject.toml`

## What The Current Code Does

### Schedule model

`src/bedtime_guard/schedule.py` currently includes:

- `DebugMode` with:
  - `off`
  - `bedtime_now`
  - `bedtime_in_10_minutes`
- `SchedulePhase` with:
  - `inactive`
  - `wind_down`
  - `guarded`
  - `snoozed`
  - `released`
- `ScheduleConfig`
- `ScheduleSnapshot`
- `compute_schedule_snapshot(...)`

Important behavior already implemented:

- Wakeup release is based on `last_snooze_at` when present.
- If there was no snooze, wakeup release is based on bedtime.
- `time_scale` accelerates:
  - wind-down timing
  - snooze durations
  - wakeup release timing
- Debug mode supports:
  - immediate bedtime
  - bedtime 10 minutes from now

### Snooze model

`src/bedtime_guard/snooze.py` currently includes:

- `SnoozeTier`
- `SnoozeDecision`
- `FixedPhraseSource`
- `choose_snooze_decision(...)`
- `matches_passphrase(...)`

Important behavior already implemented:

- Snooze ladder durations are `10`, `5`, `2`, and `1` minute.
- Passphrase matching is case-sensitive by default.
- Snooze duration is scaled by `time_scale`.
- `FixedPhraseSource.DEFAULT_PHRASES` contains 19 phrases of varying length.

The phrases range from very short examples like:

- `Sleep!`
- `Bedtime!`

to much longer sleep-oriented and tomorrow-oriented phrases.

### Policy, state, and events

Already implemented:

- TOML policy loading and validation in `src/bedtime_guard/policy.py`
- Runtime state persistence in `src/bedtime_guard/state.py`
- JSONL event logging in `src/bedtime_guard/events.py`

### Platform boundary

`src/bedtime_guard/platforms.py` is a pure-Python adapter boundary for:

- warning actions
- guard show/hide actions
- guard reactivation enable/disable actions
- phase transition planning

This was done specifically to keep the shared behavior portable before building deeper platform-specific UI.

### macOS overlay spike

`src/bedtime_guard/ui/macos_overlay_spike.py` currently provides a very small PySide6 proof of concept:

- borderless widget
- always-on-top flags
- one overlay window per `QScreen`
- full-screen show
- simple centered text
- `Esc` exits the spike
- `--confirm` is required so it is not launched accidentally
- a Qt-only reactivation attempt when the app loses activation

This spike is meant as a platform sanity check, not a real enforcement path yet.

### Guard screen UI

`src/bedtime_guard/ui/guard_screen.py` currently provides a fuller guarded-state prototype:

- a dismissable wind-down warning window
- one full-screen guard window per `QScreen`
- current time
- time since bedtime
- computed release time
- a `Snooze` button and passphrase prompt
- typed passphrase checking against the current snooze phrase
- temporary hidden `snoozed` state after a correct passphrase
- return to guarded state when the snooze expires
- Qt-only reactivation attempt after deactivation
- automatic exit when the computed schedule reaches `released`
- `Esc` exits the prototype manually

The default manual command uses `bedtime_in_10_minutes` and `time_scale=1/60`, so it starts in `wind_down`, shows a short warning, enters guarded state shortly after launch, and then releases roughly 5 minutes later:

```bash
.venv/bin/python src/bedtime_guard/ui/guard_screen.py --confirm
```

Focused automated verification for the guard and snooze flow:

```bash
.venv/bin/python -m pytest tests/test_guard_screen.py
```

## Verification Status

Automated checks that passed in this repo:

- `python3 -m py_compile src/bedtime_guard/ui/macos_overlay_spike.py tests/test_macos_overlay_spike.py`
- `.venv/bin/python -m unittest discover -s tests -v`

At the last run, the test suite passed with 41 tests.

## Environment Lesson From This Chat

We accidentally tried the PySide6 overlay spike in the remote Linux environment even though the real target for this milestone is macOS.

The Linux run failed with a Qt platform plugin error about `xcb`, specifically mentioning a missing `libxcb-cursor0`.

That failure means:

- the remote Linux environment is not the right place to validate Step 2.1
- the failure does not tell us anything meaningful about macOS overlay feasibility
- the next meaningful manual test should happen on the local Mac

## Manual Spike Command

For Step 2.1, the current manual proof-of-concept command is:

```bash
.venv/bin/python src/bedtime_guard/ui/macos_overlay_spike.py --confirm
```

This command is also now written into the Step 2.1 section of `BEDTIME_APP_DESIGN.md`.

## Copying The Repo To The Local Mac

The user said the real implementation and testing should happen on their local Mac, at:

- `/Users/user/code2/expr/sleep`

Suggested copy commands from the local Mac:

Basic `scp` version:

```bash
mkdir -p /Users/user/code2/expr
scp -r user@dev:~/Documents/code/expr/productivity/sleep /Users/user/code2/expr/
```

Cleaner `rsync` version that skips `.venv` and `__pycache__`:

```bash
mkdir -p /Users/user/code2/expr
rsync -av --exclude '.venv' --exclude '__pycache__' user@dev:~/Documents/code/expr/productivity/sleep/ /Users/user/code2/expr/sleep/
```

Recommended local setup afterward:

```bash
cd /Users/user/code2/expr/sleep
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Likely Next Step In The Next Chat

The most natural next step is `Step 2.5` from the design doc: prototype logging and debug flow.

Before going too far on UI work, it would be sensible to:

- move the repo to the local Mac
- recreate the virtual environment there
- run the macOS overlay spike locally
- record what happens with:
  - Spaces
  - Mission Control
  - full-screen apps
  - multiple monitors
  - sleep and wake behavior

## Small Process Notes

- The user wanted milestone steps to be broken into smaller steps with separate verification lists.
- The user wanted completed steps marked complete directly in the design doc as work progresses.
- The user wanted verification sections to distinguish:
  - things the assistant can verify
  - things the user should verify manually
- The user specifically asked for exact files to inspect when a manual verification step depends on code.
