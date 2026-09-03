"""Immutable typed views over validated, still-untrusted F-02 payloads."""
from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from .validate import validate_payload

def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(child) for child in value)
    return value


class ImmutablePayload:
    payload_type: str = ""
    def __init__(self, payload: Mapping[str, Any]):
        raise TypeError("use from_payload() to construct an immutable payload")

    @classmethod
    def from_payload(cls, value: Mapping[str, Any]):
        if not isinstance(value, Mapping):
            raise TypeError("payload must be a mapping")
        checked = validate_payload(dict(value), cls.payload_type)
        instance = object.__new__(cls)
        object.__setattr__(instance, "payload", _freeze(dict(checked)))
        object.__setattr__(instance, "document_id", checked["document_id"])
        object.__setattr__(instance, "board_id", checked.get("board_id") or checked.get("selection", {}).get("board_id"))
        return instance

    @classmethod
    def from_document(cls, value: Mapping[str, Any]):
        from .validate import payload_from_document
        return cls.from_payload(payload_from_document(value, cls.payload_type))

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("immutable payload")

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.document_id!r})"


class BoardRegistry(ImmutablePayload):
    payload_type = "board-registry/v1"


class PlatformManifest(ImmutablePayload):
    payload_type = "platform-manifest/v1"


class InstallerPlan(ImmutablePayload):
    payload_type = "installer-plan/v1"


class QualificationRecord(ImmutablePayload):
    payload_type = "qualification-record/v1"


class BootHealth(ImmutablePayload):
    payload_type = "boot-health/v1"


class OwnerApproval(ImmutablePayload):
    payload_type = "owner-approval/v1"


class BootSuccessMark(ImmutablePayload):
    payload_type = "boot-success-mark/v1"


class DtbMutationEnvelope(ImmutablePayload):
    payload_type = "dtb-mutation-envelope/v1"


__all__ = ["BoardRegistry", "PlatformManifest", "InstallerPlan", "QualificationRecord", "BootHealth", "OwnerApproval", "BootSuccessMark", "DtbMutationEnvelope"]
