#!/usr/bin/env python3
"""Fail-closed provenance fence for transactional connector deployment.

This wrapper sits above ``deploy_connector_transactionally.py``. It refuses to
replace an existing XaaS connector module unless a sidecar receipt proves that
the bytes currently on disk are exactly the bytes previously manufactured by
this generator path. A human edit therefore removes overwrite authority until
the operator explicitly reconciles provenance.

``--check`` exposes the same admission decision as canonical JSON without
invoking the transactional child or mutating any governed filesystem surface.
The emitted admission digest binds that SELECT result to the exact governed
filesystem bytes/existence so a later CONSTRUCT can fail closed on stale input.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCHEMA = "chatman.ash-connector-provenance/1"
PREFLIGHT_SCHEMA = "chatman.ash-connector-preflight/1"
ADMISSION_STATE_SCHEMA = "chatman.ash-connector-admission-state/1"
PACK_DIR = Path(os.environ.get("CONNECTOR_PACK_DIR", str(Path(__file__).resolve().parent.parent)))
TRANSACTIONAL_DEPLOY = Path(
    os.environ.get(
        "TRANSACTIONAL_DEPLOY_PATH",
        str(Path(__file__).resolve().parent / "deploy_connector_transactionally.py"),
    )
)
ONTOLOGY_PATH = PACK_DIR / "ontology.ttl"
XAAS_ROOT = Path(os.environ.get("XAAS_ROOT", str(Path.home() / "xaas")))
SPARQL_BRIDGE_PATH = XAAS_ROOT / "lib" / "xaas" / "sparql_bridge.ex"
COMMAND_OVERRIDE = os.environ.get("CONNECTOR_TRANSACTION_CMD_OVERRIDE")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class Snapshot:
    path: Path
    existed: bool
    content: bytes | None

    @classmethod
    def capture(cls, path: Path) -> "Snapshot":
        if path.exists():
            return cls(path, True, path.read_bytes())
        return cls(path, False, None)

    def restore(self) -> None:
        if self.existed:
            assert self.content is not None
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_bytes(self.content)
        elif self.path.exists():
            self.path.unlink()


@dataclass(frozen=True)
class Admission:
    admitted: bool
    disposition: str
    reason: str


def snake(name: str) -> str:
    return name.replace("-", "_")


def output_path_for(tool_name: str) -> Path:
    if "__" not in tool_name:
        raise ValueError("tool name must contain '__'")
    _, short_name = tool_name.split("__", 1)
    return XAAS_ROOT / "lib" / "xaas" / "operations" / f"autofde_planner_{snake(short_name)}.ex"


def provenance_path_for(dest: Path) -> Path:
    return dest.with_name(dest.name + ".ggen-provenance.json")


def digest_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_receipt(tool_name: str, dest: Path, content: bytes) -> dict[str, str]:
    return {
        "schema": SCHEMA,
        "tool_name": tool_name,
        "output_file": str(dest.relative_to(XAAS_ROOT)),
        "sha256": digest_bytes(content),
    }


def state_component(label: str, path: Path) -> dict[str, object]:
    """Describe governed state without embedding machine-specific root paths."""
    if not path.exists():
        return {"label": label, "exists": False, "sha256": None}
    return {"label": label, "exists": True, "sha256": digest_bytes(path.read_bytes())}


def admission_state_digest(tool_name: str, dest: Path, sidecar: Path) -> str:
    """Bind SELECT evidence to exact governed bytes/existence, portably."""
    subject = {
        "schema": ADMISSION_STATE_SCHEMA,
        "tool_name": tool_name,
        "output_file": str(dest.relative_to(XAAS_ROOT)),
        "surfaces": [
            state_component("ontology", ONTOLOGY_PATH),
            state_component("destination", dest),
            state_component("sparql_bridge", SPARQL_BRIDGE_PATH),
            state_component("provenance", sidecar),
        ],
    }
    canonical = json.dumps(subject, sort_keys=True, separators=(",", ":")).encode()
    return digest_bytes(canonical)


def assess_existing_destination(tool_name: str, dest: Path, sidecar: Path) -> Admission:
    if not dest.exists():
        if sidecar.exists():
            return Admission(False, "refused", f"orphan provenance sidecar exists without destination: {sidecar}")
        return Admission(True, "first_write", "destination absent and no orphan provenance sidecar exists")
    if not sidecar.exists():
        return Admission(
            False,
            "refused",
            f"existing destination {dest} has no generator provenance receipt; refusing to overwrite potentially hand-authored bytes",
        )
    try:
        receipt = json.loads(sidecar.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return Admission(False, "refused", f"invalid provenance receipt {sidecar}: {exc}")
    expected = canonical_receipt(tool_name, dest, dest.read_bytes())
    if receipt != expected or not SHA256_RE.fullmatch(str(receipt.get("sha256", ""))):
        return Admission(
            False,
            "refused",
            f"provenance mismatch for {dest}; current bytes are not the exact previously-manufactured subject (possible hand edit or receipt drift)",
        )
    return Admission(True, "regenerate", "existing destination matches its exact generator provenance receipt")


def admit_existing_destination(tool_name: str, dest: Path, sidecar: Path) -> bool:
    admission = assess_existing_destination(tool_name, dest, sidecar)
    if not admission.admitted:
        print(f"REFUSED: {admission.reason}", file=sys.stderr)
    return admission.admitted


def preflight_record(
    tool_name: str,
    dest: Path,
    admission: Admission,
    admission_digest: str,
) -> dict[str, object]:
    return {
        "schema": PREFLIGHT_SCHEMA,
        "tool_name": tool_name,
        "output_file": str(dest.relative_to(XAAS_ROOT)),
        "admitted": admission.admitted,
        "disposition": admission.disposition,
        "reason": admission.reason,
        "authority": "SELECT_ONLY",
        "child_invoked": False,
        "admission_digest": admission_digest,
    }


def restore_all(snapshots: list[Snapshot], reason: str) -> bool:
    failures: list[str] = []
    for snapshot in reversed(snapshots):
        try:
            snapshot.restore()
        except OSError as exc:
            failures.append(f"{snapshot.path}: {exc}")
    if failures:
        print("ROLLBACK_FAILED after " + reason + ": " + "; ".join(failures), file=sys.stderr)
        return False
    return True


def write_receipt_atomic(sidecar: Path, receipt: dict[str, str]) -> None:
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    tmp = sidecar.with_name(sidecar.name + ".tmp")
    payload = json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n"
    tmp.write_text(payload)
    tmp.replace(sidecar)


def parse_args(args: list[str]) -> tuple[bool, str | None, str] | None:
    check_only = False
    required_digest: str | None = None
    remaining = list(args)
    if remaining[:1] == ["--check"]:
        check_only = True
        remaining = remaining[1:]
    elif remaining[:1] == ["--admission-digest"]:
        if len(remaining) < 3:
            return None
        required_digest = remaining[1]
        remaining = remaining[2:]
    if len(remaining) != 1 or remaining[0].startswith("-"):
        return None
    return check_only, required_digest, remaining[0]


def main(argv: list[str] | None = None) -> int:
    parsed = parse_args(list(sys.argv[1:] if argv is None else argv))
    if parsed is None:
        print(
            "usage: deploy_connector_with_provenance.py [--check | --admission-digest <sha256>] <tool-name>",
            file=sys.stderr,
        )
        return 2
    check_only, required_digest, tool_name = parsed
    try:
        dest = output_path_for(tool_name)
    except ValueError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    sidecar = provenance_path_for(dest)
    current_digest = admission_state_digest(tool_name, dest, sidecar)

    if check_only:
        admission = assess_existing_destination(tool_name, dest, sidecar)
        print(
            json.dumps(
                preflight_record(tool_name, dest, admission, current_digest),
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        if not admission.admitted:
            print(f"REFUSED: {admission.reason}", file=sys.stderr)
            return 1
        return 0

    if required_digest is not None:
        if not SHA256_RE.fullmatch(required_digest):
            print("REFUSED: admission digest must be exactly 64 lowercase hexadecimal characters", file=sys.stderr)
            return 1
        if current_digest != required_digest:
            print(
                "REFUSED: stale admission digest; governed filesystem state changed after preflight "
                f"expected={required_digest} actual={current_digest}",
                file=sys.stderr,
            )
            return 1

    admission = assess_existing_destination(tool_name, dest, sidecar)
    if not admission.admitted:
        print(f"REFUSED: {admission.reason}", file=sys.stderr)
        return 1

    snapshots = [
        Snapshot.capture(ONTOLOGY_PATH),
        Snapshot.capture(dest),
        Snapshot.capture(SPARQL_BRIDGE_PATH),
        Snapshot.capture(sidecar),
    ]
    cmd = json.loads(COMMAND_OVERRIDE) if COMMAND_OVERRIDE else [
        sys.executable,
        str(TRANSACTIONAL_DEPLOY),
        tool_name,
    ]
    result = subprocess.run(cmd, cwd=PACK_DIR, env=os.environ.copy(), text=True)
    if result.returncode != 0:
        if not restore_all(snapshots, f"child exit {result.returncode}"):
            return 3
        return result.returncode
    if not dest.exists():
        print(f"REFUSED: transactional deploy returned success but destination is absent: {dest}", file=sys.stderr)
        restore_all(snapshots, "missing destination after successful child")
        return 1
    try:
        write_receipt_atomic(sidecar, canonical_receipt(tool_name, dest, dest.read_bytes()))
    except OSError as exc:
        print(f"REFUSED: could not persist provenance receipt: {exc}", file=sys.stderr)
        return 3 if not restore_all(snapshots, "provenance receipt write failure") else 1
    print(f"OK: connector deployment committed with provenance receipt {sidecar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
