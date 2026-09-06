#!/usr/bin/env python3
"""Verify the Zephyr West workspace as a composition surface.

The verifier checks identity/policy correspondence only. It never grants component
ALIVE standing and never actuates external systems.
"""

from __future__ import annotations

import argparse
import configparser
import copy
import json
import re
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from west.manifest import Manifest

ROOT = Path(__file__).resolve().parents[1]
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _repo_name(url: str) -> str:
    return url.rstrip("/").removesuffix(".git").split("/")[-1]


def _project_repo(project: Any) -> str:
    return project.url.rstrip("/").removesuffix(".git")


def _import_specs(root_data: dict[str, Any]) -> list[dict[str, str]]:
    spec = root_data.get("manifest", {}).get("self", {}).get("import", [])
    if isinstance(spec, (str, dict)):
        spec = [spec]
    result: list[dict[str, str]] = []
    for item in spec or []:
        if isinstance(item, str):
            result.append({"file": item, "path-prefix": ""})
        elif isinstance(item, dict) and isinstance(item.get("file"), str):
            unknown = set(item) - {"file", "path-prefix"}
            if unknown:
                raise SystemExit(
                    "REFUSED:WEST_SELF_IMPORT_MAP_UNSUPPORTED_BY_LOCAL_VERIFIER:"
                    + ",".join(sorted(unknown))
                )
            result.append(
                {"file": item["file"], "path-prefix": str(item.get("path-prefix", ""))}
            )
        else:
            raise SystemExit("REFUSED:WEST_SELF_IMPORT_INVALID")
    return result


def _resolve_import_project(
    project: dict[str, Any], body: dict[str, Any], root_body: dict[str, Any], prefix: str
) -> dict[str, Any]:
    out = copy.deepcopy(project)
    imported_remotes = {r["name"]: r["url-base"] for r in body.get("remotes", [])}
    root_remotes = {r["name"]: r["url-base"] for r in root_body.get("remotes", [])}
    defaults = body.get("defaults", {})
    root_defaults = root_body.get("defaults", {})

    if "url" not in out:
        remote = out.get("remote") or defaults.get("remote") or root_defaults.get("remote")
        base = imported_remotes.get(remote) or root_remotes.get(remote)
        if not base:
            raise SystemExit(f"REFUSED:WEST_IMPORT_REMOTE_UNRESOLVED:{out['name']}:{remote}")
        repo_path = out.get("repo-path", out["name"])
        out["url"] = f"{base.rstrip('/')}/{repo_path}"
    out.pop("remote", None)
    out.pop("repo-path", None)
    out.setdefault("revision", defaults.get("revision", root_defaults.get("revision", "master")))

    project_path = PurePosixPath(str(out.get("path", out["name"])))
    if prefix:
        project_path = PurePosixPath(prefix) / project_path
    out["path"] = str(project_path)
    return out


