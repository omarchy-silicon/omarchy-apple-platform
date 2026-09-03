"""Bounded local content-addressed artifact and immutable channel store."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .errors import BuildProvenanceError, StoreError, TrustRejection
from .models import CHANNELS, PackageIndex, TrustedTrustContext
from .operations import promotion_operation_bytes, rollback_operation_bytes
from .trust import TrustAdapter, require_trusted_context
from .util import MAX_DOCUMENT_BYTES, MAX_OUTPUT_BYTES, canonical_bytes, digest_bytes, expect_digest, expect_string, read_json


def _safe_component(value: str, path: str) -> str:
    if not isinstance(value, str) or not value or value in {".", ".."} or "/" in value or "\\" in value or "\x00" in value:
        raise StoreError("UNSAFE_PATH", path, "path component is not safe")
    return value


class LocalArtifactStore:
    """Filesystem store with create-only objects and append-only channel records."""

    def __init__(self, root: str | os.PathLike[str], *, max_object_bytes: int = MAX_OUTPUT_BYTES):
        raw_root = Path(root).absolute()
        if raw_root.is_symlink():
            raise StoreError("UNSAFE_PATH", "$", "store root may not be a symlink")
        for ancestor in (raw_root, *raw_root.parents):
            # macOS exposes the system temporary directory as /tmp -> /private/tmp.
            # It is the one platform-owned link permitted for isolated test roots;
            # links introduced anywhere below it remain rejected. Verify its
            # destination too, so a replaced system link is not trusted.
            if ancestor.is_symlink():
                try:
                    platform_temp_link = ancestor == Path("/tmp") and ancestor.resolve(strict=True) == Path("/private/tmp")
                except OSError:
                    platform_temp_link = False
                if not platform_temp_link:
                    raise StoreError("UNSAFE_PATH", "$", "store path may not traverse a symlink")
            if ancestor.exists() and not ancestor.is_dir():
                raise StoreError("UNSAFE_PATH", "$", "store path may not traverse a non-directory")
        self.root = raw_root.resolve()
        self.max_object_bytes = max_object_bytes
        self.objects = self.root / "objects" / "sha256"
        self.channels = self.root / "channels"
        self._ensure_directory(self.root, "$", parents=True)
        self._ensure_directory(self.root / "objects", "$.objects")
        self._ensure_directory(self.objects, "$.objects.sha256")
        self._ensure_directory(self.channels, "$.channels")

    @staticmethod
    def _ensure_directory(path: Path, field: str, *, parents: bool = False) -> None:
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise StoreError("UNSAFE_PATH", field, "store path must be a real directory")
        try:
            path.mkdir(parents=parents, exist_ok=True)
        except OSError as error:
            raise StoreError("STORE_INIT_FAILURE", field, "store directory could not be created") from error
        if path.is_symlink() or not path.is_dir():
            raise StoreError("UNSAFE_PATH", field, "store path must be a real directory")

    def _object_path(self, digest: str) -> Path:
        expect_digest(digest, "$.digest")
        path = self.objects / digest.removeprefix("sha256:")
        if path.parent != self.objects or path.is_symlink():
            raise StoreError("UNSAFE_PATH", "$.digest", "object path is unsafe")
        return path

    def put(self, data: bytes, *, expected_digest: str | None = None) -> str:
        if not isinstance(data, bytes):
            raise StoreError("TYPE_MISMATCH", "$.data", "bytes required")
        if len(data) > self.max_object_bytes:
            raise StoreError("RESOURCE_LIMIT", "$.data", "object byte limit exceeded")
        actual = digest_bytes(data)
        if expected_digest is not None and expected_digest != actual:
            raise StoreError("DIGEST_MISMATCH", "$.expected_digest", "object bytes differ from expected digest")
        target = self._object_path(actual)
        if target.exists():
            if target.is_symlink() or not target.is_file() or target.read_bytes() != data:
                raise StoreError("IMMUTABLE_OBJECT_CONFLICT", "$.digest", "occupied digest does not contain the same bytes")
            return actual
        temporary: Path | None = None
        try:
            fd, name = tempfile.mkstemp(prefix=".put-", dir=self.objects)
            temporary = Path(name)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                if target.is_symlink() or not target.is_file() or target.read_bytes() != data:
                    raise StoreError("IMMUTABLE_OBJECT_CONFLICT", "$.digest", "occupied digest does not contain the same bytes") from None
            return actual
        except StoreError:
            raise
        except OSError as error:
            raise StoreError("STORE_WRITE_FAILURE", "$.digest", "object could not be stored") from error
        finally:
            if temporary is not None:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass

    def read(self, digest: str) -> bytes:
        path = self._object_path(digest)
        try:
            if path.is_symlink() or not path.is_file():
                raise StoreError("OBJECT_MISSING", "$.digest", "content-addressed object is missing")
            data = path.read_bytes()
        except StoreError:
            raise
        except OSError as error:
            raise StoreError("OBJECT_READ_FAILURE", "$.digest", "object could not be read") from error
        if len(data) > self.max_object_bytes:
            raise StoreError("RESOURCE_LIMIT", "$.digest", "object byte limit exceeded")
        if digest_bytes(data) != digest:
            raise StoreError("DIGEST_MISMATCH", "$.digest", "stored bytes failed rehash")
        return data

    def _channel_path(self, channel: str, release_id: str, *, allow_existing_node: bool = False) -> Path:
        channel = _safe_component(channel, "$.channel")
        release_id = _safe_component(release_id, "$.release_id")
        if channel not in CHANNELS:
            raise StoreError("UNKNOWN_CHANNEL", "$.channel", "channel is outside the closed vocabulary")
        directory = self.channels / channel
        self._ensure_directory(directory, "$.channel")
        path = directory / f"{release_id}.json"
        if path.parent != directory or (path.is_symlink() and not allow_existing_node):
            raise StoreError("UNSAFE_PATH", "$.release_id", "channel record path is unsafe")
        return path

    def publish_index(
        self,
        index: PackageIndex,
        *,
        adapter: TrustAdapter | None = None,
        expires_at: str | None = None,
        replay_id: str | None = None,
        signer_role: str | None = None,
        context: TrustedTrustContext | None = None,
    ) -> str:
        try:
            index = PackageIndex.from_dict(index.to_dict())
        except Exception as error:
            if isinstance(error, StoreError):
                raise
            raise StoreError("INDEX_INVALID", "$.index", "package index is not a closed valid record") from error
        if context is not None:
            raise TrustRejection("TRUST_ADAPTER_REQUIRED", "$.context", "raw trust contexts cannot authorize publication")
        if index.channel == "stable":
            raise StoreError("STABLE_PROMOTION_REQUIRES_F07", "$.channel", "stable publication is not a direct F-04 operation")
        requested_role = "package-index"
        if signer_role is not None and signer_role != requested_role:
            raise TrustRejection("TRUST_ROLE_REJECTED", "$.signer_role", "publication requires the package-index role")
        index_bytes = canonical_bytes(index.to_dict())
        require_trusted_context(
            adapter,
            index_bytes,
            schema_set_digest=index.schema_set_digest,
            signer_role=requested_role,
            channel=index.channel,
            expires_at=expires_at,
            replay_id=replay_id,
        )
        for artifact in index.artifacts:
            self.read(artifact.content_digest)
        for digest in index.rollback_artifact_digests:
            self.read(digest)
        index_object_digest = self.put(index_bytes)
        record = {"version": "channel-record/v1", "channel": index.channel, "release_id": index.release_id, "index_digest": index_object_digest, "artifact_set_digest": index.artifact_set_digest, "rollback_artifact_digests": list(index.rollback_artifact_digests)}
        record["record_digest"] = digest_bytes(b"omarchy-channel-record/v1\x00" + canonical_bytes(record))
        self._put_channel_record(index.channel, index.release_id, record)
        return index_object_digest

    def _put_channel_record(self, channel: str, release_id: str, record: dict[str, Any]) -> None:
        path = self._channel_path(channel, release_id, allow_existing_node=True)
        data = canonical_bytes(record) + b"\n"
        if len(data) > MAX_DOCUMENT_BYTES:
            raise StoreError("RESOURCE_LIMIT", "$.channel", "channel record byte limit exceeded")
        if path.exists():
            if path.is_symlink() or not path.is_file():
                raise StoreError("IMMUTABLE_CHANNEL_CONFLICT", "$.release_id", "channel record cannot be overwritten")
            try:
                existing = path.read_bytes()
            except OSError as error:
                raise StoreError("IMMUTABLE_CHANNEL_CONFLICT", "$.release_id", "channel record cannot be overwritten") from error
            if existing != data:
                raise StoreError("IMMUTABLE_CHANNEL_CONFLICT", "$.release_id", "channel record cannot be overwritten")
            return
        if path.is_symlink():
            raise StoreError("IMMUTABLE_CHANNEL_CONFLICT", "$.release_id", "channel record cannot be overwritten")
        temporary: Path | None = None
        try:
            fd, name = tempfile.mkstemp(prefix=".channel-", dir=path.parent)
            temporary = Path(name)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError:
                if path.is_symlink() or not path.is_file():
                    raise StoreError("IMMUTABLE_CHANNEL_CONFLICT", "$.release_id", "channel record cannot be overwritten") from None
                try:
                    existing = path.read_bytes()
                except OSError as error:
                    raise StoreError("IMMUTABLE_CHANNEL_CONFLICT", "$.release_id", "channel record cannot be overwritten") from error
                if existing != data:
                    raise StoreError("IMMUTABLE_CHANNEL_CONFLICT", "$.release_id", "channel record cannot be overwritten") from None
        except StoreError:
            raise
        except OSError as error:
            raise StoreError("STORE_WRITE_FAILURE", "$.channel", "channel record could not be stored") from error
        finally:
            if temporary is not None:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass

    def read_channel(self, channel: str, release_id: str) -> dict[str, Any]:
        path = self._channel_path(channel, release_id)
        try:
            data = path.read_bytes()
        except OSError as error:
            raise StoreError("CHANNEL_RECORD_MISSING", "$.release_id", "channel record is missing") from error
        try:
            record = json.loads(data)
        except (ValueError, UnicodeDecodeError) as error:
            raise StoreError("CHANNEL_RECORD_INVALID", "$.release_id", "channel record is invalid") from error
        expected = record.get("record_digest")
        body = {key: value for key, value in record.items() if key != "record_digest"}
        if expected != digest_bytes(b"omarchy-channel-record/v1\x00" + canonical_bytes(body)):
            raise StoreError("CHANNEL_RECORD_INVALID", "$.record_digest", "channel record digest mismatch")
        return record

    def promote(
        self,
        source_channel: str,
        target_channel: str,
        release_id: str,
        *,
        adapter: TrustAdapter | None = None,
        expires_at: str | None = None,
        replay_id: str | None = None,
        signer_role: str | None = None,
        context: TrustedTrustContext | None = None,
    ) -> str:
        if source_channel not in CHANNELS or target_channel not in CHANNELS:
            raise StoreError("UNKNOWN_CHANNEL", "$.channel", "channel is outside the closed vocabulary")
        if context is not None:
            raise TrustRejection("TRUST_ADAPTER_REQUIRED", "$.context", "raw trust contexts cannot authorize promotion")
        requested_role = "promotion/f07" if target_channel == "stable" else "package-index"
        if signer_role is not None and signer_role != requested_role:
            raise TrustRejection("TRUST_ROLE_REJECTED", "$.signer_role", "promotion role is not valid for the target channel")
        source = self.read_channel(source_channel, release_id)
        index_digest = expect_digest(source["index_digest"], "$.index_digest")
        source_record_digest = expect_digest(source["record_digest"], "$.record_digest")
        index = PackageIndex.from_dict(json.loads(self.read(index_digest)))
        if index.channel == "stable" or index.release_id != release_id:
            raise StoreError("CHANNEL_BINDING_MISMATCH", "$.index_digest", "source index is not bound to channel record")
        source_rollback = tuple(source["rollback_artifact_digests"])
        if source.get("artifact_set_digest") != index.artifact_set_digest or source_rollback != index.rollback_artifact_digests:
            raise StoreError("CHANNEL_BINDING_MISMATCH", "$.rollback_artifact_digests", "source rollback set is not bound to index")
        operation_bytes = promotion_operation_bytes(
            source_channel=source_channel,
            target_channel=target_channel,
            release_id=release_id,
            source_record_digest=source_record_digest,
            source_index_digest=index_digest,
            artifact_set_digest=index.artifact_set_digest,
            rollback_artifact_digests=index.rollback_artifact_digests,
        )
        require_trusted_context(
            adapter,
            operation_bytes,
            schema_set_digest=index.schema_set_digest,
            signer_role=requested_role,
            channel=target_channel,
            expires_at=expires_at,
            replay_id=replay_id,
        )
        for artifact in index.artifacts:
            self.read(artifact.content_digest)
        for digest in index.rollback_artifact_digests:
            self.read(digest)
        # Promotion copies the existing index and artifact digests. The channel
        # record is the namespace projection; it never rewrites index bytes.
        record = {"version": "channel-record/v1", "channel": target_channel, "release_id": release_id, "index_digest": source["index_digest"], "artifact_set_digest": source["artifact_set_digest"], "rollback_artifact_digests": list(source["rollback_artifact_digests"])}
        record["record_digest"] = digest_bytes(b"omarchy-channel-record/v1\x00" + canonical_bytes(record))
        self._put_channel_record(target_channel, release_id, record)
        return index_digest

    def _object_metadata_digest(self, digest: str) -> str:
        """Return the digest of the exact canonical metadata bytes in an object."""

        return digest_bytes(self.read(digest))

    def rollback(
        self,
        channel: str,
        failed_release_id: str,
        restore_release_id: str,
        *,
        adapter: TrustAdapter | None = None,
        expires_at: str | None = None,
        replay_id: str | None = None,
        signer_role: str | None = None,
        context: TrustedTrustContext | None = None,
    ) -> str:
        if context is not None:
            raise TrustRejection("TRUST_ADAPTER_REQUIRED", "$.context", "raw trust contexts cannot authorize rollback")
        requested_role = "promotion/f07" if channel == "stable" else "emergency/recovery"
        if signer_role is not None and signer_role != requested_role:
            raise TrustRejection("TRUST_ROLE_REJECTED", "$.signer_role", "rollback role is not valid for the requested channel")
        try:
            failed = self.read_channel(channel, failed_release_id)
            restored = self.read_channel(channel, restore_release_id)
            if failed.get("channel") != channel or failed.get("release_id") != failed_release_id or restored.get("channel") != channel or restored.get("release_id") != restore_release_id:
                raise StoreError("ROLLBACK_BINDING_MISMATCH", "$.channel", "rollback records are not bound to requested channel and release")
            failed_index_digest = expect_digest(failed["index_digest"], "$.failed_index_digest")
            restore_index_digest = expect_digest(restored["index_digest"], "$.restored_index_digest")
            failed_record_digest = expect_digest(failed["record_digest"], "$.failed_record_digest")
            restore_record_digest = expect_digest(restored["record_digest"], "$.restore_record_digest")
            failed_index = PackageIndex.from_dict(json.loads(self.read(failed_index_digest)))
            if failed_index.release_id != failed_release_id or failed_index.channel == "stable":
                raise StoreError("ROLLBACK_BINDING_MISMATCH", "$.failed_index_digest", "failed index is not bound to requested release")
            if failed.get("artifact_set_digest") != failed_index.artifact_set_digest or tuple(failed.get("rollback_artifact_digests", ())) != failed_index.rollback_artifact_digests:
                raise StoreError("ROLLBACK_BINDING_MISMATCH", "$.failed_index_digest", "failed rollback set is not bound to index")
            restore_bytes = self.read(restore_index_digest)
            restore_payload = json.loads(restore_bytes)
            if not isinstance(restore_payload, dict) or "rollback_artifact_digests" not in restore_payload:
                raise StoreError("ROLLBACK_ARTIFACT_MISSING", "$.rollback_artifact_digests", "rollback artifact member is missing")
            restore_index = PackageIndex.from_dict(restore_payload)
        except StoreError as error:
            if error.code in {"ROLLBACK_BINDING_MISMATCH", "ROLLBACK_ARTIFACT_MISSING"}:
                raise
            if error.code in {"OBJECT_MISSING", "DIGEST_MISMATCH"}:
                raise StoreError("ROLLBACK_ARTIFACT_MISSING", "$.restored_index_digest", "rollback index object is unavailable") from error
            raise StoreError("ROLLBACK_BINDING_MISMATCH", "$.restored_index_digest", "rollback index record is unavailable") from error
        except BuildProvenanceError as error:
            if error.code == "MISSING_FIELD" and error.path.endswith(".rollback_artifact_digests"):
                raise StoreError("ROLLBACK_ARTIFACT_MISSING", "$.rollback_artifact_digests", "rollback artifact member is missing") from error
            raise StoreError("ROLLBACK_BINDING_MISMATCH", "$.restored_index_digest", "rollback index record is invalid") from error
        except Exception as error:
            raise StoreError("ROLLBACK_BINDING_MISMATCH", "$.restored_index_digest", "rollback index record is invalid") from error
        if restore_index.channel != channel or restore_index.release_id != restore_release_id:
            raise StoreError("ROLLBACK_BINDING_MISMATCH", "$.restored_index_digest", "rollback index is not bound to requested channel and release")
        if restored.get("artifact_set_digest") != restore_index.artifact_set_digest or tuple(restored.get("rollback_artifact_digests", ())) != restore_index.rollback_artifact_digests:
            raise StoreError("ROLLBACK_BINDING_MISMATCH", "$.rollback_artifact_digests", "restored rollback set is not bound to index")
        operation_bytes = rollback_operation_bytes(
            channel=channel,
            failed_release_id=failed_release_id,
            restore_release_id=restore_release_id,
            failed_record_digest=failed_record_digest,
            restore_record_digest=restore_record_digest,
            failed_index_digest=failed_index_digest,
            restore_index_digest=restore_index_digest,
            restore_artifact_set_digest=restore_index.artifact_set_digest,
            rollback_artifact_digests=restore_index.rollback_artifact_digests,
        )
        require_trusted_context(
            adapter,
            operation_bytes,
            schema_set_digest=restore_index.schema_set_digest,
            signer_role=requested_role,
            channel=channel,
            expires_at=expires_at,
            replay_id=replay_id,
        )
        if not restore_index.rollback_artifact_digests:
            raise StoreError("ROLLBACK_ARTIFACT_MISSING", "$.rollback_artifact_digests", "rollback set is empty")
        for artifact in restore_index.artifacts:
            try:
                self.read(artifact.content_digest)
            except StoreError as error:
                raise StoreError("ROLLBACK_ARTIFACT_MISSING", "$.artifacts", "rollback artifact is unavailable") from error
        for digest in restore_index.rollback_artifact_digests:
            try:
                self.read(digest)
            except StoreError as error:
                raise StoreError("ROLLBACK_ARTIFACT_MISSING", "$.rollback_artifact_digests", "rollback artifact is unavailable") from error
        # The recovery record is append-only and points only at the retained
        # existing index; no build or fetch is performed here.
        recovery_id = f"rollback-{failed_release_id}-to-{restore_release_id}"
        recovery = {"version": "rollback-record/v1", "channel": channel, "release_id": recovery_id, "failed_index_digest": failed_index_digest, "restored_index_digest": restore_index_digest, "restored_artifact_set_digest": restore_index.artifact_set_digest}
        recovery["record_digest"] = digest_bytes(b"omarchy-rollback-record/v1\x00" + canonical_bytes(recovery))
        self._put_channel_record(channel, recovery_id, recovery)
        return restore_index_digest


ArtifactStore = LocalArtifactStore
