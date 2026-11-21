"""A deterministic reference adapter for contract tests and local development.

It is intentionally read-mostly and stores only supplied records in memory. It does
not access the filesystem, execute modules, invoke a shell, or use the network.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Iterable

from .errors import AuthorizationError, InvalidRequest, ResourceNotFound
from .models import (
    AdapterEvent,
    AdapterInfo,
    ArtifactRecord,
    Capability,
    IntegrityResult,
    Page,
    RequestContext,
    SourceRecord,
)

_MAX_PAGE_SIZE = 1000


class ReferenceAdapter:
    def __init__(self, *, sources: Iterable[SourceRecord] = (), artifacts: Iterable[ArtifactRecord] = ()):
        self._sources = tuple(sources)
        self._artifacts = tuple(artifacts)
        self._events: list[AdapterEvent] = []
        self._cursor_key = secrets.token_bytes(32)

    def describe(self) -> AdapterInfo:
        return AdapterInfo(
            name="primordium-reference-adapter",
            adapter_version="1.0.0",
            protocol_version="1.0",
            runtime="python",
            capabilities=frozenset(Capability),
            read_only=True,
        )

    def read_sources(self, ctx: RequestContext, *, cursor: str | None = None, limit: int = 100) -> Page[SourceRecord]:
        self._authorize(ctx, Capability.READ_SOURCES)
        return self._page(self._sources, cursor, limit)

    def read_artifacts(self, ctx: RequestContext, *, cursor: str | None = None, limit: int = 100) -> Page[ArtifactRecord]:
        self._authorize(ctx, Capability.READ_ARTIFACTS)
        return self._page(self._artifacts, cursor, limit)

    def verify_source(self, ctx: RequestContext, source_id: str) -> IntegrityResult:
        self._authorize(ctx, Capability.VERIFY_INTEGRITY)
        for source in self._sources:
            if source.source_id == source_id:
                # The reference adapter has no filesystem authority. It verifies
                # the recorded value is well-formed, but reports current content
                # as unavailable rather than making a false verification claim.
                valid_hash = len(source.sha256) == 64 and all(c in "0123456789abcdef" for c in source.sha256.lower())
                return IntegrityResult(source_id, source.sha256, None, None, "unavailable" if valid_hash else "invalid_recorded_hash")
        raise ResourceNotFound(f"source not found: {source_id}", request_id=ctx.request_id, audit_id=ctx.audit_id)

    def emit_event(self, ctx: RequestContext, event: AdapterEvent) -> str:
        self._authorize(ctx, Capability.EMIT_EVENTS)
        if event.audit_id != ctx.audit_id or event.request_id != ctx.request_id:
            raise InvalidRequest("event correlation does not match request context", request_id=ctx.request_id, audit_id=ctx.audit_id)
        self._events.append(event)
        return event.event_id

    @property
    def events(self) -> tuple[AdapterEvent, ...]:
        return tuple(self._events)

    def _authorize(self, ctx: RequestContext, capability: Capability) -> None:
        if datetime.now(timezone.utc) > ctx.deadline:
            raise AuthorizationError("request deadline exceeded", request_id=ctx.request_id, audit_id=ctx.audit_id)
        if not ctx.allows(capability):
            raise AuthorizationError(f"capability not approved: {capability.value}", request_id=ctx.request_id, audit_id=ctx.audit_id)

    def _page(self, items: tuple, cursor: str | None, limit: int) -> Page:
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= _MAX_PAGE_SIZE:
            raise InvalidRequest(f"limit must be between 1 and {_MAX_PAGE_SIZE}")
        offset = self._decode_cursor(cursor) if cursor else 0
        if offset > len(items):
            raise InvalidRequest("cursor is past the end of the collection")
        chunk = items[offset : offset + limit]
        next_cursor = self._encode_cursor(offset + len(chunk)) if offset + len(chunk) < len(items) else None
        return Page(tuple(chunk), next_cursor)

    def _encode_cursor(self, offset: int) -> str:
        raw = str(offset).encode()
        sig = hmac.new(self._cursor_key, raw, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(raw + b"." + sig).decode().rstrip("=")

    def _decode_cursor(self, cursor: str) -> int:
        try:
            padded = cursor + "=" * (-len(cursor) % 4)
            raw, sig = base64.urlsafe_b64decode(padded.encode()).rsplit(b".", 1)
            expected = hmac.new(self._cursor_key, raw, hashlib.sha256).digest()
            if not hmac.compare_digest(sig, expected):
                raise ValueError
            offset = int(raw)
            if offset < 0:
                raise ValueError
            return offset
        except (ValueError, TypeError, base64.binascii.Error):
            raise InvalidRequest("invalid cursor") from None
