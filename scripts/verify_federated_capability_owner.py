#!/usr/bin/env python3
"""Admit a repository's thin DfCM projection of the canonical capability graph.

The capability and release definitions remain in chatman-ecosystem. Participating
repositories carry only exact-subject projections. This court proves graph,
release-role, dependency, and authority correspondence; it never promotes an
operational capability to ALIVE and never performs consequential DO.
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
MUTATING_AUTHORITIES = {
    "modify_external_object", "communicate", "merge", "delete",
    "spend", "approve", "release",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
SCHEMA = "chatman.federated-capability-owner.v1"
DFCM_SCHEMA = "chatman.dfcm-release.v1"
CONTROL_REPOSITORY = "seanchatmangpt/chatman-ecosystem"
RELEASE_MANIFEST = pathlib.Path("release/v26.9.1/manifest.toml")
DFCM_CONTRACT = pathlib.Path("release/v26.9.1/dfcm.toml")
REQUIRED_STAGES = [
    "OBSERVE", "ADMIT", "SELECT", "CONSTRUCT", "AUTHORIZE", "DO", "RECEIPT", "REPLAY"
]


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
        raise FederationError("REFUSED:GIT_IDENTITY_UNAVAILABLE")
    value = completed.stdout.strip()
    if not HEX40.fullmatch(value):
        raise FederationError("REFUSED:GIT_IDENTITY_INVALID")
    return value


def git_is_ancestor(root: pathlib.Path, ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


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


def required_release_components(control_root: pathlib.Path) -> dict[str, dict[str, Any]]:
    payload = load_toml(control_root / RELEASE_MANIFEST)
    components = {
        item.get("id", ""): item
        for item in payload.get("components", [])
        if item.get("required") is True
    }
    if not components or "" in components:
        raise FederationError("REFUSED:RELEASE_COMPONENT_GRAPH_EMPTY")
    return components


def dfcm_profiles(control_root: pathlib.Path) -> dict[str, dict[str, Any]]:
    payload = load_toml(control_root / DFCM_CONTRACT)
    if payload.get("schema") != DFCM_SCHEMA:
        raise FederationError("REFUSED:DFCM_RELEASE_SCHEMA")
    if payload.get("version") != "26.9.1":
        raise FederationError("REFUSED:DFCM_RELEASE_VERSION")
    if payload.get("ambient_do") is not False:
        raise FederationError("REFUSED:DFCM_RELEASE_AMBIENT_DO")
    if payload.get("automatic_irreversible_do") is not False:
        raise FederationError("REFUSED:DFCM_RELEASE_AUTOMATIC_IRREVERSIBLE_DO")
    if payload.get("required_stages") != REQUIRED_STAGES:
        raise FederationError("REFUSED:DFCM_RELEASE_STAGE_CLOSURE")
    profiles = {item.get("id", ""): item for item in payload.get("component", [])}
    if not profiles or "" in profiles:
        raise FederationError("REFUSED:DFCM_RELEASE_PROFILE_EMPTY")
    return profiles


def registered_owner_ids(control_root: pathlib.Path) -> set[str]:
    payload = load_toml(control_root / "catalog" / "repositories.toml")
    declared = {item.get("id", "") for item in payload.get("repository", [])}
    for item in required_release_components(control_root).values():
        repository = item.get("repository", "")
        if isinstance(repository, str) and "/" in repository:
            declared.add(f"repository:{normalize_repo_name(repository)}")
    return declared


def normalize_repo_name(value: str) -> str:
    return value.rsplit("/", 1)[-1].lower()


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_dfcm_release(control_root: pathlib.Path, items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    release = required_release_components(control_root)
    profiles = dfcm_profiles(control_root)
    if set(profiles) != set(release):
        missing = sorted(set(release) - set(profiles))
        extra = sorted(set(profiles) - set(release))
        raise FederationError(
            f"REFUSED:DFCM_RELEASE_COMPONENT_CLOSURE:missing={','.join(missing)}:extra={','.join(extra)}"
        )

    by_owner: dict[str, set[str]] = {}
    by_id = {item["id"]: item for item in items}
    for item in items:
        by_owner.setdefault(item["owner"], set()).add(item["id"])

    for component_id, profile in profiles.items():
        manifest = release[component_id]
        for field in ("repository", "role"):
            if profile.get(field) != manifest.get(field):
                raise FederationError(f"REFUSED:DFCM_RELEASE_{field.upper()}:{component_id}")
        if profile.get("depends_on", []) != manifest.get("depends_on", []):
            raise FederationError(f"REFUSED:DFCM_RELEASE_DEPENDENCIES:{component_id}")
        authorities = profile.get("allowed_authorities")
        if not isinstance(authorities, list) or not authorities or not all(isinstance(v, str) for v in authorities):
            raise FederationError(f"REFUSED:DFCM_RELEASE_AUTHORITY_SHAPE:{component_id}")
        if not isinstance(profile.get("simulation_only"), bool):
            raise FederationError(f"REFUSED:DFCM_RELEASE_SIMULATION_SHAPE:{component_id}")
        do_mode = profile.get("do_mode")
        if do_mode not in {"none", "brokered"}:
            raise FederationError(f"REFUSED:DFCM_RELEASE_DO_MODE:{component_id}")
        owner_id = f"repository:{normalize_repo_name(profile['repository'])}"
        canonical_owned = by_owner.get(owner_id, set())
        profiled_owned = set(profile.get("owned_capabilities", []))
        if canonical_owned != profiled_owned:
            missing = sorted(canonical_owned - profiled_owned)
            extra = sorted(profiled_owned - canonical_owned)
            raise FederationError(
                f"REFUSED:DFCM_RELEASE_OWNERSHIP:{component_id}:missing={','.join(missing)}:extra={','.join(extra)}"
            )
        for cid in profiled_owned:
            if cid not in by_id:
                raise FederationError(f"REFUSED:DFCM_RELEASE_UNKNOWN_CAPABILITY:{component_id}:{cid}")
        if do_mode == "none":
            escaped = sorted(set(authorities) & MUTATING_AUTHORITIES)
            if escaped:
                raise FederationError(
                    f"REFUSED:DFCM_RELEASE_DO_ESCAPE:{component_id}:{','.join(escaped)}"
                )
            do_caps = sorted(cid for cid in profiled_owned if by_id[cid].get("class") == "DO")
            if do_caps:
                raise FederationError(
                    f"REFUSED:DFCM_RELEASE_UNBROKERED_DO:{component_id}:{','.join(do_caps)}"
                )
        else:
            do_caps = [by_id[cid] for cid in profiled_owned if by_id[cid].get("class") == "DO"]
            if not do_caps:
                raise FederationError(f"REFUSED:DFCM_RELEASE_BROKER_WITHOUT_DO:{component_id}")
            for capability in do_caps:
                if capability.get("broker_required") is not True or capability.get("receipt_required") is not True:
                    raise FederationError(
                        f"REFUSED:DFCM_RELEASE_DO_WITHOUT_BROKER_RECEIPT:{component_id}:{capability['id']}"
                    )
    return profiles


def admit(
    descriptor: dict[str, Any],
    control_root: pathlib.Path,
    descriptor_path: pathlib.Path,
    expected_repository: str | None = None,
    subject_root: pathlib.Path | None = None,
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
    caller_subject = None
    if subject_root is not None:
        caller_subject = git_head(subject_root)
        if not git_is_ancestor(subject_root, base_sha, caller_subject):
            raise FederationError("REFUSED:FEDERATED_BASE_NOT_ANCESTOR")

    owner_id = descriptor.get("owner_id", "")
    if owner_id not in registered_owner_ids(control_root):
        raise FederationError(f"REFUSED:UNREGISTERED_CAPABILITY_OWNER:{owner_id}")
    if owner_id != f"repository:{normalize_repo_name(repository)}":
        raise FederationError("REFUSED:FEDERATED_OWNER_REPOSITORY_MISMATCH")

    allowed_authorities = descriptor.get("allowed_authorities", [])
    if not isinstance(allowed_authorities, list) or not all(
        isinstance(value, str) for value in allowed_authorities
    ):
        raise FederationError("REFUSED:AUTHORITY_CEILING_SHAPE")
    allowed_authorities_set = set(allowed_authorities)

    if descriptor.get("ambient_do", False) is not False:
        raise FederationError("REFUSED:AMBIENT_DO")
    if descriptor.get("automatic_irreversible_do", False) is not False:
        raise FederationError("REFUSED:AUTOMATIC_IRREVERSIBLE_DO")
    simulation_only = descriptor.get("simulation_only", False)
    if not isinstance(simulation_only, bool):
        raise FederationError("REFUSED:SIMULATION_BOUNDARY_SHAPE")

    items = load_capabilities(control_root)
    index = {item["id"]: item for item in items}
    profiles = validate_dfcm_release(control_root, items)
    canonical_owned = {item["id"] for item in items if item.get("owner") == owner_id}

    release_component = descriptor.get("release_component")
    release_role = None
    do_mode = None
    if release_component is not None:
        profile = profiles.get(release_component)
        if profile is None:
            raise FederationError(f"REFUSED:UNKNOWN_RELEASE_COMPONENT:{release_component}")
        if profile.get("repository") != repository:
            raise FederationError("REFUSED:RELEASE_REPOSITORY_MISMATCH")
        release_role = descriptor.get("release_role")
        if release_role != profile.get("role"):
            raise FederationError("REFUSED:RELEASE_ROLE_MISMATCH")
        if descriptor.get("release_dependencies", []) != profile.get("depends_on", []):
            raise FederationError("REFUSED:RELEASE_DEPENDENCY_MISMATCH")
        if allowed_authorities != profile.get("allowed_authorities"):
            raise FederationError("REFUSED:RELEASE_AUTHORITY_MISMATCH")
        if simulation_only is not profile.get("simulation_only"):
            raise FederationError("REFUSED:RELEASE_SIMULATION_MISMATCH")
        do_mode = descriptor.get("do_mode")
        if do_mode != profile.get("do_mode"):
            raise FederationError("REFUSED:RELEASE_DO_MODE_MISMATCH")
        if set(profile.get("owned_capabilities", [])) != canonical_owned:
            raise FederationError("REFUSED:RELEASE_OWNER_CAPABILITY_DRIFT")
        if do_mode == "none" and allowed_authorities_set & MUTATING_AUTHORITIES:
            raise FederationError("REFUSED:RELEASE_MUTATING_AUTHORITY_WITHOUT_BROKER")

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
            if authority not in allowed_authorities_set:
                raise FederationError(f"REFUSED:EXACT_AUTHORITY_MISSING:{cid}:{authority}")
            if projection.get("broker_required") is not canonical.get("broker_required"):
                raise FederationError(f"REFUSED:BROKER_PROJECTION_DRIFT:{cid}")
            if projection.get("receipt_required") is not canonical.get("receipt_required"):
                raise FederationError(f"REFUSED:RECEIPT_PROJECTION_DRIFT:{cid}")
            if canonical.get("class") == "DO":
                if simulation_only:
                    raise FederationError(f"REFUSED:SIMULATION_OWNER_WITH_DO:{cid}")
                if do_mode == "none":
                    raise FederationError(f"REFUSED:UNBROKERED_RELEASE_DO:{cid}")
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

    if simulation_only and allowed_authorities_set & MUTATING_AUTHORITIES:
        raise FederationError("REFUSED:SIMULATION_AUTHORITY_ESCAPE")

    result = {
        "schema": "chatman.federated-capability-admission.v2",
        "repository": repository,
        "owner_id": owner_id,
        "base_sha": base_sha,
        "control_plane_subject": f"git:{control_sha}",
        "descriptor_sha256": digest(descriptor_path),
        "owned_capabilities": owner_count,
        "source_participations": source_count,
        "simulation_only": simulation_only,
        "ambient_do": False,
        "automatic_irreversible_do": False,
        "capability_standing_promoted": False,
        "standing": "ALIVE",
    }
    if caller_subject is not None:
        result["caller_subject"] = f"git:{caller_subject}"
        result["base_ancestry_verified"] = True
    if release_component is not None:
        result["release_component"] = release_component
        result["release_role"] = release_role
        result["do_mode"] = do_mode
        result["release_dependencies"] = descriptor.get("release_dependencies", [])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-plane-root", type=pathlib.Path, required=True)
    parser.add_argument("--descriptor", type=pathlib.Path, required=True)
    parser.add_argument("--expected-repository")
    parser.add_argument("--subject-root", type=pathlib.Path)
    args = parser.parse_args()
    descriptor = load_toml(args.descriptor)
    result = admit(
        descriptor,
        args.control_plane_root,
        args.descriptor,
        expected_repository=args.expected_repository,
        subject_root=args.subject_root,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FederationError, OSError, tomllib.TOMLDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
