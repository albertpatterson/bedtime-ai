# Bedtime Guard App Design

## Purpose

Build a local app or program that helps me stop games, videos, and other high-stimulation activities when it is time for bed.

The app should be firm enough to interrupt autopilot behavior, but not so brittle or hostile that I end up disabling it permanently. The core job is to make the intended bedtime path easier than the avoidance path.

## Design Principles

- Treat bedtime as a transition, not only a hard cutoff.
- Prefer fail-closed behavior during protected sleep hours.
- Avoid making the app so annoying that I want to fully disable it.
- Avoid creating a frustrating trap for legitimate emergencies.
- Keep configuration explicit and inspectable.
- Start with a narrow, reliable version before adding polish.

## Core User Story

When bedtime approaches, the system gives me a warning and starts adding friction to recreational computer use. At bedtime, the app either covers the desktop with the guard or temporarily snoozes the guard. After the wakeup condition is reached, normal computer use resumes automatically.

## Initial Scope

The first useful version should support:

- A configured bedtime.
- A wakeup rule based on time since the last snooze.
- A debug mode that can set bedtime to now or 10 minutes from now and accelerate timing.
- A pre-bed warning period.
- A full-screen lock or overlay mode.
- A snooze flow that temporarily reveals the desktop.
- Friction that applies broadly instead of relying on a curated app list.
- macOS support as the development and testing target.
- Windows support as the second required platform after macOS is solid.
- Linux support as an eventual possibility, with no current use case.
- Logging of bedtime events and snoozes.

Out of scope for the first design:

- Cross-device sync.
- Mobile enforcement.
- AI coaching.
- Cloud accounts.
- Perfect tamper resistance.
- Anti-tamper behavior such as fighting system clock changes.
- Deep per-application classification.

## Full-Screen Guard UI

The main intervention is a full-screen guard that appears at bedtime, covers every display, and makes continued computer use require an intentional snooze.

This is both the primary UI and the primary enforcement mechanism. The app should not need to know whether the current distraction is a game, a video site, a launcher, or a browser tab. At bedtime, the whole desktop session becomes guarded.

### Guard Behavior

The guard should:

- Open as a borderless full-screen window.
- Cover all connected displays.
- Stay above normal app windows where the operating system allows it.
- Capture keyboard and mouse focus where the operating system allows it.
- While guarded, attempt to reclaim focus or reassert the full-screen guard after deactivation where the operating system allows it.
- Reappear if dismissed accidentally during guarded hours.
- Show a clear bedtime message, the current time, and the next automatic release time.
- Show how far past bedtime it is.
- Offer one primary action: snooze.

The guard should not:

- Try to classify every app as good or bad.
- Force-close programs by default.
- Hide recovery information.
- Depend on website or network rules for the first useful version.

### Guard Phases

The same full-screen UI can support multiple phases:

- `wind_down`: easily dismissed warnings as bedtime approaches.
- `guarded`: normal desktop use is covered by the guard.
- `snooze_prompt`: the user enters the current passphrase before access is granted.
- `snoozed`: the guard is temporarily relaxed.
- `release`: the wakeup rule has been satisfied and normal use resumes.

### Snooze Flow

The guarded desktop has a deliberately simple model:

- Guard active: the full-screen UI covers the desktop.
- Snooze active: the guard disappears temporarily and normal desktop interaction is available.

Snooze should be possible but intentionally inconvenient. The app should not provide a menu of sanctioned desktop activities inside the guard; it should either guard the desktop or snooze the guard.

Snoozes are unlimited, but they get less useful as it gets later. The app should make "just one more snooze" increasingly unrewarding without creating a hard wall that encourages uninstalling or disabling the app.

Suggested first version:

- Unlimited snoozes.
- Snooze duration shrinks as time after bedtime increases.
- Required passphrase gets longer or more difficult as time after bedtime increases.
- Event log entry with timestamp, duration, and passphrase tier.

Example snooze ladder:

- 0-30 minutes after bedtime: 10 minute snooze, short passphrase.
- 30-60 minutes after bedtime: 5 minute snooze, medium passphrase.
- 60-120 minutes after bedtime: 2 minute snooze, longer passphrase.
- 120+ minutes after bedtime: 1 minute snooze, very long passphrase.

Possible refinements later:

