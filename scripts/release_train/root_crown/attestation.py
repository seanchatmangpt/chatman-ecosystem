"""H4 post-tag attestation: ``release/<v>/hardening/{current-conformance,ATTESTATION}.json``.

Stdlib only, no network. Both outputs are deterministic projections of committed bytes
(+ the materialized tag subject for the exact historical replay):

  current-conformance.json  the POST_TAG crown re-evaluated in-process over the committed
                            post-tag observations (``inputs/current/``: public observation,
                            local-git tag observation, ancestry, the operator run record) and
                            compared byte-for-byte with the committed run output
                            (``inputs/current/crown-receipt.json``): historical standing,
                            current standing, per-term states, refusals, typed remaining
                            rows, exit code
  ATTESTATION.json          tag unchanged (raw tag object vs both observations), frozen
                            payload tree unchanged, hardening projections current, every
                            lane's PR/merge sha/receipt locator verified against
                            ``inputs/attestation-observations.json`` (observed by
                            ``scripts/observe_attestation.py``), 0 non-durable locators
                            under ``release/<v>/hardening/**`` except typed residue rows,
                            Weaver status on the observed root head, mutation survivors,
                            autonomic receipt standings, and the operator-only actions
                            (``operator-actions.json``) with their observed state

``--check`` re-projects and prints ``REFUSED:PROJECTION_DRIFT:<path>`` on any byte
difference (exit 2); ``--write`` rewrites both outputs. The attestation's own standing is
``ALIVE`` only when every check holds; it never upgrades the release's current standing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator

from . import hardening, posttag
from .crown import attest

GENERATED = (
    "scripts/release_train/root_crown/attestation.py -- do not edit; run --write"
)
SCHEMA_ATTESTATION = "https://chatman.dev/root-crown/hardening/attestation/v1"
SCHEMA_CURRENT = "https://chatman.dev/root-crown/hardening/current-conformance/v1"
ATTESTATION = "ATTESTATION.json"
CURRENT = "current-conformance.json"
CURRENT_DIR = "inputs/current"
LANES = "inputs/attestation-lanes.json"
LANE_OBSERVATIONS = "inputs/attestation-observations.json"
ACTIONS = "operator-actions.json"
MUTATION_REPORT = "inputs/mutation-report.json"
EXIT = {"ALIVE": 0, "BLOCKED": 3, "REFUSED": 2}
# Files whose bytes are observed/recorded evidence content, not locator-bearing records:
# a machine path inside them is what an observed artifact or log said, never a locator.
EVIDENCE_CONTENT = (
    ("evidence/courts/", "court evidence bytes (logs, receipts as produced)"),
    ("evidence/topology/", "topology replay evidence bytes"),
    (
        "evidence/locator-rules.json",
        "locator rules: regex patterns over tagged locators, not locators",
    ),
    ("inputs/objects/", "raw git objects"),
    ("inputs/current/", "post-tag observations and the recorded run output"),
    ("receipts/run-", "committed crown run receipts and their observations"),
    ("inputs/current-observations.json", "observation snapshot (PR-5)"),
    ("inputs/scorecard-observations.json", "observation snapshot (PR-5)"),
    ("inputs/delta-observations.json", "observation snapshot (PR-4)"),
)
SELF = (ATTESTATION,)
_DURABLE = re.compile(
    r"^(git:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}:\S+|git-notes:refs/notes/[A-Za-z0-9_./-]+@[0-9a-f]{40}|https://\S+)$"
)
_LOCALISH = re.compile(
    r"(^/(?!subjects/|requirements/)|^~|^local:|scratchpad/|\.claude/|(?<![\w.])/?tmp/|/private/|/Users/)"
)
_TYPED = re.compile(
    r"(BLOCKED|UNSUPPORTED|REFUSED|RESIDUE|LOCAL_HOST_OBSERVATION|not a locator)"
)
_PROSE_KEYS = {
    "GENERATED",
    "HANDWRITTEN",
    "OBSERVED",
    "_about",
    "cmd",
    "command",
    "commands",
    "description",
    "detail",
    "materialization",
    "message",
    "note",
    "notes",
    "observers",
    "reason",
    "title",
    "verification",
}


class AttestationError(ValueError):
    pass


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dump(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


# ------------------------------------------------------------------ current conformance


def current_conformance(
    root: Path, release: str, hardening_dir: Path, subject_dir: Path
) -> dict[str, Any]:
    cur = hardening_dir / CURRENT_DIR
    run = _load(cur / "run.json")
    observations = _load(cur / "observations.json")
    previous = _load(hardening_dir / run["previous_path"])
    tag_observation = _load(cur / "tag-observation.json")
    ancestry = {
        line.strip()
        for line in (cur / "ancestry.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    verdict = attest(
        root / "release" / release,
        observations,
        previous,
        run["crown_sha"],
        root=root,
        requested_mode="POST_TAG",
        head_sha=run["head_sha"],
        subject_dir=subject_dir,
        hardening_dir=hardening_dir,
        tag_observation=tag_observation,
        ancestry=ancestry,
    )
    receipt = verdict.receipt
    committed_bytes = (cur / "crown-receipt.json").read_bytes()
    recomputed_bytes = _dump(receipt)
    historical = receipt.get("historical") or {}
    current = receipt.get("current") or {}
    inputs = {
        f"{CURRENT_DIR}/{p.name}": _sha256(p.read_bytes())
        for p in sorted(cur.iterdir())
        if p.is_file() and p.name != "crown-receipt.json"
    }
    inputs[run["previous_path"]] = _sha256(
        (hardening_dir / run["previous_path"]).read_bytes()
    )
    exit_code = EXIT[verdict.standing]
    return {
        "GENERATED": GENERATED,
        "schema": SCHEMA_CURRENT,
        "release": release,
        "mode": receipt["mode"],
        "crown_sha": run["crown_sha"],
        "head_sha": run["head_sha"],
        "observed_at": observations.get("observed_at"),
        "observation_authority": receipt.get("observation_authority"),
        "inputs_sha256": inputs,
        "replay": {
            "committed_receipt": f"{CURRENT_DIR}/crown-receipt.json",
            "committed_sha256": _sha256(committed_bytes),
            "recomputed_sha256": _sha256(recomputed_bytes),
            "receipt_digest": receipt["receipt_digest"],
            "result": "EXACT" if committed_bytes == recomputed_bytes else "DIVERGED",
        },
        "historical": {
            "standing": historical.get("standing"),
            "replay_standing": historical.get("replay_standing"),
            "replayed_digest": (historical.get("replay") or {}).get("replayed_digest"),
            "standing_ceiling": historical.get("standing_ceiling"),
            "refusals": historical.get("refusals", []),
        },
        "current": {
            "standing": current.get("standing"),
            "refusals": current.get("refusals", []),
            "blockers": current.get("blockers", []),
            "drift": current.get("drift", {}),
        },
        "standing": verdict.standing,
        "terms": {k: v["state"] for k, v in sorted(receipt["terms"].items())},
        "refusals": sorted(set(verdict.refusals)),
        "remaining": [
            {
                "id": r["id"],
                "state": r["state"],
                "code": r["code"],
                "failure_class": r["failure_class"],
                "broken_term": r["broken_term"],
            }
            for r in verdict.remaining
        ],
        "exit_code": exit_code,
        "recorded_exit_code": run["exit_code"],
        "authority": "NONE",
    }


# ------------------------------------------------------------------ locator scan


def _exempt(rel: str) -> str | None:
    for prefix, reason in EVIDENCE_CONTENT:
        if rel.startswith(prefix):
            return reason
    return None


def _walk(
    value: Any, pointer: str, holder: dict[str, Any] | None
) -> Iterator[tuple[str, str, str, dict[str, Any] | None]]:
    if isinstance(value, dict):
        for key, item in value.items():
            prose = key in _PROSE_KEYS or key.endswith("reason")
            if prose and (
                isinstance(item, str)
                or (isinstance(item, list) and all(isinstance(x, str) for x in item))
            ):
                continue
            yield from _walk(item, f"{pointer}/{key}", value)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from _walk(item, f"{pointer}/{i}", holder)
    elif isinstance(value, str):
        key = pointer.rsplit("/", 1)[-1]
        yield pointer, key, value, holder


def classify_locator(key: str, value: str, holder: dict[str, Any] | None) -> str | None:
    """None when the string is not locator-like; else DURABLE / REBOUND / TYPED_RESIDUE / VIOLATION."""
    if key.endswith("pointer"):
        return None
    if not (key.endswith("locator") or _LOCALISH.search(value)):
        return None
    if _DURABLE.match(value):
        return "DURABLE"
    siblings = holder or {}
    for skey, svalue in siblings.items():
        if skey == key or not isinstance(svalue, str):
            continue
        rebinder = (
            skey.endswith("locator")
            or skey in ("to", "durable_output")
            or f"{skey}_original" == key
        )
        if rebinder and _DURABLE.match(svalue):
            return "REBOUND"
    if _TYPED.search(value) or any(
        isinstance(v, str) and _TYPED.search(v)
        for k, v in siblings.items()
        if k != key and k not in _PROSE_KEYS
    ):
        return "TYPED_RESIDUE"
    return "VIOLATION"


def scan_locators(hardening_dir: Path) -> dict[str, Any]:
    counts = {"DURABLE": 0, "REBOUND": 0, "TYPED_RESIDUE": 0, "VIOLATION": 0}
    violations: list[dict[str, str]] = []
    scanned: list[str] = []
    exempt: dict[str, str] = {}
    for path in sorted(hardening_dir.rglob("*.json")):
        rel = path.relative_to(hardening_dir).as_posix()
        if rel in SELF:
            continue
        reason = _exempt(rel)
        if reason is not None:
            exempt[rel] = reason
            continue
        scanned.append(rel)
        for pointer, key, value, holder in _walk(_load(path), "", None):
            verdict = classify_locator(key, value, holder)
            if verdict is None:
                continue
            counts[verdict] += 1
            if verdict == "VIOLATION":
                violations.append(
                    {"file": rel, "json_pointer": pointer, "value": value}
                )
    return {
        "rule": (
            "every locator-like JSON string (key *locator, or an absolute, home, tmp, scratch, .claude or local: "
            "path) in a non-evidence hardening record is DURABLE (CE23-9 git:, git-notes: or https://), REBOUND "
            "(a sibling *locator, to or durable_output, or X beside X_original, is durable), TYPED_RESIDUE (a typed "
            "BLOCKED, UNSUPPORTED, REFUSED, RESIDUE or LOCAL_HOST_OBSERVATION disposition beside it), else "
            "VIOLATION; prose keys (command, note, *reason, ...) are not locators"
        ),
        "scanned_files": scanned,
        "exempt_evidence_content": exempt,
        "counts": counts,
        "violations": violations,
        "result": "HOLDS" if not violations else "REFUSED:NON_DURABLE_LOCATOR",
    }


# ------------------------------------------------------------------ lanes


def lane_rows(
    hardening_dir: Path,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    lanes_bytes = (hardening_dir / LANES).read_bytes()
    lanes = json.loads(lanes_bytes)["lanes"]
    observed = _load(hardening_dir / LANE_OBSERVATIONS)
    refusals: list[str] = []
    if observed.get("lanes_sha256") != _sha256(lanes_bytes):
        refusals.append(
            "REFUSED:LANE_OBSERVATION_STALE:attestation-lanes.json changed after observation"
        )
    by_id = {row["id"]: row for row in observed.get("lanes", [])}
    rows = []
    for lane in lanes:
        obs = by_id.get(lane["id"])
        problems: list[str] = []
        if obs is None or obs.get("error"):
            problems.append("LANE_UNOBSERVED")
            obs = obs or {}
        if obs.get("pr_head") != lane["head_sha"]:
            problems.append("PR_HEAD_MISMATCH")
        if lane["disposition"] == "MERGED":
            if obs.get("pr_state") != "MERGED":
                problems.append("PR_NOT_MERGED")
            if obs.get("pr_merge_commit") != lane["merge_sha"]:
                problems.append("MERGE_SHA_MISMATCH")
            if obs.get("merge_on_default") != "ON_DEFAULT":
                problems.append("MERGE_NOT_ON_DEFAULT")
        elif obs.get("pr_state") != "CLOSED" or obs.get("pr_merge_commit") is not None:
            problems.append("DISPOSITION_MISMATCH")
        receipt = obs.get("receipt") or {}
        if receipt.get("locator") != lane["receipt_locator"] or receipt.get("error"):
            problems.append("RECEIPT_UNRESOLVED")
        elif not _DURABLE.match(lane["receipt_locator"]):
            problems.append("RECEIPT_LOCATOR_NOT_DURABLE")
        verdict = "VERIFIED" if not problems else "REFUSED:" + ",".join(problems)
        if problems:
            refusals.append(
                f"REFUSED:LANE_UNVERIFIED:{lane['id']}:{','.join(problems)}"
            )
        rows.append(
            {
                "id": lane["id"],
                "repository": lane["repository"],
                "pr": lane["pr"],
                "disposition": lane["disposition"],
                "head_sha": lane["head_sha"],
                "merge_sha": lane["merge_sha"],
                "default_branch": obs.get("default_branch"),
                "merge_on_default": obs.get("merge_on_default"),
                "receipt_locator": lane["receipt_locator"],
                "receipt_kind": lane["receipt_kind"],
                "receipt_sha256": receipt.get("sha256"),
                "reported_standing": lane["reported_standing"],
                "reported_blockers": lane["reported_blockers"],
                "verification": verdict,
            }
        )
    return rows, refusals, observed


# ------------------------------------------------------------------ operator actions


def _performed(expect: Any, value: Any) -> bool:
    if isinstance(expect, str) and expect.startswith(">="):
        return isinstance(value, int) and value >= int(expect[2:])
    return value == expect


def operator_actions(
    hardening_dir: Path, governance: dict[str, Any]
) -> list[dict[str, Any]]:
    doc = _load(hardening_dir / ACTIONS)
    rows = []
    for action in sorted(doc["actions"], key=lambda a: a["order"]):
        key = action.get("observation")
        observed = governance.get(key) if key else None
        if key is None:
            state = action["standing"]
            basis = "UNOBSERVED (no GET-only observation for this action)"
        elif key not in governance:
            state = action["standing"]
            basis = f"UNOBSERVED ({key} absent from observations)"
        elif _performed(action["performed_when"], observed):
            state = "PERFORMED"
            basis = f"{key}={json.dumps(observed)}"
        else:
            state = action["standing"]
            basis = f"{key}={json.dumps(observed)} (performed when {json.dumps(action['performed_when'])})"
        rows.append(
            {
                "id": action["id"],
                "title": action["title"],
                "owner": action["owner"],
                "state": state,
                "failure_class": None
                if state == "PERFORMED"
                else action["failure_class"],
                "broken_term": None if state == "PERFORMED" else action["broken_term"],
                "rfc0004_s39": action["rfc0004_s39"],
                "observed": basis,
                "verification": action["verification"],
            }
        )
    return rows


# ------------------------------------------------------------------ attestation


def attestation(
    root: Path,
    release: str,
    repository: str,
    subject_dir: Path,
    current: dict[str, Any],
) -> dict[str, Any]:
    hardening_dir = root / "release" / release / "hardening"
    record = hardening.project_tag_subject(hardening_dir, release, repository)
    refusals: list[str] = []

    tag = record["tag"]
    local = _load(hardening_dir / CURRENT_DIR / "tag-observation.json")
    public = _load(hardening_dir / CURRENT_DIR / "observations.json").get("tag") or {}
    tag_checks = {}
    for source, obs in (("local-git", local), ("github-api", public)):
        same = (
            obs.get("object_sha") == tag["object_sha"]
            and obs.get("sha") == tag["target_sha"]
            and obs.get("object_type") == tag["object_type"]
        )
        tag_checks[source] = {
            "object_sha": obs.get("object_sha"),
            "sha": obs.get("sha"),
            "object_type": obs.get("object_type"),
            "result": "UNCHANGED" if same else "REFUSED:TAG_MOVED",
        }
        if not same:
            refusals.append(f"REFUSED:TAG_MOVED:{source}")

    payload = posttag.payload_refusals(root, record)
    refusals += payload
    drift = hardening.check(
        hardening_dir,
        hardening.outputs(hardening_dir, release, repository, subject_dir, root),
    )
    drift = [line.replace(root.as_posix().rstrip("/") + "/", "") for line in drift]
    refusals += drift

    lanes, lane_refusals, observed = lane_rows(hardening_dir)
    refusals += lane_refusals

    locators = scan_locators(hardening_dir)
    if locators["violations"]:
        refusals.append(f"REFUSED:NON_DURABLE_LOCATOR:{len(locators['violations'])}")

    mutation = _load(hardening_dir / MUTATION_REPORT)
    survivors = list(mutation.get("survivors", []))
    if survivors:
        refusals.append(f"REFUSED:MUTANT_SURVIVORS:{len(survivors)}")

    weaver_obs = observed.get("weaver") or {}
    runs = weaver_obs.get("runs") or []
    latest = runs[-1] if runs else None
    weaver = {
        "workflow": weaver_obs.get("workflow"),
        "head_sha": weaver_obs.get("head_sha"),
        "runs": runs,
        "state": "PASS"
        if latest and latest.get("conclusion") == "success"
        else ("UNOBSERVED" if latest is None else f"FAIL:{latest.get('conclusion')}"),
    }

    autonomy_path = root / "release" / release / "autonomy" / "autonomic-receipt.json"
    if autonomy_path.is_file():
        receipt = _load(autonomy_path)
        autonomy = {
            "receipt": f"release/{release}/autonomy/autonomic-receipt.json",
            "receipt_digest": receipt.get("receipt_digest"),
            "standings": receipt.get("standings"),
            "exit": receipt.get("exit"),
            "blocked_gates": receipt.get("blocked_gates"),
            "passed_gates": receipt.get("passed_gates"),
        }
    else:
        autonomy = {"state": "NOT_EVALUATED"}

    actions = operator_actions(hardening_dir, observed.get("governance") or {})
    remaining_actions = [a for a in actions if a["state"] != "PERFORMED"]

    if current["replay"]["result"] != "EXACT":
        refusals.append("REFUSED:CURRENT_CONFORMANCE_REPLAY_DIVERGED")
    if current["exit_code"] != current["recorded_exit_code"]:
        refusals.append("REFUSED:CURRENT_CONFORMANCE_EXIT_MISMATCH")

    refusals = sorted(set(refusals))
    return {
        "GENERATED": GENERATED,
        "schema": SCHEMA_ATTESTATION,
        "release": release,
        "repository": repository,
        "tag": {
            "name": tag["name"],
            "object_sha": tag["object_sha"],
            "target_sha": tag["target_sha"],
            "observations": tag_checks,
        },
        "frozen_payload": {
            "path": record["payload"]["path"],
            "tagged_tree_sha": record["payload"]["tree_sha"],
            "excludes": record["payload"]["post_tag_excludes"],
            "result": "UNCHANGED" if not payload else payload[0],
        },
        "hardening_projection": {
            "result": "CURRENT" if not drift else "DRIFT",
            "drift": drift,
        },
        "lanes": {
            "observed_at": observed.get("observed_at"),
            "authority": observed.get("authority"),
            "rows": lanes,
            "verified": sum(1 for r in lanes if r["verification"] == "VERIFIED"),
            "total": len(lanes),
        },
        "locators": locators,
        "weaver": weaver,
        "mutation": {
            "report": MUTATION_REPORT,
            "total": mutation.get("total"),
            "killed": mutation.get("killed"),
            "survivors": len(survivors),
            "all_killed": mutation.get("all_killed"),
        },
        "autonomy": autonomy,
        "current_conformance": {
            "path": CURRENT,
            "mode": current["mode"],
            "historical": current["historical"]["standing"],
            "historical_replay": current["historical"]["replay_standing"],
            "current": current["current"]["standing"],
            "standing": current["standing"],
            "terms": current["terms"],
            "exit_code": current["exit_code"],
            "replay": current["replay"]["result"],
        },
        "operator_actions": {
            "source": ACTIONS,
            "rows": actions,
            "remaining": [
                f"{a['id']}:{a['state']}({a['failure_class']}/{a['broken_term']})"
                for a in remaining_actions
            ],
        },
        "refusals": refusals,
        "standing": {
            "attestation": "ALIVE" if not refusals else "REFUSED",
            "historical": current["historical"]["standing"],
            "current": current["standing"],
            "autonomy": (autonomy.get("standings") or {}).get(
                "autonomy", "NOT_EVALUATED"
            ),
            "authority": "WAITING_EXTERNAL_AUTHORITY"
            if remaining_actions
            else "AUTHORIZED",
        },
        "authority": "NONE",
    }


def outputs(
    root: Path, release: str, repository: str, subject_dir: Path
) -> dict[str, bytes]:
    hardening_dir = root / "release" / release / "hardening"
    current = current_conformance(root, release, hardening_dir, subject_dir)
    return {
        CURRENT: _dump(current),
        ATTESTATION: _dump(
            attestation(root, release, repository, subject_dir, current)
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m scripts.release_train.root_crown.attestation"
    )
    parser.add_argument("--release", required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--subject-tree", type=Path, required=True, help="git archive of the tag commit"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    release_dir = args.root / "release" / args.release
    hardening_dir = release_dir / "hardening"
    try:
        pins = _load(release_dir / "pins.json")
        rendered = outputs(
            args.root, args.release, pins["root_repository"], args.subject_tree
        )
    except (
        AttestationError,
        hardening.HardeningError,
        FileNotFoundError,
        KeyError,
        ValueError,
    ) as exc:
        print(f"REFUSED:{exc}", file=sys.stderr)
        return 2
    if args.write:
        for name, data in rendered.items():
            (hardening_dir / name).write_bytes(data)
        print(f"WROTE:{','.join(sorted(rendered))}")
        return 0
    drift = hardening.check(hardening_dir, rendered)
    for line in drift:
        print(line)
    if drift:
        return 2
    attested = json.loads(rendered[ATTESTATION])
    print(
        f"ATTESTATION_CURRENT:{hardening_dir.as_posix()}:attestation={attested['standing']['attestation']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
