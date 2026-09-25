"""Post-tag crown (RFC-0004 §45 after the tag exists): the tag is immutable history.

Once ``release/<v>/hardening/TAG-SUBJECT.json`` records the tag, a run on any later
commit is POST_TAG. It never re-litigates the tag against the new head (the PRE_TAG
``CROWN_SHA_SPLIT`` / ``TAG_SHA_SPLIT`` refusals would make every post-tag commit
REFUSED). Instead it reports two separate standings:

* ``historical`` — the tagged release, replayed: the tag object, its commit and the
  subject trees recompute from committed raw bytes and the materialized subject; the
  tag-named receipt's own digest and its observations digest recompute; the tag-time
  crown code, imported in isolation from the subject, reproduces the recorded
  ``receipt_digest`` byte-for-byte (else typed ``REPLAY_DIVERGED``); and the hardened
  (current) evaluator re-evaluates the same inputs, reported as ``standing_ceiling``.
* ``current`` — the attested head: the frozen payload still hashes to the tagged tree
  (else ``PAYLOAD_MUTATED_POST_TAG``), the tag still names the recorded object and
  subject (``TAG_MUTATED`` / ``TAG_SUBJECT_SPLIT``), and the head is evaluated with the
  post-tag tag binding. Drift is reported, never used to refuse history.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import binding, gitobj
from .evidence import EVALUATORS, Context, Evaluator, in_tree_pass
from .model import BLOCKED, PASS, REFUSED, ReqState, Requirement, code_of, digest
from .hardening import OBJECTS, POST_TAG_EXCLUDES, TAG_SUBJECT, HardeningError, project_tag_subject

HISTORICAL_EXACT = "HISTORICAL_RELEASE_REPLAY_EXACT"
HISTORICAL_DIVERGED = "HISTORICAL_RELEASE_REPLAY_DIVERGED"
# Observed subject->container deltas of the immutable pairs (observe_release_heads.py
# --post-tag-bindings). Consumed by the hardened ceiling and the current evaluation, never by
# the exact replay (tag-time code, tag-time inputs).
DELTA_OBSERVATIONS = "inputs/delta-observations.json"


def with_deltas(observations: dict[str, Any] | None, hardening_dir: Path | None) -> dict[str, Any] | None:
    """``observations`` with the committed delta observations overlaid (binding.overlay_deltas)."""
    if not isinstance(observations, dict) or hardening_dir is None:
        return observations
    path = hardening_dir / DELTA_OBSERVATIONS
    if not path.is_file():
        return observations
    return binding.overlay_deltas(observations, json.loads(path.read_text(encoding="utf-8")))


def load_record(hardening_dir: Path | None) -> dict[str, Any] | None:
    if hardening_dir is None:
        return None
    path = hardening_dir / TAG_SUBJECT
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def subject_of(record: dict[str, Any] | None, tag_name: str | None = None, head: str | None = None) -> dict[str, Any]:
    if record is None:
        return {"tag": tag_name, "tag_object_sha": None, "commit_sha": head, "tree_sha": None}
    return {
        "tag": record["tag"]["name"],
        "tag_object_sha": record["tag"]["object_sha"],
        "commit_sha": record["subject"]["commit_sha"],
        "tree_sha": record["subject"]["tree_sha"],
    }


def tag_sources(observations: dict[str, Any] | None, tag_observation: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Every independent observation of the tag (API observer, local git), labelled."""
    sources = []
    if isinstance(observations, dict) and isinstance(observations.get("tag"), dict):
        sources.append(dict(observations["tag"], source="observer"))
    if isinstance(tag_observation, dict):
        sources.append(dict(tag_observation, source=tag_observation.get("source", "tag-observation")))
    return sources


