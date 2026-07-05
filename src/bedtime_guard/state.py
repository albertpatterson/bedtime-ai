from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from json import dump, load
from pathlib import Path


@dataclass(frozen=True)
class RuntimeState:
    last_snooze_at: datetime | None = None
    active_snooze_expires_at: datetime | None = None
    last_known_phase: str | None = None


def _serialize_dt(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def _deserialize_dt(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value)


def save_runtime_state(path: Path, state: RuntimeState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(state)
    payload["last_snooze_at"] = _serialize_dt(state.last_snooze_at)
    payload["active_snooze_expires_at"] = _serialize_dt(state.active_snooze_expires_at)
    with path.open("w", encoding="utf-8") as handle:
        dump(payload, handle, indent=2, sort_keys=True)


def load_runtime_state(path: Path) -> RuntimeState:
    if not path.exists():
        return RuntimeState()
    with path.open("r", encoding="utf-8") as handle:
        payload = load(handle)
    return RuntimeState(
        last_snooze_at=_deserialize_dt(payload.get("last_snooze_at")),
        active_snooze_expires_at=_deserialize_dt(
            payload.get("active_snooze_expires_at")
        ),
        last_known_phase=payload.get("last_known_phase"),
    )
