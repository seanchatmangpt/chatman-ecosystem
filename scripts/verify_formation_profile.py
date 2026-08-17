#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "catalog" / "formation.toml"

COMPONENT_PATHS = {
    "seanchatmangpt/biblegym": "src/biblegym/knowing_christ.py",
    "seanchatmangpt/ggen-marketplace": "packs/knowing-christ-formation-pack/ontology.ttl",
}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class Refused(RuntimeError):
    pass


def _literal_assignment(tree: ast.Module, name: str) -> Any:
    for node in tree.body:
        value: ast.expr | None = None
        target_name: str | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                target_name = target.id
                value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name = node.target.id
            value = node.value
        if target_name == name and value is not None:
            return ast.literal_eval(value)
    raise Refused(f"missing literal assignment {name}")


def _packet_return(tree: ast.Module) -> ast.Dict:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "knowing_christ_packet":
            for child in ast.walk(node):
                if isinstance(child, ast.Return) and isinstance(child.value, ast.Dict):
                    return child.value
    raise Refused("knowing_christ_packet must return a literal dict surface")


def _dict_value(node: ast.Dict, key: str) -> ast.expr:
    for raw_key, raw_value in zip(node.keys, node.values):
        if isinstance(raw_key, ast.Constant) and raw_key.value == key:
            return raw_value
    raise Refused(f"knowing_christ_packet missing {key}")


def parse_biblegym(source: str) -> dict[str, Any]:
    tree = ast.parse(source)
    program_id = _literal_assignment(tree, "PROGRAM_ID")
    goal = _literal_assignment(tree, "PROGRAM_GOAL")
    raw_steps = _literal_assignment(tree, "_STEPS")
    packet = _packet_return(tree)

    title = ast.literal_eval(_dict_value(packet, "title"))
    cadence = ast.literal_eval(_dict_value(packet, "cadence"))
    authority = ast.literal_eval(_dict_value(packet, "authority"))
    fences = sorted(ast.literal_eval(_dict_value(packet, "fences")))
    cross_cutting = ast.literal_eval(_dict_value(packet, "cross_cutting"))

    steps: list[dict[str, Any]] = []
    for step in raw_steps:
        steps.append(
            {
                "id": step["id"],
                "order": step["order"],
                "title": step["title"],
                "scripture_refs": list(step["scripture_refs"]),
                "definition": step["theme"],
                "practice": step["practice"],
            }
        )
    steps.sort(key=lambda item: item["order"])

    return {
        "program_id": program_id,
        "title": title,
        "goal": goal,
        "cadence": cadence,
        "authority": authority,
        "steps": steps,
        "cross_cutting": dict(sorted(cross_cutting.items())),
        "fences": fences,
    }


def _quoted_value(body: str, predicate: str) -> str:
    match = re.search(rf"{re.escape(predicate)}\s+\"([^\"]*)\"", body, re.DOTALL)
    if not match:
        raise Refused(f"missing {predicate} in Turtle block")
    return match.group(1)


def _quoted_values(body: str, predicate: str) -> list[str]:
    match = re.search(rf"{re.escape(predicate)}\s+(.*?)\s*;", body, re.DOTALL)
    if not match:
        raise Refused(f"missing {predicate} in Turtle block")
    values = re.findall(r'"([^\"]*)"', match.group(1))
    if not values:
        raise Refused(f"{predicate} has no quoted values")
    return values


