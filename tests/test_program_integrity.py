from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from omarchy_program import ProgramValidationError, validate_program

ROOT = Path(__file__).parents[1]
PROGRAM = ROOT / "PROGRAM.md"
LOCK = ROOT / "data/program/program-integrity.lock.json"


class ProgramIntegrityTests(unittest.TestCase):
    def run_mutation(self, mutation):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            program = root / "PROGRAM.md"
            lock = root / "lock.json"
            shutil.copy2(PROGRAM, program)
            shutil.copy2(LOCK, lock)
            mutation(program)
            with self.assertRaises(ProgramValidationError) as caught:
                validate_program(program, lock)
            return caught.exception

    def mutate_text(self, needle, replacement):
        def mutation(path):
            text = path.read_text()
            self.assertEqual(text.count(needle), 1)
            path.write_text(text.replace(needle, replacement))

        return mutation

    def test_current_program_has_closed_census_and_complete_f07_closure(self):
        result = validate_program(PROGRAM, LOCK)
        self.assertEqual(result["decision"], "ACCEPT")
        self.assertEqual(result["slice_count"], 52)
        self.assertEqual(result["closure_count"], 52)
        self.assertTrue(result["closure_includes_p03"])
        self.assertFalse(result["release_ready"])
        self.assertEqual(result["status_counts"], {"DONE": 2, "IN PROGRESS": 6, "TODO": 38, "HUMAN-ONLY BLOCKED": 6})

    def test_cli_output_is_stable_json_and_never_infers_release_ready(self):
        command = [sys.executable, "-m", "omarchy_program", "--program", str(PROGRAM), "--lock", str(LOCK)]
        first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
        second = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(json.loads(first.stdout)["release_ready"], False)
        self.assertEqual(first.stderr, "")

    def test_hostile_graph_and_ledger_cases_fail_closed(self):
        cases = [
            ("| F-05 | omarchy-apple-platform | Build candidate assembly, hostile fixtures, generated consumer bindings, and cross-repository compatibility validator | F-03, F-04, F-06, Q-00, Q-01 | TODO |", "| F-05 | omarchy-apple-platform | Build candidate assembly, hostile fixtures, generated consumer bindings, and cross-repository compatibility validator | F-03, UNKNOWN-99, F-06, Q-00, Q-01 | TODO |"),
            ("| F-03 | omarchy-apple-platform | Establish signed metadata trust root, key roles, expiry, rotation, and offline recovery | F-02 | IN PROGRESS |", "| F-03 | omarchy-apple-platform | Establish signed metadata trust root, key roles, expiry, rotation, and offline recovery | F-02, F-02 | IN PROGRESS |"),
            ("| F-03 | omarchy-apple-platform | Establish signed metadata trust root, key roles, expiry, rotation, and offline recovery | F-02 | IN PROGRESS |", "| F-03 | omarchy-apple-platform | Establish signed metadata trust root, key roles, expiry, rotation, and offline recovery | F-03 | IN PROGRESS |"),
            ("| F-03 | omarchy-apple-platform | Establish signed metadata trust root, key roles, expiry, rotation, and offline recovery | F-02 | IN PROGRESS |", "| F-02 | omarchy-apple-platform | Establish signed metadata trust root, key roles, expiry, rotation, and offline recovery | F-02 | IN PROGRESS |"),
            ("| F-03 | omarchy-apple-platform | Establish signed metadata trust root, key roles, expiry, rotation, and offline recovery | F-02 | IN PROGRESS |", "| F-03 | omarchy-apple-platform | Establish signed metadata trust root, key roles, expiry, rotation, and offline recovery | F-02 | DONE |"),
            ("| P-03 | omarchy-mac | Complete command/application ARM parity census and tracked porting queue | F-01 | IN PROGRESS |", "| P-03 | omarchy-mac | Complete command/application ARM parity census and tracked porting queue | F-01 | TODO |"),
        ]
        expected = {"UNKNOWN_DEPENDENCY", "DUPLICATE_DEPENDENCY", "SELF_DEPENDENCY", "STATUS_LAUNDERING", "STATUS_CENSUS_INVALID", "SLICE_COUNT_OR_DUPLICATE"}
        for needle, replacement in cases:
            error = self.run_mutation(self.mutate_text(needle, replacement))
            self.assertIn(error.code, expected, (needle, error.code))

    def test_missing_slice_and_f07_closure_omission_are_rejected(self):
        def remove_row(path):
            text = path.read_text()
            row = "| P-03 | omarchy-mac | Complete command/application ARM parity census and tracked porting queue | F-01 | IN PROGRESS |\n"
            self.assertEqual(text.count(row), 1)
            path.write_text(text.replace(row, ""))

        error = self.run_mutation(remove_row)
        self.assertIn(error.code, {"SLICE_COUNT_OR_DUPLICATE", "SLICE_HISTORY_EDITED_OR_REORDERED"})
        error = self.run_mutation(self.mutate_text("F-05, P-03, P-05, I-09, B-04, Q-04, Q-05, Q-06, Q-07, Q-08", "F-05, P-05, I-09, B-04, Q-04, Q-05, Q-06, Q-07, Q-08"))
        self.assertIn(error.code, {"F07_CLOSURE_INCOMPLETE", "EXTRA_TERMINAL", "SLICE_HISTORY_EDITED_OR_REORDERED"})

    def test_progress_rows_are_append_only_and_malformed_markdown_is_rejected(self):
        def edit_history(path):
            text = path.read_text()
            path.write_text(text.replace("Organization and repositories created", "Organization and repositories DELETED", 1))

        self.assertEqual(self.run_mutation(edit_history).code, "HISTORY_EDITED_OR_REORDERED")

        def delete_history(path):
            lines = path.read_text().splitlines(True)
            target = next(line for line in lines if "Repository ancestry verified" in line)
            lines.remove(target)
            path.write_text("".join(lines))

        self.assertEqual(self.run_mutation(delete_history).code, "HISTORY_DELETED")

        def reorder_history(path):
            lines = path.read_text().splitlines(True)
            first = next(i for i, line in enumerate(lines) if "Organization and repositories created" in line)
            second = next(i for i, line in enumerate(lines) if "Repository ancestry verified" in line)
            lines[first], lines[second] = lines[second], lines[first]
            path.write_text("".join(lines))

        self.assertEqual(self.run_mutation(reorder_history).code, "HISTORY_EDITED_OR_REORDERED")
        def malformed_header(path):
            text = path.read_text()
            marker = "| Timestamp | Event | Evidence or result |\n|---|---|---|"
            self.assertEqual(text.count(marker), 1)
            path.write_text(text.replace(marker, "| Timestamp | Event | Evidence or result |\n| --- | --- | --- |", 1))

        self.assertEqual(self.run_mutation(malformed_header).code, "PROGRESS_HEADER_INVALID")

        def false_done(path):
            with path.open("a") as stream:
                stream.write("| 2026-09-03 | F-02 is DONE | forged completion evidence |\n")

        self.assertEqual(self.run_mutation(false_done).code, "FALSE_STATUS_EVIDENCE")

    def test_human_only_and_extra_terminal_guards_bite(self):
        error = self.run_mutation(self.mutate_text("B-01, human m1n1 owner", "B-01"))
        self.assertIn(error.code, {"HUMAN_ONLY_CONSTRAINT", "SLICE_HISTORY_EDITED_OR_REORDERED"})
        error = self.run_mutation(self.mutate_text("F-05, P-03, P-05, I-09, B-04, Q-04, Q-05, Q-06, Q-07, Q-08", "P-03, P-05, I-09, B-04, Q-04, Q-05, Q-06, Q-07, Q-08"))
        self.assertIn(error.code, {"EXTRA_TERMINAL", "F07_CLOSURE_INCOMPLETE", "SLICE_HISTORY_EDITED_OR_REORDERED"})


if __name__ == "__main__":
    unittest.main()
