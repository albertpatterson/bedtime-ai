# Config Step 4.2

This note is for the current configuration milestone:

- `Step 4.2: Minimal Schedule Config Command`

The goal is to provide a tiny command for changing the few settings we actually want to expose in normal use: bedtime and, optionally, warning lead time.

## Minimal Schedule Update Command

This is the intended normal-user path.

Update bedtime only and keep the current `wind_down_minutes` value:

```bash
.venv/bin/python -m bedtime_guard.set_schedule --config-path "$PWD/.tmp-settings/config.toml" --bedtime 22:15
```

Update both bedtime and wind-down minutes:

```bash
.venv/bin/python -m bedtime_guard.set_schedule --config-path "$PWD/.tmp-settings/config.toml" --bedtime 22:15 --wind-down-minutes 20
```

## Optional Pre-Bootstrap Command

If you want to create the config first and inspect it before using the schedule-update command:

```bash
.venv/bin/python -m bedtime_guard.config_files --platform darwin --home-dir "$PWD/.tmp-settings-home" --write-default-config
```

## Automated Verification

Focused tests:

```bash
.venv/bin/python -m pytest tests/test_set_schedule.py tests/test_policy_state_events.py tests/test_config_files.py
```

Full suite:

```bash
.venv/bin/python -m pytest
```

## What To Verify Manually

- The schedule-update command works without hand-creating the config first.
- Changing bedtime alone preserves the current `wind_down_minutes` value.
- Changing bedtime plus `--wind-down-minutes` updates both fields and leaves the rest of the file alone.
- The resulting config stays readable as plain TOML.
- The minimal schedule-update command changes only the intended fields and preserves the rest of the config.

## Files To Inspect

- [src/bedtime_guard/set_schedule.py](/Users/user/code2/expr/sleep/src/bedtime_guard/set_schedule.py:1)
- [src/bedtime_guard/policy.py](/Users/user/code2/expr/sleep/src/bedtime_guard/policy.py:1)
- [src/bedtime_guard/config_files.py](/Users/user/code2/expr/sleep/src/bedtime_guard/config_files.py:1)
- [tests/test_set_schedule.py](/Users/user/code2/expr/sleep/tests/test_set_schedule.py:1)
- [tests/test_policy_state_events.py](/Users/user/code2/expr/sleep/tests/test_policy_state_events.py:1)
