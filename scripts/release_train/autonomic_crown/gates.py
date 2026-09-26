"""RFC-0005 §7 gate table: transcription court + gate-result admission.

``gates.json`` is transcribed from the imported RFC-0005 §7 table. ``project`` re-derives
the rows from the premise text; any difference (missing, extra or altered row) is
``REFUSED:GATE_COVERAGE_GAP``. ``admit`` enforces §7's last rule: a gate is PASS only
with an evidence digest (``GATE_PASS_WITHOUT_EVIDENCE`` otherwise), and every non-PASS
gate carries a typed code.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from scripts.release_train.root_crown.requirements import premise_sections

from .model import CODES, GATE_IDS, GATE_STATES, SCHEMA_GATES, Finding, GateResult

FIELDS = ("id", "name", "metric", "threshold", "evidence_kind")
_ROW = re.compile(r"^\| (U-\d{2}) \|(.*)\|\s*$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def project(rfc_text: str) -> dict[str, Any]:
    """The gate rows of the RFC-0005 §7 table, in table order."""
    rows = []
    for line in premise_sections(rfc_text).get("§7", "").splitlines():
        m = _ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(2).split("|")]
        if len(cells) != len(FIELDS) - 1:
            continue
        rows.append(dict(zip(FIELDS, [m.group(1), *cells])))
    return {
        "schema": SCHEMA_GATES,
        "source": "RFC-0005 §7",
        "gates": rows,
    }


def coverage(doc: dict[str, Any], rfc_text: str) -> list[Finding]:
    """GATE_COVERAGE_GAP for every gate row that differs from the premise table."""
    expected = {r["id"]: r for r in project(rfc_text)["gates"]}
    findings: list[Finding] = []
    if set(expected) != set(GATE_IDS):
        findings.append(Finding("GATE_COVERAGE_GAP", "RFC-0005§7", f"premise table ids={sorted(expected)}"))
    rows = doc.get("gates") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        return findings + [Finding("GATE_COVERAGE_GAP", "gates.json", "gates is not a list")]
    seen: dict[str, dict[str, Any]] = {}
    for row in rows:
        gid = row.get("id") if isinstance(row, dict) else None
        if not isinstance(gid, str) or gid in seen:
            findings.append(Finding("GATE_COVERAGE_GAP", str(gid), "malformed or duplicate row"))
            continue
        seen[gid] = row
    for gid in sorted(set(expected) - set(seen)):
        findings.append(Finding("GATE_COVERAGE_GAP", gid, "in premise, not in gates.json"))
    for gid in sorted(set(seen) - set(expected)):
        findings.append(Finding("GATE_COVERAGE_GAP", gid, "in gates.json, not in premise"))
    for gid in sorted(set(seen) & set(expected)):
        for key in FIELDS:
            if seen[gid].get(key) != expected[gid][key]:
                findings.append(
                    Finding("GATE_COVERAGE_GAP", gid, f"{key}={seen[gid].get(key)!r} premise={expected[gid][key]!r}")
                )
    return findings


def admit(results: Iterable[GateResult]) -> list[Finding]:
    """A gate result set is admissible only if total, typed and evidence-backed on PASS."""
    findings: list[Finding] = []
    by_id = {r.id: r for r in results}
    for gid in GATE_IDS:
        r = by_id.get(gid)
        if r is None:
            findings.append(Finding("GATE_COVERAGE_GAP", gid, "no gate result"))
            continue
        if r.state not in GATE_STATES:
            findings.append(Finding("GATE_COVERAGE_GAP", gid, f"state={r.state}"))
        elif r.state == "PASS":
            ev = r.evidence or {}
            if not _DIGEST.match(str(ev.get("digest", ""))):
                findings.append(Finding("GATE_PASS_WITHOUT_EVIDENCE", gid, "PASS with no evidence digest"))
        elif r.code not in CODES:
            findings.append(Finding("GATE_COVERAGE_GAP", gid, f"{r.state} without a typed code"))
    return findings
