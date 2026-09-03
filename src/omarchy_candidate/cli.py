"""Deterministic offline F-05 CLI; it never promotes or publishes."""

from __future__ import annotations

import argparse
import os
import sys

from omarchy_platform.canonical import canonical_bytes
from omarchy_platform.strictjson import parse
from omarchy_platform.errors import ParseError

from .assemble import assemble_candidate
from .errors import CandidateAssemblyError
from .models import CandidateManifest


MAX_INPUT_BYTES = 4 * 1024 * 1024


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CandidateAssemblyError("CLI_INVALID", "$.arguments", "candidate command arguments are invalid")


def _open_regular(path: str, limit: int) -> tuple[int, int]:
    """Open a regular file through a no-symlink descriptor walk."""
    if not isinstance(path, str) or not path or "\0" in path:
        raise CandidateAssemblyError("INPUT_INVALID", "$", "candidate input path is invalid")
    try:
        lexical = os.path.abspath(path)
        if not os.path.isabs(lexical):
            raise CandidateAssemblyError("INPUT_INVALID", "$", "candidate input path is invalid")
        # macOS exposes /tmp as the fixed system alias /private/tmp. Walk the
        # physical spelling so the trusted system alias is not mistaken for a
        # caller-created parent symlink.
        if (lexical == "/tmp" or lexical.startswith("/tmp/")) and os.path.realpath("/tmp") == "/private/tmp":
            lexical = "/private" + lexical
        components = [part for part in lexical.split(os.sep) if part]
        if not components or any(part in {".", ".."} for part in components):
            raise CandidateAssemblyError("INPUT_INVALID", "$", "candidate input path is invalid")
        flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
        directory_flags = flags | os.O_DIRECTORY
        parent_fd = os.open(os.sep, directory_flags)
        try:
            for component in components[:-1]:
                next_fd = os.open(component, directory_flags, dir_fd=parent_fd)
                os.close(parent_fd)
                parent_fd = next_fd
            file_fd = os.open(components[-1], flags | os.O_NONBLOCK, dir_fd=parent_fd)
        finally:
            os.close(parent_fd)
        stat_result = os.fstat(file_fd)
        if not __import__("stat").S_ISREG(stat_result.st_mode) or stat_result.st_size > limit:
            os.close(file_fd)
            raise CandidateAssemblyError("INPUT_INVALID", "$", "candidate input must be a bounded regular file")
        return file_fd, stat_result.st_size
    except CandidateAssemblyError:
        raise
    except (OSError, UnicodeError, ValueError) as error:
        raise CandidateAssemblyError("INPUT_INVALID", "$", "candidate input could not be opened safely") from error


