"""Requirement-graph admission for the v26.9.25 root crown.

``requirements.json`` is the source of truth (stdlib JSON, canonical digests).
Its rows are transcribed from the imported RFC-0004 §48 (AC-01..AC-19) and §47
(falsifiers 1..14 -> F-01..F-14); the coverage rule refuses any drift between the
imported premise text and the rows.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from .model import KINDS, TERMS, Requirement

_HEADING = re.compile(r"^(#{1,2}) (\d+(?:\.\d+)?)\.? ", re.MULTILINE)
_AC = re.compile(r"^AC-(\d{2}) ", re.MULTILINE)
_REQUIRED_FIELDS = (
    "id",
    "kind",
    "term",
    "owner_repo",
    "acceptance",
    "evidence_kind",
    "evidence_locator",
    "premise_refs",
)


def premise_sections(text: str) -> dict[str, str]:
    """Numbered RFC sections ``§n`` / ``§n.m`` -> normalized text (heading to next numbered heading)."""
    matches = list(_HEADING.finditer(text))
    out: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.start() : end]
        normalized = "\n".join(line.rstrip() for line in body.strip().splitlines())
        key = f"§{match.group(2)}"
        # The operator RFC is carried once; a repeated number would be an ambiguous premise.
        if key in out:
            out[key] = out[key] + "\n" + normalized
        else:
            out[key] = normalized
    return out


def rfc_requirement_ids(text: str) -> set[str]:
    """AC ids from §48 and falsifier ids (F-NN) from the numbered list of §47."""
    sections = premise_sections(text)
    ids = {f"AC-{m.group(1)}" for m in _AC.finditer(sections.get("§48", ""))}
    for line in sections.get("§47", "").splitlines():
        m = re.match(r"^(\d+)\. ", line)
        if m:
            ids.add(f"F-{int(m.group(1)):02d}")
    return ids


def load_rows(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def to_requirement(row: dict[str, Any]) -> Requirement:
    return Requirement(
        id=row["id"],
        kind=row["kind"],
        term=row["term"],
        owner_repo=row["owner_repo"],
        acceptance=row["acceptance"],
        evidence_kind=row["evidence_kind"],
        evidence_locator=row["evidence_locator"],
        premise_refs=tuple(row["premise_refs"]),
        depends_on=tuple(row.get("depends_on", ())),
        required=bool(row.get("required", True)),
    )


def validate_requirements(
    doc: dict[str, Any],
    pins: dict[str, Any],
    rfc_text: str,
    evidence_kinds: Iterable[str],
) -> list[str]:
    refusals: list[str] = []
    rows = doc.get("requirements")
    if not isinstance(rows, list) or not rows:
        return ["REFUSED:REQ_MALFORMED:requirements:empty"]
    kinds = set(evidence_kinds)
    sections = premise_sections(rfc_text)
    admitted_owners = {entry["repository"] for entry in pins.get("repos", {}).values()}
    seen: dict[str, int] = {}
    per_term = {term: 0 for term in TERMS}
    well_formed: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        rid = row.get("id", f"requirements[{index}]") if isinstance(row, dict) else f"requirements[{index}]"
        if not isinstance(row, dict):
            refusals.append(f"REFUSED:REQ_MALFORMED:{rid}:row")
            continue
        bad = [
            key
            for key in _REQUIRED_FIELDS
            if key not in row or (key != "premise_refs" and (not isinstance(row[key], str) or not row[key].strip()))
        ]
        if not bad and (not isinstance(row["premise_refs"], list) or not row["premise_refs"]):
            bad.append("premise_refs")
        if not bad and row["kind"] not in KINDS:
            bad.append("kind")
        if not bad and not isinstance(row.get("required", True), bool):
            bad.append("required")
        if bad:
            refusals.extend(f"REFUSED:REQ_MALFORMED:{rid}:{key}" for key in bad)
            continue
        seen[rid] = seen.get(rid, 0) + 1
        well_formed.append(row)
        if row["term"] not in TERMS:
            refusals.append(f"REFUSED:REQ_TERM_UNBOUND:{rid}:{row['term']}")
        else:
            per_term[row["term"]] += 1
        if row["owner_repo"] not in admitted_owners:
            refusals.append(f"REFUSED:REQ_OWNER_UNADMITTED:{rid}:{row['owner_repo']}")
        for ref in row["premise_refs"]:
            if ref not in sections:
                refusals.append(f"REFUSED:REQ_PREMISE_UNBOUND:{rid}:{ref}")
        if row["evidence_kind"] not in kinds:
            refusals.append(f"REFUSED:REQ_KIND_UNKNOWN:{rid}:{row['evidence_kind']}")
    for rid, count in sorted(seen.items()):
        if count > 1:
            refusals.append(f"REFUSED:REQ_DUPLICATE_ID:{rid}")
    for term, count in per_term.items():
        if count == 0:
            refusals.append(f"REFUSED:REQ_TERM_UNBOUND:{term}:no-requirement")
    declared = set(seen)
    expected = rfc_requirement_ids(rfc_text)
    for missing in sorted(expected - declared):
        refusals.append(f"REFUSED:REQ_COVERAGE_GAP:{missing}:not-in-requirements")
    for extra in sorted(declared - expected):
        refusals.append(f"REFUSED:REQ_COVERAGE_GAP:{extra}:not-in-premise")
    ids = set(seen)
    for row in well_formed:
        for dep in row.get("depends_on", []):
            if dep not in ids:
                refusals.append(f"REFUSED:REQ_MALFORMED:{row['id']}:depends_on={dep}")
    return sorted(set(refusals))


def load_requirements(path: str | Path) -> tuple[Requirement, ...]:
    doc = load_rows(path)
    return tuple(to_requirement(row) for row in doc["requirements"])