def select_mode(
    requested: str, record: dict[str, Any] | None, tags: list[dict[str, Any]], head_sha: str | None
) -> tuple[str, list[str]]:
    """(mode, typed blockers).

    ``auto``: POST_TAG exactly when the committed record (hardening/TAG-SUBJECT.json)
    exists; the record, not a live observation, is the lawful entry into post-tag
    semantics (a tag observed elsewhere without a record stays the PRE_TAG
    ``TAG_SHA_SPLIT`` refusal). An explicit POST_TAG without a record is the typed
    blocker ``TAG_UNRECORDED``. The tag observations are then verified against the record
    (``verify_tag_subject``), never used to choose it.
    """
    if requested == "PRE_TAG":
        return "PRE_TAG", []
    if record is not None:
        return "POST_TAG", []
    if requested == "POST_TAG":
        observed = sorted({str(t.get("sha")) for t in tags if t.get("sha")})
        return "POST_TAG", [
            f"BLOCKED:TAG_UNRECORDED:POST_TAG requested; hardening/TAG-SUBJECT.json absent (observed {','.join(observed) or 'none'})"
        ]
    return "PRE_TAG", []


def verify_tag_subject(
    record: dict[str, Any], hardening_dir: Path, tags: list[dict[str, Any]]
) -> tuple[list[str], list[str]]:
    """(refusals, blockers) binding the record to raw bytes and to every tag observation."""
    refusals: list[str] = []
    blockers: list[str] = []
    objects = gitobj.RawObjects(hardening_dir / OBJECTS)
    if objects.mismatches:
        refusals.append("REFUSED:TAG_OBJECT_DIGEST_MISMATCH:" + ",".join(objects.mismatches))
    try:
        recomputed = project_tag_subject(hardening_dir, record["release"], record["repository"])
    except (HardeningError, gitobj.GitObjectError, KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        text = str(exc)
        code = text.split(":", 1)[0] if text.split(":", 1)[0].isupper() else "TAG_OBJECT_DIGEST_MISMATCH"
        refusals.append(f"REFUSED:{code}:{text}")
        return sorted(set(refusals)), blockers
    for section, code in (
        ("tag", "TAG_MUTATED"),
        ("subject", "TAG_SUBJECT_SPLIT"),
        ("payload", "TAG_SUBJECT_SPLIT"),
        ("tag_receipt", "TAG_RECEIPT_SPLIT"),
        ("raw_objects", "TAG_OBJECT_DIGEST_MISMATCH"),
    ):
        if record.get(section) != recomputed.get(section):
            refusals.append(f"REFUSED:{code}:TAG-SUBJECT.json {section} does not recompute from raw objects")
    receipt_ref = recomputed["tag_receipt"]
    receipt_path = hardening_dir / str(receipt_ref["path"])
    from .crown import receipt_digest_of

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt_digest_of(receipt) != receipt.get("receipt_digest")
        or receipt.get("receipt_digest") != recomputed["tag"]["message_receipt_digest"]
    ):
        refusals.append(f"REFUSED:TAG_RECEIPT_SPLIT:{receipt_ref['path']} does not recompute to the tag message digest")
    if receipt.get("crown_sha") != recomputed["subject"]["commit_sha"] or receipt.get("standing") != "ALIVE":
        refusals.append(
            f"REFUSED:TAG_RECEIPT_SPLIT:tag receipt crown_sha={receipt.get('crown_sha')} "
            f"standing={receipt.get('standing')} vs tag target {recomputed['subject']['commit_sha']}"
        )
    if not tags:
        blockers.append("BLOCKED:OBSERVATION_MISSING:tag not observed (no observer tag, no --tag-observation)")
    for tag in tags:
        src = tag.get("source")
        if tag.get("error"):
            blockers.append(f"BLOCKED:OBSERVATION_MISSING:{src}:tag {tag.get('error')}")
            continue
        if tag.get("sha") is None:
            refusals.append(
                f"REFUSED:TAG_MUTATED:{src}:{record['tag']['name']} absent (recorded {record['tag']['object_sha']})"
            )
            continue
        if tag.get("sha") != record["subject"]["commit_sha"]:
            refusals.append(
                f"REFUSED:TAG_SUBJECT_SPLIT:{src}:{record['tag']['name']}^{{commit}}={tag.get('sha')} "
                f"recorded={record['subject']['commit_sha']}"
            )
        if tag.get("object_sha") is None:
            blockers.append(f"BLOCKED:OBSERVATION_MISSING:{src}:tag object id unobserved")
        elif tag.get("object_sha") != record["tag"]["object_sha"]:
            refusals.append(
                f"REFUSED:TAG_MUTATED:{src}:{record['tag']['name']}={tag.get('object_sha')} "
                f"recorded={record['tag']['object_sha']}"
            )
    return sorted(set(refusals)), sorted(set(blockers))


