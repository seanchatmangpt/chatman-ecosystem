#!/usr/bin/env python3
"""Fail-closed admission for live Azure authority proven through GymAct + BRCE.

This verifier removes the old control-plane dead end where Azure could only be
represented as permanently BLOCKED. It does not grant authority. Instead it
admits an ALIVE transition only when an exact GymAct subject, an explicit
bounded Azure DO scope, a live probe, and replayable BRCE evidence are all
present in the authority record. A missing record remains a typed BLOCKED
state and is valid configuration, never silently upgraded.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "chatman-ecosystem.live-azure-authority/1"
DEFAULT_PATH = Path("release/v26.9.1/live-azure-authority.json")
EXPECTED_GYMACT_REPOSITORY = "seanchatmangpt/gymact"
EXPECTED_GYMACT_SHA = "ac436398003630907530331a1eca2d71c3fd50dc"
EXPECTED_PROVIDER = "platform-console-ontology"
EXPECTED_PROVIDER_BLOB_SHA = "efd02f211809c8e8aabd75967b443203f1fcf027"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9_.-]+:[^\s]+$")
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
SECRET_KEYS = {
    "client_secret",
    "secret",
    "password",
    "access_token",
    "refresh_token",
    "credential",
    "credentials",
}


class AzureAuthorityRefusal(ValueError):
    pass


def _refuse(code: str) -> None:
    raise AzureAuthorityRefusal(f"REFUSED:{code}")


def _require_exact_keys(value: Any, required: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _refuse(f"{label}_INVALID")
    keys = set(value)
    missing = sorted(required - keys)
    extra = sorted(keys - required)
    if missing:
        _refuse(f"{label}_KEY_MISSING:" + ",".join(missing))
    if extra:
        _refuse(f"{label}_KEY_UNADMITTED:" + ",".join(extra))
    return value


def _reject_secret_material(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in SECRET_KEYS:
                _refuse(f"SECRET_MATERIAL_FORBIDDEN:{path}.{key}")
            _reject_secret_material(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_material(child, f"{path}[{index}]")


def _validate_gymact_subject(value: Any) -> dict[str, Any]:
    subject = _require_exact_keys(
        value,
        {"repository", "sha", "provider", "provider_blob_sha"},
        "GYMACT_SUBJECT",
    )
    if subject["repository"] != EXPECTED_GYMACT_REPOSITORY:
        _refuse("GYMACT_REPOSITORY_MISMATCH")
    if subject["sha"] != EXPECTED_GYMACT_SHA or not SHA_RE.fullmatch(subject["sha"]):
        _refuse("GYMACT_SUBJECT_MISMATCH")
    if subject["provider"] != EXPECTED_PROVIDER:
        _refuse("GYMACT_PROVIDER_MISMATCH")
    if subject["provider_blob_sha"] != EXPECTED_PROVIDER_BLOB_SHA:
        _refuse("GYMACT_PROVIDER_BLOB_MISMATCH")
    return subject


def _validate_token(value: Any, label: str) -> str:
    if not isinstance(value, str) or not TOKEN_RE.fullmatch(value):
        _refuse(label)
    return value


def _validate_uuid(value: Any, label: str) -> str:
    if not isinstance(value, str) or not UUID_RE.fullmatch(value):
        _refuse(label)
    return value


def _validate_authority(value: Any, subject: dict[str, Any]) -> dict[str, Any]:
    authority = _require_exact_keys(
        value,
        {
            "authority_class",
            "authority_ref",
            "scopes",
            "azure_tenant_id",
            "azure_subscription_id",
            "azure_principal_object_id",
            "credential_kind",
            "gymact_execution",
            "brce",
            "live_probe",
        },
        "AZURE_AUTHORITY",
    )
    if authority["authority_class"] != "DO":
        _refuse("AZURE_AUTHORITY_CLASS")
    _validate_token(authority["authority_ref"], "AZURE_AUTHORITY_REF")

    scopes = authority["scopes"]
    if not isinstance(scopes, list) or not scopes or not all(isinstance(v, str) for v in scopes):
        _refuse("AZURE_SCOPE_INVALID")
    if len(scopes) != len(set(scopes)):
        _refuse("AZURE_SCOPE_DUPLICATE")
    if any(scope == "*" or "*" in scope or not scope.startswith("azure.") for scope in scopes):
        _refuse("AZURE_SCOPE_AMBIENT_OR_UNBOUNDED")

    _validate_uuid(authority["azure_tenant_id"], "AZURE_TENANT_ID")
    _validate_uuid(authority["azure_subscription_id"], "AZURE_SUBSCRIPTION_ID")
    _validate_uuid(authority["azure_principal_object_id"], "AZURE_PRINCIPAL_OBJECT_ID")
    if authority["credential_kind"] not in {"federated_oidc", "managed_identity", "service_principal_certificate"}:
        _refuse("AZURE_CREDENTIAL_KIND")

    execution = _require_exact_keys(
        authority["gymact_execution"],
        {"repository", "sha", "executed_sha", "provider", "result", "receipt", "verifier", "replay"},
        "GYMACT_EXECUTION",
    )
    if execution["repository"] != subject["repository"]:
        _refuse("GYMACT_EXECUTION_REPOSITORY")
    if execution["sha"] != subject["sha"] or execution["executed_sha"] != subject["sha"]:
        _refuse("GYMACT_EXECUTION_IDENTITY")
    if execution["provider"] != subject["provider"]:
        _refuse("GYMACT_EXECUTION_PROVIDER")
    if execution["result"] != "ADMITTED":
        _refuse("GYMACT_AUTHORITY_NOT_ADMITTED")
    for field in ("receipt", "verifier", "replay"):
        _validate_token(execution[field], f"GYMACT_EXECUTION_{field.upper()}")

    brce = _require_exact_keys(
        authority["brce"],
        {"exclusive_do_path", "zero_unreceipted_actuation", "receipt", "verifier", "replay"},
        "BRCE",
    )
    if brce["exclusive_do_path"] is not True:
        _refuse("BRCE_NOT_EXCLUSIVE_DO_PATH")
    if brce["zero_unreceipted_actuation"] is not True:
        _refuse("ZERO_UNRECEIPTED_ACTUATION_DISABLED")
    for field in ("receipt", "verifier", "replay"):
        _validate_token(brce[field], f"BRCE_{field.upper()}")

    probe = _require_exact_keys(
        authority["live_probe"],
        {"scope", "executed", "consequence_class", "receipt", "replay"},
        "LIVE_PROBE",
    )
    if probe["executed"] is not True or probe["consequence_class"] != "DO":
        _refuse("LIVE_AZURE_DO_NOT_EXECUTED")
    if probe["scope"] not in scopes:
        _refuse("LIVE_PROBE_SCOPE_NOT_ADMITTED")
    _validate_token(probe["receipt"], "LIVE_PROBE_RECEIPT")
    _validate_token(probe["replay"], "LIVE_PROBE_REPLAY")
    return authority


def verify(data: Any) -> dict[str, Any]:
    root = _require_exact_keys(data, {"schema", "standing", "blocker", "gymact_subject", "authority"}, "DOCUMENT")
    _reject_secret_material(root)
    if root["schema"] != SCHEMA:
        _refuse("SCHEMA")
    subject = _validate_gymact_subject(root["gymact_subject"])

    standing = root["standing"]
    if standing == "BLOCKED":
        if root["blocker"] != "LIVE_AZURE_AUTHORITY" or root["authority"] is not None:
            _refuse("BLOCKED_STATE_INCONSISTENT")
        return {
            "schema": SCHEMA,
            "effective_standing": "BLOCKED:LIVE_AZURE_AUTHORITY",
            "gymact_subject": subject["sha"],
            "authority_admitted": False,
            "do_authority": False,
        }
    if standing != "ALIVE":
        _refuse("STANDING")
    if root["blocker"] is not None:
        _refuse("ALIVE_WITH_BLOCKER")
    authority = _validate_authority(root["authority"], subject)
    return {
        "schema": SCHEMA,
        "effective_standing": "ALIVE",
        "gymact_subject": subject["sha"],
        "authority_admitted": True,
        "do_authority": True,
        "authority_ref": authority["authority_ref"],
        "scopes": authority["scopes"],
        "azure_subscription_id": authority["azure_subscription_id"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--admission", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--require-alive", action="store_true")
    args = parser.parse_args(argv)
    try:
        with args.admission.open("r", encoding="utf-8") as handle:
            report = verify(json.load(handle))
        if args.require_alive and report["effective_standing"] != "ALIVE":
            print("BLOCKED:LIVE_AZURE_AUTHORITY", file=sys.stderr)
            return 3
        print(json.dumps(report, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, AzureAuthorityRefusal) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