- Also increase friction after many snoozes in one night.
- Show a plain summary of how many snoozes have already happened.
- Let the passphrase be a configured sentence that reinforces the bedtime intention.
- Keep settings easy to change outside guarded hours so the app remains livable.
- Require extra friction for configuration changes during guarded hours.

### Wakeup Rule

The app should hide the overlay once enough time has passed since the last snooze. The initial target is 5 hours since the most recent snooze.

This makes the release time follow actual behavior:

- If I stop snoozing and go to bed, the guard releases roughly 5 hours later.
- If I keep snoozing, the release time keeps moving later.
- If I never snooze after bedtime, the release time can be based on bedtime itself.

The guarded screen should show the computed release time so it is clear when the overlay will disappear.

### Platform Priorities

The platform priority is:

- macOS first: this is the required development and testing platform.
- Windows second: this is needed after the macOS version is in good shape.
- Linux third: keep the architecture open to it, but there is no current use case.

The guard should use one shared core with platform adapters so the later Windows port does not require rewriting schedule, snooze, wakeup, debug, policy, or logging logic.

Platform adapters:

- macOS adapter: launch agent integration, full-screen/top-level window behavior, guarded-state reactivation attempts, notifications, and accessibility permission notes if needed.
- Windows adapter: startup integration, topmost full-screen windows, guarded-state reactivation attempts, and notifications.
- Linux adapter: desktop autostart or systemd user integration, X11/Wayland-specific full-screen behavior, guarded-state reactivation attempts where feasible, and notifications, deferred until there is a real use case.

## Recommended Architecture

Start with a local desktop app plus a small background scheduler.

Components:

- `Scheduler`: determines current phase from bedtime, wakeup rule, grace period, and snoozes.
- `Debug Schedule Mode`: overrides the normal bedtime during development or manual testing.
- `Notification UI`: easily dismissed wind-down warnings before bedtime.
- `Overlay UI`: full-screen interface shown during guarded periods.
- `Friction Controller`: decides whether normal interaction, wind-down prompts, full-screen guard, or snooze mode is active.
- `Platform Adapter`: handles autostart, full-screen behavior, guarded-state reactivation behavior, and notifications per OS.
- `Policy Config`: local file defining schedules, grace rules, and snooze rules.
- `Runtime State`: local file containing last snooze timestamp, active snooze expiry, and last known schedule state.
- `Event Log`: append-only local log of warnings, guard activations, and snoozes.

Possible states:

- `inactive`: normal use.
- `wind_down`: bedtime is approaching; warnings are shown.
- `guarded`: normal desktop use requires intentional friction.
- `snoozed`: temporary access is allowed after intentional friction.
- `released`: enforcement has ended and normal use resumes.

Debug schedule mode:

- `off`: use the configured bedtime and normal timing.
- `bedtime_now`: treat bedtime as the current time.
- `bedtime_in_10_minutes`: treat bedtime as 10 minutes from the current time.

Debug mode should also accelerate the snooze ladder and wakeup rule so the full cycle can be tested over a few minutes. It should be visually obvious when active so it is not mistaken for the real schedule.

## User Experience

### Wind-Down Screen

Before bedtime, the app should give a visible warning, such as:

- 30 minutes before: gentle notification.
- 15 minutes before: slightly stronger notification.
- 5 minutes before: easily dismissed final reminder.

Wind-down warnings should:

- Avoid taking over the full screen.
- Be easy to dismiss.
- Make the upcoming bedtime clear.
- Avoid countdown pressure.

Wind-down warnings and warning logs are separate concerns:

- Wind-down warnings are user-facing reminders shown during `wind_down`.
- Warning logs are internal event records that those reminders were shown.
- The app should support both, but they do not need to be implemented in the same step.

### Guarded Screen

At bedtime, the screen becomes a full-screen guard.

The guard should avoid stimulating content. It should be plain, calm, and direct.

The guarded screen should show:

- Bedtime status.
- Current time.
- Time elapsed since bedtime.
- Automatic release time.
- A snooze button.

### Snooze Screen

The snooze screen should feel deliberate, not dramatic. It should ask for the current passphrase, show the snooze duration, and then temporarily release the guard as soon as the passphrase is entered correctly.

## Policy Model

Example policy fields:

```toml
[schedule]
bedtime = "22:30"
wind_down_minutes = 30
wakeup_hours_after_last_snooze = 5

[debug]
mode = "off" # "off", "bedtime_now", or "bedtime_in_10_minutes"
time_scale = 1.0 # applies to wind-down warnings, ladder thresholds, snooze durations, and wakeup release
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
```

