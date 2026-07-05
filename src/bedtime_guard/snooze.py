from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class SnoozeTier:
    minutes_after_bedtime: int
    duration_minutes: int
    passphrase_words: int

    def __post_init__(self) -> None:
        if self.minutes_after_bedtime < 0:
            raise ValueError("minutes_after_bedtime must be non-negative")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.passphrase_words <= 0:
            raise ValueError("passphrase_words must be positive")


@dataclass(frozen=True)
class SnoozeDecision:
    tier_index: int
    tier: SnoozeTier
    passphrase: str


class FixedPhraseSource:
    """Fixed messages grouped from shorter to longer tiers."""

    DEFAULT_PHRASES = (
        "Sleep!",
        "Bedtime!",
        "Go to bed.",
        "Sleep now.",
        "Rest is worth it.",
        "Tomorrow starts tonight.",
        "A rested morning begins now.",
        "One more video is not worth tomorrow.",
        "Tonight's sleep is tomorrow's energy.",
        "Stopping now is kinder than pushing later.",
        "A shorter night will make tomorrow harder than this moment feels.",
        "If I stop now, tomorrow gets a calmer, steadier, more capable version of me.",
        "The future I want tomorrow is built by closing this out and giving sleep a chance tonight.",
        "More sleep tonight means more patience, energy, focus, and enjoyment for the day ahead.",
        "Staying up later steals energy from the morning I want and makes tomorrow smaller than it needs to be.",
        "Sleep matters more than one more video.",
        "Tomorrow deserves a rested version of me.",
        "I will feel better tomorrow if I stop now and let sleep do its job instead of asking tomorrow to pay for tonight.",
        "There is nothing I am doing right now that will help more than getting real sleep and meeting tomorrow with a clearer mind.",
    )

    def __init__(self, phrases: tuple[str, ...] | None = None) -> None:
        self._phrases = phrases or self.DEFAULT_PHRASES
        if not self._phrases:
            raise ValueError("at least one fixed passphrase is required")

    def phrase_for_tier(self, tier_index: int) -> str:
        capped_index = min(max(tier_index, 0), len(self._phrases) - 1)
        return self._phrases[capped_index]


def _scaled_timedelta(minutes: int, time_scale: float) -> timedelta:
    return timedelta(minutes=minutes * time_scale)


def choose_snooze_decision(
    *,
    minutes_since_bedtime: int,
    tiers: tuple[SnoozeTier, ...],
    phrase_source: FixedPhraseSource | None = None,
    time_scale: float = 1.0,
) -> SnoozeDecision:
    if not tiers:
        raise ValueError("at least one snooze tier is required")
    if time_scale <= 0:
        raise ValueError("time_scale must be positive")

    ordered_tiers = tuple(sorted(tiers, key=lambda tier: tier.minutes_after_bedtime))
    chosen_index = 0
    for index, tier in enumerate(ordered_tiers):
        if minutes_since_bedtime >= tier.minutes_after_bedtime:
            chosen_index = index
        else:
            break

    chosen_tier = ordered_tiers[chosen_index]
    source = phrase_source or FixedPhraseSource()
    scaled_duration = _scaled_timedelta(chosen_tier.duration_minutes, time_scale)
    scaled_minutes = max(1, int(scaled_duration.total_seconds() // 60))
    scaled_tier = SnoozeTier(
        minutes_after_bedtime=chosen_tier.minutes_after_bedtime,
        duration_minutes=scaled_minutes,
        passphrase_words=chosen_tier.passphrase_words,
    )
    return SnoozeDecision(
        tier_index=chosen_index,
        tier=scaled_tier,
        passphrase=source.phrase_for_tier(chosen_index),
    )


def matches_passphrase(*, expected: str, entered: str, case_sensitive: bool = True) -> bool:
    if case_sensitive:
        return entered == expected
    return entered.casefold() == expected.casefold()
