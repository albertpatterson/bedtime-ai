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
- Windows, macOS, and Linux support as a design requirement.
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

### Cross-Platform Guard Requirements

The guard must work on Windows, macOS, and Linux, but each OS has different rules for always-on-top windows, focus capture, notifications, and autostart.

The design should therefore use one shared core with per-OS adapters:

- Shared core: schedule calculation, state machine, policy parsing, event logging, and snooze rules.
- Windows adapter: startup integration, topmost full-screen windows, and notifications.
- macOS adapter: launch agent integration, full-screen/top-level window behavior, notifications, and accessibility permission notes if needed.
- Linux adapter: desktop autostart or systemd user integration, X11/Wayland-specific full-screen behavior, and notifications.

The first prototype should target macOS. Windows and Linux support should remain part of the design, but macOS should be the first platform used to prove the guard behavior and snooze flow.

## Recommended Architecture

Start with a local desktop app plus a small background scheduler.

Components:

- `Scheduler`: determines current phase from bedtime, wakeup rule, grace period, and snoozes.
- `Debug Schedule Mode`: overrides the normal bedtime during development or manual testing.
- `Notification UI`: easily dismissed wind-down warnings before bedtime.
- `Overlay UI`: full-screen interface shown during guarded periods.
- `Friction Controller`: decides whether normal interaction, wind-down prompts, full-screen guard, or snooze mode is active.
- `Platform Adapter`: handles autostart, full-screen behavior, and notifications per OS.
- `Policy Config`: local file defining schedules, grace rules, and snooze rules.
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

### Guarded Screen

At bedtime, the screen becomes a full-screen guard.

The guard should avoid stimulating content. It should be plain, calm, and direct.

The guarded screen should show:

- Bedtime status.
- Current time.
- Time elapsed since bedtime.
- Automatic release time.
- Current snooze duration and passphrase length.
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
time_scale = 1.0 # lower values compress timing for manual testing
debug_wakeup_minutes_after_last_snooze = 5

[snooze]
enabled = true
uses_per_night = "unlimited"
require_passphrase = true

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
- Windows, macOS, and Linux differ in topmost-window behavior.

## Implementation Paths To Compare Later

### Cross-Platform Desktop App

Candidate stack:

- Shared application core.
- Per-OS adapters for autostart, notifications, and full-screen behavior.
- A UI toolkit that supports Windows, macOS, and Linux.

Good fit if we want one product shape across all target operating systems.

### Python Desktop App

Candidate stack:

- Python.
- PySide or PyQt for full-screen UI.
- Platform-specific hooks for autostart and window behavior.

Good fit if we want quick local iteration and simple packaging experiments. Cross-platform packaging will need deliberate testing.

### Electron Or Tauri App

Candidate stack:

- Web UI for overlay and settings.
- Node or Rust backend for process monitoring and OS integration.

Good fit if we want a polished interface and more established cross-platform packaging.

### Native Per-OS Adapters

Candidate stack:

- Windows service or startup task plus desktop UI.
- macOS launch agent plus desktop UI.
- Linux desktop autostart or systemd user service plus desktop UI.

Good fit if robustness matters more than keeping the implementation identical on every OS.

## Milestone Plan

### Milestone 1: Design And Simulation

Build:

- Define schedule states.
- Define policy config.
- Add wakeup rule based on the last snooze.
- Add debug schedule mode for bedtime now and bedtime 10 minutes from now.
- Add accelerated debug timing for snooze ladder and wakeup release.
- Define cross-platform adapter boundaries.
- Write sample event logs.
- Simulate state transitions without enforcing anything.

I can verify:

- Schedule state calculations for normal bedtime, wind-down, guarded, snoozed, and released states.
- Snooze ladder selection at each configured time threshold.
- Wakeup release calculation from the last snooze timestamp.
- Debug mode behavior for bedtime now, bedtime 10 minutes from now, and accelerated timing.
- Policy parsing and validation, including invalid or missing fields.
- Event log shape using generated sample events.

