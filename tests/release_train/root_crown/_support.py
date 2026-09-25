"""Real-file fixtures for the root crown tests (Chicago style: real files, real courts).

``alive_tree`` materializes a complete, ALIVE-shaped release tree in a temp dir: the
committed release/v26.9.25 inputs, closure rows with passing implementation courts, a
local topology receipt, an ALIVE XPROD-001 case, and re-projected outputs. The
matching ``alive_observations`` are what a clean read-only observer run would record
when every producer has landed its receipt. Every mutant test starts from it and
breaks exactly one thing.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from scripts.release_train.root_crown import projector

REPO = Path(__file__).resolve().parents[3]
RELEASE = "v26.9.25"
CROWN_SHA = "c" * 40
OBSERVED_AT = "2026-09-25T13:00:00Z"
DIGEST = "sha256:" + "a" * 64


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class Tree:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.release_dir = self.root / "release" / RELEASE

    def cleanup(self) -> None:
        self._tmp.cleanup()

    def reproject(self) -> None:
        projector.write(self.release_dir)

    def inputs(self) -> projector.Inputs:
        return projector.load_inputs(self.release_dir)


def committed_tree() -> Tree:
    tree = Tree()
    shutil.copytree(REPO / "release" / RELEASE, tree.release_dir)
    shutil.copytree(REPO / "release" / "v26.9.24", tree.root / "release" / "v26.9.24")
    return tree


def alive_case(pins: dict[str, Any]) -> dict[str, Any]:
    subjects = [
        {"repository": p["repository"], "subject_sha": p["sha"]}
        for key, p in sorted(pins["repos"].items())
        if key in {"autofde-lab", "gymact"}
    ]
    evidence = [
        {
            "evidence_id": f"E-{i}",
            "repository": s["repository"],
            "subject_sha": s["subject_sha"],
            "formalism": formalism,
            "claim_id": "CLAIM-1",
            "artifact_digest": DIGEST,
            "validator": "fixture-validator",
            "validator_digest": DIGEST,
            "result": "PASS",
        }
        for i, (s, formalism) in enumerate(zip(subjects, ["TLA+", "OCEL2"]))
    ]
    return {
        "case_id": "XPROD-001",
        "semantic_subject_id": "fixture",
        "subjects": subjects,
        "required_formalisms": ["TLA+", "OCEL2"],
        "evidence": evidence,
        "relations": [{"relation_id": "R-1", "left": "TLA+", "right": "OCEL2", "claim_id": "CLAIM-1"}],
        "mutants": [],
    }


def alive_tree() -> Tree:
    tree = committed_tree()
    closure = load(tree.release_dir / "closure.json")
    for row in closure["subjects"]:
        row["impl_standing"] = "ALIVE"
        row.pop("impl_type", None)
        row["courts"] = [{"court": "fixture-court", "result": "PASS", "sha": row["sha"], "required": True}]
    dump(tree.release_dir / "closure.json", closure)
    dump(tree.release_dir / "observations" / "TOPOLOGY-RECEIPT.json", {"standing": "ALIVE", "m_term": {"holds": True}})
    pins = load(tree.release_dir / "pins.json")
    dump(tree.root / "docs/jira/v26.9.25/xprod-cases/XPROD-001.json", alive_case(pins))
    tree.reproject()
    return tree


def alive_observations(tree: Tree, crown_sha: str = CROWN_SHA) -> dict[str, Any]:
    pins = load(tree.release_dir / "pins.json")
    reqs = load(tree.release_dir / "requirements.json")["requirements"]
    repos = {}
    for pin in pins["repos"].values():
        head = crown_sha if pin.get("root") else pin["sha"]
        repos[pin["repository"]] = {
            "pin_sha": pin["sha"],
            "default_branch": pin["ref"],
            "head_sha": head,
            "compare_status": "identical",
            "visibility": pin.get("visibility", "public"),
        }
    artifacts = {}
    for req in reqs:
        locator = req["evidence_locator"]
        if locator.startswith("local:"):
            continue
        repo = locator.partition(":")[0]
        head = repos[repo]["head_sha"]
        artifacts[locator] = {
            "sha256": "b" * 64,
            "head_sha": head,
            "subject_compare": "identical",
            "json": {
                "standing": "ALIVE",
                "subject_sha": head,
                "transport_receipt": DIGEST,
                "execution_receipt": DIGEST,
            },
        }
    case = load(tree.root / "docs/jira/v26.9.25/xprod-cases/XPROD-001.json")
    subjects = {f"{s['repository']}@{s['subject_sha']}": "identical" for s in case["subjects"]}
    return {
        "schema": "https://chatman.dev/root-crown/observations/v1",
        "release": RELEASE,
        "observed_at": OBSERVED_AT,
        "authority": "fixture",
        "environment": {"cold": True, "run_id": "fixture"},
        "repos": repos,
        "artifacts": artifacts,
        "subjects": subjects,
        "tag": {"name": RELEASE, "sha": None},
        "local_worktrees": {"observed_at": "2026-09-25T12:00:00Z", "source": "fixture", "worktrees": []},
    }
