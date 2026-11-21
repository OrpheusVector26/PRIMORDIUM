"""Safe, dependency-light helpers for A2A v1.0 card negotiation.

This module validates and negotiates agent cards but does not perform network I/O,
execute received code, or claim cryptographic signature verification. Signature
verification belongs at the transport boundary with a vetted JWS/RFC 8785 stack.
"""
from __future__ import annotations

import uuid
from typing import Any

A2A_PROTOCOL_VERSION = "1.0"
SUPPORTED_BINDINGS = frozenset({"JSONRPC"})
SUPPORTED_INPUT_MODES = frozenset({"text/plain", "application/json"})
REQUIRED_CARD_FIELDS = (
    "name", "description", "supportedInterfaces", "version",
    "capabilities", "defaultInputModes", "defaultOutputModes", "skills",
)
LEGACY_MARKERS = frozenset({"url", "preferredTransport", "additionalInterfaces", "protocolVersion", "security"})


class A2AError(ValueError):
    """Base error for card validation and negotiation failures."""


class CardSchemaError(A2AError):
    pass


class LegacyCardError(A2AError):
    pass


class ProtocolVersionError(A2AError):
    pass


class NegotiationError(A2AError):
    pass


def detect_legacy_card(card: dict[str, Any]) -> None:
    markers = sorted(LEGACY_MARKERS.intersection(card))
    if markers:
        raise LegacyCardError(
            "card contains A2A v0.x field(s) "
            f"{markers}; this boundary speaks v1.0 and requires supportedInterfaces"
        )


def validate_card(card: dict[str, Any]) -> list[str]:
    """Return all structural defects found in an A2A v1 card."""
    defects: list[str] = []
    if not isinstance(card, dict):
        return [f"card root is {type(card).__name__}, expected object"]
    missing = [field for field in REQUIRED_CARD_FIELDS if field not in card]
    if missing:
        defects.append(f"missing required fields: {missing}")
        return defects

    interfaces = card["supportedInterfaces"]
    if not isinstance(interfaces, list) or not interfaces:
        defects.append("supportedInterfaces is empty or not a list")
    else:
        for index, interface in enumerate(interfaces):
            if not isinstance(interface, dict):
                defects.append(f"supportedInterfaces[{index}] is not an object")
                continue
            for field in ("url", "protocolBinding", "protocolVersion"):
                if field not in interface:
                    defects.append(f"supportedInterfaces[{index}] missing {field!r}")

    skills = card["skills"]
    if not isinstance(skills, list) or not skills:
        defects.append("skills is empty or not a list")
    else:
        for index, skill in enumerate(skills):
            if not isinstance(skill, dict):
                defects.append(f"skills[{index}] is not an object")
                continue
            for field in ("id", "name", "description", "tags"):
                if field not in skill:
                    defects.append(f"skills[{index}] missing {field!r}")
            if "tags" in skill and not isinstance(skill["tags"], list):
                defects.append(f"skills[{index}].tags is not a list")

    for field in ("defaultInputModes", "defaultOutputModes"):
        if not isinstance(card[field], list) or not card[field]:
            defects.append(f"{field} is empty or not a list")
    if not isinstance(card["capabilities"], dict):
        defects.append("capabilities is not an object")
    return defects


def select_interface(card: dict[str, Any]) -> dict[str, Any]:
    """Select the first compatible interface, skipping unsupported entries."""
    skipped: list[str] = []
    for index, interface in enumerate(card.get("supportedInterfaces", [])):
        if not isinstance(interface, dict):
            skipped.append(f"[{index}] not-an-object")
            continue
        if interface.get("protocolVersion") != A2A_PROTOCOL_VERSION:
            skipped.append(f"[{index}] protocolVersion={interface.get('protocolVersion')!r}")
            continue
        if interface.get("protocolBinding") not in SUPPORTED_BINDINGS:
            skipped.append(f"[{index}] protocolBinding={interface.get('protocolBinding')!r}")
            continue
        return interface
    raise ProtocolVersionError(
        f"no interface speaks protocolVersion {A2A_PROTOCOL_VERSION!r} over "
        f"{sorted(SUPPORTED_BINDINGS)}; skipped: {skipped or 'none'}"
    )


def negotiate(card: dict[str, Any], requested_tags: set[str], *, streaming: bool = False) -> dict[str, Any]:
    """Return the compatible skill/mode intersection or raise a typed error."""
    defects = validate_card(card)
    if defects:
        raise CardSchemaError("; ".join(defects))
    interface = select_interface(card)
    matched = [skill["id"] for skill in card["skills"] if requested_tags.intersection(skill.get("tags", []))]
    if not matched:
        offered = sorted({tag for skill in card["skills"] for tag in skill.get("tags", [])})
        raise NegotiationError(f"no skill matches {sorted(requested_tags)}; offered tags: {offered}")
    if streaming and not card["capabilities"].get("streaming", False):
        raise NegotiationError("streaming requested but capabilities.streaming is false")
    inputs = [mode for mode in card["defaultInputModes"] if mode in SUPPORTED_INPUT_MODES]
    if not inputs:
        raise NegotiationError(f"no input mode overlap; agent accepts {card['defaultInputModes']}")
    return {
        "endpoint": interface["url"],
        "protocol_binding": interface["protocolBinding"],
        "matched_skills": matched,
        "input_modes": inputs,
        "output_modes": list(card["defaultOutputModes"]),
        "streaming": streaming,
    }


def build_handshake_envelope(agent_id: str, requested_skills: list[str]) -> dict[str, Any]:
    return {
        "envelopeVersion": "1.0",
        "intent": "handshake",
        "from": {"agentId": agent_id, "protocolVersion": A2A_PROTOCOL_VERSION, "skillsOffered": []},
        "requestedSkills": requested_skills,
        "modes": {"input": ["application/json"], "output": ["application/json"]},
        "budget": {"maxTurns": 6, "maxWallClockS": 900},
        "constraints": {
            "evidenceLabels": ["High", "Medium", "Low", "Speculative"],
            "noStubs": True,
            "requireClassicalBaseline": True,
        },
        "acceptance": "Response names the baseline, scaling, confidence, and verification step.",
    }


def build_send_message(envelope: dict[str, Any], *, message_id: str | None = None) -> dict[str, Any]:
    message_id = message_id or str(uuid.uuid4())
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "method": "SendMessage",
        "params": {
            "message": {
                "messageId": message_id,
                "role": "ROLE_USER",
                "parts": [{"data": envelope, "mediaType": "application/json"}],
            }
        },
    }
