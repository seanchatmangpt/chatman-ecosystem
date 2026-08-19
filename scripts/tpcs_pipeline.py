#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "catalog" / "tpcs.toml"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_STANDING = {"UNKNOWN", "PARTIAL_ALIVE", "ALIVE", "BLOCKED", "BUILD_BROKEN", "UNSUPPORTED"}


class FederationRefusal(RuntimeError):
    pass


def load_config(path: Path = CONFIG) -> dict[str, Any]:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _refuse(cfg: dict[str, Any], key: str, detail: str) -> None:
    raise FederationRefusal(f"{cfg['refusals'][key]}: {detail}")


def validate_config(cfg: dict[str, Any]) -> None:
    if cfg.get("version") != "tpcs-federation/1" or cfg.get("role") != "composition-and-standing":
        _refuse(cfg, "invalid_contract", "wrong federation identity")
    if cfg.get("canonical_repo") != "seanchatmangpt/tcps" or cfg.get("canonical_pr") != 1:
        _refuse(cfg, "invalid_contract", "canonical TCPS coordinate changed")
    if not SHA40.fullmatch(str(cfg.get("canonical_head", ""))):
        _refuse(cfg, "invalid_contract", "canonical head is not an exact SHA")
    if not SHA40.fullmatch(str(cfg.get("projector_sha", ""))):
        _refuse(cfg, "invalid_contract", "projector is not exact-SHA bound")
    if cfg.get("canonical_standing") not in ALLOWED_STANDING:
        _refuse(cfg, "invalid_contract", "standing vocabulary is not admitted")
    for forbidden in ("implementation_code_allowed", "actuation_authority", "acceptance_mutation_authority", "wip_mutation_authority"):
        if cfg.get(forbidden) is not False:
            _refuse(cfg, "authority_escalation", f"{forbidden} must remain false")
    if cfg.get("zero_unreceipted_actuation") is not True:
        _refuse(cfg, "authority_escalation", "zero-unreceipted-actuation must remain true")
    ownership = cfg.get("ownership", {})
    if ownership.get("factory") != cfg["canonical_repo"] or ownership.get("composition") != "seanchatmangpt/chatman-ecosystem":
        _refuse(cfg, "invalid_contract", "ownership boundary drift")
    capabilities = cfg.get("capabilities", {}).get("required", [])
    if not capabilities or len(capabilities) != len(set(capabilities)) or not all(isinstance(x, str) and x for x in capabilities):
        _refuse(cfg, "invalid_contract", "capability closure must be unique and non-empty")
    evidence = cfg.get("evidence", {})
    head = cfg["canonical_head"]
    if evidence.get("runtime_artifact") != f"tcps-runtime-{head}":
        _refuse(cfg, "invalid_contract", "runtime artifact identity drift")
    if evidence.get("projection_artifact") != f"tcps-projection-{head}":
        _refuse(cfg, "invalid_contract", "projection artifact identity drift")
    if evidence.get("runtime_receipt_required") is not True or evidence.get("projection_receipt_required") is not True:
        _refuse(cfg, "invalid_contract", "both canonical receipt rails are mandatory")


