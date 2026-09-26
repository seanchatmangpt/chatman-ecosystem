"""Durability scan: U-11 (cold reconstruction) and U-14 (hidden local state).

U-11 fails while any receipt the loop consumes lives only in a retention-bound store:
an Actions artifact upload with ``retention-days``, a chain parent read back with
``gh run download``, or an edge whose evidence is an https artifact URL (RFC-0005 §12:
crown chain receipts stored only as Actions artifacts).

U-14 fails while the path depends on state that exists only on an operator host:
observations whose observer/authority is ``operator-local``, or an observe/repair edge
whose evidence is supplied by a person (RFC-0005 §12: ``test_loop`` re-evidence by hand).
"""

from __future__ import annotations

import re
from typing import Any

from .edges import is_operational_dependency

_RETENTION = re.compile(r"^\s*retention-days:\s*\d+")
_UPLOAD = re.compile(r"uses:\s*actions/upload-artifact@")
_RUN_DOWNLOAD = re.compile(r"gh run download")
_ARTIFACT_URL = re.compile(r"^https://github\.com/[^/]+/[^/]+/actions/runs/\d+/artifacts")


def non_durable_receipts(workflow_text: str, edges: list[dict[str, Any]]) -> list[str]:
    out = []
    lines = workflow_text.splitlines()
    uploads = [i for i, line in enumerate(lines, start=1) if _UPLOAD.search(line)]
    for number, line in enumerate(lines, start=1):
        if _RETENTION.match(line) and uploads:
            out.append(f"workflow:{number}:artifact-retention")
        if _RUN_DOWNLOAD.search(line):
            out.append(f"workflow:{number}:chain-parent-from-artifact")
    for edge in edges:
        if _ARTIFACT_URL.match(edge["evidence"]["locator"]):
            out.append(f"edge:{edge['id']}:actions-artifact")
    return sorted(out)


def hidden_local_state(observations: dict[str, Any], edges: list[dict[str, Any]]) -> list[str]:
    out = []
    for key in ("private_repos", "local_worktrees"):
        block = observations.get(key) or {}
        who = f"{block.get('observer', '')} {block.get('authority', '')}"
        if "operator-local" in who:
            out.append(f"observations:{key}:operator-local")
    for edge in edges:
        if edge["stage"] in ("observe", "repair") and is_operational_dependency(edge):
            out.append(f"edge:{edge['id']}:hand-supplied-{edge['stage']}")
    return sorted(out)