def parse_marketplace(source: str) -> dict[str, Any]:
    program_match = re.search(
        r"kcf:knowing-christ-v1\s+a\s+kcf:FormationProgram\s*;(.*?)(?=\n\nkcf:step-01-)",
        source,
        re.DOTALL,
    )
    if not program_match:
        raise Refused("missing knowing-christ-v1 FormationProgram")
    program = program_match.group(1)

    step_pattern = re.compile(
        r"kcf:step-(\d{2})-([a-z0-9-]+)\s+a\s+kcf:FormationStep\s*;(.*?)(?=\n\nkcf:(?:step-\d{2}-|principle-|no-)|\Z)",
        re.DOTALL,
    )
    steps: list[dict[str, Any]] = []
    for match in step_pattern.finditer(source):
        declared_order = int(match.group(1))
        step_id = match.group(2)
        body = match.group(3)
        order_match = re.search(r"kcf:order\s+(\d+)\s*;", body)
        if not order_match:
            raise Refused(f"step {step_id} missing kcf:order")
        order = int(order_match.group(1))
        if order != declared_order:
            raise Refused(f"step {step_id} IRI/order mismatch: {declared_order} != {order}")
        steps.append(
            {
                "id": step_id,
                "order": order,
                "title": _quoted_value(body, "dcterms:title"),
                "scripture_refs": _quoted_values(body, "kcf:scriptureRef"),
                "definition": _quoted_value(body, "skos:definition"),
                "practice": _quoted_value(body, "kcf:practice"),
            }
        )
    steps.sort(key=lambda item: item["order"])

    principle_pattern = re.compile(
        r"kcf:principle-[a-z0-9-]+\s+a\s+kcf:FormationPrinciple\s*;(.*?)(?=\n\nkcf:(?:principle-|no-)|\Z)",
        re.DOTALL,
    )
    cross_cutting: dict[str, str] = {}
    for match in principle_pattern.finditer(source):
        body = match.group(1)
        code = _quoted_value(body, "kcf:principleCode")
        if code in cross_cutting:
            raise Refused(f"duplicate principleCode {code}")
        cross_cutting[code] = _quoted_value(body, "skos:definition")

    fences = sorted(set(re.findall(r'kcf:fenceCode\s+"([^\"]+)"', source)))
    return {
        "program_id": "knowing-christ-v1",
        "title": _quoted_value(program, "dcterms:title"),
        "goal": _quoted_value(program, "kcf:goal"),
        "cadence": _quoted_value(program, "kcf:cadence"),
        "authority": _quoted_value(program, "kcf:authority"),
        "steps": steps,
        "cross_cutting": dict(sorted(cross_cutting.items())),
        "fences": fences,
    }


def _semantic_findings(left: Any, right: Any, path: str = "$contract") -> list[str]:
    findings: list[str] = []
    if type(left) is not type(right):
        return [f"{path}: type {type(left).__name__} != {type(right).__name__}"]
    if isinstance(left, dict):
        left_keys = set(left)
        right_keys = set(right)
        for key in sorted(left_keys - right_keys):
            findings.append(f"{path}.{key}: missing from marketplace contract")
        for key in sorted(right_keys - left_keys):
            findings.append(f"{path}.{key}: missing from BibleGym contract")
        for key in sorted(left_keys & right_keys):
            findings.extend(_semantic_findings(left[key], right[key], f"{path}.{key}"))
        return findings
    if isinstance(left, list):
        if len(left) != len(right):
            findings.append(f"{path}: length {len(left)} != {len(right)}")
        for index, (l_value, r_value) in enumerate(zip(left, right)):
            findings.extend(_semantic_findings(l_value, r_value, f"{path}[{index}]"))
        return findings
    if left != right:
        findings.append(f"{path}: {left!r} != {right!r}")
    return findings


def _load_profile() -> dict[str, Any]:
    with PROFILE.open("rb") as handle:
        return tomllib.load(handle)


