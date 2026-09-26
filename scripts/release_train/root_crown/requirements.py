"""Requirement-graph admission for the root crown.

``requirements.json`` is the source of truth (stdlib JSON, canonical digests).
Its rows are transcribed from the imported RFC-0004 §48 (AC-01..AC-19) and §47
(falsifiers 1..14 -> F-01..F-14); the coverage rule refuses any drift between the
imported premise text and the rows.

The evaluated term set is the premise's (``model.release_terms``). A term bound by another
premise of the set (``model.TERM_PREMISE``, e.g. U -> RFC-0005) is admitted against that
premise: its rows cite ``<RFC>§n`` references (RFC-0005 §10), the premise member must be
imported with a recomputing sha256, and the rows sit outside RFC-0004 §47/§48 coverage.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from .model import KINDS, TERM_PREMISE, Requirement, release_terms, sha256_bytes

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


def split_ref(ref: str) -> tuple[str | None, str]:
    """``RFC-0005§7`` -> (``RFC-0005``, ``§7``); an unqualified ``§n`` -> (None, ``§n``) = RFC-0004.

    Same grammar as ``berthier.split_ref`` (RFC-0005 §10.2), without the default premise id.
    """
    head, sep, tail = ref.partition("§")
    return (head, f"§{tail}") if sep and head else (None, ref)


def _premise_set_refusals(doc: dict[str, Any], premise_set: dict[str, str], terms: tuple[str, ...]) -> list[str]:
    """Every premise member a declared term needs is imported and its bytes recompute."""
    refusals: list[str] = []
    premise = doc.get("premise")
    declared = {
        e.get("rfc_id"): e
        for e in (premise.get("set", []) if isinstance(premise, dict) and isinstance(premise.get("set"), list) else [])
        if isinstance(e, dict)
    }
    for term in terms:
        rfc = TERM_PREMISE.get(term)
        if rfc is None:
            continue
        entry = declared.get(rfc)
        if entry is None or rfc not in premise_set:
            refusals.append(f"REFUSED:REQ_PREMISE_UNBOUND:{term}:{rfc}-not-imported")
        elif sha256_bytes(premise_set[rfc].encode("utf-8")) != entry.get("sha256"):
            refusals.append(f"REFUSED:REQ_PREMISE_UNBOUND:{term}:{rfc}-sha256-mismatch")
    return refusals


def validate_requirements(
    doc: dict[str, Any],
    pins: dict[str, Any],
    rfc_text: str,
    evidence_kinds: Iterable[str],
    premise_set: dict[str, str] | None = None,
) -> list[str]:
    refusals: list[str] = []
    rows = doc.get("requirements")
    if not isinstance(rows, list) or not rows:
        return ["REFUSED:REQ_MALFORMED:requirements:empty"]
    kinds = set(evidence_kinds)
    sections = premise_sections(rfc_text)
    members = dict(premise_set or {})
    member_sections = {rfc: premise_sections(text) for rfc, text in sorted(members.items())}
    terms, term_refusals = release_terms(doc)
    refusals += term_refusals + _premise_set_refusals(doc, members, terms)
    admitted_owners = {entry["repository"] for entry in pins.get("repos", {}).values()}
    seen: dict[str, int] = {}
    premise_bound: set[str] = set()
    per_term = {term: 0 for term in terms}
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
        if row["term"] not in terms:
            refusals.append(f"REFUSED:REQ_TERM_UNBOUND:{rid}:{row['term']}")
        else:
            per_term[row["term"]] += 1
        if row["owner_repo"] not in admitted_owners:
            refusals.append(f"REFUSED:REQ_OWNER_UNADMITTED:{rid}:{row['owner_repo']}")
        term_rfc = TERM_PREMISE.get(row["term"])
        if term_rfc is not None:
            premise_bound.add(rid)
            if not any(split_ref(ref)[0] == term_rfc for ref in row["premise_refs"]):
                refusals.append(f"REFUSED:REQ_PREMISE_UNBOUND:{rid}:term {row['term']} cites no {term_rfc} section")
        for ref in row["premise_refs"]:
            rfc, section = split_ref(ref)
            if section not in (sections if rfc is None else member_sections.get(rfc, {})):
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
    for extra in sorted(declared - expected - premise_bound):
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