def _read_bounded(path: str, limit: int) -> bytes:
    file_fd, expected_size = _open_regular(path, limit)
    try:
        chunks: list[bytes] = []
        total = 0
        while total <= limit:
            chunk = os.read(file_fd, min(131072, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                raise CandidateAssemblyError("RESOURCE_LIMIT", "$", "input byte limit exceeded")
        if total != expected_size:
            raise CandidateAssemblyError("INPUT_INVALID", "$", "candidate input changed while being read")
        return b"".join(chunks)
    except CandidateAssemblyError:
        raise
    except (OSError, ValueError) as error:
        raise CandidateAssemblyError("INPUT_INVALID", "$", "candidate input could not be read safely") from error
    finally:
        os.close(file_fd)


def _exclusive_output(path: str, data: bytes, *, permitted_root: str) -> None:
    if len(data) > 4 * 1024 * 1024:
        raise CandidateAssemblyError("RESOURCE_LIMIT", "$.output", "output byte limit exceeded")
    try:
        if not isinstance(permitted_root, str) or not permitted_root or not os.path.isabs(permitted_root):
            raise CandidateAssemblyError("OUTPUT_PATH_INVALID", "$.output_root", "permitted root realpath differs from lexical path")
        root_lexical = os.path.abspath(permitted_root)
        root_real = os.path.realpath(root_lexical)
        alias = root_lexical == "/tmp" or root_lexical.startswith("/tmp/")
        if not os.path.isdir(root_real) or os.path.islink(root_lexical) or (root_lexical != root_real and not (alias and root_real == "/private" + root_lexical)):
            raise CandidateAssemblyError("OUTPUT_ROOT_INVALID", "$.output_root", "permitted root must be an existing real directory")
        target_lexical = os.path.abspath(path if os.path.isabs(path) else os.path.join(os.getcwd(), path))
        relative = os.path.relpath(target_lexical, root_lexical)
        parts = relative.split(os.sep)
        if not parts or parts[-1] in {"", ".", ".."} or any(part in {".", ".."} for part in parts):
            raise CandidateAssemblyError("OUTPUT_PATH_INVALID", "$.output", "output must remain under permitted root")
        root_fd = os.open(root_real, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
        parent_fd = root_fd
        temporary_name = None
        committed = False
        try:
            for component in parts[:-1]:
                next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=parent_fd)
                if parent_fd != root_fd:
                    os.close(parent_fd)
                parent_fd = next_fd
            target_name = parts[-1]
            for sequence in range(100):
                candidate = f".candidate-{os.getpid()}-{sequence}"
                try:
                    fd = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600, dir_fd=parent_fd)
                    temporary_name = candidate
                    break
                except FileExistsError:
                    continue
            else:
                raise CandidateAssemblyError("OUTPUT_WRITE_FAILURE", "$.output", "temporary output name could not be allocated")
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(os.path.basename(temporary_name), target_name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd, follow_symlinks=False)
            committed = True
            try:
                os.fsync(parent_fd)
            except OSError as error:
                try:
                    os.unlink(target_name, dir_fd=parent_fd)
                    committed = False
                except OSError:
                    pass
                raise CandidateAssemblyError("OUTPUT_WRITE_FAILURE", "$.output", "output directory could not be committed") from error
        except FileExistsError as error:
            raise CandidateAssemblyError("OUTPUT_CONFLICT", "$.output", "output already exists") from error
        finally:
            if temporary_name is not None:
                removed = False
                for _attempt in range(3):
                    try:
                        os.unlink(temporary_name, dir_fd=parent_fd)
                        removed = True
                        break
                    except OSError:
                        continue
                if not removed:
                    if committed:
                        try:
                            os.unlink(target_name, dir_fd=parent_fd)
                        except OSError:
                            pass
                    raise CandidateAssemblyError("OUTPUT_WRITE_FAILURE", "$.output", "temporary output could not be cleaned safely")
            if parent_fd != root_fd:
                os.close(parent_fd)
            os.close(root_fd)
    except CandidateAssemblyError:
        raise
    except (OSError, UnicodeError, ValueError) as error:
        raise CandidateAssemblyError("OUTPUT_WRITE_FAILURE", "$.output", "output could not be written") from error


def _read(path: str) -> object:
    try:
        data = _read_bounded(path, MAX_INPUT_BYTES)
        return parse(data)
    except CandidateAssemblyError:
        raise
    except ParseError as error:
        raise CandidateAssemblyError(error.code, error.path, error.message) from error
    except (OSError, ValueError, TypeError, UnicodeError) as error:
        raise CandidateAssemblyError("INPUT_INVALID", "$", "candidate input is invalid") from error


def main(argv: list[str] | None = None) -> int:
    parser = _ArgumentParser(prog="omarchy-candidate")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_ArgumentParser)
    assemble = sub.add_parser("assemble")
    assemble.add_argument("--input", required=True)
    assemble.add_argument("--output")
    assemble.add_argument("--output-root")
    verify = sub.add_parser("verify")
    verify.add_argument("--input", required=True)
    try:
        args = parser.parse_args(argv)
        if args.command == "verify":
            manifest = CandidateManifest.from_dict(_read(args.input))
            sys.stdout.buffer.write(canonical_bytes({"decision": "STRUCTURAL_ONLY", "candidate_digest": manifest.candidate_digest}) + b"\n")
            return 0
        manifest = assemble_candidate(_read(args.input))
        output = manifest.bytes() + b"\n"
        if args.output:
            if not args.output_root:
                raise CandidateAssemblyError("OUTPUT_ROOT_REQUIRED", "$.output_root", "explicit permitted output root is required")
            _exclusive_output(args.output, output, permitted_root=args.output_root)
        else:
            sys.stdout.buffer.write(output)
        return 0
    except CandidateAssemblyError as error:
        sys.stderr.buffer.write(canonical_bytes(error.as_dict()) + b"\n")
        return 2
    except (OSError, UnicodeError):
        sys.stderr.buffer.write(canonical_bytes({"code": "OUTPUT_WRITE_FAILURE", "path": "$.output", "detail": "output could not be written"}) + b"\n")
        return 2
