"""Stable exceptions exposed by the adapter boundary."""
from __future__ import annotations


class AdapterError(Exception):
    """Base class for safe, public adapter failures."""

    code = "adapter_error"

    def __init__(self, message: str, *, request_id: str | None = None, audit_id: str | None = None):
        super().__init__(message)
        self.message = message
        self.request_id = request_id
        self.audit_id = audit_id


class AuthorizationError(AdapterError):
    code = "not_authorized"


class AdapterUnavailable(AdapterError):
    code = "adapter_unavailable"


class IncompatibleProtocol(AdapterError):
    code = "incompatible_protocol"


class InvalidRequest(AdapterError):
    code = "invalid_request"


class ResourceNotFound(AdapterError):
    code = "resource_not_found"


class IntegrityUnavailable(AdapterError):
    code = "integrity_unavailable"