## Disable Posture

The app should not try to prevent or handle determined bypasses. If I decide to kill the process, change the system time, reboot, uninstall the app, or use another device, that is outside the app's scope.

The design goal is different: make the normal path tolerable enough that I am less likely to fully disable the system.

Design choices that reduce the urge to disable it:

- Snoozes are always available.
- Snoozes become shorter instead of disappearing.
- Passphrases become longer instead of the app becoming punitive.
- Settings remain understandable and editable outside guarded hours.
- The guard explains what will happen next and when it will release.
- Recovery instructions are clear.

Important constraint:

The app does not need to be impossible to bypass. It needs to interrupt impulsive continuation reliably enough that the better choice becomes easier, while staying tolerable enough that I keep it installed.

## Safety And Failure Modes

The app should not trap me out of necessary computer use.

Required recovery paths:

- Snooze.
- Automatic release after the wakeup rule is satisfied.
- Clear visible explanation of what is happening.
- Manual recovery instructions stored outside the app.

Failure cases to design for:

- Overlay appears at the wrong time.
- Time zone or daylight saving change.
- Multi-monitor display problems.
- App crashes while policy is active.
- The guard interrupts something with unsaved work.
- Computer wakes from sleep during guarded hours.
- System clock is incorrect.
- macOS, Windows, and eventually Linux differ in topmost-window behavior.

## Implementation Clarifications

These decisions were clarified before implementation begins.

### Platform Overlay Feasibility

- The first implementation task for any platform should be a tiny PySide6 overlay spike before building or porting the full app for that platform.
- The spike should verify that a PySide6 full-screen, always-on-top overlay is good enough for the platform's real desktop behavior.
- Do not invest deeply in platform-specific implementation until the overlay sanity check passes for that platform.
- For macOS, test Spaces, Mission Control, full-screen apps, wake from sleep, and multiple displays.
- For Windows, test borderless full-screen apps, Alt+Tab, Win key shortcuts, lock screen, virtual desktops, wake from sleep, and multiple displays.
- For Linux, test X11 and Wayland separately if a real Linux use case appears.

### Passphrase Behavior

- Snooze passphrases should be fixed messages.
- Messages should mix phrases about the importance of sleep, looking forward to tomorrow, and discouraging staying up further.
- Matching should be case-sensitive.
- Phrase length or difficulty should increase with the snooze tier.

### Debug Timing Semantics

- Debug mode should accelerate all timing: wind-down warning offsets, snooze ladder thresholds, snooze durations, and wakeup release.
- The goal is to test warnings, overlay activation, several snoozes, and wakeup release within about 5 minutes.
- Prefer a single `time_scale` plus a `debug_target_cycle_minutes` sanity target over separate debug fields for each timing rule.

### Runtime State Persistence

- Runtime state should be persisted in a local file.
- The state file should include at least the last snooze timestamp, active snooze expiry, and last known schedule state.
- Crash, reboot, and autostart recovery should read this file before computing current state.

### Config Change Friction

- Changing settings during guarded hours should require the current snooze passphrase.
- Settings changes during guarded hours should be logged.

### Notification Handling

- Use whatever is most reliable and consistent across platforms.
- A dedicated small warning window is acceptable if it is more predictable than native notifications.
- Native notifications are not required for the first version.

### File Locations

- Config: `~/Library/Application Support/BedtimeGuard/config.toml`
- Logs: `~/Library/Logs/BedtimeGuard/events.jsonl`
- Runtime state: `~/Library/Application Support/BedtimeGuard/state.json`
- Recovery instructions: repo doc plus copied local text file near config.

## Python Desktop App Implementation

The implementation should be a Python desktop app, with a shared pure-Python core and thin platform adapters for desktop integration.

### Technology Stack

- Python 3.12+ for the application core.
- PySide6 / Qt for Python for the desktop UI, full-screen guard window, snooze prompt, and basic notifications.
- Qt Widgets rather than QML for the first version, because the UI is simple and form-like.
- `tomllib` for reading TOML policy files.
- `dataclasses`, `datetime`, `zoneinfo`, and `pathlib` for schedule, time-zone, and file-path logic.
- JSON Lines for append-only event logs.
- `pytest` for schedule, snooze ladder, debug timing, wakeup release, config parsing, and logging tests.

