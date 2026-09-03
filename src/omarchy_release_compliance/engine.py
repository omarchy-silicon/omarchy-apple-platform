"""Pure F-06 inventory validation, evaluation, and attestation projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any
from urllib.parse import urlsplit

from omarchy_platform.canonical import canonical_bytes, domain_digest
from omarchy_release_compliance.policy import vocabulary

VERSION = "release-compliance/v1"
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_TOP = ("version", "policy", "candidate", "manifest", "schema_set", "artifacts")
_TARGET = ("id", "version", "digest")
_ARTIFACT = (
    "artifact_id", "component_id", "content_digest", "source_digest", "upstream_digest", "fork_digest",
    "source_uri", "artifact_class", "spdx_expression", "copyright_notice", "source_offer",
    "redistribution", "owner_decision", "firmware_policy", "asset_policy", "generated", "build_provenance", "sbom_ref",
    "candidate_ref", "manifest_ref", "schema_set_ref",
)
_NOTICE = ("id", "text")
_OFFER = ("status", "location", "digest", "expires_at")
_DECISION = ("decision_id", "evidence_digest", "decided_at", "expires_at")


@dataclass(frozen=True)
class Failure:
    code: str
    path: str
    detail: str


class ComplianceError(ValueError):
    """A stable, structured rejection from the policy seam."""

    def __init__(self, code: str, path: str, detail: str):
        super().__init__(f"{code} at {path}: {detail}")
        self.code, self.path, self.detail = code, path, detail

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "detail": self.detail}


def _fail(code: str, path: str, detail: str) -> None:
    raise ComplianceError(code, path, detail)


def _object(value: Any, path: str, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("INCOMPLETE_INVENTORY", path, "object required")
    actual = tuple(value)
    unknown = sorted(set(actual) - set(keys))
    missing = sorted(set(keys) - set(actual))
    if unknown:
        _fail("UNKNOWN_FIELD", f"{path}.{unknown[0]}", "field is not in the closed grammar")
    if missing:
        _fail("INCOMPLETE_INVENTORY", f"{path}.{missing[0]}", "required field is absent")
    return value


def _string(value: Any, path: str, *, identifier: bool = False) -> str:
    if not isinstance(value, str) or not value:
        _fail("INCOMPLETE_INVENTORY", path, "non-empty string required")
    if identifier and (not _ID.fullmatch(value) or any(ord(c) > 127 for c in value)):
        _fail("INVALID_IDENTIFIER", path, "identifier must be bounded ASCII")
    return value


def _digest(value: Any, path: str) -> str:
    if value is None:
        return value
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        _fail("INVALID_DIGEST", path, "lowercase sha256 digest required")
    return value


def _timestamp(value: Any, path: str) -> datetime:
    _string(value, path)
    if not _UTC.fullmatch(value):
        _fail("INVALID_TIMESTAMP", path, "UTC timestamp must use YYYY-MM-DDTHH:MM:SSZ")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _fail("INVALID_TIMESTAMP", path, "invalid UTC timestamp")


def _target(value: Any, path: str) -> dict[str, Any]:
    target = _object(value, path, _TARGET)
    _string(target["id"], f"{path}.id", identifier=True)
    _string(target["version"], f"{path}.version")
    _digest(target["digest"], f"{path}.digest")
    return target


def _immutable_uri(value: Any, path: str) -> str:
    uri = _string(value, path)
    parsed = urlsplit(uri)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        _fail("MUTABLE_SOURCE_URI", path, "only pinned HTTPS URIs are accepted")
    if parsed.query or parsed.fragment or "%" in parsed.path:
        _fail("MUTABLE_SOURCE_URI", path, "query, fragment, and encoded paths are not immutable")
    if not re.search(r"sha256:[0-9a-f]{64}", parsed.path) and not re.search(r"(?:^|[/_-])v?\d+\.\d+(?:\.\d+)?(?:[/_.-]|$)", parsed.path):
        _fail("MUTABLE_SOURCE_URI", path, "URI must contain a pinned digest or version")
    return uri


def _sorted_unique(items: list[Any], path: str, field: str) -> None:
    ids = [_string(item.get(field), f"{path}[{index}].{field}", identifier=True) if isinstance(item, dict) else "" for index, item in enumerate(items)]
    if len(set(ids)) != len(ids):
        _fail("DUPLICATE_ID", path, f"duplicate {field}")
    if ids != sorted(ids):
        _fail("UNSORTED_IDS", path, f"{field} list must be sorted")


def _check_ref(ref: Any, expected: dict[str, Any], path: str) -> None:
    got = _target(ref, path)
    if got != expected:
        _fail("TARGET_BINDING_MISMATCH", path, "candidate, manifest, and schema-set references must match exactly")


def _artifact(item: Any, path: str, candidate: dict, manifest: dict, schema_set: dict, now: datetime) -> None:
    a = _object(item, path, _ARTIFACT)
    _string(a["artifact_id"], f"{path}.artifact_id", identifier=True)
    _string(a["component_id"], f"{path}.component_id", identifier=True)
    for field in ("content_digest", "source_digest", "upstream_digest", "fork_digest"):
        _digest(a[field], f"{path}.{field}")
    if a["source_digest"] is None:
        _fail("INCOMPLETE_INVENTORY", f"{path}.source_digest", "source digest is required")
    if a["content_digest"] is None:
        _fail("INCOMPLETE_INVENTORY", f"{path}.content_digest", "content digest is required")
    _immutable_uri(a["source_uri"], f"{path}.source_uri")
    if a["source_digest"] not in a["source_uri"]:
        _fail("DIGEST_MISMATCH", f"{path}.source_uri", "pinned URI digest does not match source_digest")
    if a["artifact_class"] not in vocabulary()["artifact_classes"]:
        _fail("UNKNOWN_ARTIFACT_CLASS", f"{path}.artifact_class", "artifact class is outside policy vocabulary")
    if a["spdx_expression"] not in vocabulary()["spdx_expressions"]:
        _fail("UNKNOWN_SPDX", f"{path}.spdx_expression", "SPDX expression is outside policy vocabulary")
    if a["firmware_policy"] not in vocabulary()["firmware_policy"]:
        _fail("UNKNOWN_FIRMWARE_POLICY", f"{path}.firmware_policy", "firmware policy is outside vocabulary")
    if a["artifact_class"] == "firmware" and a["firmware_policy"] == "not-applicable":
        _fail("FIRMWARE_POLICY_MISSING", f"{path}.firmware_policy", "firmware needs an explicit policy classification")
    if a["artifact_class"] != "firmware" and a["firmware_policy"] != "not-applicable":
        _fail("INVALID_FIRMWARE_POLICY", f"{path}.firmware_policy", "non-firmware artifact must be not-applicable")
    if a["asset_policy"] not in vocabulary()["asset_policy"]:
        _fail("UNKNOWN_ASSET_POLICY", f"{path}.asset_policy", "asset policy is outside vocabulary")
    if a["artifact_class"] == "asset" and a["asset_policy"] == "not-applicable":
        _fail("ASSET_POLICY_MISSING", f"{path}.asset_policy", "asset needs an explicit policy classification")
    if a["artifact_class"] != "asset" and a["asset_policy"] != "not-applicable":
        _fail("INVALID_ASSET_POLICY", f"{path}.asset_policy", "non-asset artifact must be not-applicable")
    notices = a["copyright_notice"]
    if not isinstance(notices, list) or not notices:
        _fail("NOTICE_MISSING", f"{path}.copyright_notice", "at least one copyright/NOTICE record is required")
    _sorted_unique(notices, f"{path}.copyright_notice", "id")
    for index, notice in enumerate(notices):
        n = _object(notice, f"{path}.copyright_notice[{index}]", _NOTICE)
        _string(n["id"], f"{path}.copyright_notice[{index}].id", identifier=True)
        _string(n["text"], f"{path}.copyright_notice[{index}].text")
    offer = a["source_offer"]
    if not isinstance(offer, dict):
        _fail("SOURCE_OFFER_MISSING", f"{path}.source_offer", "source-offer record is required")
    offer = _object(offer, f"{path}.source_offer", _OFFER)
    if offer["status"] not in vocabulary()["source_offer_status"] or offer["status"] != "offered":
        _fail("SOURCE_OFFER_MISSING", f"{path}.source_offer.status", "redistributed artifacts require offered source")
    _immutable_uri(offer["location"], f"{path}.source_offer.location")
    _digest(offer["digest"], f"{path}.source_offer.digest")
    if offer["digest"] != a["source_digest"] or offer["location"] != a["source_uri"]:
        _fail("DIGEST_MISMATCH", f"{path}.source_offer", "source offer must match source identity")
    expiry = _timestamp(offer["expires_at"], f"{path}.source_offer.expires_at")
    if expiry <= now:
        _fail("SOURCE_OFFER_EXPIRED", f"{path}.source_offer.expires_at", "source offer is expired")
    redist = a["redistribution"]
    if redist not in vocabulary()["redistribution"]:
        _fail("UNKNOWN_REDISTRIBUTION", f"{path}.redistribution", "redistribution state is outside vocabulary")
    if redist == "unknown":
        _fail("REDISTRIBUTION_UNKNOWN", f"{path}.redistribution", "unknown redistribution cannot pass closed policy")
    if redist == "prohibited":
        _fail("REDISTRIBUTION_PROHIBITED", f"{path}.redistribution", "prohibited artifact cannot be redistributed")
    if redist == "direct-fetch-only":
        _fail("REDISTRIBUTION_DIRECT_FETCH_ONLY", f"{path}.redistribution", "direct-fetch-only artifact cannot be redistributed")
    decision = a["owner_decision"]
    if not isinstance(decision, dict):
        _fail("OWNER_DECISION_MISSING", f"{path}.owner_decision", "owner/legal decision is required")
    decision = _object(decision, f"{path}.owner_decision", _DECISION)
    _string(decision["decision_id"], f"{path}.owner_decision.decision_id", identifier=True)
    _digest(decision["evidence_digest"], f"{path}.owner_decision.evidence_digest")
    decided = _timestamp(decision["decided_at"], f"{path}.owner_decision.decided_at")
    expires = _timestamp(decision["expires_at"], f"{path}.owner_decision.expires_at")
    if decision["evidence_digest"] is None or expires <= decided:
        _fail("OWNER_DECISION_MISSING", f"{path}.owner_decision", "decision evidence and valid interval are required")
    if expires <= now:
        _fail("OWNER_DECISION_EXPIRED", f"{path}.owner_decision.expires_at", "owner/legal decision is expired")
    if not isinstance(a["generated"], bool):
        _fail("INCOMPLETE_INVENTORY", f"{path}.generated", "generated must be boolean")
    if a["generated"]:
        if not isinstance(a["build_provenance"], dict) or not a["build_provenance"]:
            _fail("PROVENANCE_MISSING", f"{path}.build_provenance", "generated artifacts require build provenance")
        if not isinstance(a["sbom_ref"], str) or not a["sbom_ref"]:
            _fail("SBOM_MISSING", f"{path}.sbom_ref", "generated artifacts require an SBOM reference")
    else:
        if a["build_provenance"] is not None or a["sbom_ref"] is not None:
            _fail("INVALID_PROVENANCE", f"{path}.build_provenance", "non-generated artifacts must use null provenance/SBOM")
    _check_ref(a["candidate_ref"], candidate, f"{path}.candidate_ref")
    _check_ref(a["manifest_ref"], manifest, f"{path}.manifest_ref")
    _check_ref(a["schema_set_ref"], schema_set, f"{path}.schema_set_ref")
    if a["fork_digest"] is not None and a["upstream_digest"] is None:
        _fail("FORK_UPSTREAM_AMBIGUOUS", f"{path}.fork_digest", "a fork must name its upstream digest")
    if a["fork_digest"] is not None and a["artifact_class"] != "fork":
        _fail("FORK_UPSTREAM_AMBIGUOUS", f"{path}.fork_digest", "fork digest requires fork artifact class")
    if a["artifact_class"] == "fork" and a["fork_digest"] is None:
        _fail("FORK_UPSTREAM_AMBIGUOUS", f"{path}.fork_digest", "fork artifacts require fork digest")


def validate(bundle: Any, *, now: datetime | None = None) -> dict[str, Any]:
    """Validate and return a defensive copy of an accepted bundle."""
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        _fail("INVALID_TIMESTAMP", "$.now", "evaluation time must be timezone-aware")
    top = _object(bundle, "$", _TOP)
    if top["version"] != VERSION:
        _fail("UNSUPPORTED_VERSION", "$.version", "unsupported release-compliance version")
    policy = _object(top["policy"], "$.policy", ("version", "digest"))
    if policy["version"] != vocabulary()["version"]:
        _fail("UNSUPPORTED_POLICY", "$.policy.version", "unsupported policy version")
    expected_policy = domain_digest("omarchy-compliance-policy/v1", vocabulary())
    if policy["digest"] != expected_policy:
        _fail("POLICY_DIGEST_MISMATCH", "$.policy.digest", "policy digest does not match closed vocabulary")
    candidate, manifest, schema_set = (_target(top[key], f"$.{key}") for key in ("candidate", "manifest", "schema_set"))
    artifacts = top["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        _fail("INCOMPLETE_INVENTORY", "$.artifacts", "at least one artifact is required")
    _sorted_unique(artifacts, "$.artifacts", "artifact_id")
    components = []
    for index, item in enumerate(artifacts):
        if not isinstance(item, dict):
            _fail("INCOMPLETE_INVENTORY", f"$.artifacts[{index}]", "artifact object required")
        components.append(item.get("component_id"))
        _artifact(item, f"$.artifacts[{index}]", candidate, manifest, schema_set, now)
    if any(not isinstance(component, str) for component in components):
        _fail("INCOMPLETE_INVENTORY", "$.artifacts", "component IDs are required")
    if len(set(components)) != len(components):
        _fail("DUPLICATE_ID", "$.artifacts", "duplicate component_id")
    if components != sorted(components):
        _fail("UNSORTED_IDS", "$.artifacts", "component IDs must be sorted")
    return bundle


def evaluate(bundle: Any, *, now: datetime | None = None) -> dict[str, Any]:
    """Return a closed allow/reject result without throwing for policy failures."""
    try:
        accepted = validate(bundle, now=now)
    except ComplianceError as error:
        return {"version": VERSION, "decision": "reject", **error.as_dict()}
    policy_digest = bundle["policy"]["digest"]
    candidate, manifest, schema_set = (bundle[key] for key in ("candidate", "manifest", "schema_set"))
    inventory_digest = domain_digest("omarchy-release-inventory/v1", bundle["artifacts"])
    bundle_digest = domain_digest("omarchy-release-bundle/v1", bundle)
    return {
        "version": VERSION, "decision": "allow", "code": "OK", "path": "$", "detail": "compliant",
        "inventory_digest": inventory_digest, "policy_digest": policy_digest,
        "candidate_digest": candidate["digest"], "manifest_digest": manifest["digest"],
        "schema_set_digest": schema_set["digest"], "bundle_digest": bundle_digest,
    }


def attest(bundle: Any, *, now: datetime | None = None) -> bytes:
    """Project an accepted result into unsigned evidence bytes."""
    result = evaluate(bundle, now=now)
    if result["decision"] != "allow":
        raise ComplianceError(result["code"], result["path"], result.get("detail", "rejected"))
    projection = {
        "version": "f06-compliance-attestation/v1",
        "decision": "allow",
        "signed": False,
        "trusted": False,
        "promotable": False,
        "inventory_digest": result["inventory_digest"],
        "policy_digest": result["policy_digest"],
        "candidate_digest": result["candidate_digest"],
        "manifest_digest": result["manifest_digest"],
        "schema_set_digest": result["schema_set_digest"],
        "bundle_digest": result["bundle_digest"],
    }
    return canonical_bytes(projection)
