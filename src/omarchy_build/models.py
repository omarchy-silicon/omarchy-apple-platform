"""Closed immutable F-04 records and their canonical JSON projections."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .errors import BuildProvenanceError
from .util import (
    ARTIFACT_ID_RE,
    BUILDER_ID_RE,
    DIGEST_RE,
    INPUT_ID_RE,
    ID_RE,
    MAX_OUTPUT_BYTES,
    RECIPE_ID_RE,
    canonical_bytes,
    digest_bytes,
    digest_value,
    expect_digest,
    expect_enum,
    expect_list,
    expect_object,
    expect_string,
    immutable_https_uri,
    safe_relative_path,
    sorted_unique,
)

CHANNELS = {"edge", "rc", "stable"}
HIGH_TRUST_CLASSES = {
    "bootloader",
    "kernel",
    "firmware",
    "device-tree",
    "mesa",
    "userspace-package",
    "release-index",
}
MEDIA_TYPES = {"application/octet-stream", "application/x-tar", "application/gzip", "application/json"}


def _tuple_dicts(values: list[dict[str, Any]], path: str) -> tuple[dict[str, Any], ...]:
    return tuple(dict(value) for value in values)


def _verify_digest(value: Mapping[str, Any], without: str, domain: str, path: str) -> str:
    supplied = expect_digest(value[without], f"{path}.{without}")
    body = {key: child for key, child in value.items() if key != without}
    expected = digest_value(domain, body)
    if supplied != expected:
        raise BuildProvenanceError("DIGEST_MISMATCH", f"{path}.{without}", "record digest does not match canonical content")
    return supplied


@dataclass(frozen=True)
class InputRef:
    input_id: str
    kind: str
    uri: str
    commit: str
    digest: str
    media_type: str
    relative_path: str

    KEYS = ("input_id", "kind", "uri", "commit", "digest", "media_type", "relative_path")

    @classmethod
    def from_dict(cls, value: Any, path: str = "$") -> "InputRef":
        value = expect_object(value, cls.KEYS, path)
        input_id = expect_string(value["input_id"], f"{path}.input_id", pattern=INPUT_ID_RE)
        kind = expect_enum(value["kind"], f"{path}.kind", {"source", "toolchain", "recipe", "generated", "opaque-boot-envelope"})
        uri = immutable_https_uri(value["uri"], f"{path}.uri")
        commit = expect_string(value["commit"], f"{path}.commit")
        if len(commit) < 7 or any(character not in "0123456789abcdef" for character in commit):
            raise BuildProvenanceError("MUTABLE_INPUT", f"{path}.commit", "exact lowercase commit required")
        digest = expect_digest(value["digest"], f"{path}.digest")
        media_type = expect_enum(value["media_type"], f"{path}.media_type", MEDIA_TYPES)
        relative_path = safe_relative_path(value["relative_path"], f"{path}.relative_path")
        return cls(input_id, kind, uri, commit, digest, media_type, relative_path)

    def to_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.KEYS}


@dataclass(frozen=True)
class SourceClosure:
    recipe_id: str
    recipe_digest: str
    inputs: tuple[InputRef, ...]
    closure_digest: str

    KEYS = ("version", "recipe_id", "recipe_digest", "inputs", "closure_digest")

    @classmethod
    def from_dict(cls, value: Any, path: str = "$") -> "SourceClosure":
        value = expect_object(value, cls.KEYS, path)
        if value["version"] != "source-lock/v1":
            raise BuildProvenanceError("UNSUPPORTED_VERSION", f"{path}.version", "source-lock/v1 required")
        recipe_id = expect_string(value["recipe_id"], f"{path}.recipe_id", pattern=RECIPE_ID_RE)
        recipe_digest = expect_digest(value["recipe_digest"], f"{path}.recipe_digest")
        raw_inputs = expect_list(value["inputs"], f"{path}.inputs", nonempty=True)
        inputs = tuple(InputRef.from_dict(item, f"{path}.inputs[{index}]") for index, item in enumerate(raw_inputs))
        sorted_unique([item.input_id for item in inputs], f"{path}.inputs")
        closure_digest = _verify_digest(value, "closure_digest", "omarchy-source-closure/v1", path)
        return cls(recipe_id, recipe_digest, inputs, closure_digest)

    def body(self) -> dict[str, Any]:
        return {"version": "source-lock/v1", "recipe_id": self.recipe_id, "recipe_digest": self.recipe_digest, "inputs": [item.to_dict() for item in self.inputs]}

    def to_dict(self) -> dict[str, Any]:
        return {**self.body(), "closure_digest": self.closure_digest}

    @classmethod
    def create(cls, recipe_id: str, recipe_digest: str, inputs: tuple[InputRef, ...]) -> "SourceClosure":
        body = {"version": "source-lock/v1", "recipe_id": recipe_id, "recipe_digest": recipe_digest, "inputs": [item.to_dict() for item in inputs]}
        return cls(recipe_id, recipe_digest, inputs, digest_value("omarchy-source-closure/v1", body))


@dataclass(frozen=True)
class BuilderDefinition:
    builder_id: str
    backend: str
    architecture: str
    image_digest: str
    toolchain_digest: str
    environment_digest: str
    network_policy: str
    root_policy: str
    high_trust_classes: tuple[str, ...]
    definition_digest: str

    KEYS = ("version", "builder_id", "backend", "architecture", "image_digest", "toolchain_digest", "environment_digest", "network_policy", "root_policy", "high_trust_classes", "definition_digest")

    @classmethod
    def from_dict(cls, value: Any, path: str = "$") -> "BuilderDefinition":
        value = expect_object(value, cls.KEYS, path)
        if value["version"] != "builder-definition/v1":
            raise BuildProvenanceError("UNSUPPORTED_VERSION", f"{path}.version", "builder-definition/v1 required")
        builder_id = expect_string(value["builder_id"], f"{path}.builder_id", pattern=BUILDER_ID_RE)
        backend = expect_enum(value["backend"], f"{path}.backend", {"fixture-subprocess/v1"})
        architecture = expect_enum(value["architecture"], f"{path}.architecture", {"aarch64", "x86_64"})
        image_digest = expect_digest(value["image_digest"], f"{path}.image_digest")
        toolchain_digest = expect_digest(value["toolchain_digest"], f"{path}.toolchain_digest")
        environment_digest = expect_digest(value["environment_digest"], f"{path}.environment_digest")
        if value["network_policy"] != "denied":
            raise BuildProvenanceError("NETWORK_POLICY_REJECTED", f"{path}.network_policy", "network must be denied")
        if value["root_policy"] != "isolated-temp-root":
            raise BuildProvenanceError("ROOT_POLICY_REJECTED", f"{path}.root_policy", "isolated temporary root required")
        classes = tuple(expect_string(item, f"{path}.high_trust_classes[{index}]") for index, item in enumerate(expect_list(value["high_trust_classes"], f"{path}.high_trust_classes")))
        if any(item not in HIGH_TRUST_CLASSES for item in classes):
            raise BuildProvenanceError("UNKNOWN_ENUM", f"{path}.high_trust_classes", "unknown high-trust class")
        sorted_unique(classes, f"{path}.high_trust_classes")
        definition_digest = _verify_digest(value, "definition_digest", "omarchy-builder-definition/v1", path)
        return cls(builder_id, backend, architecture, image_digest, toolchain_digest, environment_digest, "denied", "isolated-temp-root", classes, definition_digest)

    def body(self) -> dict[str, Any]:
        return {"version": "builder-definition/v1", "builder_id": self.builder_id, "backend": self.backend, "architecture": self.architecture, "image_digest": self.image_digest, "toolchain_digest": self.toolchain_digest, "environment_digest": self.environment_digest, "network_policy": self.network_policy, "root_policy": self.root_policy, "high_trust_classes": list(self.high_trust_classes)}

    def to_dict(self) -> dict[str, Any]:
        return {**self.body(), "definition_digest": self.definition_digest}

    @classmethod
    def create(cls, builder_id: str, image_digest: str, toolchain_digest: str, environment_digest: str, *, architecture: str = "aarch64", high_trust_classes: tuple[str, ...] = tuple(sorted(HIGH_TRUST_CLASSES))) -> "BuilderDefinition":
        body = {"version": "builder-definition/v1", "builder_id": builder_id, "backend": "fixture-subprocess/v1", "architecture": architecture, "image_digest": image_digest, "toolchain_digest": toolchain_digest, "environment_digest": environment_digest, "network_policy": "denied", "root_policy": "isolated-temp-root", "high_trust_classes": list(high_trust_classes)}
        return cls(builder_id, "fixture-subprocess/v1", architecture, image_digest, toolchain_digest, environment_digest, "denied", "isolated-temp-root", high_trust_classes, digest_value("omarchy-builder-definition/v1", body))


@dataclass(frozen=True)
class Recipe:
    recipe_id: str
    input_ids: tuple[str, ...]
    read_paths: tuple[str, ...]
    output_path: str
    output_media_type: str
    prefix: str
    recipe_digest: str

    KEYS = ("version", "recipe_id", "input_ids", "read_paths", "output_path", "output_media_type", "prefix", "recipe_digest")

    @classmethod
    def from_dict(cls, value: Any, path: str = "$") -> "Recipe":
        value = expect_object(value, cls.KEYS, path)
        if value["version"] != "fixture-recipe/v1":
            raise BuildProvenanceError("UNSUPPORTED_VERSION", f"{path}.version", "fixture-recipe/v1 required")
        recipe_id = expect_string(value["recipe_id"], f"{path}.recipe_id", pattern=RECIPE_ID_RE)
        input_ids = sorted_unique([expect_string(item, f"{path}.input_ids[{index}]", pattern=INPUT_ID_RE) for index, item in enumerate(expect_list(value["input_ids"], f"{path}.input_ids", nonempty=True))], f"{path}.input_ids")
        read_paths = tuple(safe_relative_path(item, f"{path}.read_paths[{index}]") for index, item in enumerate(expect_list(value["read_paths"], f"{path}.read_paths", nonempty=True)))
        if len(set(read_paths)) != len(read_paths):
            raise BuildProvenanceError("DUPLICATE_SEMANTIC_KEY", f"{path}.read_paths", "read paths must be unique")
        output_path = safe_relative_path(value["output_path"], f"{path}.output_path")
        output_media_type = expect_enum(value["output_media_type"], f"{path}.output_media_type", MEDIA_TYPES)
        prefix = expect_string(value["prefix"], f"{path}.prefix")
        recipe_digest = _verify_digest(value, "recipe_digest", "omarchy-fixture-recipe/v1", path)
        return cls(recipe_id, input_ids, read_paths, output_path, output_media_type, prefix, recipe_digest)

    def body(self) -> dict[str, Any]:
        return {"version": "fixture-recipe/v1", "recipe_id": self.recipe_id, "input_ids": list(self.input_ids), "read_paths": list(self.read_paths), "output_path": self.output_path, "output_media_type": self.output_media_type, "prefix": self.prefix}

    def to_dict(self) -> dict[str, Any]:
        return {**self.body(), "recipe_digest": self.recipe_digest}

    @classmethod
    def create(cls, recipe_id: str, input_ids: tuple[str, ...], read_paths: tuple[str, ...], output_path: str = "dist/artifact.bin", output_media_type: str = "application/octet-stream", prefix: str = "omarchy-fixture/v1") -> "Recipe":
        body = {"version": "fixture-recipe/v1", "recipe_id": recipe_id, "input_ids": list(input_ids), "read_paths": list(read_paths), "output_path": output_path, "output_media_type": output_media_type, "prefix": prefix}
        return cls(recipe_id, input_ids, read_paths, output_path, output_media_type, prefix, digest_value("omarchy-fixture-recipe/v1", body))


@dataclass(frozen=True)
class OutputRecord:
    path: str
    media_type: str
    byte_count: int
    content_digest: str

    KEYS = ("path", "media_type", "byte_count", "content_digest")

    @classmethod
    def from_dict(cls, value: Any, path: str = "$") -> "OutputRecord":
        value = expect_object(value, cls.KEYS, path)
        output_path = safe_relative_path(value["path"], f"{path}.path")
        media_type = expect_enum(value["media_type"], f"{path}.media_type", MEDIA_TYPES)
        count = value["byte_count"]
        if not isinstance(count, int) or isinstance(count, bool) or count < 0 or count > MAX_OUTPUT_BYTES:
            raise BuildProvenanceError("INVALID_NUMBER", f"{path}.byte_count", "bounded non-negative byte count required")
        digest = expect_digest(value["content_digest"], f"{path}.content_digest")
        return cls(output_path, media_type, count, digest)

    def to_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.KEYS}


def artifact_set_digest(outputs: tuple[OutputRecord, ...]) -> str:
    return digest_value("omarchy-artifact-set/v1", [item.to_dict() for item in outputs])


@dataclass(frozen=True)
class BuildResult:
    builder_id: str
    builder_definition_digest: str
    recipe_id: str
    recipe_digest: str
    source_closure_digest: str
    toolchain_digest: str
    environment_digest: str
    outputs: tuple[OutputRecord, ...]
    artifact_set_digest: str
    provenance_digest: str
    sbom_digest: str
    result_digest: str
    output_bytes: Mapping[str, bytes] = field(default_factory=dict, compare=False, repr=False)

    KEYS = ("version", "builder_id", "builder_definition_digest", "recipe_id", "recipe_digest", "source_closure_digest", "toolchain_digest", "environment_digest", "outputs", "artifact_set_digest", "provenance_digest", "sbom_digest", "result_digest")

    @classmethod
    def from_dict(cls, value: Any, path: str = "$") -> "BuildResult":
        value = expect_object(value, cls.KEYS, path)
        if value["version"] != "build-result/v1":
            raise BuildProvenanceError("UNSUPPORTED_VERSION", f"{path}.version", "build-result/v1 required")
        builder_id = expect_string(value["builder_id"], f"{path}.builder_id", pattern=BUILDER_ID_RE)
        builder_definition_digest = expect_digest(value["builder_definition_digest"], f"{path}.builder_definition_digest")
        recipe_id = expect_string(value["recipe_id"], f"{path}.recipe_id", pattern=RECIPE_ID_RE)
        recipe_digest = expect_digest(value["recipe_digest"], f"{path}.recipe_digest")
        source_closure_digest = expect_digest(value["source_closure_digest"], f"{path}.source_closure_digest")
        toolchain_digest = expect_digest(value["toolchain_digest"], f"{path}.toolchain_digest")
        environment_digest = expect_digest(value["environment_digest"], f"{path}.environment_digest")
        raw_outputs = expect_list(value["outputs"], f"{path}.outputs", nonempty=True)
        outputs = tuple(OutputRecord.from_dict(item, f"{path}.outputs[{index}]") for index, item in enumerate(raw_outputs))
        if [item.path for item in outputs] != sorted(item.path for item in outputs) or len({item.path for item in outputs}) != len(outputs):
            raise BuildProvenanceError("UNSORTED_IDS", f"{path}.outputs", "output paths must be unique and sorted")
        artifact_digest = expect_digest(value["artifact_set_digest"], f"{path}.artifact_set_digest")
        if artifact_digest != artifact_set_digest(outputs):
            raise BuildProvenanceError("DIGEST_MISMATCH", f"{path}.artifact_set_digest", "output set digest mismatch")
        provenance_digest = expect_digest(value["provenance_digest"], f"{path}.provenance_digest")
        sbom_digest = expect_digest(value["sbom_digest"], f"{path}.sbom_digest")
        result_digest = _verify_digest(value, "result_digest", "omarchy-build-result/v1", path)
        return cls(builder_id, builder_definition_digest, recipe_id, recipe_digest, source_closure_digest, toolchain_digest, environment_digest, outputs, artifact_digest, provenance_digest, sbom_digest, result_digest)

    def body(self) -> dict[str, Any]:
        return {"version": "build-result/v1", "builder_id": self.builder_id, "builder_definition_digest": self.builder_definition_digest, "recipe_id": self.recipe_id, "recipe_digest": self.recipe_digest, "source_closure_digest": self.source_closure_digest, "toolchain_digest": self.toolchain_digest, "environment_digest": self.environment_digest, "outputs": [item.to_dict() for item in self.outputs], "artifact_set_digest": self.artifact_set_digest, "provenance_digest": self.provenance_digest, "sbom_digest": self.sbom_digest}

    def to_dict(self) -> dict[str, Any]:
        return {**self.body(), "result_digest": self.result_digest}

    @classmethod
    def create(cls, *, builder_id: str, builder_definition_digest: str, recipe_id: str, recipe_digest: str, source_closure_digest: str, toolchain_digest: str, environment_digest: str, outputs: tuple[OutputRecord, ...], provenance_digest: str, sbom_digest: str, output_bytes: Mapping[str, bytes] | None = None) -> "BuildResult":
        artifact_digest = artifact_set_digest(outputs)
        body = {"version": "build-result/v1", "builder_id": builder_id, "builder_definition_digest": builder_definition_digest, "recipe_id": recipe_id, "recipe_digest": recipe_digest, "source_closure_digest": source_closure_digest, "toolchain_digest": toolchain_digest, "environment_digest": environment_digest, "outputs": [item.to_dict() for item in outputs], "artifact_set_digest": artifact_digest, "provenance_digest": provenance_digest, "sbom_digest": sbom_digest}
        return cls(builder_id, builder_definition_digest, recipe_id, recipe_digest, source_closure_digest, toolchain_digest, environment_digest, outputs, artifact_digest, provenance_digest, sbom_digest, digest_value("omarchy-build-result/v1", body), output_bytes or {})


@dataclass(frozen=True)
class SbomEntry:
    output_path: str
    component_id: str
    version: str
    digest: str
    dependencies: tuple[str, ...]
    notice_ref: str

    KEYS = ("output_path", "component_id", "version", "digest", "dependencies", "notice_ref")

    @classmethod
    def from_dict(cls, value: Any, path: str = "$") -> "SbomEntry":
        value = expect_object(value, cls.KEYS, path)
        output_path = safe_relative_path(value["output_path"], f"{path}.output_path")
        component_id = expect_string(value["component_id"], f"{path}.component_id", pattern=ARTIFACT_ID_RE)
        version = expect_string(value["version"], f"{path}.version")
        digest = expect_digest(value["digest"], f"{path}.digest")
        dependencies = sorted_unique([expect_string(item, f"{path}.dependencies[{index}]") for index, item in enumerate(expect_list(value["dependencies"], f"{path}.dependencies"))], f"{path}.dependencies")
        notice_ref = expect_digest(value["notice_ref"], f"{path}.notice_ref")
        return cls(output_path, component_id, version, digest, dependencies, notice_ref)

    def to_dict(self) -> dict[str, Any]:
        return {"output_path": self.output_path, "component_id": self.component_id, "version": self.version, "digest": self.digest, "dependencies": list(self.dependencies), "notice_ref": self.notice_ref}


@dataclass(frozen=True)
class Sbom:
    artifact_set_digest: str
    entries: tuple[SbomEntry, ...]
    sbom_digest: str

    KEYS = ("version", "artifact_set_digest", "entries", "sbom_digest")

    @classmethod
    def from_dict(cls, value: Any, path: str = "$") -> "Sbom":
        value = expect_object(value, cls.KEYS, path)
        if value["version"] != "sbom/v1":
            raise BuildProvenanceError("UNSUPPORTED_VERSION", f"{path}.version", "sbom/v1 required")
        artifact_digest = expect_digest(value["artifact_set_digest"], f"{path}.artifact_set_digest")
        entries = tuple(SbomEntry.from_dict(item, f"{path}.entries[{index}]") for index, item in enumerate(expect_list(value["entries"], f"{path}.entries", nonempty=True)))
        if [item.output_path for item in entries] != sorted(item.output_path for item in entries) or len({item.output_path for item in entries}) != len(entries):
            raise BuildProvenanceError("UNSORTED_IDS", f"{path}.entries", "SBOM output paths must be unique and sorted")
        sbom_digest = _verify_digest(value, "sbom_digest", "omarchy-sbom/v1", path)
        return cls(artifact_digest, entries, sbom_digest)

    def body(self) -> dict[str, Any]:
        return {"version": "sbom/v1", "artifact_set_digest": self.artifact_set_digest, "entries": [item.to_dict() for item in self.entries]}

    def to_dict(self) -> dict[str, Any]:
        return {**self.body(), "sbom_digest": self.sbom_digest}

    @classmethod
    def create(cls, artifact_set_digest_value: str, entries: tuple[SbomEntry, ...]) -> "Sbom":
        body = {"version": "sbom/v1", "artifact_set_digest": artifact_set_digest_value, "entries": [item.to_dict() for item in entries]}
        return cls(artifact_set_digest_value, entries, digest_value("omarchy-sbom/v1", body))


@dataclass(frozen=True)
class Provenance:
    builder_id: str
    builder_definition_digest: str
    recipe_digest: str
    source_closure_digest: str
    toolchain_digest: str
    environment_digest: str
    artifact_set_digest: str
    input_digests: tuple[str, ...]
    sbom_digest: str
    log_digest: str
    provenance_digest: str

    KEYS = ("version", "builder_id", "builder_definition_digest", "recipe_digest", "source_closure_digest", "toolchain_digest", "environment_digest", "artifact_set_digest", "input_digests", "sbom_digest", "log_digest", "provenance_digest")

    @classmethod
    def from_dict(cls, value: Any, path: str = "$") -> "Provenance":
        value = expect_object(value, cls.KEYS, path)
        if value["version"] != "build-provenance/v1":
            raise BuildProvenanceError("UNSUPPORTED_VERSION", f"{path}.version", "build-provenance/v1 required")
        builder_id = expect_string(value["builder_id"], f"{path}.builder_id", pattern=BUILDER_ID_RE)
        builder_definition_digest = expect_digest(value["builder_definition_digest"], f"{path}.builder_definition_digest")
        recipe_digest = expect_digest(value["recipe_digest"], f"{path}.recipe_digest")
        source_closure_digest = expect_digest(value["source_closure_digest"], f"{path}.source_closure_digest")
        toolchain_digest = expect_digest(value["toolchain_digest"], f"{path}.toolchain_digest")
        environment_digest = expect_digest(value["environment_digest"], f"{path}.environment_digest")
        artifact_digest = expect_digest(value["artifact_set_digest"], f"{path}.artifact_set_digest")
        input_digests = sorted_unique([expect_digest(item, f"{path}.input_digests[{index}]") for index, item in enumerate(expect_list(value["input_digests"], f"{path}.input_digests", nonempty=True))], f"{path}.input_digests")
        sbom_digest = expect_digest(value["sbom_digest"], f"{path}.sbom_digest")
        log_digest = expect_digest(value["log_digest"], f"{path}.log_digest")
        provenance_digest = _verify_digest(value, "provenance_digest", "omarchy-build-provenance/v1", path)
        return cls(builder_id, builder_definition_digest, recipe_digest, source_closure_digest, toolchain_digest, environment_digest, artifact_digest, input_digests, sbom_digest, log_digest, provenance_digest)

    def body(self) -> dict[str, Any]:
        return {"version": "build-provenance/v1", "builder_id": self.builder_id, "builder_definition_digest": self.builder_definition_digest, "recipe_digest": self.recipe_digest, "source_closure_digest": self.source_closure_digest, "toolchain_digest": self.toolchain_digest, "environment_digest": self.environment_digest, "artifact_set_digest": self.artifact_set_digest, "input_digests": list(self.input_digests), "sbom_digest": self.sbom_digest, "log_digest": self.log_digest}

    def to_dict(self) -> dict[str, Any]:
        return {**self.body(), "provenance_digest": self.provenance_digest}

    @classmethod
    def create(cls, *, builder_id: str, builder_definition_digest: str, recipe_digest: str, source_closure_digest: str, toolchain_digest: str, environment_digest: str, artifact_set_digest_value: str, input_digests: tuple[str, ...], sbom_digest: str, log_digest: str) -> "Provenance":
        body = {"version": "build-provenance/v1", "builder_id": builder_id, "builder_definition_digest": builder_definition_digest, "recipe_digest": recipe_digest, "source_closure_digest": source_closure_digest, "toolchain_digest": toolchain_digest, "environment_digest": environment_digest, "artifact_set_digest": artifact_set_digest_value, "input_digests": list(input_digests), "sbom_digest": sbom_digest, "log_digest": log_digest}
        return cls(builder_id, builder_definition_digest, recipe_digest, source_closure_digest, toolchain_digest, environment_digest, artifact_set_digest_value, input_digests, sbom_digest, log_digest, digest_value("omarchy-build-provenance/v1", body))


@dataclass(frozen=True)
class PackageArtifact:
    artifact_id: str
    artifact_class: str
    content_digest: str
    build_result_digests: tuple[str, ...]
    provenance_digest: str
    sbom_digest: str

    KEYS = ("artifact_id", "artifact_class", "content_digest", "build_result_digests", "provenance_digest", "sbom_digest")

    @classmethod
    def from_dict(cls, value: Any, path: str = "$") -> "PackageArtifact":
        value = expect_object(value, cls.KEYS, path)
        artifact_id = expect_string(value["artifact_id"], f"{path}.artifact_id", pattern=ARTIFACT_ID_RE)
        artifact_class = expect_enum(value["artifact_class"], f"{path}.artifact_class", HIGH_TRUST_CLASSES)
        content_digest = expect_digest(value["content_digest"], f"{path}.content_digest")
        result_digests = sorted_unique([expect_digest(item, f"{path}.build_result_digests[{index}]") for index, item in enumerate(expect_list(value["build_result_digests"], f"{path}.build_result_digests", nonempty=True))], f"{path}.build_result_digests")
        if len(result_digests) < 2:
            raise BuildProvenanceError("INDEPENDENT_COMPARISON_REQUIRED", f"{path}.build_result_digests", "high-trust package artifacts need two builder results")
        provenance_digest = expect_digest(value["provenance_digest"], f"{path}.provenance_digest")
        sbom_digest = expect_digest(value["sbom_digest"], f"{path}.sbom_digest")
        return cls(artifact_id, artifact_class, content_digest, result_digests, provenance_digest, sbom_digest)

    def to_dict(self) -> dict[str, Any]:
        return {"artifact_id": self.artifact_id, "artifact_class": self.artifact_class, "content_digest": self.content_digest, "build_result_digests": list(self.build_result_digests), "provenance_digest": self.provenance_digest, "sbom_digest": self.sbom_digest}


@dataclass(frozen=True)
class PackageIndex:
    release_id: str
    channel: str
    platform_manifest_id: str
    platform_manifest_digest: str
    schema_set_digest: str
    artifacts: tuple[PackageArtifact, ...]
    artifact_set_digest: str
    rollback_artifact_digests: tuple[str, ...]
    index_digest: str

    KEYS = ("version", "release_id", "channel", "platform_manifest_id", "platform_manifest_digest", "schema_set_digest", "artifacts", "artifact_set_digest", "rollback_artifact_digests", "index_digest")

    @classmethod
    def from_dict(cls, value: Any, path: str = "$") -> "PackageIndex":
        value = expect_object(value, cls.KEYS, path)
        if value["version"] != "package-index/v1":
            raise BuildProvenanceError("UNSUPPORTED_VERSION", f"{path}.version", "package-index/v1 required")
        release_id = expect_string(value["release_id"], f"{path}.release_id", pattern=ID_RE)
        channel = expect_enum(value["channel"], f"{path}.channel", CHANNELS)
        platform_manifest_id = expect_string(value["platform_manifest_id"], f"{path}.platform_manifest_id")
        platform_manifest_digest = expect_digest(value["platform_manifest_digest"], f"{path}.platform_manifest_digest")
        schema_digest = expect_digest(value["schema_set_digest"], f"{path}.schema_set_digest")
        artifacts = tuple(PackageArtifact.from_dict(item, f"{path}.artifacts[{index}]") for index, item in enumerate(expect_list(value["artifacts"], f"{path}.artifacts", nonempty=True)))
        if [item.artifact_id for item in artifacts] != sorted(item.artifact_id for item in artifacts) or len({item.artifact_id for item in artifacts}) != len(artifacts):
            raise BuildProvenanceError("UNSORTED_IDS", f"{path}.artifacts", "artifact IDs must be unique and sorted")
        artifact_digest = expect_digest(value["artifact_set_digest"], f"{path}.artifact_set_digest")
        projected = [item.to_dict() for item in artifacts]
        if artifact_digest != digest_value("omarchy-package-artifact-set/v1", projected):
            raise BuildProvenanceError("DIGEST_MISMATCH", f"{path}.artifact_set_digest", "package artifact set mismatch")
        rollback = sorted_unique([expect_digest(item, f"{path}.rollback_artifact_digests[{index}]") for index, item in enumerate(expect_list(value["rollback_artifact_digests"], f"{path}.rollback_artifact_digests", nonempty=True))], f"{path}.rollback_artifact_digests")
        index_digest = _verify_digest(value, "index_digest", "omarchy-package-index/v1", path)
        return cls(release_id, channel, platform_manifest_id, platform_manifest_digest, schema_digest, artifacts, artifact_digest, rollback, index_digest)

    def body(self) -> dict[str, Any]:
        return {"version": "package-index/v1", "release_id": self.release_id, "channel": self.channel, "platform_manifest_id": self.platform_manifest_id, "platform_manifest_digest": self.platform_manifest_digest, "schema_set_digest": self.schema_set_digest, "artifacts": [item.to_dict() for item in self.artifacts], "artifact_set_digest": self.artifact_set_digest, "rollback_artifact_digests": list(self.rollback_artifact_digests)}

    def to_dict(self) -> dict[str, Any]:
        return {**self.body(), "index_digest": self.index_digest}

    @classmethod
    def create(cls, *, release_id: str, channel: str, platform_manifest_id: str, platform_manifest_digest: str, schema_set_digest_value: str, artifacts: tuple[PackageArtifact, ...], rollback_artifact_digests: tuple[str, ...]) -> "PackageIndex":
        body = {"version": "package-index/v1", "release_id": release_id, "channel": channel, "platform_manifest_id": platform_manifest_id, "platform_manifest_digest": platform_manifest_digest, "schema_set_digest": schema_set_digest_value, "artifacts": [item.to_dict() for item in artifacts], "artifact_set_digest": digest_value("omarchy-package-artifact-set/v1", [item.to_dict() for item in artifacts]), "rollback_artifact_digests": list(rollback_artifact_digests)}
        return cls(release_id, channel, platform_manifest_id, platform_manifest_digest, schema_set_digest_value, artifacts, body["artifact_set_digest"], rollback_artifact_digests, digest_value("omarchy-package-index/v1", body))


@dataclass(frozen=True)
class TrustedTrustContext:
    accepted_role: str
    key_ids: tuple[str, ...]
    threshold: int
    metadata_digest: str
    schema_set_digest: str
    channel: str
    expires_at: str
    replay_id: str

    KEYS = ("accepted_role", "key_ids", "threshold", "metadata_digest", "schema_set_digest", "channel", "expires_at", "replay_id")

    @classmethod
    def from_dict(cls, value: Any, path: str = "$") -> "TrustedTrustContext":
        value = expect_object(value, cls.KEYS, path)
        role = expect_string(value["accepted_role"], f"{path}.accepted_role")
        raw_ids = expect_list(value["key_ids"], f"{path}.key_ids", nonempty=True)
        key_ids = sorted_unique([expect_string(item, f"{path}.key_ids[{index}]") for index, item in enumerate(raw_ids)], f"{path}.key_ids")
        threshold = value["threshold"]
        if not isinstance(threshold, int) or isinstance(threshold, bool):
            raise BuildProvenanceError("INVALID_TRUST_CONTEXT", f"{path}.threshold", "integer threshold required")
        return cls(role, key_ids, threshold, expect_digest(value["metadata_digest"], f"{path}.metadata_digest"), expect_digest(value["schema_set_digest"], f"{path}.schema_set_digest"), expect_enum(value["channel"], f"{path}.channel", CHANNELS), expect_string(value["expires_at"], f"{path}.expires_at"), expect_string(value["replay_id"], f"{path}.replay_id"))

    def __post_init__(self) -> None:
        if not self.accepted_role or not isinstance(self.accepted_role, str):
            raise BuildProvenanceError("INVALID_TRUST_CONTEXT", "$.accepted_role", "accepted role required")
        if not isinstance(self.key_ids, tuple) or any(not isinstance(item, str) or not item for item in self.key_ids) or self.key_ids != tuple(sorted(set(self.key_ids))) or not self.key_ids:
            raise BuildProvenanceError("INVALID_TRUST_CONTEXT", "$.key_ids", "key IDs must be sorted and unique")
        if not isinstance(self.threshold, int) or self.threshold < 1 or self.threshold > len(self.key_ids):
            raise BuildProvenanceError("INVALID_TRUST_CONTEXT", "$.threshold", "threshold must fit accepted key IDs")
        expect_digest(self.metadata_digest, "$.metadata_digest")
        expect_digest(self.schema_set_digest, "$.schema_set_digest")
        if self.channel not in CHANNELS:
            raise BuildProvenanceError("INVALID_TRUST_CONTEXT", "$.channel", "unknown channel")
        if not isinstance(self.expires_at, str) or not self.expires_at.endswith("Z"):
            raise BuildProvenanceError("INVALID_TRUST_CONTEXT", "$.expires_at", "UTC expiry required")
        if not self.replay_id or not isinstance(self.replay_id, str):
            raise BuildProvenanceError("INVALID_TRUST_CONTEXT", "$.replay_id", "replay identity required")

    def to_dict(self) -> dict[str, Any]:
        return {"accepted_role": self.accepted_role, "key_ids": list(self.key_ids), "threshold": self.threshold, "metadata_digest": self.metadata_digest, "schema_set_digest": self.schema_set_digest, "channel": self.channel, "expires_at": self.expires_at, "replay_id": self.replay_id}