def _load_optional(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("receipt must be a JSON object")
    return value


def verify_runtime_receipt(receipt: dict[str, Any], cfg: dict[str, Any]) -> None:
    if receipt.get("schema") != "tcps.exact-subject.v1":
        _refuse(cfg, "runtime_receipt", "runtime receipt schema mismatch")
    if receipt.get("subject_sha") != cfg["canonical_head"]:
        _refuse(cfg, "identity_drift", "runtime receipt subject differs from canonical head")
    if receipt.get("verifier_state") != "ALIVE" or receipt.get("failure_count") != 0:
        _refuse(cfg, "runtime_receipt", "canonical runtime verifier is not ALIVE")
    if not SHA64.fullmatch(str(receipt.get("verifier_sha256", ""))):
        _refuse(cfg, "runtime_receipt", "verifier report digest missing")


def verify_projection_receipt(receipt: dict[str, Any], cfg: dict[str, Any]) -> None:
    if receipt.get("schema") != "tcps.ggen-projection.v1":
        _refuse(cfg, "projection_receipt", "projection receipt schema mismatch")
    if receipt.get("subject_sha") != cfg["canonical_head"]:
        _refuse(cfg, "identity_drift", "projection receipt subject differs from canonical head")
    if receipt.get("projector_sha") != cfg["projector_sha"]:
        _refuse(cfg, "projection_receipt", "ggen projector identity drift")
    if receipt.get("projection_differences") != 0 or receipt.get("state") != "ALIVE":
        _refuse(cfg, "projection_receipt", "ggen projection is not exact zero-diff ALIVE")
    for field in ("generated_contract_py_sha256", "generated_contract_md_sha256"):
        if not SHA64.fullmatch(str(receipt.get(field, ""))):
            _refuse(cfg, "projection_receipt", f"{field} missing")


def evaluate(
    cfg: dict[str, Any],
    runtime_receipt: dict[str, Any] | None = None,
    projection_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_config(cfg)
    if runtime_receipt is not None:
        verify_runtime_receipt(runtime_receipt, cfg)
    if projection_receipt is not None:
        verify_projection_receipt(projection_receipt, cfg)
    evidence_bound = runtime_receipt is not None and projection_receipt is not None
    state = "ALIVE" if evidence_bound else "PARTIAL_ALIVE"
    body = {
        "schema": "chatman.tpcs-federation.v1",
        "canonical_repo": cfg["canonical_repo"],
        "canonical_pr": cfg["canonical_pr"],
        "canonical_ref": cfg["canonical_ref"],
        "canonical_head": cfg["canonical_head"],
        "canonical_version": cfg["canonical_version"],
        "owning_court": cfg["owning_court"],
        "projector_sha": cfg["projector_sha"],
        "required_capabilities": cfg["capabilities"]["required"],
        "runtime_receipt_bound": runtime_receipt is not None,
        "projection_receipt_bound": projection_receipt is not None,
        "runtime_receipt_digest": canonical_sha256(runtime_receipt) if runtime_receipt is not None else None,
        "projection_receipt_digest": canonical_sha256(projection_receipt) if projection_receipt is not None else None,
        "implementation_authority": False,
        "actuation_authority": False,
        "zero_unreceipted_actuation": True,
        "state": state,
    }
    return {**body, "report_sha256": canonical_sha256(body)}


def self_test(cfg: dict[str, Any]) -> None:
    validate_config(cfg)
    assert evaluate(cfg)["state"] == "PARTIAL_ALIVE"
    runtime = {
        "schema": "tcps.exact-subject.v1",
        "subject_sha": cfg["canonical_head"],
        "verifier_state": "ALIVE",
        "failure_count": 0,
        "verifier_sha256": "a" * 64,
    }
    projection = {
        "schema": "tcps.ggen-projection.v1",
        "subject_sha": cfg["canonical_head"],
        "projector_sha": cfg["projector_sha"],
        "projection_differences": 0,
        "generated_contract_py_sha256": "b" * 64,
        "generated_contract_md_sha256": "c" * 64,
        "state": "ALIVE",
    }
    assert evaluate(cfg, runtime, projection)["state"] == "ALIVE"
    stale = dict(runtime)
    stale["subject_sha"] = "0" * 40
    try:
        evaluate(cfg, stale, projection)
    except FederationRefusal as exc:
        assert str(exc).startswith(cfg["refusals"]["identity_drift"])
    else:
        raise AssertionError("stale runtime subject must be refused")


def main() -> int:
    parser = argparse.ArgumentParser(description="TCPS canonical-factory federation verifier")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--runtime-receipt")
    parser.add_argument("--projection-receipt")
    parser.add_argument("--out")
    args = parser.parse_args()
    cfg = load_config()
    if args.self_test:
        self_test(cfg)
        print("TPCS_FEDERATION_SELF_TEST_ALIVE")
        return 0
    runtime = _load_optional(args.runtime_receipt)
    projection = _load_optional(args.projection_receipt)
    report = evaluate(cfg, runtime, projection)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