The core scheduling code should not depend on PySide6. That keeps most behavior testable without opening windows.

### Python Modules

Suggested module boundaries:

- `policy`: load and validate TOML config.
- `clock`: injectable wall-clock and accelerated debug time helpers.
- `scheduler`: compute `inactive`, `wind_down`, `guarded`, `snoozed`, and `released` states.
- `snooze`: choose snooze duration and passphrase tier.
- `events`: append warnings, guard activations, snoozes, releases, and config-change attempts.
- `state`: persist and load runtime state.
- `ui`: PySide6 windows, notifications, and user input.
- `platforms`: OS-specific autostart, window flags, display enumeration, and permission notes.

### macOS Handling

macOS is the first prototype target.

Special handling:

- Start with a tiny overlay spike before building the full macOS UI.
- Use PySide6 full-screen windows on every `QScreen`.
- Try Qt top-level/full-screen/window-stays-on-top flags first.
- If plain full-screen coverage is too easy to bypass, try a Qt-only reactivation loop that responds to app deactivation by re-showing and reactivating the guard window.
- Verify behavior with Spaces, Mission Control, lock screen, wake from sleep, and multiple displays.
- Use a LaunchAgent for autostart.
- Expect possible Accessibility or notification permission prompts; document exactly what the user needs to approve.
- Keep a clear manual recovery command for disabling autostart or quitting the app.
- Current macOS spike result: Qt-only reactivation is annoying enough to be useful in the active Space, but switching to another Space is still an escape hatch we should treat as a known limitation unless a later platform-specific solution proves worthwhile.

### Windows Handling

Special handling:

- Start with a tiny overlay spike before porting the full app to Windows.
- Use PySide6 full-screen windows on every monitor.
- Test topmost behavior with games, borderless full-screen apps, Alt+Tab, Win key shortcuts, lock screen, and virtual desktops.
- Use a Startup folder shortcut or Task Scheduler entry for autostart.
- Use native notification behavior through Qt where adequate; add a Windows-specific adapter only if Qt notifications are not reliable enough.
- Document any limitations around exclusive full-screen games appearing above the guard.

Windows is the second required platform. Do this after the macOS version is reliable and the shared core is stable.

### Linux Handling

Special handling:

- Start with a tiny overlay spike before porting the full app to Linux.
- Use PySide6 full-screen windows on every monitor.
- Treat X11 and Wayland as separate behavior targets.
- On X11, verify always-on-top and focus behavior with the target desktop environment.
- On Wayland, expect stricter compositor control; document limitations if the compositor prevents reliable topmost behavior.
- Use XDG autostart for desktop-session startup; consider a systemd user service only if XDG autostart is not reliable enough.
- Test GNOME and KDE first if Linux support becomes important.

Linux is deferred. Keep the code structure compatible with a future Linux adapter, but do not spend milestone time on Linux until there is a concrete use case.

### Packaging

Packaging can come after the macOS prototype proves the behavior. The first implementation can run from a virtual environment. Later packaging should produce a normal app bundle or installer per OS, but packaging should not drive the initial architecture.

## Milestone Plan

### Milestone 1: Design And Simulation

#### Step 1.1: Core Schedule Model [Complete]

Build:

- Define schedule states.
- Add wakeup rule based on the last snooze.
- Add debug schedule mode for bedtime now and bedtime 10 minutes from now.
- Add accelerated debug timing for snooze ladder and wakeup release.

I can verify:

- Schedule state calculations for normal bedtime, wind-down, guarded, snoozed, and released states.
- Wakeup release calculation from the last snooze timestamp.
- Debug mode behavior for bedtime now, bedtime 10 minutes from now, and accelerated timing.

You should verify:

- The configured bedtime, wind-down timing, and wakeup rule feel right.
- Debug timing feels fast enough to test without becoming confusing.

#### Step 1.2: Snooze And Passphrase Model [Complete]

Build:

- Add fixed passphrase tiers with case-sensitive matching.

I can verify:

- Snooze ladder selection at each configured time threshold.
- Fixed passphrase tier selection and case-sensitive matching.

You should verify:

- Snooze durations and passphrase difficulty feel like the right amount of friction.
- The fixed messages have the right tone.

#### Step 1.3: Policy, State, And Event Files [Complete]

