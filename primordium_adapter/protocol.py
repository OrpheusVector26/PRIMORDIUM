"""Protocol contract implemented by a governed PRIMORDIUM adapter."""
from __future__ import annotations

from typing import Protocol

from .models import (
    AdapterEvent,
    AdapterInfo,
    ArtifactRecord,
    IntegrityResult,
    Page,
    RequestContext,
    SourceRecord,
)


class PrimordiumAdapter(Protocol):
    """Read-mostly, policy-mediated integration boundary."""

    def describe(self) -> AdapterInfo:
        ...

    def read_sources(self, ctx: RequestContext, *, cursor: str | None = None, limit: int = 100) -> Page[SourceRecord]:
        ...

    def read_artifacts(self, ctx: RequestContext, *, cursor: str | None = None, limit: int = 100) -> Page[ArtifactRecord]:
        ...

    def verify_source(self, ctx: RequestContext, source_id: str) -> IntegrityResult:
        ...

    def emit_event(self, ctx: RequestContext, event: AdapterEvent) -> str:
        ...
