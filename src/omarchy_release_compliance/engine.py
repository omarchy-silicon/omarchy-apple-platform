"""Pure F-06 inventory validation, evaluation, and attestation projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

from omarchy_platform.canonical import canonical_bytes, domain_digest
from omarchy_release_compliance.policy import vocabulary

VERSION = "release-compliance/v1"
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_DNS = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$")
_TOP = ("version", "policy", "candidate", "manifest", "schema_set", "artifacts")
_TARGET = ("id", "version", "digest")
_ARTIFACT = (
    "artifact_id", "component_id", "content_digest", "source_digest", "upstream_digest", "fork_digest",
    "source_uri", "artifact_class", "spdx_expression", "copyright_notice", "source_offer",
    "redistribution", "owner_decision", "firmware_policy", "asset_policy", "generated", "build_provenance", "sbom_ref",
    "candidate_ref", "manifest_ref", "schema_set_ref",
)
_NOTICE = ("version", "id", "text", "digest")
_OFFER = ("version", "status", "location", "digest", "expires_at")
_DECISION = ("version", "decision_id", "evidence_digest", "decided_at", "expires_at")
_PROVENANCE = ("version", "builder", "toolchain", "recipe_digest", "source_digest", "environment_digest", "toolchain_digest")
_SBOM = ("version", "format", "digest", "uri")
_CLOCK = lambda: datetime.now(timezone.utc)


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


def _digest(value: Any, path: str, *, required: bool = True) -> str | None:
    if value is None and not required:
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


def _immutable_uri(value: Any, path: str, expected_digests: tuple[str, ...]) -> str:
    uri = _string(value, path)
    try:
        parsed = urlsplit(uri)
        hostname = parsed.hostname
        port = parsed.port
    except (ValueError, UnicodeError):
        _fail("MUTABLE_SOURCE_URI", path, "malformed HTTPS URI")
    if parsed.scheme != "https" or not hostname or not _DNS.fullmatch(hostname) or re.search(r"[A-Z]", parsed.netloc) or parsed.username or parsed.password or port is not None:
        _fail("MUTABLE_SOURCE_URI", path, "only lowercase-host HTTPS URIs without userinfo or port are accepted")
    if parsed.query or parsed.fragment or "%" in parsed.path:
        _fail("MUTABLE_SOURCE_URI", path, "query, fragment, and percent-encoded paths are not immutable")
    if not parsed.path.startswith("/"):
        _fail("MUTABLE_SOURCE_URI", path, "absolute path is required")
    segments = parsed.path[1:].split("/")
    if not segments or any(segment in ("", ".", "..") for segment in segments):
        _fail("MUTABLE_SOURCE_URI", path, "empty, dot, and traversal path segments are forbidden")
    filename = segments[-1]
    match = re.fullmatch(r"([0-9a-f]{64})(?:\.(?:tar\.gz|tgz|zip|json))?", filename)
    if not match or match.group(1) != expected_digests[-1].removeprefix("sha256:"):
        _fail("MUTABLE_SOURCE_URI", path, "final URI filename must be the exact lowercase digest token")
    if len(expected_digests) > 1 and (len(segments) < 2 or segments[-2] != expected_digests[0].removeprefix("sha256:")):
        _fail("MUTABLE_SOURCE_URI", path, "dedicated source digest path segment is not exact")
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


def _provenance_lock() -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parents[2] / "policy/release/provenance-lock.json"
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError, TypeError):
        _fail("PROVENANCE_AUTHORITY_MISSING", "$.policy.provenance", "repository provenance authority is unavailable")
    if not isinstance(value, dict) or set(value) != {"version", "artifacts"} or value.get("version") != "f06-provenance-lock/v1" or not isinstance(value.get("artifacts"), list):
        _fail("PROVENANCE_AUTHORITY_INVALID", "$.policy.provenance", "provenance authority is not the closed version")
    records = value["artifacts"]
    keys = {"artifact_id", "source_digest", "recipe_digest", "environment_digest", "builder", "toolchain", "toolchain_digest"}
    ids = []
    for index, record in enumerate(records):
        if not isinstance(record, dict) or set(record) != keys:
            _fail("PROVENANCE_AUTHORITY_INVALID", f"$.policy.provenance.artifacts[{index}]", "provenance authority record is open or incomplete")
        _string(record["artifact_id"], f"$.policy.provenance.artifacts[{index}].artifact_id", identifier=True)
        ids.append(record["artifact_id"])
        for field in ("source_digest", "recipe_digest", "environment_digest", "toolchain_digest"):
            _digest(record[field], f"$.policy.provenance.artifacts[{index}].{field}")
        _string(record["builder"], f"$.policy.provenance.artifacts[{index}].builder", identifier=True)
        _string(record["toolchain"], f"$.policy.provenance.artifacts[{index}].toolchain", identifier=True)
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        _fail("PROVENANCE_AUTHORITY_INVALID", "$.policy.provenance.artifacts", "provenance authority IDs must be unique and sorted")
    return records


def _artifact(item: Any, path: str, candidate: dict, manifest: dict, schema_set: dict, now: datetime, authority: dict[str, dict[str, Any]]) -> None:
    a = _object(item, path, _ARTIFACT)
    _string(a["artifact_id"], f"{path}.artifact_id", identifier=True)
    _string(a["component_id"], f"{path}.component_id", identifier=True)
    _digest(a["content_digest"], f"{path}.content_digest")
    _digest(a["source_digest"], f"{path}.source_digest")
    _digest(a["upstream_digest"], f"{path}.upstream_digest", required=False)
    _digest(a["fork_digest"], f"{path}.fork_digest", required=False)
    source_uri = _immutable_uri(a["source_uri"], f"{path}.source_uri", (a["source_digest"], a["content_digest"]))
    final_segment = urlsplit(source_uri).path.rsplit("/", 1)[-1]
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
        if n["version"] != vocabulary()["notice_version"]:
            _fail("UNSUPPORTED_RECORD_VERSION", f"{path}.copyright_notice[{index}].version", "unsupported NOTICE version")
        _string(n["id"], f"{path}.copyright_notice[{index}].id", identifier=True)
        _string(n["text"], f"{path}.copyright_notice[{index}].text")
        _digest(n["digest"], f"{path}.copyright_notice[{index}].digest")
        expected_notice = domain_digest("omarchy-notice/v1", {"id": n["id"], "text": n["text"]})
        if n["digest"] != expected_notice:
            _fail("DIGEST_MISMATCH", f"{path}.copyright_notice[{index}].digest", "NOTICE digest does not match its closed record")
    offer = a["source_offer"]
    if not isinstance(offer, dict):
        _fail("SOURCE_OFFER_MISSING", f"{path}.source_offer", "source-offer record is required")
    offer = _object(offer, f"{path}.source_offer", _OFFER)
    if offer["version"] != vocabulary()["source_offer_version"]:
        _fail("UNSUPPORTED_RECORD_VERSION", f"{path}.source_offer.version", "unsupported source-offer version")
    if offer["status"] not in vocabulary()["source_offer_status"] or offer["status"] != "offered":
        _fail("SOURCE_OFFER_MISSING", f"{path}.source_offer.status", "redistributed artifacts require offered source")
    offer_location = _immutable_uri(offer["location"], f"{path}.source_offer.location", (a["source_digest"], a["content_digest"]))
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
    if decision["version"] != vocabulary()["owner_decision_version"]:
        _fail("UNSUPPORTED_RECORD_VERSION", f"{path}.owner_decision.version", "unsupported owner-decision version")
    _string(decision["decision_id"], f"{path}.owner_decision.decision_id", identifier=True)
    _digest(decision["evidence_digest"], f"{path}.owner_decision.evidence_digest")
    decided = _timestamp(decision["decided_at"], f"{path}.owner_decision.decided_at")
    expires = _timestamp(decision["expires_at"], f"{path}.owner_decision.expires_at")
    if expires <= decided:
        _fail("OWNER_DECISION_MISSING", f"{path}.owner_decision", "decision evidence and valid interval are required")
    if expires <= now:
        _fail("OWNER_DECISION_EXPIRED", f"{path}.owner_decision.expires_at", "owner/legal decision is expired")
    if not isinstance(a["generated"], bool):
        _fail("INCOMPLETE_INVENTORY", f"{path}.generated", "generated must be boolean")
    provenance = a["build_provenance"]
    if not isinstance(provenance, dict):
        _fail("PROVENANCE_MISSING", f"{path}.build_provenance", "every artifact requires locked build provenance")
    provenance = _object(provenance, f"{path}.build_provenance", _PROVENANCE)
    if provenance["version"] != vocabulary()["provenance_version"]:
        _fail("UNSUPPORTED_RECORD_VERSION", f"{path}.build_provenance.version", "unsupported provenance version")
    _string(provenance["builder"], f"{path}.build_provenance.builder", identifier=True)
    _string(provenance["toolchain"], f"{path}.build_provenance.toolchain", identifier=True)
    for field in ("recipe_digest", "source_digest", "environment_digest", "toolchain_digest"):
        _digest(provenance[field], f"{path}.build_provenance.{field}")
    locked = authority.get(a["artifact_id"])
    if locked is None:
        _fail("PROVENANCE_AUTHORITY_MISSING", f"{path}.artifact_id", "artifact is absent from repository provenance authority")
    for field in ("builder", "toolchain", "recipe_digest", "source_digest", "environment_digest", "toolchain_digest"):
        if provenance[field] != locked[field]:
            _fail("PROVENANCE_LOCK_MISMATCH", f"{path}.build_provenance.{field}", "provenance differs from repository-owned authority")
    if a["generated"]:
        sbom = a["sbom_ref"]
        if not isinstance(sbom, dict):
            _fail("SBOM_MISSING", f"{path}.sbom_ref", "generated artifacts require an SBOM reference")
        sbom = _object(sbom, f"{path}.sbom_ref", _SBOM)
        if sbom["version"] != vocabulary()["sbom_version"]:
            _fail("UNSUPPORTED_RECORD_VERSION", f"{path}.sbom_ref.version", "unsupported SBOM version")
        if sbom["format"] not in vocabulary()["sbom_formats"]:
            _fail("UNKNOWN_SBOM_FORMAT", f"{path}.sbom_ref.format", "SBOM format is outside vocabulary")
        _digest(sbom["digest"], f"{path}.sbom_ref.digest")
        _immutable_uri(sbom["uri"], f"{path}.sbom_ref.uri", (sbom["digest"],))
    else:
        if a["sbom_ref"] is not None:
            _fail("INVALID_PROVENANCE", f"{path}.sbom_ref", "non-generated artifacts must use null SBOM")
    _check_ref(a["candidate_ref"], candidate, f"{path}.candidate_ref")
    _check_ref(a["manifest_ref"], manifest, f"{path}.manifest_ref")
    _check_ref(a["schema_set_ref"], schema_set, f"{path}.schema_set_ref")
    if a["fork_digest"] is None and a["upstream_digest"] is None:
        _fail("FORK_UPSTREAM_AMBIGUOUS", f"{path}.upstream_digest", "at least one explicit upstream/fork identity is required")
    if a["fork_digest"] is not None and a["upstream_digest"] is None:
        _fail("FORK_UPSTREAM_AMBIGUOUS", f"{path}.fork_digest", "a fork must name its upstream digest")
    if a["fork_digest"] is not None and a["artifact_class"] != "fork":
        _fail("FORK_UPSTREAM_AMBIGUOUS", f"{path}.fork_digest", "fork digest requires fork artifact class")
    if a["artifact_class"] == "fork" and a["fork_digest"] is None:
        _fail("FORK_UPSTREAM_AMBIGUOUS", f"{path}.fork_digest", "fork artifacts require fork digest")
    if a["artifact_class"] != "fork" and a["upstream_digest"] is None:
        _fail("FORK_UPSTREAM_AMBIGUOUS", f"{path}.upstream_digest", "non-fork artifacts require upstream identity")


def _utc_now() -> datetime:
    """Internal clock seam; production callers cannot supply a timestamp."""
    return _CLOCK()


def _set_test_clock(clock) -> None:
    """Private test-only clock adapter, intentionally not exposed by CLI."""
    global _CLOCK
    _CLOCK = clock


def validate(bundle: Any) -> dict[str, Any]:
    """Validate and return an accepted bundle using the internal UTC clock."""
    now = _utc_now()
    if not isinstance(now, datetime) or now.tzinfo is None:
        _fail("INVALID_TIMESTAMP", "$.now", "evaluation time must be timezone-aware")
    top = _object(bundle, "$", _TOP)
    if top["version"] != VERSION:
        _fail("UNSUPPORTED_VERSION", "$.version", "unsupported release-compliance version")
    policy = _object(top["policy"], "$.policy", ("version", "digest"))
    if policy["version"] != vocabulary()["version"]:
        _fail("UNSUPPORTED_POLICY", "$.policy.version", "unsupported policy version")
    _digest(policy["digest"], "$.policy.digest")
    expected_policy = domain_digest("omarchy-compliance-policy/v1", vocabulary())
    if policy["digest"] != expected_policy:
        _fail("POLICY_DIGEST_MISMATCH", "$.policy.digest", "policy digest does not match closed vocabulary")
    candidate, manifest, schema_set = (_target(top[key], f"$.{key}") for key in ("candidate", "manifest", "schema_set"))
    authority = {record["artifact_id"]: record for record in _provenance_lock()}
    artifacts = top["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        _fail("INCOMPLETE_INVENTORY", "$.artifacts", "at least one artifact is required")
    _sorted_unique(artifacts, "$.artifacts", "artifact_id")
    components = []
    for index, item in enumerate(artifacts):
        if not isinstance(item, dict):
            _fail("INCOMPLETE_INVENTORY", f"$.artifacts[{index}]", "artifact object required")
        components.append(item.get("component_id"))
        _artifact(item, f"$.artifacts[{index}]", candidate, manifest, schema_set, now, authority)
    if any(not isinstance(component, str) for component in components):
        _fail("INCOMPLETE_INVENTORY", "$.artifacts", "component IDs are required")
    if len(set(components)) != len(components):
        _fail("DUPLICATE_ID", "$.artifacts", "duplicate component_id")
    if components != sorted(components):
        _fail("UNSORTED_IDS", "$.artifacts", "component IDs must be sorted")
    if set(authority) != {item["artifact_id"] for item in artifacts}:
        _fail("PROVENANCE_AUTHORITY_INVALID", "$.policy.provenance", "authority and inventory artifact sets must match exactly")
    return bundle


def evaluate(bundle: Any) -> dict[str, Any]:
    """Return a closed allow/reject result without throwing for policy failures."""
    try:
        validate(bundle)
        policy_digest = bundle["policy"]["digest"]
        candidate, manifest, schema_set = (bundle[key] for key in ("candidate", "manifest", "schema_set"))
        inventory_digest = domain_digest("omarchy-release-inventory/v1", bundle["artifacts"])
        bundle_digest = domain_digest("omarchy-release-bundle/v1", bundle)
        valid_until = min(min(a["source_offer"]["expires_at"], a["owner_decision"]["expires_at"]) for a in bundle["artifacts"])
    except ComplianceError as error:
        return {"version": VERSION, "decision": "reject", "clock_trusted": False, **error.as_dict()}
    except Exception:
        return {"version": VERSION, "decision": "reject", "clock_trusted": False, "code": "VALIDATION_FAILURE", "path": "$", "detail": "input failed closed validation"}
    return {
        "version": VERSION, "decision": "allow", "code": "OK", "path": "$", "detail": "compliant", "clock_trusted": False, "valid_until": valid_until,
        "inventory_digest": inventory_digest, "policy_digest": policy_digest,
        "candidate_digest": candidate["digest"], "manifest_digest": manifest["digest"],
        "schema_set_digest": schema_set["digest"], "bundle_digest": bundle_digest,
    }


def attest(bundle: Any) -> bytes:
    """Project an accepted result into unsigned evidence bytes."""
    result = evaluate(bundle)
    if result["decision"] != "allow":
        raise ComplianceError(result["code"], result["path"], result.get("detail", "rejected"))
    projection = {
        "version": "f06-compliance-attestation/v1",
        "decision": "allow",
        "signed": False,
        "trusted": False,
        "promotable": False,
        "clock_trusted": False,
        "valid_until": result["valid_until"],
        "inventory_digest": result["inventory_digest"],
        "policy_digest": result["policy_digest"],
        "candidate_digest": result["candidate_digest"],
        "manifest_digest": result["manifest_digest"],
        "schema_set_digest": result["schema_set_digest"],
        "bundle_digest": result["bundle_digest"],
    }
    return canonical_bytes(projection)