Build:

- Define policy config.
- Add local runtime state persistence.
- Write sample event logs.

I can verify:

- Policy parsing and validation, including invalid or missing fields.
- Runtime state read/write behavior.
- Event log shape using generated sample events.

You should verify:

- The generated event log contains the kind of information you would actually want to review.
- The default config, log, and state file locations feel reasonable.

#### Step 1.4: Platform Adapter Boundary [Complete]

Build:

- Define platform adapter boundaries.
- Simulate state transitions without enforcing anything.

I can verify:

- Shared core logic can run without PySide6.
- Platform adapter interface can represent overlay, warning, notification, autostart, and recovery behavior.
- Platform adapter interface can explicitly enable and disable guard reactivation behavior while guarded.

You should verify:

- The platform boundary matches how you expect to work: macOS first, Windows later, Linux deferred.
- Look at [platforms.py](/home/user/Documents/code/expr/productivity/sleep/src/bedtime_guard/platforms.py) to confirm the adapter interface and planned action types feel right.
- Look at [test_platforms.py](/home/user/Documents/code/expr/productivity/sleep/tests/test_platforms.py) to confirm the transition behavior matches how you expect warnings and guard actions to flow.

### Milestone 2: Full-Screen Guard Prototype

#### Step 2.1: macOS Overlay Spike [Complete]

Build:

- Run a tiny macOS PySide6 overlay spike before building the full UI.

I can verify:

- The spike creates a borderless full-screen window on every detected `QScreen`.
- The spike uses the intended Qt full-screen and window-stays-on-top flags.
- The spike includes a minimal manual exit/recovery path.
- The spike code compiles and the current automated tests pass.

You should verify:

- The macOS overlay behavior with Spaces, Mission Control, full-screen apps, wake from sleep, and multiple displays is good enough for this project.
- The overlay actually interrupts normal desktop interaction enough to be useful.
- Note whether guarded-state reactivation meaningfully increases friction after app deactivation, even if Spaces remain a limitation.
- Run the spike manually with `.venv/bin/python src/bedtime_guard/ui/macos_overlay_spike.py --confirm`.
- Look at [src/bedtime_guard/ui/macos_overlay_spike.py](/home/user/Documents/code/expr/productivity/sleep/src/bedtime_guard/ui/macos_overlay_spike.py) for the current spike behavior and window flags.
- Look at [tests/test_macos_overlay_spike.py](/home/user/Documents/code/expr/productivity/sleep/tests/test_macos_overlay_spike.py) for the current automated coverage of the spike entrypoint.
- Look at [pyproject.toml](/home/user/Documents/code/expr/productivity/sleep/pyproject.toml) if you want to confirm the current UI dependency choice and version pin.

#### Step 2.2: Guard Screen UI [Complete]

Build:

- Show full-screen overlay during guarded state.
- Support release after the wakeup rule is satisfied.

I can verify:

- The app enters guarded state at the expected time.
- The overlay renders the current time, time since bedtime, and computed release time.
- In debug mode, `Esc` exits the prototype immediately as a manual recovery path.
- Wakeup release hides the overlay.

You should verify:

- The guard feels plain and calm rather than irritating.
- The full-screen guard actually prevents normal desktop interaction on your Mac.
- Run the guard prototype manually with `.venv/bin/python src/bedtime_guard/ui/guard_screen.py --confirm`.
- Look at [src/bedtime_guard/ui/guard_screen.py](/Users/user/code2/expr/sleep/src/bedtime_guard/ui/guard_screen.py:1) for the current guard layout, timing refresh, reactivation behavior, and auto-release logic.
- Look at [tests/test_guard_screen.py](/Users/user/code2/expr/sleep/tests/test_guard_screen.py:1) for the current automated coverage of guard rendering inputs and release behavior.
- Run `.venv/bin/python -m pytest tests/test_guard_screen.py` if you want the focused automated verification command for this step.

#### Step 2.3: Snooze Prompt UI [Complete]

Build:

- Support typed snooze passphrases.

I can verify:

- Correct passphrases activate snooze, and incorrect passphrases do not.
- Snooze expiration returns to guarded state.

You should verify:

