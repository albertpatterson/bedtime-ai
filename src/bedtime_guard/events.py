from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from json import dumps
from pathlib import Path


@dataclass(frozen=True)
class EventRecord:
    event_type: str
    occurred_at: str
    details: dict[str, object]


def build_event_record(
    *, event_type: str, occurred_at: datetime, details: dict[str, object]
) -> EventRecord:
    return EventRecord(
        event_type=event_type,
        occurred_at=occurred_at.isoformat(),
        details=details,
    )


def append_event_record(path: Path, record: EventRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(dumps(asdict(record), sort_keys=True))
        handle.write("\n")
