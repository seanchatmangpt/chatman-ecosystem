"""Pure projection of ``scorecard.json`` and ``benchmark.json`` (stdlib only, no I/O).

Inputs are already-loaded documents: the committed scorecard observation
(``hardening/inputs/scorecard-observations.json``), the generated ``closure-final.json`` and
``requirements-matrix.json``, and ``release/<v>/autonomy/edges.json`` when it exists.
Every metric carries its definition, its falsifier and a standing from the vocabulary
ALIVE | PARTIAL_ALIVE | UNKNOWN | UNSUPPORTED; a metric whose input is absent is a typed
UNKNOWN, never a zero. No metric is an ordering: the multi-objective hypervolume is
``UNSUPPORTED(no admitted ordering)`` until a reference point and objective directions are
admitted.
"""

from __future__ import annotations

import re
from typing import Any

SCHEMA_SCORECARD = "https://chatman.dev/release-scorecard/scorecard/v1"
SCHEMA_BENCHMARK = "https://chatman.dev/release-scorecard/benchmark/v1"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
REPO_FIELDS = ("files", "loc", "generated_files", "generated_loc", "marketplace_reused_loc")
VERDICT_RESULTS = ("PASS", "FAIL", "BASELINE_BLOCKER")


def _ok_repos(release_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {r: v for r, v in release_doc.get("repos", {}).items() if not v.get("error") and v.get("loc") is not None}


def _coverage_standing(measured: int, total: int) -> str:
    if measured == 0:
        return "UNKNOWN"
    return "ALIVE" if measured == total else "PARTIAL_ALIVE"


def _metric(mid: str, name: str, value: Any, unit: str, standing: str, definition: str, falsifier: str, source: str, **extra: Any) -> dict[str, Any]:
    out = {
        "id": mid,
        "name": name,
        "value": value,
        "unit": unit,
        "standing": standing,
        "definition": definition,
        "falsifier": falsifier,
        "source": source,
    }
    out.update(extra)
    return out


def metrics(
    observation: dict[str, Any],
    closure_final: dict[str, Any],
    matrix: dict[str, Any],
    edges: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    release = observation["release"]
    params = observation.get("parameters", {})
    current = observation["releases"][release]
    ok = _ok_repos(current)
    total = len(current.get("repos", {}))
    coverage = _coverage_standing(len(ok), total)
    errors = sorted(r for r, v in current.get("repos", {}).items() if r not in ok)
    obs_src = f"release/{release}/hardening/inputs/scorecard-observations.json"
    out: list[dict[str, Any]] = []
    out.append(
        _metric(
            "SC-01", "generated_loc", sum(v["generated_loc"] for v in ok.values()), "LOC", coverage,
            f"non-blank lines of UTF-8 text files whose first {params.get('header_bytes')} bytes match "
            f"/{params.get('generated_markers')}/, summed over git archives of the pinned SHAs",
            "re-running observe --check on the same pins drifts, or a pinned file carrying a marker in its header is not counted",
            obs_src, repos_measured=len(ok), repos_pinned=total, repos_unmeasured=errors,
        )
    )
    handwritten = sum(v["handwritten"]["loc"] for v in ok.values())
    ledgered = sorted(r for r, v in ok.items() if v["handwritten"]["ledgers"])
    out.append(
        _metric(
            "SC-02", "handwritten_loc", handwritten, "LOC", coverage if ledgered else "UNKNOWN",
            "non-blank lines of the text files named by HANDWRITTEN.md ledger rows (first column) of the same pinned tree",
            "a ledger row names an existing pinned file that is not counted, or an unledgered file is counted",
            obs_src, repos_with_ledger=ledgered,
            unmatched_ledger_entries=sum(len(v["handwritten"]["unmatched_entries"]) for v in ok.values()),
        )
    )
    reused_repos = {r: v for r, v in ok.items() if v.get("marketplace_reused_loc") is not None}
    out.append(
        _metric(
            "SC-03", "marketplace_reused_loc", sum(v["marketplace_reused_loc"] for v in reused_repos.values()), "LOC",
            coverage if current.get("marketplace_pinned") else "UNKNOWN",
            f"non-blank lines of text files (>= {params.get('min_reuse_loc')} LOC, outside ggen-marketplace) whose git blob id "
            "is a blob of the pinned ggen-marketplace tree",
            "a file byte-identical to a pinned marketplace blob is not counted, or a counted file's blob is absent from the marketplace tree",
            obs_src,
        )
    )
    surfaces = observation.get("new_surfaces", {})
    measured_pairs = len(surfaces.get("repos", {}))
    dup_standing = _coverage_standing(measured_pairs, total)
    new_loc = surfaces.get("new_surface_loc") or 0
    out.append(
        _metric(
            "SC-04", "duplicated_loc", surfaces.get("duplicated_loc"), "LOC", dup_standing,
            f"lines of new derivable surfaces (non-generated {','.join(params.get('derivable_ext', []))} files whose blob changed "
            f"since the predecessor pin) covered by a {params.get('window')}-line normalized-line window (sha256) occurring at >= 2 locations",
            "planting one copied window into a new surface does not raise the count, or a window occurring once is counted",
            obs_src, new_surface_loc=new_loc,
            ratio=round(surfaces["duplicated_loc"] / new_loc, 6) if new_loc else None,
            no_predecessor=surfaces.get("no_predecessor", []),
        )
    )
    harnesses = observation.get("mutation_harnesses", [])
    good = [h for h in harnesses if not h.get("error") and h.get("total")]
    killed = sum(h["killed"] for h in good)
    total_mutants = sum(h["total"] for h in good)
    out.append(
        _metric(
            "SC-05", "mutation_kill_ratio", round(killed / total_mutants, 6) if total_mutants else None, "ratio",
            _coverage_standing(len(good), len(harnesses)) if harnesses else "UNKNOWN",
            "sum(killed) / sum(total) over the harness outputs named by final-lanes.json mutation_harnesses, each read at its durable locator",
            "a harness output at its locator reports a survivor that the ratio does not reflect, or a harness bytes digest differs from the recorded sha256",
            obs_src, killed=killed, total=total_mutants,
            harnesses=[{k: h.get(k) for k in ("name", "killed", "total", "locator", "sha256", "error")} for h in harnesses],
        )
    )
    out.append(
        _metric(
            "SC-06", "projections_count", sum(v["generated_files"] for v in ok.values()), "files", coverage,
            "count of pinned text files carrying a generated marker in their header (projections of a generator)",
            "a marker-carrying pinned file is not counted", obs_src,
        )
    )
    courts = [c for row in closure_final.get("subjects", []) for c in row.get("courts", [])]
    executed = [c for c in courts if c.get("result") in VERDICT_RESULTS]
    by_result: dict[str, int] = {}
    for court in courts:
        by_result[str(court.get("result"))] = by_result.get(str(court.get("result")), 0) + 1
    out.append(
        _metric(
            "SC-07", "formal_courts_executed", len(executed), "courts", "ALIVE" if courts else "UNKNOWN",
            "court entries of closure-final.json that produced a verdict (result PASS, FAIL or BASELINE_BLOCKER); "
            "BLOCKED courts are listed but not counted",
            "a court counted here has no durable evidence the release closure court resolves, or a verdict court is omitted",
            f"release/{release}/hardening/closure-final.json", by_result=dict(sorted(by_result.items())),
            durable=sum(1 for c in executed if str(c.get("evidence_locator", "")).startswith("git:")),
        )
    )
    rows = matrix.get("rows", [])
    n = len(rows)
    receipt = sum(1 for r in rows if _SHA40.fullmatch(str(r.get("subject_sha", ""))) and str(r.get("evidence_container", "")).startswith("git:"))
    authority = sum(1 for r in rows if r.get("authority"))
    evidence = sum(1 for r in rows if r.get("evidence_digest"))
    for mid, name, count, definition in (
        ("SC-08", "receipt_coverage", receipt, "rows with an exact 40-hex subject_sha and a git: evidence container"),
        ("SC-09", "authority_coverage", authority, "rows declaring the authority the requirement needs"),
        ("SC-10", "evidence_coverage", evidence, "rows whose evidence bytes have a recorded sha256"),
    ):
        out.append(
            _metric(
                mid, name, round(count / n, 6) if n else None, "ratio", "ALIVE" if n else "UNKNOWN",
                f"{definition} / all rows of requirements-matrix.json",
                "a counted row's container does not resolve or its digest does not recompute", f"release/{release}/hardening/requirements-matrix.json",
                covered=count, rows=n,
            )
        )
    if isinstance(edges, dict):
        retired = [e for e in edges.get("edges", []) if str(e.get("status", "")).upper() == "RETIRED"]
        out.append(
            _metric(
                "SC-11", "coordination_edges_retired", len(retired), "edges", "ALIVE",
                "LLM/coordination edges of autonomy/edges.json whose status is RETIRED",
                "an edge counted RETIRED still carries a human or LLM hop in its latest receipt", f"release/{release}/autonomy/edges.json",
                edges=len(edges.get("edges", [])),
            )
        )
    else:
        out.append(
            _metric(
                "SC-11", "coordination_edges_retired", None, "edges", f"UNKNOWN(release/{release}/autonomy/edges.json absent)",
                "LLM/coordination edges of autonomy/edges.json whose status is RETIRED",
                "edges.json lands and this metric stays UNKNOWN", f"release/{release}/autonomy/edges.json",
            )
        )
    return out


def scorecard(
    observation: dict[str, Any],
    closure_final: dict[str, Any],
    matrix: dict[str, Any],
    edges: dict[str, Any] | None,
    generated: str,
) -> dict[str, Any]:
    items = metrics(observation, closure_final, matrix, edges)
    return {
        "GENERATED": generated,
        "schema": SCHEMA_SCORECARD,
        "release": observation["release"],
        "predecessor": observation["predecessor"],
        "authority": "NONE",
        "metrics": items,
        "hypervolume": {
            "standing": "UNSUPPORTED(no admitted ordering)",
            "detail": "no reference point or objective directions are admitted for these metrics; a scalar ranking would be an unadmitted ordering",
        },
        "standing_summary": {s: sum(1 for m in items if m["standing"] == s) for s in sorted({m["standing"] for m in items})},
    }


def benchmark(observation: dict[str, Any], generated: str) -> dict[str, Any]:
    release, predecessor = observation["release"], observation["predecessor"]
    cur = observation["releases"][release]["repos"]
    prev = observation["releases"][predecessor]["repos"]
    rows = []
    totals = {release: {f: 0 for f in REPO_FIELDS}, predecessor: {f: 0 for f in REPO_FIELDS}}
    paired = {f: [0, 0] for f in REPO_FIELDS + ("handwritten_loc",)}
    for repository in sorted(set(cur) | set(prev)):
        a, b = prev.get(repository), cur.get(repository)
        row: dict[str, Any] = {"repository": repository}
        for label, doc in ((predecessor, a), (release, b)):
            if doc is None or doc.get("error") or doc.get("loc") is None:
                row[label] = {"sha": (doc or {}).get("sha"), "standing": f"UNKNOWN({(doc or {}).get('error') or 'NOT_PINNED'})"}
                continue
            row[label] = {"sha": doc["sha"], **{f: doc.get(f) for f in REPO_FIELDS}, "handwritten_loc": doc["handwritten"]["loc"]}
            for f in REPO_FIELDS:
                totals[label][f] += doc.get(f) or 0
        if "loc" in row.get(predecessor, {}) and "loc" in row.get(release, {}):
            row["delta"] = {
                f: (row[release][f] or 0) - (row[predecessor][f] or 0) for f in REPO_FIELDS + ("handwritten_loc",)
            }
            for f in paired:
                paired[f][0] += row[predecessor][f] or 0
                paired[f][1] += row[release][f] or 0
        rows.append(row)
    return {
        "GENERATED": generated,
        "schema": SCHEMA_BENCHMARK,
        "release": release,
        "predecessor": predecessor,
        "authority": "NONE",
        "definition": "per-repository measures of the pinned release against its predecessor pins (git archives); "
        "delta = release - predecessor over repositories measured at both",
        "falsifier": "a repository measured at both pins has a delta that differs from the difference of its two rows",
        "rows": rows,
        "totals": totals,
        "paired_totals": {f: {predecessor: v[0], release: v[1], "delta": v[1] - v[0]} for f, v in paired.items()},
        "paired_repositories": sum(1 for r in rows if "delta" in r),
        "generated_share": {
            label: round(totals[label]["generated_loc"] / totals[label]["loc"], 6) if totals[label]["loc"] else None
            for label in (predecessor, release)
        },
    }