def verify_subject_tree(subject_dir: Path, record: dict[str, Any]) -> list[str]:
    """Every recorded subject path of the materialized tag subject hashes to its tree id."""
    refusals = []
    for path, expected in sorted(record["subject"]["paths"].items()):
        target = subject_dir / path
        actual = gitobj.tree_sha_of_dir(target) if target.is_dir() else None
        if actual != expected:
            refusals.append(f"REFUSED:SUBJECT_TREE_MISMATCH:{path}:materialized={actual}:recorded={expected}")
    return refusals


def _standing(refusals: list[str], blockers: list[str]) -> str:
    return "REFUSED" if refusals else ("BLOCKED" if blockers else "ALIVE")


def historical_standing(
    record: dict[str, Any], hardening_dir: Path, subject_dir: Path | None, root: Path
) -> dict[str, Any]:
    """Exact replay of the tag-named receipt + the hardened re-evaluation ceiling."""
    from . import crown, replay

    ref = record["tag_receipt"]
    receipt = json.loads((hardening_dir / ref["path"]).read_text(encoding="utf-8"))
    observations = json.loads((hardening_dir / ref["observations_path"]).read_text(encoding="utf-8"))
    previous = (
        json.loads((hardening_dir / ref["previous_path"]).read_text(encoding="utf-8"))
        if ref.get("previous_path")
        else None
    )
    refusals: list[str] = []
    blockers: list[str] = []
    if crown.receipt_digest_of(receipt) != ref["receipt_digest"]:
        refusals.append(f"REFUSED:TAG_RECEIPT_SPLIT:{ref['path']} digest does not recompute")
    observed_digest = digest(observations)
    if observed_digest != receipt.get("observations_digest"):
        refusals.append(
            f"REFUSED:HISTORICAL_OBSERVATION_SPLIT:{ref['observations_path']}={observed_digest} "
            f"receipt.observations_digest={receipt.get('observations_digest')}"
        )
    out: dict[str, Any] = {
        "tag_receipt": {"path": ref["path"], "receipt_digest": ref["receipt_digest"]},
        "observations": {"path": ref["observations_path"], "digest": observed_digest},
        "previous": {"path": ref.get("previous_path"), "receipt_digest": ref.get("previous_receipt_digest")},
        "replay": {"exact": False, "expected_digest": ref["receipt_digest"], "replayed_digest": None, "detail": ""},
        "standing_ceiling": None,
        "hardened": None,
    }
    commit = record["subject"]["commit_sha"]
    if subject_dir is None or not subject_dir.is_dir():
        blockers.append("BLOCKED:SUBJECT_ABSENT:no materialized tag subject (--subject-tree)")
    elif not refusals:
        tree_refusals = verify_subject_tree(subject_dir, record)
        refusals += tree_refusals
        if not tree_refusals:
            result = replay.replay(
                subject_dir, record["release"], observations, previous, commit, ref["receipt_digest"]
            )
            out["replay"] = {
                "exact": result.exact,
                "expected_digest": result.expected_digest,
                "replayed_digest": result.receipt_digest,
                "replayed_standing": result.standing,
                "detail": result.detail,
            }
            if result.refusal():
                blockers.append(str(result.refusal()))
            hardened = crown.evaluate(
                subject_dir / "release" / record["release"],
                with_deltas(observations, hardening_dir),
                previous,
                commit,
                root=subject_dir,
                mode="PRE_TAG",
            )
            out["standing_ceiling"] = hardened.standing
            out["hardened"] = {
                "standing": hardened.standing,
                "refusals": [code_of(r) for r in hardened.refusals],
                "remaining": [f"{r['id']}:{r['state']}:{r['code']}" for r in hardened.remaining],
            }
    out["refusals"] = sorted(set(refusals))
    out["blockers"] = sorted(set(blockers))
    out["standing"] = _standing(out["refusals"], out["blockers"])
    out["replay_standing"] = HISTORICAL_EXACT if out["replay"]["exact"] else HISTORICAL_DIVERGED
    return out


