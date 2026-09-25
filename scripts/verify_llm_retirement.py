#!/usr/bin/env python3
"""Validate the LLM retirement map, compute LDR/IRR, and select the retirement frontier.

The map (catalog/llm-retirement.toml) records reachable edges that need open-ended LLM
reasoning and how far each has moved toward deterministic machinery. This verifier:

* checks each edge's claimed ladder state against the evidence that state requires, and
  that every evidence path exists at the subject (a claim is not evidence);
* computes LLMResidue, LDR, and, against a git baseline, IRR plus a monotonic ratchet
  (no deleted edge, no unexplained ladder regression);
* replaces the "what should this session retire next" judgment with a deterministic
  argmax over frequency * llm_cost * reuse * formalizability.

Retirement state is not component standing and never promotes anything to ALIVE.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAP_RELPATH = "catalog/llm-retirement.toml"
SCHEMA = "chateco.llm-retirement-map.v1"

EXPECTED_STATES = [
    "UNKNOWN",
    "LLM_ONLY",
    "FORMALIZATION_CANDIDATE",
    "MACHINE_CANDIDATE",
    "MACHINE_PARTIAL",
    "MACHINE_VERIFIED",
    "LLM_RETIRED",
]
EXPECTED_CLOSED = {"MACHINE_VERIFIED", "LLM_RETIRED"}
SCORE_FIELDS = ("frequency", "llm_cost", "reuse", "formalizability")
SCORE_BASES = {"ESTIMATED", "MEASURED"}
REQUIRED_REFUSALS = {
    "EVIDENCE_PATH_MISSING",
    "STATE_EVIDENCE_INSUFFICIENT",
    "LLM_MECHANISM_CLOSED",
    "TERMINAL_RESIDUAL_ADVANCED",
    "SELF_EVIDENCE",
    "LADDER_REGRESSION",
    "EDGE_DELETED",
}


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def validate_map(doc: dict[str, Any], root: Path) -> list[str]:
    """Return typed refusals for the map; an empty list means the map is admissible."""
    errors: list[str] = []

    if doc.get("schema") != SCHEMA:
        errors.append(f"MAP_INVALID:schema must be {SCHEMA}")
    try:
        dt.date.fromisoformat(str(doc.get("observed_at")))
    except ValueError:
        errors.append("MAP_INVALID:observed_at must be an ISO date")

    ladder = doc.get("ladder", {})
    states = ladder.get("states")
    if states != EXPECTED_STATES:
        errors.append("MAP_INVALID:ladder.states must equal the retirement ladder in order")
        return errors
    if set(ladder.get("closed", [])) != EXPECTED_CLOSED:
        errors.append("MAP_INVALID:ladder.closed must be MACHINE_VERIFIED and LLM_RETIRED")
    requires: dict[str, list[str]] = ladder.get("requires", {})
    unknown_states = sorted(set(requires) - set(states))
    if unknown_states:
        errors.append(f"MAP_INVALID:ladder.requires names unknown states: {', '.join(unknown_states)}")
    path_fields = set(ladder.get("path_fields", {}).get("fields", []))

    mechanisms: dict[str, str] = doc.get("mechanisms", {})
    if mechanisms.get("semantic-unknown") != "LLM":
        errors.append("MAP_INVALID:semantic-unknown must be the only LLM mechanism")
    llm_classes = sorted(k for k, v in mechanisms.items() if v == "LLM" and k != "semantic-unknown")
    if llm_classes:
        errors.append(f"MAP_INVALID:known residue classes route to LLM: {', '.join(llm_classes)}")

    terminal = set(doc.get("refusals", {}).get("terminal", []))
    missing_refusals = sorted(REQUIRED_REFUSALS - terminal)
    if missing_refusals:
        errors.append(f"MAP_INVALID:missing terminal refusals: {', '.join(missing_refusals)}")

    seen: set[str] = set()
    for index, edge in enumerate(doc.get("edge", [])):
        edge_id = edge.get("id")
        if not isinstance(edge_id, str) or not edge_id.startswith("edge:"):
            errors.append(f"MAP_INVALID:edge[{index}] requires an id starting with edge:")
            continue
        if edge_id in seen:
            errors.append(f"MAP_INVALID:duplicate edge id {edge_id}")
            continue
        seen.add(edge_id)
        errors.extend(_validate_edge(edge, states, requires, path_fields, mechanisms, root))

    return errors


def _validate_edge(
    edge: dict[str, Any],
    states: list[str],
    requires: dict[str, list[str]],
    path_fields: set[str],
    mechanisms: dict[str, str],
    root: Path,
) -> list[str]:
    errors: list[str] = []
    edge_id = edge["id"]

    for field in ("title", "owner"):
        if not _present(edge.get(field)):
            errors.append(f"MAP_INVALID:{edge_id} requires {field}")

    residue_class = edge.get("residue_class")
    if residue_class not in mechanisms:
        errors.append(f"MAP_INVALID:{edge_id} residue_class {residue_class!r} is not a declared class")
    elif edge.get("mechanism") != mechanisms[residue_class]:
        errors.append(f"MAP_INVALID:{edge_id} mechanism must be {mechanisms[residue_class]}")

    for field in SCORE_FIELDS:
        value = edge.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
            errors.append(f"MAP_INVALID:{edge_id} {field} must be an integer 1..5")
    if edge.get("score_basis") not in SCORE_BASES:
        errors.append(f"MAP_INVALID:{edge_id} score_basis must be ESTIMATED or MEASURED")

    state = edge.get("retirement_state")
    if state not in states:
        errors.append(f"MAP_INVALID:{edge_id} retirement_state {state!r} is not on the ladder")
        return errors
    rank = states.index(state)

    if edge.get("mechanism") == "LLM" and rank > states.index("LLM_ONLY"):
        errors.append(f"LLM_MECHANISM_CLOSED:{edge_id} routes to LLM but claims {state}")
    if edge.get("terminal_residual") is True and rank > states.index("LLM_ONLY"):
        errors.append(f"TERMINAL_RESIDUAL_ADVANCED:{edge_id} is the admitted residual; split recurrences into new edges")

    for ladder_state in states[1 : rank + 1]:
        for field in requires.get(ladder_state, []):
            if not _present(edge.get(field)):
                errors.append(f"STATE_EVIDENCE_INSUFFICIENT:{edge_id} claims {state} without {field}")

    for field in sorted(path_fields):
        for relpath in _as_list(edge.get(field)):
            if not isinstance(relpath, str) or not relpath:
                errors.append(f"MAP_INVALID:{edge_id} {field} entries must be repository paths")
                continue
            if Path(relpath).as_posix() == MAP_RELPATH:
                errors.append(f"SELF_EVIDENCE:{edge_id} {field} cites the retirement map itself")
                continue
            resolved = (root / relpath).resolve()
            if root.resolve() not in resolved.parents or not resolved.exists():
                errors.append(f"EVIDENCE_PATH_MISSING:{edge_id} {field} {relpath}")

    return errors


def _rank(doc: dict[str, Any], edge: dict[str, Any]) -> int:
    return doc["ladder"]["states"].index(edge["retirement_state"])


def metrics(doc: dict[str, Any]) -> dict[str, Any]:
    closed = set(doc["ladder"]["closed"])
    edges = doc.get("edge", [])
    histogram = {state: 0 for state in doc["ladder"]["states"]}
    for edge in edges:
        histogram[edge["retirement_state"]] += 1
    residue = sum(1 for edge in edges if edge["retirement_state"] not in closed)
    return {
        "observed_at": doc["observed_at"],
        "edges": len(edges),
        "closed": len(edges) - residue,
        "llm_residue": residue,
        "ldr": round(residue / len(edges), 4) if edges else 0.0,
        "histogram": histogram,
    }


def score(edge: dict[str, Any]) -> int:
    result = 1
    for field in SCORE_FIELDS:
        result *= edge[field]
    return result


def frontier(doc: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    """SELECT argmax_e frequency*llm_cost*reuse*formalizability over reachable open edges."""
    closed = set(doc["ladder"]["closed"])
    candidates = [
        edge
        for edge in doc.get("edge", [])
        if edge["retirement_state"] not in closed
        and edge.get("terminal_residual") is not True
        and not _present(edge.get("blocked"))
    ]
    candidates.sort(key=lambda edge: (-score(edge), edge["id"]))
    return [
        {
            "id": edge["id"],
            "score": score(edge),
            "score_basis": edge["score_basis"],
            "retirement_state": edge["retirement_state"],
            "mechanism": edge["mechanism"],
        }
        for edge in candidates[:limit]
    ]


def compare(before: dict[str, Any], after: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    """Ratchet `after` against `before`; return refusals and the IRR report."""
    errors: list[str] = []
    before_edges = {edge["id"]: edge for edge in before.get("edge", [])}
    after_edges = {edge["id"]: edge for edge in after.get("edge", [])}

    for edge_id in sorted(set(before_edges) - set(after_edges)):
        errors.append(f"EDGE_DELETED:{edge_id} (residue is retired on the ladder, never deleted)")

    for edge_id in sorted(set(before_edges) & set(after_edges)):
        old, new = before_edges[edge_id], after_edges[edge_id]
        if _rank(after, new) < _rank(before, old) and not _present(new.get("regression_reason")):
            errors.append(
                f"LADDER_REGRESSION:{edge_id} {old['retirement_state']} -> "
                f"{new['retirement_state']} without regression_reason"
            )

    m_before, m_after = metrics(before), metrics(after)
    days = (
        dt.date.fromisoformat(str(after["observed_at"]))
        - dt.date.fromisoformat(str(before["observed_at"]))
    ).days
    delta_closed = m_after["closed"] - m_before["closed"]
    report = {
        "baseline_observed_at": m_before["observed_at"],
        "delta_closed": delta_closed,
        "delta_llm_residue": m_after["llm_residue"] - m_before["llm_residue"],
        "delta_ldr": round(m_after["ldr"] - m_before["ldr"], 4),
        "days": days,
        "irr_per_day": round(delta_closed / days, 4) if days > 0 else None,
        "discovered_edges": sorted(set(after_edges) - set(before_edges)),
        "advanced_edges": sorted(
            edge_id
            for edge_id in set(before_edges) & set(after_edges)
            if _rank(after, after_edges[edge_id]) > _rank(before, before_edges[edge_id])
        ),
    }
    return errors, report


def load_baseline(root: Path, ref: str) -> dict[str, Any] | None:
    """Load the map at `ref`; None when the map did not exist there (empty baseline)."""
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:{MAP_RELPATH}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        probe = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            capture_output=True,
            check=False,
        )
        if probe.returncode != 0:
            raise ValueError(f"baseline ref {ref!r} does not resolve to a commit")
        return None
    return tomllib.loads(result.stdout.decode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--map", type=Path, default=None, help=f"defaults to <root>/{MAP_RELPATH}")
    parser.add_argument("--frontier", type=int, default=0, metavar="N", help="print the top N edges to retire next")
    parser.add_argument("--baseline-ref", default=None, help="git ref to ratchet against and compute IRR from")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    doc = load_toml(args.map or root / MAP_RELPATH)
    errors = validate_map(doc, root)
    if errors:
        for error in errors:
            print(f"REFUSED:{error}")
        return 2

    report: dict[str, Any] = {"metrics": metrics(doc)}
    if args.frontier > 0:
        report["frontier"] = frontier(doc, args.frontier)

    if args.baseline_ref:
        try:
            before = load_baseline(root, args.baseline_ref)
        except ValueError as error:
            print(f"REFUSED:BASELINE_UNRESOLVED:{error}")
            return 2
        if before is None:
            report["ratchet"] = {
                "baseline_observed_at": None,
                "discovered_edges": sorted(edge["id"] for edge in doc.get("edge", [])),
            }
        else:
            # Baseline evidence paths are not re-checked: they name the baseline tree.
            if before.get("ladder", {}).get("states") != EXPECTED_STATES:
                print("REFUSED:BASELINE_INVALID:baseline ladder differs from the retirement ladder")
                return 2
            ratchet_errors, report["ratchet"] = compare(before, doc)
            for error in ratchet_errors:
                print(f"REFUSED:{error}")
            if ratchet_errors:
                return 2

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
