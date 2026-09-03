"""Bounded, offline validation of PROGRAM.md and its append-only history."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .errors import ProgramValidationError

MAX_PROGRAM_BYTES = 1_000_000
MAX_SLICE_ROWS = 128
MAX_PROGRESS_ROWS = 4096
MAX_DEPENDENCIES = 32
MAX_GRAPH_DEPTH = 64
EXPECTED_SLICE_COUNT = 52
STATUS_VOCABULARY = ("DONE", "IN PROGRESS", "TODO", "HUMAN-ONLY BLOCKED")
EXPECTED_STATUS_COUNTS = {"DONE": 2, "IN PROGRESS": 6, "TODO": 38, "HUMAN-ONLY BLOCKED": 6}
SLICE_ID = re.compile(r"^[A-Z]-[0-9]{2}$")
DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
ROW = re.compile(r"^\| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$")
PROGRESS_ROW = re.compile(r"^\| ([^|]+) \| ([^|]+) \| (.*) \|$")
ALLOWED_EXTERNAL_DEPS = {"human m1n1 owner", "shipping hardware"}
HUMAN_REPOSITORY = "m1n1-omarchy"


@dataclass(frozen=True)
class Slice:
    identifier: str
    repository: str
    deliverable: str
    dependencies: tuple[str, ...]
    status: str
    line: int
    raw: str


@dataclass(frozen=True)
class Progress:
    timestamp: str
    event: str
    evidence: str
    line: int
    raw: str


def _fail(code: str, path: str, message: str) -> None:
    raise ProgramValidationError(code, path, message)


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _section(lines: list[str], heading: str, end_heading: str | None = None) -> tuple[int, int]:
    starts = [i for i, line in enumerate(lines) if line == heading]
    if len(starts) != 1:
        _fail("SECTION_MISSING_OR_DUPLICATE", "$", f"expected one {heading!r} section")
    start = starts[0]
    end = len(lines)
    if end_heading is not None:
        ends = [i for i, line in enumerate(lines) if line == end_heading]
        if len(ends) != 1 or ends[0] <= start:
            _fail("SECTION_MISSING_OR_DUPLICATE", "$", f"expected one {end_heading!r} after {heading!r}")
        end = ends[0]
    return start, end


def _parse_slices(lines: list[str]) -> list[Slice]:
    start, end = _section(lines, "## 12. Slice ledger", "## 13. Milestones and promotion gates")
    header = "| ID | Repository | Deliverable | Depends on | Status |"
    separator = "|---|---|---|---|---|"
    try:
        header_index = lines.index(header, start + 1, end)
    except ValueError:
        _fail("LEDGER_HEADER_INVALID", "PROGRAM.md:12", "slice ledger header is missing or changed")
    if header_index + 1 >= end or lines[header_index + 1] != separator:
        _fail("LEDGER_HEADER_INVALID", f"PROGRAM.md:{header_index + 2}", "slice ledger separator is invalid")
    rows: list[Slice] = []
    saw_blank = False
    for index in range(header_index + 2, end):
        line = lines[index]
        if not line:
            saw_blank = True
            continue
        if saw_blank:
            _fail("LEDGER_TRAILING_CONTENT", f"PROGRAM.md:{index + 1}", "content follows the ledger table")
        match = ROW.fullmatch(line)
        if match is None:
            _fail("LEDGER_ROW_MALFORMED", f"PROGRAM.md:{index + 1}", "slice ledger row does not match the closed grammar")
        identifier, repository, deliverable, dependency_text, status = (part.strip() for part in match.groups())
        if not SLICE_ID.fullmatch(identifier):
            _fail("SLICE_ID_INVALID", f"PROGRAM.md:{index + 1}", "slice ID must match LETTER-00")
        if status not in STATUS_VOCABULARY:
            _fail("STATUS_INVALID", f"PROGRAM.md:{index + 1}", "status is outside the closed vocabulary")
        dependencies = _parse_dependencies(dependency_text, index + 1)
        rows.append(Slice(identifier, repository, deliverable, dependencies, status, index + 1, line))
    if not rows:
        _fail("SLICE_COUNT_INVALID", "PROGRAM.md:12", "slice ledger is empty")
    if len(rows) > MAX_SLICE_ROWS:
        _fail("RESOURCE_LIMIT", "PROGRAM.md:12", "slice row limit exceeded")
    return rows


def _parse_dependencies(value: str, line: int) -> tuple[str, ...]:
    if value == "none":
        return ()
    if not value or value.startswith(",") or value.endswith(","):
        _fail("DEPENDENCY_GRAMMAR_INVALID", f"PROGRAM.md:{line}", "dependency list is malformed")
    result: list[str] = []
    for item in value.split(","):
        item = item.strip()
        if not item or item == "none":
            _fail("DEPENDENCY_GRAMMAR_INVALID", f"PROGRAM.md:{line}", "dependency list contains an empty or none item")
        if not SLICE_ID.fullmatch(item) and item not in ALLOWED_EXTERNAL_DEPS:
            _fail("UNKNOWN_DEPENDENCY", f"PROGRAM.md:{line}", f"dependency {item!r} is not a slice or closed external prerequisite")
        if item in result:
            _fail("DUPLICATE_DEPENDENCY", f"PROGRAM.md:{line}", f"dependency {item!r} is repeated")
        result.append(item)
    if len(result) > MAX_DEPENDENCIES:
        _fail("RESOURCE_LIMIT", f"PROGRAM.md:{line}", "dependency count limit exceeded")
    return tuple(result)


def _parse_progress(lines: list[str]) -> list[Progress]:
    start, end = _section(lines, "## 19. Append-only progress log")
    expected = ("| Timestamp | Event | Evidence or result |", "|---|---|---|")
    header_candidates = [i for i in range(start + 1, end) if lines[i] == expected[0]]
    if len(header_candidates) != 1:
        _fail("PROGRESS_HEADER_INVALID", f"PROGRAM.md:{start + 1}", "append-only progress header is invalid")
    header_index = header_candidates[0]
    if header_index + 1 >= end or lines[header_index + 1] != expected[1] or "Do not edit or delete existing rows. Corrections are new rows." not in lines[start:header_index]:
        _fail("PROGRESS_HEADER_INVALID", f"PROGRAM.md:{header_index + 1}", "append-only progress header is invalid")
    progress: list[Progress] = []
    for index in range(header_index + 2, end):
        line = lines[index]
        if not line:
            _fail("PROGRESS_ROW_MALFORMED", f"PROGRAM.md:{index + 1}", "blank lines are not allowed inside progress rows")
        match = PROGRESS_ROW.fullmatch(line)
        if match is None:
            _fail("PROGRESS_ROW_MALFORMED", f"PROGRAM.md:{index + 1}", "progress row does not match the closed grammar")
        timestamp, event, evidence = (part.strip() for part in match.groups())
        if not DATE.fullmatch(timestamp):
            _fail("PROGRESS_TIMESTAMP_INVALID", f"PROGRAM.md:{index + 1}", "timestamp must be an ISO calendar date")
        if not event or not evidence:
            _fail("PROGRESS_ROW_EMPTY", f"PROGRAM.md:{index + 1}", "event and evidence must be non-empty")
        progress.append(Progress(timestamp, event, evidence, index + 1, line))
    if len(progress) > MAX_PROGRESS_ROWS:
        _fail("RESOURCE_LIMIT", "PROGRAM.md:19", "progress row limit exceeded")
    return progress


def _validate_graph(slices: list[Slice]) -> tuple[set[str], str]:
    identifiers = {item.identifier for item in slices}
    if len(slices) != EXPECTED_SLICE_COUNT or len(identifiers) != len(slices):
        _fail("SLICE_COUNT_OR_DUPLICATE", "PROGRAM.md:12", f"expected exactly {EXPECTED_SLICE_COUNT} unique slice rows")
    by_id = {item.identifier: item for item in slices}
    for item in slices:
        for dependency in item.dependencies:
            if dependency in ALLOWED_EXTERNAL_DEPS:
                continue
            if dependency not in identifiers:
                _fail("UNKNOWN_DEPENDENCY", f"PROGRAM.md:{item.line}", f"dependency {dependency!r} is not in the ledger")
            if dependency == item.identifier:
                _fail("SELF_DEPENDENCY", f"PROGRAM.md:{item.line}", "slice cannot depend on itself")
    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(identifier: str, depth: int) -> None:
        if depth > MAX_GRAPH_DEPTH:
            _fail("RESOURCE_LIMIT", f"PROGRAM.md:{by_id[identifier].line}", "dependency graph depth limit exceeded")
        if identifier in visiting:
            _fail("DEPENDENCY_CYCLE", f"PROGRAM.md:{by_id[identifier].line}", "dependency graph contains a cycle")
        if identifier in visited:
            return
        visiting.add(identifier)
        for dependency in by_id[identifier].dependencies:
            if dependency in by_id:
                walk(dependency, depth + 1)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in sorted(identifiers):
        walk(identifier, 0)
    consumers = Counter(dependency for item in slices for dependency in item.dependencies if dependency in identifiers)
    roots = {identifier for identifier in identifiers if consumers[identifier] == 0}
    if roots != {"F-07"}:
        _fail("EXTRA_TERMINAL", "PROGRAM.md:12", "F-07 must be the single stable-authority graph root")
    closure: set[str] = set()
    stack = ["F-07"]
    while stack:
        identifier = stack.pop()
        if identifier in closure:
            continue
        closure.add(identifier)
        stack.extend(dependency for dependency in by_id[identifier].dependencies if dependency in by_id)
        if len(closure) > EXPECTED_SLICE_COUNT:
            _fail("CLOSURE_INVALID", "PROGRAM.md:F-07", "F-07 closure exceeds the ledger")
    if closure != identifiers or len(closure) != EXPECTED_SLICE_COUNT or "P-03" not in closure:
        _fail("F07_CLOSURE_INCOMPLETE", "PROGRAM.md:F-07", "F-07 closure must contain exactly all 52 slices including P-03")
    f07 = by_id["F-07"]
    if "stable-promotion" not in f07.deliverable or "sole" not in f07.deliverable:
        _fail("F07_AUTHORITY_INVALID", f"PROGRAM.md:{f07.line}", "F-07 must explicitly remain the sole stable-promotion terminal")
    for item in slices:
        if ("stable-promotion" in item.deliverable.lower() or ("stable" in item.deliverable.lower() and "promotion" in item.deliverable.lower())) and item.identifier != "F-07":
            _fail("ALTERNATE_STABLE_AUTHORITY", f"PROGRAM.md:{item.line}", "stable promotion may only be described by F-07")
    return closure, "F-07"


def _validate_ownership(slices: list[Slice], text: str) -> None:
    human_rows = [item for item in slices if item.repository == HUMAN_REPOSITORY]
    if not human_rows or "human-produced opaque" not in text or "agents must not inspect" not in text.lower():
        _fail("HUMAN_ONLY_FENCE_MISSING", "PROGRAM.md:216", "m1n1 ownership and opaque-agent fence are required")
    for item in slices:
        has_human_dep = "human m1n1 owner" in item.dependencies
        if item.repository == HUMAN_REPOSITORY:
            if item.status != "HUMAN-ONLY BLOCKED" or not has_human_dep or not item.deliverable.lower().startswith("human owner"):
                _fail("HUMAN_ONLY_CONSTRAINT", f"PROGRAM.md:{item.line}", "m1n1 rows require HUMAN-ONLY BLOCKED, Human owner, and the owner dependency")
        elif has_human_dep:
            _fail("HUMAN_ONLY_CONSTRAINT", f"PROGRAM.md:{item.line}", "human m1n1 owner dependency is reserved for m1n1 rows")


def _validate_statuses(slices: list[Slice], lock: dict) -> None:
    counts = Counter(item.status for item in slices)
    if dict(counts) != EXPECTED_STATUS_COUNTS:
        _fail("STATUS_CENSUS_INVALID", "PROGRAM.md:12", f"current status census must be {EXPECTED_STATUS_COUNTS}")
    expected = lock.get("status_by_id")
    if not isinstance(expected, dict) or {item.identifier: item.status for item in slices} != expected:
        _fail("STATUS_LAUNDERING", "PROGRAM.md:12", "slice statuses differ from the immutable current census baseline")
    if any(item.status == "DONE" and item.identifier not in {"F-00", "F-01"} for item in slices):
        _fail("DONE_INFERENCE_FORBIDDEN", "PROGRAM.md:12", "DONE cannot be inferred for a slice without coordinator history")


def _validate_progress(slices: list[Slice], progress: list[Progress], lock: dict) -> None:
    historical = lock.get("progress_rows")
    if not isinstance(historical, list) or len(progress) < len(historical):
        _fail("HISTORY_DELETED", "PROGRAM.md:19", "historical progress rows may not be deleted")
    for index, expected in enumerate(historical):
        if not isinstance(expected, dict) or not isinstance(expected.get("sha256"), str):
            _fail("BASELINE_INVALID", "data/program/program-integrity.lock.json", "baseline progress row is invalid")
        if _sha256(progress[index].raw) != expected["sha256"]:
            _fail("HISTORY_EDITED_OR_REORDERED", f"PROGRAM.md:{progress[index].line}", "historical progress rows must remain byte-identical and ordered")
    baseline_count = len(historical)
    by_id = {item.identifier: item for item in slices}
    for item in progress[baseline_count:]:
        if "release-ready" in item.event.lower() or "release-ready" in item.evidence.lower():
            _fail("RELEASE_READY_INFERENCE", f"PROGRAM.md:{item.line}", "progress records may not claim release-ready state")
        mentioned = set(re.findall(r"\b[A-Z]-[0-9]{2}\b", item.raw))
        for identifier in mentioned:
            if identifier not in by_id:
                _fail("UNKNOWN_PROGRESS_SLICE", f"PROGRAM.md:{item.line}", f"progress record mentions unknown slice {identifier}")
            for status in STATUS_VOCABULARY:
                if re.search(rf"\b{re.escape(status)}\b", item.raw) and by_id[identifier].status != status:
                    _fail("FALSE_STATUS_EVIDENCE", f"PROGRAM.md:{item.line}", f"progress record claims {identifier} is {status}, but the ledger disagrees")
    evidence = lock.get("status_evidence")
    if not isinstance(evidence, dict):
        _fail("BASELINE_INVALID", "data/program/program-integrity.lock.json", "status evidence baseline is missing")
    for identifier, refs in evidence.items():
        if identifier not in by_id or by_id[identifier].status not in {"DONE", "IN PROGRESS"}:
            continue
        if not isinstance(refs, list) or not refs or any(not isinstance(ref, int) or ref < 0 or ref >= len(progress) for ref in refs):
            _fail("STATUS_EVIDENCE_INVALID", "PROGRAM.md:19", f"{identifier} lacks append-only progress evidence")
        for ref in refs:
            if ref >= baseline_count:
                _fail("STATUS_EVIDENCE_INVALID", f"PROGRAM.md:{progress[ref].line}", f"{identifier} evidence is outside the immutable baseline")
            if _sha256(progress[ref].raw) != historical[ref]["sha256"]:
                _fail("HISTORY_EDITED_OR_REORDERED", f"PROGRAM.md:{progress[ref].line}", "status evidence row is not immutable")


def build_lock(slices: list[Slice], progress: list[Progress]) -> dict:
    """Build a deterministic lock from the current PROGRAM parse."""
    evidence: dict[str, list[int]] = {}
    for item in slices:
        if item.status not in {"DONE", "IN PROGRESS"}:
            continue
        refs = [index for index, row in enumerate(progress) if re.search(rf"\b{re.escape(item.identifier)}\b", row.raw)]
        if not refs and item.identifier == "F-00":
            refs = [0]
        if not refs and item.identifier == "F-01":
            refs = [2]
        if refs:
            evidence[item.identifier] = refs
    return {
        "version": 1,
        "expected_slice_count": EXPECTED_SLICE_COUNT,
        "expected_status_counts": EXPECTED_STATUS_COUNTS,
        "status_by_id": {item.identifier: item.status for item in slices},
        "slice_structure": [
            {"id": item.identifier, "repository": item.repository, "deliverable": item.deliverable, "depends_on": list(item.dependencies)}
            for item in slices
        ],
        "progress_rows": [{"sha256": _sha256(item.raw)} for item in progress],
        "status_evidence": evidence,
    }


def _validate_lock_structure(slices: list[Slice], lock: dict) -> None:
    structure = lock.get("slice_structure")
    actual = [{"id": item.identifier, "repository": item.repository, "deliverable": item.deliverable, "depends_on": list(item.dependencies)} for item in slices]
    if structure != actual:
        _fail("SLICE_HISTORY_EDITED_OR_REORDERED", "PROGRAM.md:12", "historical slice structure must remain ordered and immutable")
    if lock.get("expected_slice_count") != EXPECTED_SLICE_COUNT or lock.get("expected_status_counts") != EXPECTED_STATUS_COUNTS:
        _fail("BASELINE_INVALID", "data/program/program-integrity.lock.json", "baseline census constants are invalid")


def validate_program(program_path: str | Path, lock_path: str | Path) -> dict:
    path = Path(program_path)
    lock_file = Path(lock_path)
    try:
        raw = path.read_bytes()
    except OSError:
        _fail("IO_FAILURE", str(path), "PROGRAM.md could not be read")
    if len(raw) > MAX_PROGRAM_BYTES:
        _fail("RESOURCE_LIMIT", str(path), "PROGRAM.md byte limit exceeded")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _fail("PROGRAM_ENCODING_INVALID", str(path), "PROGRAM.md must be UTF-8")
    lines = text.splitlines()
    if len(lines) > MAX_PROGRESS_ROWS + 1000:
        _fail("RESOURCE_LIMIT", str(path), "PROGRAM.md line limit exceeded")
    try:
        lock = json.loads(lock_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _fail("BASELINE_INVALID", str(lock_file), "integrity baseline could not be read")
    if not isinstance(lock, dict):
        _fail("BASELINE_INVALID", str(lock_file), "integrity baseline must be an object")
    slices = _parse_slices(lines)
    progress = _parse_progress(lines)
    closure, authority = _validate_graph(slices)
    _validate_ownership(slices, text)
    _validate_statuses(slices, lock)
    _validate_lock_structure(slices, lock)
    _validate_progress(slices, progress, lock)
    return {
        "decision": "ACCEPT",
        "authority": authority,
        "closure_count": len(closure),
        "closure_includes_p03": "P-03" in closure,
        "release_ready": False,
        "status_counts": {status: Counter(item.status for item in slices).get(status, 0) for status in STATUS_VOCABULARY},
        "slice_count": len(slices),
        "progress_rows": len(progress),
        "program_sha256": _sha256(raw),
        "bounded": {"max_bytes": MAX_PROGRAM_BYTES, "max_rows": MAX_SLICE_ROWS, "max_progress_rows": MAX_PROGRESS_ROWS, "max_depth": MAX_GRAPH_DEPTH},
    }


def parse_for_lock(program_path: str | Path) -> tuple[list[Slice], list[Progress]]:
    raw = Path(program_path).read_bytes()
    if len(raw) > MAX_PROGRAM_BYTES:
        _fail("RESOURCE_LIMIT", str(program_path), "PROGRAM.md byte limit exceeded")
    text = raw.decode("utf-8")
    lines = text.splitlines()
    return _parse_slices(lines), _parse_progress(lines)