def tag_binding_post(record: dict[str, Any] | None, tags: list[dict[str, Any]]) -> Evaluator:
    """Post-tag AC/F tag binding: the tag equals its record and targets the recorded subject."""

    def evaluate(req: Requirement, ctx: Context) -> ReqState:
        if record is None:
            return BLOCKED("TAG_UNRECORDED", "no hardening/TAG-SUBJECT.json")
        usable = [t for t in tags if not t.get("error")]
        if not usable:
            return BLOCKED("OBSERVATION_MISSING", "tag not observed")
        name = record["tag"]["name"]
        for tag in usable:
            if tag.get("sha") is None or (tag.get("object_sha") not in (None, record["tag"]["object_sha"])):
                return REFUSED("TAG_MUTATED", f"{tag.get('source')}:{name}={tag.get('object_sha')}/{tag.get('sha')}")
            if tag.get("sha") != record["subject"]["commit_sha"]:
                return REFUSED("TAG_SUBJECT_SPLIT", f"{tag.get('source')}:{name}^{{commit}}={tag.get('sha')}")
        return in_tree_pass(
            req,
            ctx,
            f"post-tag: {name}={record['tag']['object_sha']} -> {record['subject']['commit_sha']} (recorded, immutable)",
            "post-tag tag binding",
        )

    return evaluate


def payload_refusals(root: Path, record: dict[str, Any]) -> list[str]:
    payload = record["payload"]
    actual = gitobj.tree_sha_of_dir(root / payload["path"], exclude=POST_TAG_EXCLUDES)
    if actual != payload["tree_sha"]:
        return [f"REFUSED:PAYLOAD_MUTATED_POST_TAG:{payload['path']}={actual}:tagged={payload['tree_sha']}"]
    return []


def current_conformance(
    release_dir: Path,
    observations: dict[str, Any] | None,
    parent: dict[str, Any] | None,
    head_sha: str,
    record: dict[str, Any] | None,
    tags: list[dict[str, Any]],
    *,
    root: Path,
    evaluators: dict[str, Evaluator] | None = None,
    hardening_dir: Path | None = None,
) -> dict[str, Any]:
    from . import crown

    hardening = hardening_dir if hardening_dir is not None else release_dir / "hardening"

    registry = dict(EVALUATORS if evaluators is None else evaluators)
    registry["tag_binding"] = tag_binding_post(record, tags)
    obs = (
        with_deltas(observations, hardening)
        if isinstance(observations, dict)
        else {"authority": "none (no observer run)", "repos": {}}
    )
    verdict = crown.evaluate(release_dir, obs, parent, head_sha, root=root, evaluators=registry, mode="POST_TAG")
    refusals = list(verdict.refusals)
    if record is not None:
        refusals += payload_refusals(root, record)
    refusals = sorted(set(refusals))
    drift: dict[str, Any] = {}
    if record is not None:
        tag_receipt_heads = {}
        receipt_path = hardening / record["tag_receipt"]["path"]
        if receipt_path.is_file():
            tag_receipt_heads = json.loads(receipt_path.read_text(encoding="utf-8")).get("heads", {})
        heads = verdict.receipt.get("heads", {})
        drift["moved_since_tag"] = sorted(r for r, sha in heads.items() if tag_receipt_heads.get(r) not in (None, sha))
    root_repo = verdict.receipt.get("root_repository")
    observed_root = (obs.get("repos", {}).get(root_repo) or {}).get("head_sha")
    drift["root_observed_head"] = observed_root
    drift["root_observed_head_is_attested"] = observed_root == head_sha if observed_root else None
    standing = "REFUSED" if refusals else verdict.standing
    return {"standing": standing, "refusals": refusals, "drift": drift, "receipt": verdict.receipt}
