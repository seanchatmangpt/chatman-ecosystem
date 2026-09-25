"""Exact replay of the tag-time crown from the materialized tag subject (no subprocess).

The tag-time evaluator is imported from ``<subject>/scripts`` in isolation: every
``scripts`` / ``scripts.*`` module is evicted from ``sys.modules``, ``sys.path`` is
reduced to the subject directory plus entries that carry no ``scripts`` package, bytecode
writing is disabled (the subject tree must stay byte-identical), and every ``scripts.*``
module loaded during the replay must resolve inside the subject. Afterwards the caller's
modules and path are restored exactly. A digest that does not recompute to the recorded
tag receipt is ``REPLAY_DIVERGED``; an import that escapes the subject is
``REPLAY_DIVERGED`` too (the replay did not run the tag-time code).
"""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Replay:
    exact: bool
    receipt_digest: str | None
    expected_digest: str
    standing: str | None
    detail: str
    receipt: dict[str, Any] | None

    def refusal(self) -> str | None:
        if self.exact:
            return None
        return f"BLOCKED:REPLAY_DIVERGED:{self.detail}"


def _is_scripts_module(name: str) -> bool:
    return name == "scripts" or name.startswith("scripts.")


def _foreign_path(entry: str, subject: Path) -> bool:
    base = Path(entry or ".").resolve()
    return base != subject and (base / "scripts").is_dir()


def replay(
    subject_dir: Path,
    release: str,
    observations: dict[str, Any],
    previous: dict[str, Any] | None,
    crown_sha: str,
    expected_digest: str,
) -> Replay:
    subject = subject_dir.resolve()
    release_dir = subject / "release" / release
    saved_modules = {k: v for k, v in sys.modules.items() if _is_scripts_module(k)}
    saved_path = list(sys.path)
    saved_bytecode = sys.dont_write_bytecode
    for name in saved_modules:
        del sys.modules[name]
    sys.path[:] = [str(subject)] + [p for p in saved_path if not _foreign_path(p, subject)]
    sys.dont_write_bytecode = True
    importlib.invalidate_caches()
    try:
        try:
            module = importlib.import_module("scripts.release_train.root_crown.crown")
            verdict = module.evaluate(release_dir, observations, previous, crown_sha, root=subject)
        except Exception as exc:  # noqa: BLE001 — a crashing tag-time evaluator is a divergence, typed
            return Replay(
                False, None, expected_digest, None, f"tag-time evaluator raised {type(exc).__name__}: {exc}", None
            )
        escaped = sorted(
            name
            for name, mod in sys.modules.items()
            if _is_scripts_module(name)
            and getattr(mod, "__file__", None)
            and not Path(mod.__file__).resolve().is_relative_to(subject)
        )
        if escaped:
            return Replay(False, None, expected_digest, None, "import escaped subject: " + ",".join(escaped[:5]), None)
        receipt = verdict.receipt
        got = receipt.get("receipt_digest")
        if got != expected_digest:
            return Replay(
                False, got, expected_digest, verdict.standing, f"replayed={got}:recorded={expected_digest}", receipt
            )
        return Replay(True, got, expected_digest, verdict.standing, "byte-identical receipt digest", receipt)
    finally:
        for name in [k for k in sys.modules if _is_scripts_module(k)]:
            del sys.modules[name]
        sys.modules.update(saved_modules)
        sys.path[:] = saved_path
        sys.dont_write_bytecode = saved_bytecode
        importlib.invalidate_caches()
