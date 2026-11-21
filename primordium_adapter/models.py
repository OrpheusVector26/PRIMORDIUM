"""Typed public models for the PRIMORDIUM adapter boundary."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, Mapping, TypeVar

PROTOCOL_VERSION = "1.0"
T = TypeVar("T")


class Capability(str, Enum):
    ADAPTER_DESCRIBE = "adapter.describe"
    READ_SOURCES = "sources.read"
    READ_ARTIFACTS = "artifacts.read"
    VERIFY_INTEGRITY = "integrity.verify"
    EMIT_EVENTS = "events.emit"


class EventLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    audit_id: str
    caller: str
    deadline: datetime
    approved_capabilities: frozenset[Capability] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        for name, value in (("request_id", self.request_id), ("audit_id", self.audit_id), ("caller", self.caller)):
            if not value or not value.strip():
                raise ValueError(f"{name} must not be empty")
        if self.deadline.tzinfo is None:
            raise ValueError("deadline must be timezone-aware")

    def allows(self, capability: Capability) -> bool:
        return capability in self.approved_capabilities


@dataclass(frozen=True)
class AdapterInfo:
    name: str
    adapter_version: str
    protocol_version: str
    runtime: str
    capabilities: frozenset[Capability]
    read_only: bool = True


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    name: str
    sha256: str
    size_bytes: int
    ingested_at: datetime
    origin_class: str | None = None


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    name: str
    kind: str
    sha256: str
    size_bytes: int
    created_at: datetime


@dataclass(frozen=True)
class AdapterEvent:
    event_id: str
    audit_id: str
    request_id: str
    level: EventLevel
    event_type: str
    occurred_at: datetime
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntegrityResult:
    resource_id: str
    recorded_sha256: str
    current_sha256: str | None
    verified: bool | None
    status: str


@dataclass(frozen=True)
class Page(Generic[T]):
    items: tuple[T, ...]
    next_cursor: str | None
