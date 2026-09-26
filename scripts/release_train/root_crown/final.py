"""Final hardening outputs of a tagged release (PR-5; stdlib only, no process, no network).

Pure projections of committed bytes, written by ``hardening.py --write`` and guarded by
``hardening.py --check``:

  closure-final.json        the tagged closure rows under evidence profile ``durable/v1``:
                            courts re-bound to durable ``git:`` locators (E1 index + the
                            final-lanes rebinds), typed supersession / root / typed rows,
                            and the merged post-tag lane results appended as post-tag rows
  evidence-index.json       every durable locator the final outputs cite, with its sha256
  drift.json                the committed current-observations snapshot against the tag:
                            moved heads, the tag binding and the frozen-payload result
  audit.json                mutation summary, the superseded tag-illegal decision, the
                            beb7bc2d disposition, the release-crown reviewer blocker, Weaver
  requirements-matrix.json  the 33 requirements with historical / hardened / current states
  scorecard.json, benchmark.json   ``scripts.release_train.scorecard.project``

Inputs: ``release/<v>/closure.json`` (tagged, frozen), ``requirements.json``, the terminality
policy, ``hardening/{TAG-SUBJECT.json, evidence/INDEX.json, requirements-locators.json}``,
``hardening/inputs/{delta-observations, current-observations, final-lanes,
scorecard-observations, mutation-report}.json``, the tag-named crown receipt and its
observations, and the materialized tag subject (``--subject-tree``) for tag-commit bytes.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from . import gitobj, posttag
from .hardening import GENERATED, POST_TAG_EXCLUDES

SCHEMA = "https://chatman.dev/root-crown/hardening/{}/v1"
FINAL_LANES = "inputs/final-lanes.json"
CURRENT_OBSERVATIONS = "inputs/current-observations.json"
SCORECARD_OBSERVATIONS = "inputs/scorecard-observations.json"
MUTATION_REPORT = "inputs/mutation-report.json"
EVIDENCE_INDEX_E1 = "evidence/INDEX.json"
REQUIREMENTS_LOCATORS = "requirements-locators.json"
CLOSURE_FINAL = "closure-final.json"
EVIDENCE_INDEX = "evidence-index.json"
DRIFT = "drift.json"
AUDIT = "audit.json"
MATRIX = "requirements-matrix.json"
SCORECARD = "scorecard.json"
BENCHMARK = "benchmark.json"
OUTPUTS = (CLOSURE_FINAL, EVIDENCE_INDEX, DRIFT, AUDIT, MATRIX, SCORECARD, BENCHMARK)
MATRIX_ROWS = 33
_GIT = re.compile(r"^git:(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<sha>[0-9a-f]{40}):(?P<path>\S+)$")
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
# Failure class / broken term of the typed codes the current and hardened sections report.
TERMINAL_PASS = "PASS"


class FinalError(ValueError):
    pass


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


class Context:
    """Committed inputs of one projection."""

    def __init__(self, root: Path, release: str, record: dict[str, Any], replay: dict[str, Any], subject_dir: Path | None):
        self.root = root
        self.release = release
        self.release_dir = root / "release" / release
        self.hardening = self.release_dir / "hardening"
        self.record = record
        self.replay = replay
        self.subject_dir = subject_dir
        self.repository = record["repository"]
        self.tag_commit = record["subject"]["commit_sha"]
        self.lanes = _load(self.hardening / FINAL_LANES)
        self.current_obs = _load(self.hardening / CURRENT_OBSERVATIONS)
        self.tag_receipt = _load(self.hardening / record["tag_receipt"]["path"])
        self.tag_observations = _load(self.hardening / record["tag_receipt"]["observations_path"])

    def rel(self, name: str) -> str:
        return f"release/{self.release}/hardening/{name}"

    def local_bytes(self, locator: str) -> bytes | None:
        """Bytes of a root-repository ``git:`` locator from the tree under projection.

        Tag-commit locators read the materialized tag subject; every other commit reads the
        projected tree (a descendant of the container). The release closure court recomputes
        each digest against the container's own bytes, so a stale byte here is refused there.
        """
        match = _GIT.fullmatch(locator or "")
        if match is None or match["repo"] != self.repository:
            return None
        base = self.subject_dir if match["sha"] == self.tag_commit else self.root
        if base is None:
            return None
        path = base / match["path"]
        return path.read_bytes() if path.is_file() else None

    def digest_of(self, locator: str) -> str | None:
        data = self.local_bytes(locator)
        return _sha256(data) if data is not None else None


# ------------------------------------------------------------------ closure-final


def _find(rows: list[dict[str, Any]], subject_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("subject_id") == subject_id:
            return row
    raise FinalError(f"FINAL_ROW_UNKNOWN:{subject_id}")


def _court(row: dict[str, Any], name: str) -> dict[str, Any]:
    for court in row.get("courts", []):
        if court.get("court") == name:
            return court
    raise FinalError(f"FINAL_COURT_UNKNOWN:{row.get('subject_id')}:{name}")


def closure_final(ctx: Context) -> dict[str, Any]:
    from scripts.release_train.release_closure_court import court as closure_court

    tagged_path = ctx.release_dir / "closure.json"
    tagged = _load(tagged_path)
    index = _load(ctx.hardening / EVIDENCE_INDEX_E1)
    deltas = _load(ctx.hardening / posttag.DELTA_OBSERVATIONS)
    out = closure_court.bind_index(tagged, index, deltas)
    rows = out["subjects"]
    for row in rows:
        row["row_origin"] = "tagged"
    lanes = ctx.lanes
    for rebind in lanes.get("rebinds", []):
        court = _court(_find(rows, rebind["subject_id"]), rebind["court"])
        court["evidence_locator"] = rebind["evidence_locator"]
        court["evidence_digest"] = ctx.digest_of(rebind["evidence_locator"])
        for field in ("log", "output"):
            loc = rebind.get(f"{field}_locator")
            if loc is None:
                continue
            court[f"{field}_locator"] = loc
            if court.get(f"{field}_sha256") is None:
                court[f"{field}_sha256"] = ctx.digest_of(loc)
        for extra in ("artifact_locator", "artifact_digest"):
            if rebind.get(extra) is not None:
                court[extra] = rebind[extra]
        court["rebound_by"] = f"{ctx.rel(FINAL_LANES)}#rebinds ({rebind['detail']})"
    for sup in lanes.get("supersessions", []):
        row = _find(rows, sup["subject_id"])
        row["tagged_impl"] = {"standing": row["impl_standing"], "type": row.pop("impl_type", None)}
        row["impl_standing"] = sup["impl_standing"]
        row["successor"] = dict(sup["successor"])
    root = lanes.get("root_row")
    if root:
        row = _find(rows, root["subject_id"])
        row["tagged_impl"] = {"standing": row["impl_standing"], "type": row.pop("impl_type", None), "sha": row["sha"]}
        row["sha"] = root["sha"]
        row["impl_standing"] = root["impl_standing"]
        court = dict(root["court"], sha=root["sha"])
        court["evidence_digest"] = ctx.digest_of(court["evidence_locator"])
        row["courts"] = [court]
    for typed in lanes.get("typed_rows", []):
        row = _find(rows, typed["subject_id"])
        row["tagged_impl"] = {"standing": row["impl_standing"], "type": row.get("impl_type")}
        row["impl_standing"] = typed["impl_standing"]
        row["impl_type"] = typed["impl_type"]
    for post in lanes.get("post_tag_rows", []):
        row = {k: v for k, v in post.items() if k != "courts"}
        row.setdefault("required", False)
        row.setdefault("authority_ceiling", "NONE")
        row.setdefault("authority_claimed", "NONE")
        row["row_origin"] = "post-tag"
        courts = []
        for spec in post.get("courts", []):
            court = {"kind": "implementation", "required": False, **spec, "sha": post["sha"]}
            if court.get("evidence_digest") is None and str(court.get("evidence_locator", "")).startswith("git:"):
                court["evidence_digest"] = ctx.digest_of(court["evidence_locator"])
            courts.append(court)
        row["courts"] = courts
        rows.append(row)
    out["GENERATED"] = GENERATED
    out["_derivation"] = (
        f"release/{ctx.release}/closure.json (tagged, {_sha256(tagged_path.read_bytes())}) bound to "
        f"{ctx.rel(EVIDENCE_INDEX_E1)} and {ctx.rel(posttag.DELTA_OBSERVATIONS)} "
        f"(release_closure_court.bind_index), then {ctx.rel(FINAL_LANES)} rebinds, supersessions, "
        "root row, typed rows and post-tag rows"
    )
    out["court_command"] = (
        f"python3 scripts/durable_locator/durable_locator.py stage-root {ctx.rel(CLOSURE_FINAL)} --dest <root> && "
        f"python3 -m scripts.release_train.release_closure_court {ctx.rel(CLOSURE_FINAL)} --evidence-root <root>"
    )
    return out


# ------------------------------------------------------------------ requirements matrix


def _state_label(state: dict[str, Any] | None) -> str:
    if not state:
        return "UNKNOWN"
    if state.get("state") == TERMINAL_PASS:
        return TERMINAL_PASS
    return f"{state.get('state')}:{state.get('code')}"


def current_section(ctx: Context) -> dict[str, Any]:
    obs = ctx.current_obs
    head = (obs.get("repos", {}).get(ctx.repository) or {}).get("head_sha")
    tags = posttag.tag_sources(obs, None)
    return posttag.current_conformance(
        ctx.release_dir, obs, None, head, ctx.record, tags, root=ctx.root, hardening_dir=ctx.hardening
    )


def requirements_matrix(ctx: Context, current: dict[str, Any]) -> dict[str, Any]:
    from .binding import POLICY_ROOT

    reqs = _load(ctx.release_dir / "requirements.json")["requirements"]
    terminality = {r["id"]: r for r in _load(POLICY_ROOT / ctx.release / "terminality.json")["rows"]}
    locators = {r["id"]: r for r in _load(ctx.hardening / REQUIREMENTS_LOCATORS)["rows"]}
    hardened = {}
    for item in (ctx.replay.get("historical", {}).get("hardened") or {}).get("remaining", []):
        rid, state, code = item.split(":", 2)
        hardened[rid] = f"{state}:{code}"
    historical_states = ctx.tag_receipt["requirements"]
    current_states = current["receipt"]["requirements"]
    artifacts = ctx.tag_observations.get("artifacts", {})
    # Private repositories are observed operator-locally (observations/private-repos.json).
    private = {
        f"{repo}:{r['path']}": r.get("sha256")
        for repo, rec in ((ctx.tag_observations.get("private_repos") or {}).get("repos") or {}).items()
        for r in rec.get("receipts", [])
    }
    exit_path = ctx.hardening / ctx.record["tag_receipt"]["path"].rsplit("/", 1)[0] / "exit-code"
    tag_exit = int(exit_path.read_text(encoding="utf-8").strip()) if exit_path.is_file() else None
    rows = []
    for req in reqs:
        rid = req["id"]
        policy = terminality[rid]
        loc = locators[rid]
        container = loc["durable_locator"]
        digest = ctx.digest_of(container)
        if digest is None:
            recorded = (artifacts.get(loc["tagged_locator"]) or {}).get("sha256") or private.get(loc["tagged_locator"])
            digest = f"sha256:{recorded}" if recorded else None
        hist = historical_states.get(rid)
        cur = current_states.get(rid)
        states = {"historical": _state_label(hist), "hardened": hardened.get(rid, _state_label(hist)), "current": _state_label(cur)}
        worst = next((s for s in (states["current"], states["hardened"]) if s != TERMINAL_PASS), None)
        if worst is None:
            standing = "ALIVE"
        else:
            source = cur if states["current"] != TERMINAL_PASS else None
            term = (source or {}).get("broken_term")
            fclass = (source or {}).get("failure_class")
            code = worst.split(":", 1)[1] if ":" in worst else worst
            standing = f"{worst.split(':', 1)[0]}({';'.join(x for x in (code, term, fclass) if x)})"
        rows.append(
            {
                "id": rid,
                "term": req["term"],
                "owner_repo": req["owner_repo"],
                "required_state": policy["required_success_state"],
                "observed_state": states,
                "subject_sha": (hist or {}).get("subject_sha"),
                "evidence_digest": digest,
                "evidence_container": container,
                "command": (
                    f"python3 -m scripts.release_train.root_crown --release {ctx.release} --mode POST_TAG "
                    f"--observations {ctx.rel(CURRENT_OBSERVATIONS)} --crown-sha <head> --head-sha <head> "
                    f"--subject-tree <git archive {ctx.tag_commit}> --hardening-dir release/{ctx.release}/hardening "
                    f"--out <receipt>  # evaluator {req['evidence_kind']}"
                ),
                "exit": tag_exit,
                "falsifier": (
                    f"the {req['evidence_kind']} evaluator over {container} yields a state outside "
                    f"{policy['allowed_terminal_states']} ({policy['evidence_required']})"
                ),
                "authority": policy["authority_required"],
                "standing": standing,
                "standing_ceiling": policy["standing_ceiling"],
            }
        )
    if len(rows) != MATRIX_ROWS:
        raise FinalError(f"MATRIX_ROWS:{len(rows)}!={MATRIX_ROWS}")
    return {
        "GENERATED": GENERATED,
        "schema": SCHEMA.format("requirements-matrix"),
        "release": ctx.release,
        "authority": "NONE",
        "sections": {
            "historical": f"{ctx.record['tag_receipt']['path']} (tag-named receipt, {ctx.record['tag_receipt']['receipt_digest']}); exit = its run exit-code",
            "hardened": "replay-receipt.json historical.hardened.remaining (current evaluator over tag-time inputs + delta observations)",
            "current": f"{CURRENT_OBSERVATIONS} through posttag.current_conformance at the observed root head (receipt {current['receipt']['receipt_digest']})",
        },
        "rows": rows,
    }


# ------------------------------------------------------------------ drift


def payload_freeze(ctx: Context) -> dict[str, Any]:
    payload = ctx.record["payload"]
    actual = gitobj.tree_sha_of_dir(ctx.root / payload["path"], exclude=POST_TAG_EXCLUDES)
    return {
        "path": payload["path"],
        "excludes": list(POST_TAG_EXCLUDES),
        "tagged_tree_sha": payload["tree_sha"],
        "recomputed_tree_sha": actual,
        "result": "HOLDS" if actual == payload["tree_sha"] else "REFUSED:PAYLOAD_MUTATED_POST_TAG",
    }


def drift(ctx: Context, current: dict[str, Any], container: str | None) -> dict[str, Any]:
    obs = ctx.current_obs
    tag_heads = ctx.tag_receipt.get("heads", {})
    repos = {}
    for repository, rec in sorted(obs.get("repos", {}).items()):
        head = rec.get("head_sha")
        repos[repository] = {
            "pin_sha": rec.get("pin_sha"),
            "tag_receipt_head": tag_heads.get(repository),
            "observed_head": head,
            "compare_status": rec.get("compare_status"),
            "moved_since_tag": tag_heads.get(repository) not in (None, head),
            "error": rec.get("error"),
        }
    tag = obs.get("tag") or {}
    obs_path = ctx.hardening / CURRENT_OBSERVATIONS
    locator = f"git:{ctx.repository}@{container}:{ctx.rel(CURRENT_OBSERVATIONS)}" if container else None
    return {
        "GENERATED": GENERATED,
        "schema": SCHEMA.format("drift"),
        "release": ctx.release,
        "authority": "NONE",
        "observations": {
            "path": ctx.rel(CURRENT_OBSERVATIONS),
            "locator": locator,
            "sha256": _sha256(obs_path.read_bytes()),
            "observed_at": obs.get("observed_at"),
            "observation_authority": obs.get("authority"),
        },
        "tag": {
            "recorded_object_sha": ctx.record["tag"]["object_sha"],
            "recorded_commit_sha": ctx.tag_commit,
            "observed_object_sha": tag.get("object_sha"),
            "observed_commit_sha": tag.get("sha"),
            "holds": tag.get("object_sha") == ctx.record["tag"]["object_sha"] and tag.get("sha") == ctx.tag_commit,
            "subject_delta_paths": len((tag.get("subject_delta") or {}).get("paths", [])),
        },
        "payload_freeze": payload_freeze(ctx),
        "root": current["drift"],
        "repos": repos,
        "moved_since_tag": sorted(r for r, v in repos.items() if v["moved_since_tag"]),
        "current": {
            "standing": current["standing"],
            "refusals": current["refusals"],
            "blockers": current["blockers"],
            "receipt_digest": current["receipt"]["receipt_digest"],
            "remaining": [f"{r['id']}:{r['state']}:{r['code']}" for r in current["receipt"].get("remaining", [])],
        },
        "law": "drift is reported, never used to refuse history (posttag.py); the historical replay stays HISTORICAL_RELEASE_REPLAY_EXACT",
    }


# ------------------------------------------------------------------ audit


def audit(ctx: Context, observation: dict[str, Any], freeze: dict[str, Any]) -> dict[str, Any]:
    report = _load(ctx.hardening / MUTATION_REPORT)
    lanes_audit = ctx.lanes.get("audit", {})
    tagged_illegal_path = ctx.release_dir / "tag-illegal.json"
    tagged_illegal = _load(tagged_illegal_path)
    run_dir = ctx.record["tag_receipt"]["path"].rsplit("/", 1)[0]
    decision = _load(ctx.hardening / run_dir / "tag-decision.json")
    e1 = ctx.lanes["containers"]["e1"]["commit"]
    return {
        "GENERATED": GENERATED,
        "schema": SCHEMA.format("audit"),
        "release": ctx.release,
        "authority": "NONE",
        "mutation": {
            "root_crown": {
                "path": ctx.rel(MUTATION_REPORT),
                "killed": report.get("killed"),
                "total": report.get("total"),
                "survivors": report.get("survivors"),
                "all_killed": report.get("all_killed"),
                "source_digests": len(report.get("source_digests", {})),
            },
            "harnesses": observation.get("mutation_harnesses", []),
        },
        "tag_illegal": {
            "tagged": {
                "path": f"release/{ctx.release}/tag-illegal.json",
                "sha256": _sha256(tagged_illegal_path.read_bytes()),
                "decision": tagged_illegal.get("decision"),
                "crown_sha": tagged_illegal.get("crown_sha"),
                "receipt_digest": tagged_illegal.get("receipt_digest"),
            },
            "superseded_by": {
                "run_id": ctx.record["tag"].get("approval_run"),
                "decision": decision.get("decision"),
                "crown_sha": decision.get("crown_sha"),
                "receipt_digest": decision.get("receipt_digest"),
                "locator": f"git:{ctx.repository}@{e1}:{ctx.rel(run_dir + '/tag-decision.json')}",
            },
            "standing": "SUPERSEDED" if decision.get("decision") == "LEGAL" else "UNKNOWN",
            "note": "the tagged tag-illegal.json is frozen payload (never edited); the tag-named run's LEGAL decision supersedes it",
        },
        "beb7bc2d": lanes_audit.get("beb7bc2d"),
        "release_crown_reviewer": lanes_audit.get("release_crown_environment"),
        "weaver": lanes_audit.get("weaver"),
        "cancelled_runs": lanes_audit.get("cancelled_runs", []),
        "frozen_payload": freeze,
        "observed_at": lanes_audit.get("observed_at"),
    }


# ------------------------------------------------------------------ evidence index


def evidence_index(ctx: Context, closure: dict[str, Any], matrix: dict[str, Any], observation: dict[str, Any], drift_doc: dict[str, Any]) -> dict[str, Any]:
    entries: dict[str, dict[str, Any]] = {}

    def add(locator: Any, digest: Any, role: str) -> None:
        if not isinstance(locator, str) or not (locator.startswith("git:") or locator.startswith("https://")):
            return
        entry = entries.setdefault(locator, {"locator": locator, "sha256": None, "roles": []})
        if digest and entry["sha256"] is None:
            entry["sha256"] = digest if str(digest).startswith("sha256:") else f"sha256:{digest}"
        if role not in entry["roles"]:
            entry["roles"].append(role)

    for i, row in enumerate(closure.get("subjects", [])):
        for j, court in enumerate(row.get("courts", [])):
            where = f"{CLOSURE_FINAL}#/subjects/{i}/courts/{j}"
            add(court.get("evidence_locator"), court.get("evidence_digest"), f"{where}/evidence_locator")
            add(court.get("log_locator"), court.get("log_sha256"), f"{where}/log_locator")
            add(court.get("output_locator"), court.get("output_sha256"), f"{where}/output_locator")
            add(court.get("artifact_locator"), court.get("artifact_digest"), f"{where}/artifact_locator")
        succ = row.get("successor") or {}
        add(succ.get("locator"), None, f"{CLOSURE_FINAL}#/subjects/{i}/successor/locator")
    for k, row in enumerate(matrix.get("rows", [])):
        add(row.get("evidence_container"), row.get("evidence_digest"), f"{MATRIX}#/rows/{k}/evidence_container")
    for k, harness in enumerate(observation.get("mutation_harnesses", [])):
        add(harness.get("locator"), harness.get("sha256"), f"{SCORECARD_OBSERVATIONS}#/mutation_harnesses/{k}")
    add(drift_doc["observations"].get("locator"), drift_doc["observations"].get("sha256"), f"{DRIFT}#/observations/locator")
    rows = []
    for locator in sorted(entries):
        entry = entries[locator]
        match = _GIT.fullmatch(locator)
        entry["kind"] = "git" if match else "https"
        entry["container"] = {"repository": match["repo"], "sha": match["sha"]} if match else None
        entry["recomputable_offline"] = bool(match)
        rows.append(entry)
    return {
        "GENERATED": GENERATED,
        "schema": SCHEMA.format("evidence-index"),
        "release": ctx.release,
        "authority": "NONE",
        "rows": rows,
        "summary": {
            "locators": len(rows),
            "git": sum(1 for r in rows if r["kind"] == "git"),
            "https": sum(1 for r in rows if r["kind"] == "https"),
            "without_digest": sum(1 for r in rows if r["sha256"] is None),
            "containers": sorted({f"{r['container']['repository']}@{r['container']['sha']}" for r in rows if r["container"]}),
        },
        "verify": f"python3 scripts/durable_locator/durable_locator.py stage-root {ctx.rel(EVIDENCE_INDEX)} --dest <root> (resolves every git: row; digests recompute)",
    }


# ------------------------------------------------------------------ entry point


def _dump(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def outputs(root: Path, release: str, record: dict[str, Any], replay: dict[str, Any], subject_dir: Path | None) -> dict[str, bytes]:
    """{name: bytes} of the final outputs, or {} when the final-lanes input is absent."""
    from scripts.release_train.scorecard import project as scorecard_project

    hardening_dir = root / "release" / release / "hardening"
    if not (hardening_dir / FINAL_LANES).is_file():
        return {}
    ctx = Context(root, release, record, replay, subject_dir)
    e3 = ctx.lanes["containers"].get("e3", {}).get("commit")
    closure = closure_final(ctx)
    current = current_section(ctx)
    matrix = requirements_matrix(ctx, current)
    drift_doc = drift(ctx, current, e3)
    observation = _load(hardening_dir / SCORECARD_OBSERVATIONS)
    edges_path = root / "release" / release / "autonomy" / "edges.json"
    edges = _load(edges_path) if edges_path.is_file() else None
    return {
        CLOSURE_FINAL: _dump(closure),
        MATRIX: _dump(matrix),
        DRIFT: _dump(drift_doc),
        AUDIT: _dump(audit(ctx, observation, drift_doc["payload_freeze"])),
        EVIDENCE_INDEX: _dump(evidence_index(ctx, closure, matrix, observation, drift_doc)),
        SCORECARD: _dump(scorecard_project.scorecard(observation, closure, matrix, edges, GENERATED)),
        BENCHMARK: _dump(scorecard_project.benchmark(observation, GENERATED)),
    }
