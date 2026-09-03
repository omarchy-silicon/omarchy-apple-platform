"""Closed F-05 candidate input/output models and authority seams."""

from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping, Protocol

from omarchy_platform.canonical import canonical_bytes
from omarchy_platform.strictjson import parse

from .errors import CandidateAssemblyError
from .generated import INPUT_VERSION, OUTPUT_VERSION, REQUIRED_GATE_IDS, VERSION

_DIGEST = "sha256:"


def digest_bytes(value: bytes) -> str:
    return _DIGEST + sha256(value).hexdigest()


def digest_value(domain: str, value: Any) -> str:
    return digest_bytes(domain.encode("ascii") + b"\0" + canonical_bytes(value))


def _fail(code: str, path: str, detail: str) -> None:
    raise CandidateAssemblyError(code, path, detail)


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(child) for child in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_thaw(child) for child in value]
    return value


def _closed(value: Any, fields: tuple[str, ...], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("TYPE_MISMATCH", path, "closed object required")
    unknown = sorted(set(value) - set(fields))
    missing = [key for key in fields if key not in value]
    if unknown:
        _fail("UNKNOWN_FIELD", f"{path}.{unknown[0]}", "field is not in the closed contract")
    if missing:
        _fail("MISSING_FIELD", f"{path}.{missing[0]}", "required field is absent")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        _fail("INVALID_STRING", path, "bounded non-empty string required")
    try:
        bounded = len(value.encode("utf-8")) <= 512
    except UnicodeError:
        bounded = False
    if not bounded:
        _fail("INVALID_STRING", path, "bounded UTF-8 string required")
    return value


def _digest(value: Any, path: str) -> str:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith(_DIGEST) or any(char not in "0123456789abcdef" for char in value[7:]):
        _fail("INVALID_DIGEST", path, "lowercase sha256 digest required")
    return value


def _sorted(values: list[str], path: str) -> tuple[str, ...]:
    if any(not isinstance(value, str) for value in values) or len(values) != len(set(values)):
        _fail("DUPLICATE_ID", path, "IDs must be unique")
    if values != sorted(values):
        _fail("UNSORTED_IDS", path, "IDs must be sorted")
    return tuple(values)


_CAPABILITY_TOKEN = object()


@dataclass(frozen=True, init=False)
class _AuthorityCapability:
    """Private result constructed by an F-03/F-06/Q-00/Q-01 adapter."""

    authority: str
    subject: str
    digest: str
    board_id: str
    profile_id: str
    channel: str
    expires_at: str
    replay_id: str
    metadata_digest: str
    schema_set_digest: str

    def __init__(self, authority: str, subject: str, digest: str, board_id: str, profile_id: str, channel: str, expires_at: str, replay_id: str, metadata_digest: str, schema_set_digest: str, *, _token: object | None = None):
        if _token is not _CAPABILITY_TOKEN:
            raise TypeError("authority capabilities are issued only by an adapter")
        for name, value in locals().copy().items():
            if name not in {"self", "_token"}:
                object.__setattr__(self, name, value)
        self.__post_init__()

    def __post_init__(self) -> None:
        _string(self.authority, "$.authority")
        _string(self.subject, "$.subject")
        _digest(self.digest, "$.digest")
        _digest(self.metadata_digest, "$.metadata_digest")
        _digest(self.schema_set_digest, "$.schema_set_digest")
        _string(self.board_id, "$.board_id")
        _string(self.profile_id, "$.profile_id")
        if self.channel not in {"edge", "rc", "stable"}:
            _fail("INVALID_TRUST_RECEIPT", "$.channel", "unknown channel")
        _string(self.expires_at, "$.expires_at")
        _string(self.replay_id, "$.replay_id")


class CandidateAuthority(Protocol):
    """Adapters verify exact canonical source bytes and return a private result."""

    def verify_canonical(self, kind: str, source_bytes: bytes, *, digest: str, board_id: str, profile_id: str, channel: str, schema_set_digest: str, verification_time: str, subject: str) -> _AuthorityCapability: ...


class ArtifactReader(Protocol):
    def read(self, digest: str) -> bytes: ...


@dataclass(frozen=True)
class CandidateAssemblyInput:
    candidate_id: str
    channel: str
    board_id: str
    profile_id: str
    firmware: dict[str, str]
    platform: dict[str, Any]
    intake: dict[str, str]
    qualification: dict[str, Any]
    package: dict[str, Any]
    compliance: dict[str, str]
    required_gates: tuple[dict[str, Any], ...]
    rollback: tuple[str, ...]
    source: dict[str, Any]

    FIELDS = ("version", "candidate_id", "channel", "board_id", "profile_id", "firmware", "platform", "intake", "qualification", "package", "compliance", "required_gates", "rollback", "source")

    @classmethod
    def from_dict(cls, value: Any) -> "CandidateAssemblyInput":
        try:
            value = deepcopy(value)
        except (TypeError, ValueError, UnicodeError):
            _fail("TYPE_MISMATCH", "$", "candidate value is not copyable")
        value = _closed(value, cls.FIELDS, "$")
        if value["version"] != INPUT_VERSION:
            _fail("UNSUPPORTED_VERSION", "$.version", f"{INPUT_VERSION} required")
        candidate_id = _string(value["candidate_id"], "$.candidate_id")
        channel = _string(value["channel"], "$.channel")
        if channel not in {"edge", "rc", "stable"}:
            _fail("UNKNOWN_CHANNEL", "$.channel", "channel is outside the closed vocabulary")
        board_id, profile_id = _string(value["board_id"], "$.board_id"), _string(value["profile_id"], "$.profile_id")
        firmware = _closed(value["firmware"], ("firmware_id", "version", "build_digest"), "$.firmware")
        for field in ("firmware_id",):
            _string(firmware[field], f"$.firmware.{field}")
        if not isinstance(firmware["version"], str) or not __import__("re").fullmatch(r"(?:0|[1-9][0-9]{0,4})\.(?:0|[1-9][0-9]{0,4})\.(?:0|[1-9][0-9]{0,4})", firmware["version"]):
            _fail("INVALID_FIRMWARE_VERSION", "$.firmware.version", "F-02-compatible semantic version required")
        _digest(firmware["build_digest"], "$.firmware.build_digest")
        platform = _closed(value["platform"], ("manifest_id", "manifest_digest", "schema_set_digest", "tuple_id", "abi_version", "artifact_ids"), "$.platform")
        for field in ("manifest_id", "tuple_id", "abi_version"):
            _string(platform[field], f"$.platform.{field}")
        for field in ("manifest_digest", "schema_set_digest"):
            _digest(platform[field], f"$.platform.{field}")
        _sorted(platform["artifact_ids"], "$.platform.artifact_ids")
        intake = _closed(value["intake"], ("dataset_digest", "record_id", "record_digest"), "$.intake")
        _digest(intake["dataset_digest"], "$.intake.dataset_digest"); _string(intake["record_id"], "$.intake.record_id"); _digest(intake["record_digest"], "$.intake.record_digest")
        qualification = _closed(value["qualification"], ("inventory_digest", "record_id", "record_digest", "outcome", "admission"), "$.qualification")
        _digest(qualification["inventory_digest"], "$.qualification.inventory_digest"); _string(qualification["record_id"], "$.qualification.record_id"); _digest(qualification["record_digest"], "$.qualification.record_digest")
        if qualification["outcome"] != "FULL" or qualification["admission"] != "QUALIFIED":
            _fail("QUALIFICATION_REQUIRED", "$.qualification", "only FULL/QUALIFIED records can enter a candidate")
        package = _closed(value["package"], ("release_id", "index_digest", "artifact_set_digest", "schema_set_digest", "tuple_id", "abi_version", "index", "artifacts", "rollback_artifact_digests"), "$.package")
        for field in ("release_id", "tuple_id", "abi_version"):
            _string(package[field], f"$.package.{field}")
        for field in ("index_digest", "artifact_set_digest", "schema_set_digest"):
            _digest(package[field], f"$.package.{field}")
        if package["schema_set_digest"] != platform["schema_set_digest"]:
            _fail("SCHEMA_SET_MISMATCH", "$.package.schema_set_digest", "package and platform schema sets differ")
        if package["tuple_id"] != platform["tuple_id"] or package["abi_version"] != platform["abi_version"]:
            _fail("TUPLE_ABI_MISMATCH", "$.package", "package tuple and ABI differ from platform manifest")
        artifacts = package["artifacts"]
        if not isinstance(artifacts, list) or not artifacts:
            _fail("MISSING_ARTIFACT", "$.package.artifacts", "at least one package artifact is required")
        checked_artifacts = []
        for index, item in enumerate(artifacts):
            path = f"$.package.artifacts[{index}]"
            item = _closed(item, ("artifact_id", "component_id", "content_digest", "sbom_digest", "provenance_digest"), path)
            for field in ("artifact_id", "component_id"):
                _string(item[field], f"{path}.{field}")
            for field in ("content_digest", "sbom_digest", "provenance_digest"):
                _digest(item[field], f"{path}.{field}")
            checked_artifacts.append(item)
        ids = _sorted([item["artifact_id"] for item in checked_artifacts], "$.package.artifacts")
        _sorted([item["component_id"] for item in checked_artifacts], "$.package.component_ids")
        if tuple(platform["artifact_ids"]) != ids:
            _fail("ARTIFACT_SET_MISMATCH", "$.package.artifacts", "platform artifact set differs from package artifact set")
        rollback = _sorted(package["rollback_artifact_digests"], "$.package.rollback_artifact_digests")
        if not rollback:
            _fail("ROLLBACK_SET_MISSING", "$.package.rollback_artifact_digests", "rollback set is required")
        compliance = _closed(value["compliance"], ("attestation_digest", "decision"), "$.compliance")
        _digest(compliance["attestation_digest"], "$.compliance.attestation_digest")
        if compliance["decision"] != "allow":
            _fail("COMPLIANCE_DENIED", "$.compliance.decision", "compliance must explicitly allow")
        gates = value["required_gates"]
        if not isinstance(gates, list):
            _fail("GATE_CENSUS_INVALID", "$.required_gates", "gate census must be an array")
        gate_rows = []
        for index, gate in enumerate(gates):
            path = f"$.required_gates[{index}]"
            gate = _closed(gate, ("gate_id", "status", "evidence_digest"), path)
            _string(gate["gate_id"], f"{path}.gate_id"); _digest(gate["evidence_digest"], f"{path}.evidence_digest")
            if gate["status"] != "pass":
                _fail("GATE_NOT_PASSED", f"{path}.status", "required gates cannot be warning-success")
            gate_rows.append(gate)
        gate_ids = [row["gate_id"] for row in gate_rows]
        if len(gate_ids) != len(set(gate_ids)):
            _fail("DUPLICATE_ID", "$.required_gates", "gate IDs must be unique")
        if tuple(row["gate_id"] for row in gate_rows) != REQUIRED_GATE_IDS:
            missing = sorted(set(REQUIRED_GATE_IDS) - {row["gate_id"] for row in gate_rows})
            extra = sorted({row["gate_id"] for row in gate_rows} - set(REQUIRED_GATE_IDS))
            if missing:
                _fail("GATE_MISSING", "$.required_gates", missing[0])
            if extra:
                _fail("GATE_EXTRA", "$.required_gates", extra[0])
            _fail("GATE_CENSUS_INVALID", "$.required_gates", "gate IDs must be ordered exactly")
        source = _closed(value["source"], ("commit", "tool_versions"), "$.source")
        _string(source["commit"], "$.source.commit")
        if len(source["commit"]) != 40 or any(char not in "0123456789abcdef" for char in source["commit"]):
            _fail("MUTABLE_SOURCE", "$.source.commit", "exact lowercase source commit required")
        versions = source["tool_versions"]
        if not isinstance(versions, dict) or not versions:
            _fail("TOOL_VERSION_MISSING", "$.source.tool_versions", "tool versions are required")
        if list(versions) != sorted(versions) or len(versions) != len(set(versions)):
            _fail("UNSORTED_IDS", "$.source.tool_versions", "tool version keys must be unique and sorted")
        for key, version in versions.items():
            _string(key, "$.source.tool_versions"); _string(version, f"$.source.tool_versions.{key}")
        return cls(candidate_id, channel, board_id, profile_id, firmware, platform, intake, qualification, package, compliance, tuple(gate_rows), rollback, source)

    def body(self) -> dict[str, Any]:
        return {"version": INPUT_VERSION, "candidate_id": self.candidate_id, "channel": self.channel, "board_id": self.board_id, "profile_id": self.profile_id, "firmware": self.firmware, "platform": self.platform, "intake": self.intake, "qualification": self.qualification, "package": self.package, "compliance": self.compliance, "required_gates": list(self.required_gates), "rollback": list(self.rollback), "source": self.source}


_MANIFEST_TOKEN = object()


@dataclass(frozen=True, init=False)
class CandidateManifest:
    body_value: Mapping[str, Any]
    candidate_digest: str

    def __init__(self, body_value: Mapping[str, Any], candidate_digest: str, *, _token: object | None = None):
        if _token is not _MANIFEST_TOKEN:
            raise TypeError("use assemble_candidate() or from_dict() to construct a candidate manifest")
        object.__setattr__(self, "body_value", _freeze(dict(body_value)))
        object.__setattr__(self, "candidate_digest", candidate_digest)

    def _unchecked_dict(self) -> dict[str, Any]:
        return {**_thaw(self.body_value), "candidate_digest": self.candidate_digest}

    def to_dict(self) -> dict[str, Any]:
        checked = type(self).from_dict(self._unchecked_dict())
        return checked._unchecked_dict()

    def bytes(self) -> bytes:
        checked = type(self).from_dict(self._unchecked_dict())
        return canonical_bytes(checked._unchecked_dict())

    @classmethod
    def from_dict(cls, value: Any) -> "CandidateManifest":
        value = _closed(value, CandidateAssemblyInput.FIELDS + ("candidate_digest",), "$")
        if value["version"] != __import__("omarchy_candidate.generated", fromlist=["OUTPUT_VERSION"]).OUTPUT_VERSION:
            _fail("UNSUPPORTED_VERSION", "$.version", "candidate-manifest/v1 required")
        candidate_digest = _digest(value["candidate_digest"], "$.candidate_digest")
        data = dict(value); data.pop("candidate_digest"); data["version"] = INPUT_VERSION
        checked = CandidateAssemblyInput.from_dict(data)
        expected = digest_value("omarchy-candidate-manifest/v1", {**checked.body(), "version": OUTPUT_VERSION})
        if expected != candidate_digest:
            _fail("DIGEST_MISMATCH", "$.candidate_digest", "candidate manifest digest does not match canonical body")
        return cls({**checked.body(), "version": OUTPUT_VERSION}, candidate_digest, _token=_MANIFEST_TOKEN)
    def validate_state(self, platform_bytes: bytes, intake_bytes: bytes, qualification_bytes: bytes, *, board_id: str, profile_id: str, verification_time: str) -> None: ...