- The snooze passphrase friction feels useful rather than hostile.
- Run the guard prototype manually with `.venv/bin/python src/bedtime_guard/ui/guard_screen.py --confirm`.
- Verify that `Snooze` opens a passphrase prompt, an incorrect passphrase keeps the guard active, a correct passphrase temporarily hides the guard, and the guard returns when the snooze expires.
- Look at [src/bedtime_guard/ui/guard_screen.py](/Users/user/code2/expr/sleep/src/bedtime_guard/ui/guard_screen.py:1) for the current snooze prompt layout, passphrase submission flow, and snooze/guard transitions.
- Look at [src/bedtime_guard/snooze.py](/Users/user/code2/expr/sleep/src/bedtime_guard/snooze.py:1) for the tier selection, scaled snooze duration, and passphrase matching rules.
- Look at [tests/test_guard_screen.py](/Users/user/code2/expr/sleep/tests/test_guard_screen.py:1) for the automated coverage of correct passphrases, incorrect passphrases, and return-to-guard behavior.
- Run `.venv/bin/python -m pytest tests/test_guard_screen.py` if you want the focused automated verification command for this step.

#### Step 2.4: Wind-Down Warning UI [Complete]

Build:

- Show dismissable warnings during `wind_down`.
- Keep the warning UI visible enough to notice without taking over the full screen.

I can verify:

- The app enters `wind_down` at the expected time.
- Warning UI appears during `wind_down` and stops once guarded mode begins.
- The warning UI can be dismissed without breaking the schedule transition into guarded mode.

You should verify:

- The warnings feel noticeable without being obnoxious.
- The warning UI is easy to dismiss and does not feel like a second guard.
- Run the prototype manually with `.venv/bin/python src/bedtime_guard/ui/guard_screen.py --confirm`.
- Verify that the default debug run starts with a dismissable warning, then transitions into the full guard a short time later.
- Look at [src/bedtime_guard/ui/guard_screen.py](/Users/user/code2/expr/sleep/src/bedtime_guard/ui/guard_screen.py:1) for the current warning window, guard window, and phase transition logic.
- Look at [src/bedtime_guard/platforms.py](/Users/user/code2/expr/sleep/src/bedtime_guard/platforms.py:1) for the existing warning action boundary and phase planning.
- Look at [tests/test_guard_screen.py](/Users/user/code2/expr/sleep/tests/test_guard_screen.py:1) and [tests/test_platforms.py](/Users/user/code2/expr/sleep/tests/test_platforms.py:1) for the automated coverage of `wind_down` behavior and phase transitions.
- Run `.venv/bin/python -m pytest tests/test_guard_screen.py` if you want the focused automated verification command for this step.

#### Step 2.5: Prototype Logging And Debug Flow [Complete]

Build:

- Log warning events, guard activations, and snoozes.
- Test manually on macOS first while keeping adapter boundaries clean.

I can verify:

- Warning events, guard activations, snoozes, and releases are logged.
- Debug mode can run bedtime, warning, guard, snooze, and release behavior in a few minutes.

You should verify:

- Debug mode lets you test the bedtime-to-release flow in a few minutes.
- Run the prototype manually with `.venv/bin/python src/bedtime_guard/ui/guard_screen.py --confirm`.
- Inspect `.runtime/guard_events.jsonl` after a debug run to confirm that warning, guard, snooze, dismiss, and release events are being written in a readable sequence.
- Inspect `.runtime/guard_state.json` after a debug run to confirm the runtime state tracks the last snooze time, active snooze expiry, and last known phase.
- Look at [src/bedtime_guard/ui/guard_screen.py](/Users/user/code2/expr/sleep/src/bedtime_guard/ui/guard_screen.py:1) for the current prototype logging and state persistence integration.
- Look at [src/bedtime_guard/events.py](/Users/user/code2/expr/sleep/src/bedtime_guard/events.py:1) and [src/bedtime_guard/state.py](/Users/user/code2/expr/sleep/src/bedtime_guard/state.py:1) for the event log and runtime state helpers used by the prototype.
- Look at [tests/test_guard_screen.py](/Users/user/code2/expr/sleep/tests/test_guard_screen.py:1) for the automated coverage of warning, guard, snooze, release, event log, and runtime state behavior.
- Run `.venv/bin/python -m pytest tests/test_guard_screen.py` if you want the focused automated verification command for this step.

Note:

- This step is about logging and debug flow.
- User-facing wind-down warnings or notifications are a separate UI feature from logged warning events.

### Milestone 3: Windows Port

