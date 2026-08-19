#!/usr/bin/env python3
"""Admit a repository's thin projection of the canonical capability graph.

The capability definition remains in chatman-ecosystem. Owning repositories
carry only an ownership projection pinned to an exact control-plane subject.
This verifier proves correspondence and authority ceilings; it never promotes
an operational capability to ALIVE and never performs consequential DO.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import tomllib
from typing import Any

ALLOWED_LOCAL_STANDING = {
    "UNKNOWN", "CANDIDATE", "PARTIAL_ALIVE", "BLOCKED", "UNSUPPORTED"
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
SCHEMA = "chatman.federated-capability-owner.v1"
CONTROL_REPOSITORY = "seanchatmangpt/chatman-ecosystem"


class FederationError(RuntimeError):
    pass


def git_head(root: pathlib.Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise FederationError("REFUSED:CONTROL_PLANE_GIT_IDENTITY_UNAVAILABLE")
    value = completed.stdout.strip()
    if not HEX40.fullmatch(value):
        raise FederationError("REFUSED:CONTROL_PLANE_GIT_IDENTITY_INVALID")
    return value


def load_toml(path: pathlib.Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_capabilities(control_root: pathlib.Path) -> list[dict[str, Any]]:
    verifier_path = control_root / "scripts" / "verify_capabilities.py"
    spec = importlib.util.spec_from_file_location("verify_capabilities", verifier_path)
    if spec is None or spec.loader is None:
        raise FederationError("REFUSED:CAPABILITY_VERIFIER_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify(module.load_default(control_root))


def registered_owner_ids(control_root: pathlib.Path) -> set[str]:
    payload = load_toml(control_root / "catalog" / "repositories.toml")
    return {item.get("id", "") for item in payload.get("repository", [])}


def normalize_repo_name(value: str) -> str:
    return value.rsplit("/", 1)[-1].lower()


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def admit(
    descriptor: dict[str, Any],
    control_root: pathlib.Path,
    descriptor_path: pathlib.Path,
    expected_repository: str | None = None,
) -> dict[str, Any]:
    if descriptor.get("schema") != SCHEMA:
        raise FederationError("REFUSED:FEDERATION_SCHEMA")
    if descriptor.get("version") != "26.9.1":
        raise FederationError("REFUSED:FEDERATION_VERSION")
    if descriptor.get("control_plane_repository") != CONTROL_REPOSITORY:
        raise FederationError("REFUSED:CONTROL_PLANE_REPOSITORY")

    control_sha = git_head(control_root)
    if descriptor.get("control_plane_subject") != f"git:{control_sha}":
        raise FederationError("REFUSED:CONTROL_PLANE_SUBJECT_DRIFT")

    repository = descriptor.get("repository", "")
    if not isinstance(repository, str) or "/" not in repository:
        raise FederationError("REFUSED:FEDERATED_REPOSITORY_IDENTITY")
    if expected_repository is not None and repository != expected_repository:
        raise FederationError("REFUSED:FEDERATED_REPOSITORY_MISMATCH")

    base_sha = descriptor.get("base_sha", "")
    if not isinstance(base_sha, str) or not HEX40.fullmatch(base_sha):
        raise FederationError("REFUSED:FEDERATED_BASE_IDENTITY")

    owner_id = descriptor.get("owner_id", "")
    if owner_id not in registered_owner_ids(control_root):
        raise FederationError(f"REFUSED:UNREGISTERED_CAPABILITY_OWNER:{owner_id}")

    allowed_authorities = descriptor.get("allowed_authorities", [])
    if not isinstance(allowed_authorities, list) or not all(
        isinstance(value, str) for value in allowed_authorities
    ):
        raise FederationError("REFUSED:AUTHORITY_CEILING_SHAPE")
    allowed_authorities = set(allowed_authorities)

    ambient_do = descriptor.get("ambient_do", False)
    if ambient_do is not False:
        raise FederationError("REFUSED:AMBIENT_DO")
    simulation_only = descriptor.get("simulation_only", False)
    if not isinstance(simulation_only, bool):
        raise FederationError("REFUSED:SIMULATION_BOUNDARY_SHAPE")

    items = load_capabilities(control_root)
    index = {item["id"]: item for item in items}
    canonical_owned = {item["id"] for item in items if item.get("owner") == owner_id}

    declared = descriptor.get("capability", [])
    if not isinstance(declared, list):
        raise FederationError("REFUSED:FEDERATED_CAPABILITY_SHAPE")

    seen: set[str] = set()
    declared_owned: set[str] = set()
    owner_count = 0
    source_count = 0
    short_repo = normalize_repo_name(repository)

    for projection in declared:
        cid = projection.get("id", "")
        if cid in seen:
            raise FederationError(f"REFUSED:DUPLICATE_FEDERATED_CAPABILITY:{cid}")
        seen.add(cid)
        canonical = index.get(cid)
        if canonical is None:
            raise FederationError(f"REFUSED:UNKNOWN_FEDERATED_CAPABILITY:{cid}")

        standing = projection.get("standing")
        if standing not in ALLOWED_LOCAL_STANDING:
            raise FederationError(f"REFUSED:UNEARNED_FEDERATED_STANDING:{cid}")

        relationship = projection.get("relationship")
        if relationship == "owner":
            owner_count += 1
            declared_owned.add(cid)
            if canonical.get("owner") != owner_id:
                raise FederationError(f"REFUSED:CAPABILITY_OWNER_MISMATCH:{cid}")
            authority = canonical.get("required_authority")
            if authority not in allowed_authorities:
                raise FederationError(f"REFUSED:EXACT_AUTHORITY_MISSING:{cid}:{authority}")
            if projection.get("broker_required") is not canonical.get("broker_required"):
                raise FederationError(f"REFUSED:BROKER_PROJECTION_DRIFT:{cid}")
            if projection.get("receipt_required") is not canonical.get("receipt_required"):
                raise FederationError(f"REFUSED:RECEIPT_PROJECTION_DRIFT:{cid}")
            if canonical.get("class") == "DO":
                if simulation_only:
                    raise FederationError(f"REFUSED:SIMULATION_OWNER_WITH_DO:{cid}")
                if projection.get("broker_required") is not True or projection.get("receipt_required") is not True:
                    raise FederationError(f"REFUSED:DO_WITHOUT_BROKER_RECEIPT:{cid}")
        elif relationship == "source":
            source_count += 1
            sources = {normalize_repo_name(value) for value in canonical.get("source_repositories", [])}
            if short_repo not in sources:
                raise FederationError(f"REFUSED:CAPABILITY_SOURCE_MISMATCH:{cid}")
            if projection.get("broker_required") is not False:
                raise FederationError(f"REFUSED:SOURCE_PROJECTION_IMPLIES_BROKER:{cid}")
            if projection.get("receipt_required") is not False:
                raise FederationError(f"REFUSED:SOURCE_PROJECTION_IMPLIES_RECEIPT:{cid}")
        else:
            raise FederationError(f"REFUSED:CAPABILITY_RELATIONSHIP:{cid}")

    if declared_owned != canonical_owned:
        missing = sorted(canonical_owned - declared_owned)
        extra = sorted(declared_owned - canonical_owned)
        raise FederationError(
            f"REFUSED:OWNER_CAPABILITY_COVERAGE:missing={','.join(missing)}:extra={','.join(extra)}"
        )

    if simulation_only and any(
        authority in allowed_authorities
        for authority in {"modify_external_object", "communicate", "merge", "delete", "spend", "approve", "release"}
    ):
        raise FederationError("REFUSED:SIMULATION_AUTHORITY_ESCAPE")

    return {
        "schema": "chatman.federated-capability-admission.v1",
        "repository": repository,
        "owner_id": owner_id,
        "base_sha": base_sha,
        "control_plane_subject": f"git:{control_sha}",
        "descriptor_sha256": digest(descriptor_path),
        "owned_capabilities": owner_count,
        "source_participations": source_count,
        "simulation_only": simulation_only,
        "ambient_do": False,
        "capability_standing_promoted": False,
        "standing": "ALIVE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-plane-root", type=pathlib.Path, required=True)
    parser.add_argument("--descriptor", type=pathlib.Path, required=True)
    parser.add_argument("--expected-repository")
    args = parser.parse_args()
    descriptor = load_toml(args.descriptor)
    result = admit(
        descriptor,
        args.control_plane_root,
        args.descriptor,
        expected_repository=args.expected_repository,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FederationError, OSError, tomllib.TOMLDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
