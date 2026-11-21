"""PRIMORDIUM adapter boundary."""
from .models import (
    PROTOCOL_VERSION,
    AdapterEvent,
    AdapterInfo,
    ArtifactRecord,
    Capability,
    EventLevel,
    IntegrityResult,
    Page,
    RequestContext,
    SourceRecord,
)
from .protocol import PrimordiumAdapter
from .reference import ReferenceAdapter
from .a2a import build_handshake_envelope, build_send_message, negotiate, validate_card

__all__ = [
    "PROTOCOL_VERSION",
    "AdapterEvent",
    "AdapterInfo",
    "ArtifactRecord",
    "Capability",
    "EventLevel",
    "IntegrityResult",
    "Page",
    "PrimordiumAdapter",
    "ReferenceAdapter",
    "RequestContext",
    "SourceRecord",
    "build_handshake_envelope",
    "build_send_message",
    "negotiate",
    "validate_card",
]
