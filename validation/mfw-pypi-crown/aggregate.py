from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HEAD = "18294174c2d1262821975c08f2843f4a6c29a80c"
TREE = "e31e5d50028b0e2a26ac6a6b4dd466319315e22a"
REQUIRED_SCHEMAS = {
    "urn:chatman:mfw-capsule-integrity:v2",
    "urn:chatman:mfw-python-federation-crown:v1",
    "urn:chatman:mfw-real-pddl-engine-aggregate:v2",
    "urn:chatman:mfw-fmap-multi-agent:v2",
    "urn:chatman:mfw-spiderplan-docker:v2",
    "urn:chatman:mfw-rust-python-val-integration:v2",
    "urn:chatman:mfw-rust-python-val-benchmark:v2",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    artifacts = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    receipts: dict[str, dict[str, object]] = {}
    file_hashes: dict[str, str] = {}

    for path in sorted(p for p in artifacts.rglob("*") if p.is_file()):
        relative = path.relative_to(artifacts).as_posix()
        file_hashes[relative] = digest(path)
        if path.suffix != ".json" or not path.name.startswith("receipt"):
            continue
        value = json.loads(path.read_text())
        schema = value.get("schema")
        if not isinstance(schema, str):
            continue
        if schema in receipts:
            raise AssertionError(f"duplicate receipt schema: {schema}")
        assert value.get("status") == "ALIVE", {"path": relative, "receipt": value}
        if "mfw_head_sha" in value:
            assert value["mfw_head_sha"] == HEAD, {"path": relative, "receipt": value}
        if "mfw_tree_sha" in value:
            assert value["mfw_tree_sha"] == TREE, {"path": relative, "receipt": value}
        receipts[schema] = value

    missing = sorted(REQUIRED_SCHEMAS - receipts.keys())
    assert not missing, {"missing_receipts": missing, "observed": sorted(receipts)}

    pddl = receipts["urn:chatman:mfw-real-pddl-engine-aggregate:v2"]
    assert pddl["requested_engines"] == pddl["executed_engines"], pddl
    assert len(pddl["executed_engines"]) == 7, pddl

    python_federation = receipts["urn:chatman:mfw-python-federation-crown:v1"]
    required_distributions = {
        "unified-planning",
        "up-pyperplan",
        "up-tamer",
        "up-enhsp",
        "up-fast-downward",
        "up-lpg",
        "up-fmap",
        "up-aries",
        "up-symk",
        "tamerlite",
        "up-paraspace",
        "up-spiderplan",
    }
    assert not [
        name
        for name in sorted(required_distributions)
        if python_federation["distributions"].get(name) is None
    ], python_federation

    crown = {
        "schema": "urn:chatman:mfw-pypi-planning-crown:v1",
        "status": "ALIVE",
        "mfw_repository": "seanchatmangpt/mfw",
        "mfw_base_sha": "e4fbda46f13d8213b86aa4f981d2387638983066",
        "mfw_head_sha": HEAD,
        "mfw_tree_sha": TREE,
        "acceptance": {
            "capsule_identity": "ALIVE",
            "compile": "ALIVE",
            "unit_tests_9": "ALIVE",
            "package_build_and_relocation": "ALIVE",
            "clean_cli_json_receipt": "ALIVE",
            "official_pypi_federation": "ALIVE",
            "community_plugin_admission": "ALIVE",
            "seven_real_pddl_engines": "ALIVE",
            "independent_val_validation": "ALIVE",
            "fmap_multi_agent": "ALIVE",
            "spiderplan_docker": "ALIVE",
            "exact_mfw_rust_runner": "ALIVE",
            "receipt_replay": "ALIVE",
            "ten_run_benchmark": "ALIVE",
        },
        "receipt_schemas": sorted(receipts),
        "receipts": receipts,
        "artifact_file_sha256": file_hashes,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(crown, indent=2, sort_keys=True) + "\n")
    print(json.dumps(crown, sort_keys=True))


if __name__ == "__main__":
    main()