You should verify:

- The configured bedtime, wind-down timing, snooze ladder, and wakeup rule feel right.
- The generated event log contains the kind of information you would actually want to review.
- Debug timing feels fast enough to test without becoming confusing.

### Milestone 2: Full-Screen Guard Prototype

Build:

- Show full-screen overlay during guarded state.
- Support release after the wakeup rule is satisfied.
- Support typed snooze passphrases.
- Log warnings, guard activations, and snoozes.
- Test manually on macOS first while keeping adapter boundaries clean.

I can verify:

- The app enters guarded state at the expected time.
- The overlay renders the current time, time since bedtime, computed release time, snooze duration, and passphrase length.
- Correct passphrases activate snooze, and incorrect passphrases do not.
- Snooze expiration returns to guarded state.
- Wakeup release hides the overlay.
- Warnings, guard activations, snoozes, and releases are logged.

You should verify:

- The full-screen guard actually prevents normal desktop interaction on your Mac.
- The guard feels plain and calm rather than irritating.
- The snooze passphrase friction feels useful rather than hostile.
- Debug mode lets you test the bedtime-to-release flow in a few minutes.

### Milestone 3: Cross-Platform Guard Behavior

Build:

- Validate full-screen behavior on Windows, macOS, and Linux.
- Test multi-monitor setups.
- Test wake, lock screen, fast user switching, and virtual desktops.
- Document known OS-specific weaknesses.

I can verify:

- Shared schedule, snooze, wakeup, debug, policy, and logging logic stays platform-independent.
- Platform adapters expose the same interface for notifications, overlay behavior, and autostart.
- Documented manual test checklists exist for Windows, macOS, and Linux.
- Known OS-specific weaknesses are captured in the docs.

You should verify:

- The guard covers the displays you actually use on each target OS.
- Window focus, virtual desktops, lock/wake behavior, and multi-monitor behavior feel acceptable.
- Any OS permission prompts are understandable and not too annoying.
- The known weaknesses are acceptable for a personal-use app.

### Milestone 4: Autostart And Recovery

Build:

- Start on login.
- Restart after crash if appropriate.
- Add recovery instructions.
- Test reboot behavior on all three operating systems.

I can verify:

- Autostart configuration files or installer steps are generated as expected.
- App startup loads the policy and resumes the correct schedule state.
- Crash/restart behavior preserves enough state to compute guarded, snoozed, or released status.
- Recovery instructions are present in the repo and reference the right files or commands.
- Reboot-state handling is covered by tests where practical.

You should verify:

- The app starts after login on your actual machines.
- Recovery instructions are understandable when you are tired.
- Crash or reboot behavior does not surprise you during guarded hours.
- The app remains easy enough to live with that you are not tempted to disable autostart permanently.

## Resolved Decisions

- First prototype platform: macOS.
- App behavior: only cover the screen; do not close apps.
- Configuration changes during bedtime: require extra friction.
- Guard screen: show at least the current time and how far past bedtime it is.
- Product shape: personal-use app, but reliable and easy to use.
- Snooze friction: require increasingly difficult or long passphrases as it gets later.
- Wakeup rule: hide the overlay about 5 hours after the last snooze.
- Debug mode: support bedtime now, bedtime 10 minutes from now, and accelerated timing for short manual test cycles.

## Decisions To Make

- No open decisions right now.

## Current Recommendation

For the first iteration, build a local desktop guard with:

- A schedule-driven full-screen overlay.
- Unlimited snoozes with shorter durations and longer passphrases as it gets later.
- A wakeup release about 5 hours after the last snooze.
- Debug timing that can exercise bedtime, snoozes, and release over a few minutes.
- Broad bedtime friction for desktop use instead of app-specific rules.
- Event logging.
- A cross-platform architecture with OS adapters from the beginning.
- No website or network rules yet.

This is the smallest version that can change behavior while still teaching us where the real bypasses and frustrations are.
