"""Deterministic offline F-05 CLI; it never promotes or publishes."""

from __future__ import annotations

import argparse
import os
import tempfile
import sys
from pathlib import Path

from omarchy_platform.canonical import canonical_bytes
from omarchy_platform.strictjson import parse
from omarchy_platform.errors import ParseError

from .assemble import assemble_candidate
from .errors import CandidateAssemblyError
from .models import CandidateManifest


def _exclusive_output(path: str, data: bytes, *, permitted_root: str) -> None:
    if len(data) > 4 * 1024 * 1024:
        raise CandidateAssemblyError("RESOURCE_LIMIT", "$.output", "output byte limit exceeded")
    root = Path(permitted_root)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise CandidateAssemblyError("OUTPUT_ROOT_INVALID", "$.output_root", "permitted root must be an existing real directory")
    target = Path(path)
    if not target.is_absolute():
        target = Path.cwd() / target
    parent = target.parent
    try:
        root_lexical, root_real = os.path.abspath(str(root)), os.path.realpath(str(root))
        target_lexical = os.path.abspath(str(target))
        root_tmp_alias = (root_lexical == "/tmp" or root_lexical.startswith("/tmp/")) and root_real == "/private" + root_lexical
        if root_lexical != root_real and not root_tmp_alias:
            raise CandidateAssemblyError("OUTPUT_PATH_INVALID", "$.output_root", "permitted root realpath differs from lexical path")
        if os.path.commonpath((target_lexical, root_lexical)) != root_lexical:
            raise CandidateAssemblyError("OUTPUT_PATH_INVALID", "$.output", "output must remain under permitted root")
        if not parent.exists() or not parent.is_dir() or parent.is_symlink():
            raise CandidateAssemblyError("OUTPUT_PATH_INVALID", "$.output", "output parent must be a real directory")
        lexical_parent = os.path.abspath(str(parent))
        real_parent = os.path.realpath(str(parent))
        temporary_alias = lexical_parent == "/tmp" or lexical_parent.startswith("/tmp/")
        temporary_alias = temporary_alias and real_parent == "/private" + lexical_parent
        if lexical_parent != real_parent and not temporary_alias:
            raise CandidateAssemblyError("OUTPUT_PATH_INVALID", "$.output", "output parent realpath differs from lexical path")
        if target.exists() or target.is_symlink():
            raise CandidateAssemblyError("OUTPUT_CONFLICT", "$.output", "output already exists")
        fd, temporary_name = tempfile.mkstemp(prefix=".candidate-", dir=str(parent))
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary, target)
        except FileExistsError as error:
            raise CandidateAssemblyError("OUTPUT_CONFLICT", "$.output", "output already exists") from error
        finally:
            temporary.unlink(missing_ok=True)
    except CandidateAssemblyError:
        raise
    except OSError as error:
        raise CandidateAssemblyError("OUTPUT_WRITE_FAILURE", "$.output", "output could not be written") from error


def _read(path: str) -> object:
    try:
        data = Path(path).read_bytes()
        if len(data) > 4 * 1024 * 1024:
            raise CandidateAssemblyError("RESOURCE_LIMIT", "$", "input byte limit exceeded")
        return parse(data)
    except CandidateAssemblyError:
        raise
    except ParseError as error:
        raise CandidateAssemblyError(error.code, error.path, error.message) from error
    except (OSError, ValueError, TypeError, UnicodeDecodeError) as error:
        raise CandidateAssemblyError("INPUT_INVALID", "$", "candidate input is invalid") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omarchy-candidate")
    sub = parser.add_subparsers(dest="command", required=True)
    assemble = sub.add_parser("assemble")
    assemble.add_argument("--input", required=True)
    assemble.add_argument("--output")
    assemble.add_argument("--output-root")
    verify = sub.add_parser("verify")
    verify.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            manifest = CandidateManifest.from_dict(_read(args.input))
            sys.stdout.buffer.write(canonical_bytes({"decision": "ACCEPT", "candidate_digest": manifest.candidate_digest}) + b"\n")
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
    except OSError:
        sys.stderr.buffer.write(canonical_bytes({"code": "OUTPUT_WRITE_FAILURE", "path": "$.output", "detail": "output could not be written"}) + b"\n")
        return 2