#### Step 3.1: Windows Overlay Spike [Complete]

Build:

- Run a tiny Windows PySide6 overlay spike before porting the full app.
- Validate full-screen behavior on Windows.
- Test Windows multi-monitor setups.
- Test wake, lock screen, fast user switching, virtual desktops, Alt+Tab, and Win key behavior.

I can verify:

- The Windows overlay spike can cover all displays well enough to proceed with the Windows port.
- Known Windows overlay limitations are captured in the docs.

You should verify:

- The Windows overlay spike is good enough before we port the full app.
- The overlay behavior is acceptable with your actual Windows display and input setup.
- Run the Windows spike manually with `.venv/bin/python src/bedtime_guard/ui/windows_overlay_spike.py --confirm`.
- Build a Windows `.exe` for the spike with `.venv/bin/python scripts/build_windows_exe.py windows_overlay_spike`.
- Build a Windows `.exe` for the main prototype with `.venv/bin/python scripts/build_windows_exe.py guard_screen`.
- Look at [src/bedtime_guard/ui/windows_overlay_spike.py](/Users/user/code2/expr/sleep/src/bedtime_guard/ui/windows_overlay_spike.py:1) for the current Windows-specific spike behavior, full-screen flags, and reactivation attempt.
- Look at [scripts/build_windows_exe.py](/Users/user/code2/expr/sleep/scripts/build_windows_exe.py:1) for the current Windows `.exe` build helper and target list.
- Look at [tests/test_windows_overlay_spike.py](/Users/user/code2/expr/sleep/tests/test_windows_overlay_spike.py:1) for the automated coverage of the spike entrypoint and reactivation behavior.
- Look at [tests/test_windows_packaging.py](/Users/user/code2/expr/sleep/tests/test_windows_packaging.py:1) for the automated coverage of the Windows packaging helper.
- Run `.venv/bin/python -m pytest tests/test_windows_overlay_spike.py` if you want the focused automated verification command for this step.

#### Step 3.2: Windows Guard Port [Complete]

Build:

- Port the macOS-tested guard behavior to Windows.
- Document known Windows-specific weaknesses.

I can verify:

- Shared schedule, snooze, wakeup, debug, policy, and logging logic stays platform-independent.
- Windows adapter exposes the same interface for notifications, overlay behavior, and autostart.
- Documented manual test checklist exists for Windows.
- Known Windows-specific weaknesses are captured in the docs.

You should verify:

- The guard covers the displays you actually use on Windows.
- Window focus, virtual desktops, lock/wake behavior, and multi-monitor behavior feel acceptable on Windows.
- Any Windows permission prompts or startup setup steps are understandable and not too annoying.
- The known Windows weaknesses are acceptable for your actual use.
- Run the Windows guard prototype manually with `.venv\Scripts\python src\bedtime_guard\ui\guard_screen.py --confirm`.
- Inspect `.runtime\guard_events.jsonl` and `.runtime\guard_state.json` after a debug run so you can confirm the warning, guard, snooze, and release flow on Windows.
- Look at [src/bedtime_guard/ui/guard_screen.py](/Users/user/code2/expr/sleep/src/bedtime_guard/ui/guard_screen.py:1) for the shared warning, guard, snooze, reactivation, and logging behavior now exercised on Windows.
- Look at [src/bedtime_guard/platforms.py](/Users/user/code2/expr/sleep/src/bedtime_guard/platforms.py:1) for the current platform action boundary that keeps schedule and policy logic shared across macOS and Windows.
- Look at [tests/test_guard_screen.py](/Users/user/code2/expr/sleep/tests/test_guard_screen.py:1) for the automated coverage of warning, guard, snooze, release, logging, and persisted runtime state.
- Look at [WINDOWS_STEP_3_2_README.md](/Users/user/code2/expr/sleep/WINDOWS_STEP_3_2_README.md:1) for the Windows-specific setup, one-paste commands, manual checklist, and known weaknesses.
- Run `.venv\Scripts\python -m pytest tests\test_guard_screen.py tests\test_platforms.py` if you want the focused automated verification command for this step.

Known Windows-specific weaknesses to keep in mind at this stage:

- The current reactivation behavior is still a Qt-level topmost/refocus attempt, not a native kiosk or shell replacement.
- Users can likely still escape by moving to another virtual desktop, opening secure system UI, or otherwise using Windows features outside normal app focus rules.
- Lock, unlock, sleep, wake, and fast user switching behavior should be treated as best-effort until the Windows autostart and recovery work is finished.
- The prototype currently relies on running from Python, not an installed Windows application with polished startup integration.

