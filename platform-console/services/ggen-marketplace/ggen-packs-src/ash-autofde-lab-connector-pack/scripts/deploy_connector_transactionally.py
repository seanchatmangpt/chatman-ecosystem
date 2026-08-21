#!/usr/bin/env python3
"""Transactional filesystem boundary for ``add_connector.py --deploy``.

The existing deploy command owns generation and bridge semantics. This wrapper owns only
rollback across the three authored filesystem surfaces that command may mutate:
``ontology.ttl``, the XaaS generated resource destination, and ``sparql_bridge.ex``.
It never broadens actuation authority or invents connector behavior.
"""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PACK_DIR = Path(__file__).resolve().parent.parent
ADD_CONNECTOR = Path(__file__).resolve().parent / "add_connector.py"
ONTOLOGY_PATH = PACK_DIR / "ontology.ttl"
XAAS_ROOT = Path(os.environ.get("XAAS_ROOT", str(Path.home() / "xaas")))
SPARQL_BRIDGE_PATH = XAAS_ROOT / "lib" / "xaas" / "sparql_bridge.ex"


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    existed: bool
    content: bytes | None

    @classmethod
    def capture(cls, path: Path) -> "FileSnapshot":
        if path.exists():
            return cls(path=path, existed=True, content=path.read_bytes())
        return cls(path=path, existed=False, content=None)

    def restore(self) -> None:
        if self.existed:
            assert self.content is not None
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_bytes(self.content)
        elif self.path.exists():
            self.path.unlink()


def snake(name: str) -> str:
    return name.replace("-", "_")


def output_path_for(tool_name: str) -> Path:
    if "__" not in tool_name:
        raise ValueError("tool name must contain '__'")
    _, short_name = tool_name.split("__", 1)
    relative = Path("lib") / "xaas" / "operations" / f"autofde_planner_{snake(short_name)}.ex"
    return XAAS_ROOT / relative


def restore_all(snapshots: list[FileSnapshot], reason: str) -> None:
    failures: list[str] = []
    for snapshot in reversed(snapshots):
        try:
            snapshot.restore()
        except OSError as exc:
            failures.append(f"{snapshot.path}: {exc}")
    if failures:
        raise RuntimeError(
            "ROLLBACK_FAILED after " + reason + ": " + "; ".join(failures)
        )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0].startswith("-"):
        print("usage: deploy_connector_transactionally.py <tool-name>", file=sys.stderr)
        return 2

    tool_name = args[0]
    try:
        xaas_resource_path = output_path_for(tool_name)
    except ValueError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    snapshots = [
        FileSnapshot.capture(ONTOLOGY_PATH),
        FileSnapshot.capture(xaas_resource_path),
        FileSnapshot.capture(SPARQL_BRIDGE_PATH),
    ]

    result = subprocess.run(
        [sys.executable, str(ADD_CONNECTOR), tool_name, "--deploy"],
        cwd=PACK_DIR,
        env=os.environ.copy(),
        text=True,
    )
    if result.returncode == 0:
        print(
            f"OK: transactional connector deploy committed filesystem state for '{tool_name}'"
        )
        return 0

    try:
        restore_all(snapshots, f"child exit {result.returncode}")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 3

    print(
        f"ROLLED BACK: connector deploy for '{tool_name}' exited {result.returncode}; "
        "ontology, XaaS resource, and SparqlBridge restored to their exact pre-run state",
        file=sys.stderr,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
