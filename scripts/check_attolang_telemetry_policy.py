#!/usr/bin/env python3
"""Exhaustive *abstract* redaction-policy check, not an AttoLang runtime test.

Quint/TLC remains the authoritative model checker. This independent finite
reference enumerates all model-reachable states and mutation witnesses, then
anchors the pure AttoLang projection without pretending to run it.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path

CAPACITY = 3
ROOT = Path(__file__).resolve().parents[1]


def healthy(s: tuple[int, int, int, bool]) -> bool:
    ingested, redacted, exported, pending = s
    return (0 <= exported <= redacted <= ingested <= CAPACITY
            and (ingested == redacted + 1 if pending else ingested == redacted))


def can_export(s: tuple[int, int, int, bool]) -> bool:
    _, redacted, exported, _ = s
    return healthy(s) and redacted > exported


def next_states(s: tuple[int, int, int, bool]):
    ingested, redacted, exported, pending = s
    if not pending and ingested < CAPACITY:
        yield "ingest", (ingested + 1, redacted, exported, True)
    if pending:
        yield "redact", (ingested, redacted + 1, exported, False)
    if can_export(s):
        yield "export", (ingested, redacted, exported + 1, pending)
    yield "idle", s


def main() -> int:
    initial = (0, 0, 0, False)
    reached = {initial}
    queue = deque([initial])
    edges = set()
    while queue:
        state = queue.popleft()
        assert healthy(state), f"unsafe state: {state}"
        for action, successor in next_states(state):
            assert healthy(successor), f"{action} violated accounting: {state} -> {successor}"
            if action == "export":
                assert can_export(state), f"premature export: {state}"
                assert successor[2] == state[2] + 1
            else:
                assert successor[2] == state[2], "only export can increment exported"
            edges.add((state, action, successor))
            if successor not in reached:
                reached.add(successor)
                queue.append(successor)

    assert (1, 0, 0, True) in reached, "raw-secret witness absent"
    assert (2, 1, 0, True) in reached, "partial redaction witness absent"
    assert (3, 3, 3, False) in reached, "full throughput witness absent"
    assert not can_export((1, 0, 0, True))
    assert can_export((2, 1, 0, True)), "prior safe items remain exportable"
    assert not can_export((2, 1, 1, True)), "raw tail cannot be exported"
    for bad in [(1, 0, 1, True), (2, 3, 1, False), (4, 4, 0, False),
                (1, 1, 0, True), (2, 1, 0, False)]:
        assert not healthy(bad), f"invalid state accepted: {bad}"
        assert not can_export(bad), f"invalid state export allowed: {bad}"

    source = (ROOT / "src" / "telemetry_policy.atto").read_text()
    for required in ["define module telemetry_policy", "accounting_valid(",
                     "export_permitted(", "self_check()", "redacted > exported",
                     "ingested == redacted + 1", "exported <= redacted"]:
        assert required in source, f"AttoLang policy reference lost {required}"
    assert len(reached) > 10, "state space unexpectedly vacuous"
    print(f"PASS abstract telemetry policy: states={len(reached)} edges={len(edges)}; "
          "AttoLang compilation NOT_EXECUTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