### Milestone 4: Autostart And Recovery

#### Step 4.1: macOS Autostart And Recovery

Build:

- Start on login for macOS.
- Restart after crash if appropriate.
- Add recovery instructions.
- Test reboot behavior on macOS.

I can verify:

- macOS autostart configuration files or installer steps are generated as expected.
- App startup loads the policy and resumes the correct schedule state.
- Crash/restart behavior preserves enough state to compute guarded, snoozed, or released status.
- Recovery instructions are present in the repo and reference the right files or commands.
- macOS reboot-state handling is covered by tests where practical.

You should verify:

- The app starts after login on your Mac.
- Recovery instructions are understandable when you are tired.
- Crash or reboot behavior does not surprise you during guarded hours.
- The app remains easy enough to live with that you are not tempted to disable autostart permanently.

#### Step 4.2: Windows Autostart And Recovery

Build:

- Start on login for Windows.
- Add Windows recovery instructions.
- Test reboot behavior on Windows.

I can verify:

- Windows autostart configuration files or installer steps are generated as expected.
- Windows recovery instructions are present in the repo and reference the right files or commands.
- Shared startup-state logic works on Windows through the platform adapter.

You should verify:

- The app starts after login on your Windows machine.
- Windows recovery instructions are understandable.
- Reboot behavior does not surprise you during guarded hours.

### Deferred: Linux Adapter

#### Step L.1: Linux Overlay Spike

Build only if a real Linux use case appears:

- Run a tiny Linux PySide6 overlay spike before porting the full app.
- Test X11 and Wayland separately.

I can verify:

- The Linux overlay spike can cover all displays well enough to proceed with a Linux adapter.
- Linux overlay limitations are captured in the docs.

You should verify:

- There is an actual Linux machine or workflow that needs this.
- The Linux overlay spike is good enough before we port the full app.

#### Step L.2: Linux Adapter

Build only if the Linux overlay spike passes:

- Add Linux overlay behavior.
- Add Linux autostart.
- Document Linux-specific limitations.

I can verify:

- Shared core still works with a Linux adapter.
- Linux adapter follows the same platform interface.
- Linux test checklist exists.

You should verify:

- The guard behavior is acceptable on the target Linux desktop environment.

## Resolved Decisions

- Platform priority: macOS first, Windows second, Linux deferred until there is a real use case.
- App behavior: only cover the screen; do not close apps.
- Configuration changes during bedtime: require extra friction.
- Guard screen: show at least the current time and how far past bedtime it is.
- Product shape: personal-use app, but reliable and easy to use.
- Implementation stack: Python desktop app using PySide6 / Qt for Python, with a pure-Python core and per-OS adapters.
- Platform gate: each platform starts with a tiny PySide6 overlay feasibility spike before full implementation or porting.
- Snooze friction: require increasingly difficult or long fixed messages as it gets later, matched case-sensitively.
- Wakeup rule: hide the overlay about 5 hours after the last snooze.
- Debug mode: support bedtime now, bedtime 10 minutes from now, and accelerated timing for a full flow within about 5 minutes.
- Runtime state: persist last snooze timestamp, active snooze expiry, and last known schedule state in a local file.
- Wind-down warnings: use the most reliable cross-platform approach, including a dedicated warning window if that beats native notifications.
- Default macOS file locations: use `~/Library/Application Support/BedtimeGuard/` for config/state and `~/Library/Logs/BedtimeGuard/` for event logs.

## Decisions To Make

- No open decisions right now.

## Current Recommendation

For the first iteration, build a local desktop guard with:

- Python 3.12+ and PySide6 / Qt for Python.
- A schedule-driven full-screen overlay.
- Unlimited snoozes with shorter durations and longer passphrases as it gets later.
- A wakeup release about 5 hours after the last snooze.
- Debug timing that can exercise bedtime, snoozes, and release over a few minutes.
- Broad bedtime friction for desktop use instead of app-specific rules.
- Event logging.
- A macOS-first architecture with a shared core and OS adapters, so Windows can follow cleanly.
- No website or network rules yet.

This is the smallest version that can change behavior while still teaching us where the real bypasses and frustrations are.