def _resolved_manifest_data(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    """Resolve admitted repository-local self imports for offline structural checks."""
    root_data = yaml.safe_load((root / "west.yml").read_text(encoding="utf-8"))
    combined = copy.deepcopy(root_data)
    root_body = root_data["manifest"]
    imported_projects: list[dict[str, Any]] = []
    raw_projects: list[dict[str, Any]] = list(root_body.get("projects", []))
    import_names: list[str] = []

    for spec in _import_specs(root_data):
        path = root / spec["file"]
        if not path.is_file():
            raise SystemExit(f"REFUSED:WEST_IMPORT_MISSING:{path.relative_to(root)}")
        imported = yaml.safe_load(path.read_text(encoding="utf-8"))
        body = imported.get("manifest", {})
        if body.get("self") or body.get("group-filter"):
            raise SystemExit(f"REFUSED:WEST_IMPORT_SCOPE_TOO_BROAD:{path.relative_to(root)}")
        raw_projects.extend(body.get("projects", []))
        for project in body.get("projects", []):
            imported_projects.append(
                _resolve_import_project(project, body, root_body, spec["path-prefix"])
            )
        import_names.append(str(path.relative_to(root)))

    body = combined["manifest"]
    body["projects"] = imported_projects + body.get("projects", [])
    body.setdefault("self", {}).pop("import", None)
    return combined, raw_projects, import_names


def verify(root: Path = ROOT) -> dict[str, Any]:
    policy = tomllib.loads((root / "catalog/west.toml").read_text(encoding="utf-8"))
    release = tomllib.loads(
        (root / policy["boundaries"]["release_manifest"]).read_text(encoding="utf-8")
    )
    repositories = tomllib.loads((root / "catalog/repositories.toml").read_text(encoding="utf-8"))
    manifest_data, raw_projects, import_names = _resolved_manifest_data(root)
    manifest = Manifest.from_data(yaml.safe_dump(manifest_data, sort_keys=False))
    projects = list(manifest.projects)[1:]

    by_repo: dict[str, Any] = {}
    duplicate_repos: list[str] = []
    for project in projects:
        repo = _project_repo(project)
        if repo in by_repo:
            duplicate_repos.append(repo)
        by_repo[repo] = project
    if duplicate_repos:
        raise SystemExit(
            "REFUSED:WEST_DUPLICATE_PROJECT_REPOSITORY:" + ",".join(sorted(duplicate_repos))
        )

    paths = [project.path for project in projects]
    names = [project.name for project in projects]
    if len(paths) != len(set(paths)):
        raise SystemExit("REFUSED:WEST_DUPLICATE_PROJECT_PATH")
    if len(names) != len(set(names)):
        raise SystemExit("REFUSED:WEST_DUPLICATE_PROJECT_NAME")

    release_missing: list[str] = []
    release_mismatch: list[str] = []
    for component in release.get("components", []):
        repo = f"https://github.com/{component['repository']}"
        project = by_repo.get(repo)
        if project is None:
            release_missing.append(component["id"])
            continue
        userdata = project.userdata if isinstance(project.userdata, dict) else {}
        release_data = userdata.get("release", {}) if isinstance(userdata, dict) else {}
        expected_sha = component["sha"]
        if not SHA40.fullmatch(expected_sha):
            raise SystemExit(f"REFUSED:RELEASE_SHA_INVALID:{component['id']}")
        if release_data.get("sha") != expected_sha:
            release_mismatch.append(component["id"])
    if release_missing:
        raise SystemExit("REFUSED:WEST_RELEASE_COMPONENT_MISSING:" + ",".join(release_missing))
    if release_mismatch:
        raise SystemExit("REFUSED:WEST_RELEASE_SHA_MISMATCH:" + ",".join(release_mismatch))

    catalog_urls = {
        entry["url"].rstrip("/").removesuffix(".git")
        for entry in repositories.get("repository", [])
    }
    catalog_covered = sum(1 for repo in catalog_urls if repo in by_repo)

    gitmodules = root / ".gitmodules"
    submodule_repos: list[str] = []
    if gitmodules.exists():
        parser = configparser.ConfigParser()
        parser.read(gitmodules, encoding="utf-8")
        for section in parser.sections():
            if section.startswith("submodule "):
                url = parser.get(section, "url").rstrip("/").removesuffix(".git")
                submodule_repos.append(url)
                if url not in by_repo:
                    raise SystemExit("REFUSED:SUBMODULE_NOT_IN_WEST_WORKSPACE:" + _repo_name(url))

    required_features = {
        "manifest_version", "remotes", "defaults", "group_filter", "project_descriptions",
        "repo_path", "clone_depth", "groups", "submodules", "imports", "import_path_prefix",
        "userdata", "self_path", "extension_commands", "freeze", "resolve", "forall", "grep",
        "compare", "diff", "status",
    }
    features = policy["west_features"]
    missing_features = sorted(name for name in required_features if features.get(name) is not True)
    if missing_features:
        raise SystemExit("REFUSED:WEST_FEATURE_POLICY_INCOMPLETE:" + ",".join(missing_features))
    if len(import_names) < 2:
        raise SystemExit("REFUSED:WEST_IMPORT_FEATURE_UNDEREXERCISED")
    if not any(spec["path-prefix"] for spec in _import_specs(yaml.safe_load((root / "west.yml").read_text()))):
        raise SystemExit("REFUSED:WEST_IMPORT_PATH_PREFIX_UNEXERCISED")
    if not any(getattr(project, "submodules", False) for project in projects):
        raise SystemExit("REFUSED:WEST_SUBMODULE_FEATURE_UNEXERCISED")
    if not any(getattr(project, "clone_depth", None) == 1 for project in projects):
        raise SystemExit("REFUSED:WEST_SHALLOW_FEATURE_UNEXERCISED")
    if not any("repo-path" in project for project in raw_projects):
        raise SystemExit("REFUSED:WEST_REPO_PATH_FEATURE_UNEXERCISED")

    inventory = policy["inventory"]
    public_count = int(inventory["public_repository_count"])
    portfolio = [project for project in projects if "observed-github" in set(project.groups or [])]
    owned_public_surface = len(portfolio) + sum(
        1 for project in projects
        if _project_repo(project).startswith("https://github.com/seanchatmangpt/")
        and "observed-github" not in set(project.groups or []) and project.name != "mfw"
    ) + 1  # manifest repository (`self`)
    if owned_public_surface != public_count:
        raise SystemExit(f"REFUSED:WEST_PUBLIC_INVENTORY_MISMATCH:{owned_public_surface}!={public_count}")

    active = [project for project in projects if manifest.is_active(project)]
    if len(active) != len(release.get("components", [])):
        raise SystemExit(f"REFUSED:WEST_DEFAULT_FRONTIER_NOT_RELEASE_BOUND:{len(active)}")

    return {
        "status": "PARTIAL_ALIVE",
        "subject": "west.yml+imports",
        "authority": "VERIFY_ONLY",
        "actuation": "none",
        "project_count": len(projects),
        "active_project_count": len(active),
        "import_count": len(import_names),
        "imports": import_names,
        "public_repository_count": public_count,
        "public_portfolio_project_count": len(portfolio),
        "release_component_count": len(release.get("components", [])),
        "release_components_covered": len(release.get("components", [])) - len(release_missing),
        "catalog_repository_count": len(catalog_urls),
        "catalog_repositories_covered": catalog_covered,
        "legacy_submodules_covered": len(submodule_repos),
        "default_disabled_groups": policy["dfcm"]["default_disabled_groups"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = verify()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "PARTIAL_ALIVE west-workspace "
            f"projects={result['project_count']} active={result['active_project_count']} "
            f"release={result['release_components_covered']}/{result['release_component_count']} "
            f"catalog={result['catalog_repositories_covered']}/{result['catalog_repository_count']} "
            f"public={result['public_repository_count']} imports={result['import_count']} "
            f"legacy-submodules={result['legacy_submodules_covered']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
