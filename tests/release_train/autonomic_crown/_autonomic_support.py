"""Real-collaborator fixtures for the autonomic crown tests (Chicago style).

Every evaluation reads real bytes: the committed ``release/<v>/autonomy`` inputs and the
root repository's own git object database (``DURABLE_LOCATOR_REPOS_ROOT``, the same
variable the root-crown workflow exports; else this checkout when it is a git work tree).
Without an object database the dependent tests are a *named* skip, never a fake source.
"""

from __future__ import annotations

import atexit
import json
import os
import shutil
import tempfile
import unittest
from functools import lru_cache
from pathlib import Path
from typing import Any

from scripts.release_train.autonomic_crown import court

REPO = Path(__file__).resolve().parents[3]
RELEASE = "v26.9.25"
RELEASE_DIR = REPO / "release" / RELEASE
AUTONOMY = RELEASE_DIR / "autonomy"
RECEIPT = AUTONOMY / "autonomic-receipt.json"
WORKFLOW = REPO / ".github" / "workflows" / "root-crown.yml"
NO_DB = "no root git object database (set DURABLE_LOCATOR_REPOS_ROOT or run in a git checkout)"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def repos_root() -> Path | None:
    env = os.environ.get("DURABLE_LOCATOR_REPOS_ROOT")
    if env and (Path(env) / "chatman-ecosystem").exists():
        return Path(env)
    if (REPO / ".git").exists():
        tmp = Path(tempfile.mkdtemp(prefix="autonomic-test-repos-"))
        atexit.register(shutil.rmtree, tmp, True)
        os.symlink(REPO, tmp / "chatman-ecosystem")
        return tmp
    return None


def committed_inputs(test: unittest.TestCase, **kw: Any) -> court.Inputs:
    root = repos_root()
    if root is None:
        test.skipTest(NO_DB)
    return court.load_inputs(REPO, RELEASE, root, **kw)


_EVAL: dict[str, court.Evaluation] = {}


def committed_evaluation(test: unittest.TestCase, self_attack: bool = False) -> court.Evaluation:
    """One shared evaluation per mode (the court is deterministic over immutable inputs)."""
    key = "full" if self_attack else "nested"
    if key not in _EVAL:
        _EVAL[key] = court.evaluate(committed_inputs(test), self_attack=self_attack)
    return _EVAL[key]