def _components(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    components: dict[str, dict[str, Any]] = {}
    for component in profile.get("component", []):
        repository = component.get("repository")
        if repository in components:
            raise Refused(f"duplicate component repository {repository}")
        if not isinstance(repository, str) or not REPO_RE.fullmatch(repository):
            raise Refused(f"invalid component repository {repository!r}")
        sha = component.get("sha")
        if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
            raise Refused(f"invalid exact component sha for {repository}: {sha!r}")
        if component.get("standing") != "CANDIDATE":
            raise Refused(f"component {repository} must remain CANDIDATE in the composition profile")
        components[repository] = component
    if set(components) != set(COMPONENT_PATHS):
        raise Refused(f"formation component set mismatch: {sorted(components)}")
    return components


def _fetch_exact(repository: str, sha: str, path: str) -> str:
    url = f"https://raw.githubusercontent.com/{repository}/{sha}/{path}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "chatman-ecosystem-formation-verifier/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise Refused(f"unable to fetch exact component {repository}@{sha}:{path}: {exc}") from exc
    return payload.decode("utf-8")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _profile_findings(profile: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    formation = profile.get("formation", {})
    interpretation = profile.get("interpretation", {})
    privacy = profile.get("privacy", {})
    findings: list[str] = []

    expected = {
        "goal": contract["goal"],
        "mode": contract["cadence"],
        "standing": "CANDIDATE",
        "authority": "SELECT_CONSTRUCT_ONLY",
        "recognition_is_goal": False,
        "results_are_spiritual_score": False,
        "conversion_is_machine_scored": False,
        "pastoral_authority_is_delegated_to_ai": False,
    }
    for key, value in expected.items():
        if formation.get(key) != value:
            findings.append(f"$profile.formation.{key}: {formation.get(key)!r} != {value!r}")

    if sorted(formation.get("fences", [])) != contract["fences"]:
        findings.append("$profile.formation.fences: profile and component contract differ")
    if interpretation.get("scripture_is_source") is not True:
        findings.append("$profile.interpretation.scripture_is_source must be true")
    if interpretation.get("llm_output_is_candidate") is not True:
        findings.append("$profile.interpretation.llm_output_is_candidate must be true")
    if interpretation.get("llm_output_has_revelation_authority") is not False:
        findings.append("$profile.interpretation.llm_output_has_revelation_authority must be false")
    for key in ("raw_confession_storage", "conversion_targeting", "psychological_manipulation"):
        if privacy.get(key) is not False:
            findings.append(f"$profile.privacy.{key} must be false")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the exact Knowing Christ formation profile")
    parser.add_argument(
        "--check-refs",
        action="store_true",
        help="Fetch component source files at the exact SHAs declared in catalog/formation.toml",
    )
    parser.add_argument("--biblegym-file", type=Path)
    parser.add_argument("--marketplace-file", type=Path)
    args = parser.parse_args(argv)

    try:
        profile = _load_profile()
        components = _components(profile)

        if args.check_refs:
            biblegym_component = components["seanchatmangpt/biblegym"]
            marketplace_component = components["seanchatmangpt/ggen-marketplace"]
            biblegym_source = _fetch_exact(
                "seanchatmangpt/biblegym",
                biblegym_component["sha"],
                COMPONENT_PATHS["seanchatmangpt/biblegym"],
            )
            marketplace_source = _fetch_exact(
                "seanchatmangpt/ggen-marketplace",
                marketplace_component["sha"],
                COMPONENT_PATHS["seanchatmangpt/ggen-marketplace"],
            )
        else:
            if args.biblegym_file is None or args.marketplace_file is None:
                raise Refused("offline verification requires --biblegym-file and --marketplace-file")
            biblegym_source = args.biblegym_file.read_text(encoding="utf-8")
            marketplace_source = args.marketplace_file.read_text(encoding="utf-8")

        biblegym_contract = parse_biblegym(biblegym_source)
        marketplace_contract = parse_marketplace(marketplace_source)
        findings = _semantic_findings(biblegym_contract, marketplace_contract)
        findings.extend(_profile_findings(profile, marketplace_contract))

        canonical = json.dumps(marketplace_contract, sort_keys=True, separators=(",", ":"))
        receipt = {
            "schema": "chatman-ecosystem.formation-correspondence/1",
            "subject": os.environ.get("ECOSYSTEM_SUBJECT_SHA", "UNBOUND_LOCAL_SUBJECT"),
            "profile": str(PROFILE.relative_to(ROOT)),
            "components": [
                {
                    "repository": repository,
                    "sha": components[repository]["sha"],
                    "path": COMPONENT_PATHS[repository],
                    "source_sha256": _sha256(
                        biblegym_source if repository == "seanchatmangpt/biblegym" else marketplace_source
                    ),
                }
                for repository in sorted(components)
            ],
            "contract_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "step_count": len(marketplace_contract["steps"]),
            "principle_count": len(marketplace_contract["cross_cutting"]),
            "fence_count": len(marketplace_contract["fences"]),
            "findings": findings,
            "standing": "ALIVE" if not findings else "REFUSED",
        }
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0 if not findings else 2
    except (OSError, SyntaxError, ValueError, Refused) as exc:
        print(
            json.dumps(
                {
                    "schema": "chatman-ecosystem.formation-correspondence/1",
                    "standing": "REFUSED",
                    "findings": [str(exc)],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
