# Config Step 4.3

This note is for the current configuration milestone:

- `Step 4.3: Guarded-Hours Settings Friction [Deferred]`

The passphrase-based guarded-hours friction for settings changes is deferred for now. The current goal is to keep the schedule-change script small and usable while still logging what changes were attempted and applied.

## Short Wrapper Command

The easiest way to verify this step is the wrapper script:

Interactive run:

```bash
.venv/bin/python scripts/run_schedule_change.py
```

When the script prompts you:

- leave `Bedtime` blank to keep the current bedtime
- leave `Wind-down minutes` blank to keep the current warning lead time
- leave `Verification time` blank to use the current time
- leave `Passphrase` blank to send none, or type `auto` to use the current expected passphrase

The wrapper automatically:

- uses the repo-local throwaway home directory
- ensures the default config exists
- computes the matching config, state, and log paths
- keeps the current config value for bedtime or wind-down minutes when you leave those prompts blank

## Underlying Low-Level Commands

```bash
.venv/bin/python -m bedtime_guard.config_files --platform darwin --home-dir "$PWD/.tmp-settings-home" --write-default-config
.venv/bin/python -m bedtime_guard.set_schedule --config-path "$PWD/.tmp-settings-home/Library/Application Support/BedtimeGuard/config.toml" --event-log "$PWD/.tmp-settings-home/Library/Logs/BedtimeGuard/guard_events.jsonl" --bedtime 21:00 --wind-down-minutes 20
```

## Inspect The Event Log

After those runs, inspect:

```bash
sed -n '1,20p' "$PWD/.tmp-settings-home/Library/Logs/BedtimeGuard/guard_events.jsonl"
```

You should see readable JSONL records for:

- `schedule_change_attempted`
- `schedule_change_applied`

## Automated Verification

Focused tests:

```bash
.venv/bin/python -m pytest tests/test_run_schedule_change.py tests/test_set_schedule.py tests/test_policy_state_events.py tests/test_config_files.py
```

Full suite:

```bash
.venv/bin/python -m pytest
```

## What To Verify Manually

- The interactive script is easy to use for small schedule changes.
- Blank answers keep the current config value for bedtime and warning lead time.
- The non-interactive flags still work when you want a one-liner.
- The event log captures what happened in a sequence you can understand later.

## Files To Inspect

- [scripts/run_schedule_change.py](/Users/user/code2/expr/sleep/scripts/run_schedule_change.py:1)
- [src/bedtime_guard/set_schedule.py](/Users/user/code2/expr/sleep/src/bedtime_guard/set_schedule.py:1)
- [src/bedtime_guard/events.py](/Users/user/code2/expr/sleep/src/bedtime_guard/events.py:1)
- [tests/test_run_schedule_change.py](/Users/user/code2/expr/sleep/tests/test_run_schedule_change.py:1)
- [tests/test_set_schedule.py](/Users/user/code2/expr/sleep/tests/test_set_schedule.py:1)
- [tests/test_policy_state_events.py](/Users/user/code2/expr/sleep/tests/test_policy_state_events.py:1)
