#!/usr/bin/env python3
"""Regression tests for the fail-closed formal adapter boundary."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "formal" / "fm.toml"
FIXTURE = ROOT / "formal" / "echo.py"


class FormalBoundaryTests(unittest.TestCase):
    def test_non_conforming_fixture_is_not_an_active_adapter(self) -> None:
        manifest = tomllib.loads(MANIFEST.read_text())
        rust_adapter = manifest["adapters"]["rust"]

        self.assertEqual(rust_adapter["status"], "planned")
        self.assertNotIn("command", rust_adapter)

    def test_protocol_fixture_reports_a_mismatch(self) -> None:
        trace = "formal/trace-0.itf.json"
        completed = subprocess.run(
            [sys.executable, str(FIXTURE)],
            input=json.dumps({"adapter": "rust", "traces": [trace]}),
            capture_output=True,
            check=False,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        response = json.loads(completed.stdout)
        self.assertFalse(response["success"])
        self.assertEqual(response["traces_total"], 1)
        self.assertEqual(response["traces_passed"], 0)
        self.assertEqual(len(response["mismatches"]), 1)
        self.assertEqual(response["mismatches"][0]["trace"], trace)

    def test_sixty_four_traces_fail_closed_in_original_request_order(self) -> None:
        traces = [f"formal/trace-{index}.itf.json" for index in range(64)]
        completed = subprocess.run(
            [sys.executable, str(FIXTURE)],
            input=json.dumps({"adapter": "llvm", "traces": traces}),
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        response = json.loads(completed.stdout)
        self.assertEqual(response["protocol"], "fmctl.adapter.v1")
        self.assertIs(response["success"], False)
        self.assertEqual(response["traces_total"], len(traces))
        self.assertEqual(response["traces_passed"], 0)
        self.assertEqual(
            [mismatch["trace"] for mismatch in response["mismatches"]],
            traces,
        )
        for mismatch in response["mismatches"]:
            self.assertIsNone(mismatch["step"])
            self.assertIsNone(mismatch["action"])
            self.assertEqual(
                mismatch["actual"], {"conformance": "not implemented"}
            )
        self.assertEqual(response["implementation"]["language"], "llvm")
        self.assertEqual(
            response["implementation"]["name"],
            "formal-methods-fail-closed-fixture",
        )

    def test_absent_adapter_or_trace_batch_cannot_report_false_success(self) -> None:
        for request in [
            {"adapter": "rust", "traces": []},
            {"adapter": "rust"},
            {"adapter": "", "traces": ["formal/trace-0.itf.json"]},
            {"traces": ["formal/trace-0.itf.json"]},
        ]:
            with self.subTest(request=request):
                completed = subprocess.run(
                    [sys.executable, str(FIXTURE)],
                    input=json.dumps(request),
                    capture_output=True,
                    check=False,
                    text=True,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(completed.stdout, "")
                self.assertTrue(completed.stderr)

    def test_invalid_json_never_emits_success_envelope(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(FIXTURE)],
            input="{ invalid-json ",
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")

    def test_distinct_backend_labels_do_not_promote_protocol_fixture(self) -> None:
        for adapter in ["java", "wasm", "net", "forge", "rust"]:
            with self.subTest(adapter=adapter):
                completed = subprocess.run(
                    [sys.executable, str(FIXTURE)],
                    input=json.dumps({
                        "adapter": adapter,
                        "traces": ["formal/trace-0.itf.json"],
                    }),
                    capture_output=True,
                    check=False,
                    text=True,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                payload = json.loads(completed.stdout)
                self.assertIs(payload["success"], False)
                self.assertEqual(payload["traces_passed"], 0)
                self.assertEqual(payload["implementation"]["language"], adapter)
                self.assertEqual(len(payload["mismatches"]), 1)


if __name__ == "__main__":
    unittest.main()
