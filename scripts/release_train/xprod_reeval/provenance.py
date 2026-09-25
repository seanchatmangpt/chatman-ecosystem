"""Provenance re-verification for a committed cross-product case.

Offline mode (gating, no network):
  * every evidence ``artifact_digest`` equals sha256 over the committed
    evidence bytes named by ``provenance.file``
    -> otherwise ``REFUSED:ARTIFACT_DIGEST_MISMATCH:<evidence_id>``;
  * every ``validator_digest`` equals sha256 over the committed validator
    bytes named by ``provenance.validator_file``
    -> otherwise ``REFUSED:VALIDATOR_DIGEST_MISMATCH:<evidence_id>``;
  * a ``--receipt`` file, when given, equals the court receipt recomputed
    from the case -> otherwise ``REFUSED:RECEIPT_REPLAY_MISMATCH``.

Online mode (additionally, through ``gh api``):
  * the producer run has ``head_sha == subject_sha``, ``path == workflow``
    and ``conclusion == success``;
  * the artifact still exists and its API digest equals ``artifact_digest``
    (expired -> ``BLOCKED:PROVENANCE_EXPIRED:<evidence_id>``);
  * ``--download`` re-downloads the artifact zip and re-hashes it;
  * the validator workflow fetched at the subject hashes to
    ``validator_digest``.

Exit 0 when no REFUSED line exists (ALIVE, or BLOCKED on expiry only),
exit 2 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable

from scripts.release_train.cross_product_court.__main__ import run as court_run

Fetch = Callable[[str, bool], bytes]


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _standing(refusals: list[str]) -> str:
    if any(item.startswith("REFUSED:") for item in refusals):
        return "REFUSED"
    if any(item.startswith("BLOCKED:") for item in refusals):
        return "BLOCKED"
    return "ALIVE"


def verify_offline(
    case_path: str | Path,
    receipt_path: str | Path | None = None,
) -> dict[str, Any]:
    case_path = Path(case_path)
    base = case_path.parent
    raw = json.loads(case_path.read_text(encoding="utf-8"))
    refusals: list[str] = []
    checked: list[str] = []
    for item in raw["evidence"]:
        eid = item["evidence_id"]
        prov = item.get("provenance")
        if not isinstance(prov, dict) or "file" not in prov:
            refusals.append(f"REFUSED:PROVENANCE_MISSING:{eid}")
            continue
        evidence_file = base / prov["file"]
        if not evidence_file.is_file():
            refusals.append(f"REFUSED:EVIDENCE_BYTES_MISSING:{eid}")
        elif sha256_file(evidence_file) != item["artifact_digest"]:
            refusals.append(f"REFUSED:ARTIFACT_DIGEST_MISMATCH:{eid}")
        else:
            checked.append(f"artifact:{eid}")
        validator_file = prov.get("validator_file")
        if not validator_file or not (base / validator_file).is_file():
            refusals.append(f"REFUSED:VALIDATOR_BYTES_MISSING:{eid}")
        elif sha256_file(base / validator_file) != item["validator_digest"]:
            refusals.append(f"REFUSED:VALIDATOR_DIGEST_MISMATCH:{eid}")
        else:
            checked.append(f"validator:{eid}")
    if receipt_path is not None:
        recomputed = json.loads(json.dumps(court_run(str(case_path))[0]))
        committed = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
        if recomputed != committed:
            refusals.append("REFUSED:RECEIPT_REPLAY_MISMATCH")
        else:
            checked.append("receipt:" + str(committed.get("receipt_digest")))
    return {
        "mode": "offline",
        "case_id": raw.get("case_id"),
        "standing": _standing(refusals),
        "refusals": sorted(set(refusals)),
        "checked": checked,
    }


def gh_fetch(endpoint: str, raw: bool) -> bytes:
    argv = ["gh", "api", endpoint]
    if raw:
        argv += ["-H", "Accept: application/vnd.github.raw"]
    done = subprocess.run(argv, capture_output=True, check=False)
    if done.returncode != 0:
        raise LookupError(
            f"gh api {endpoint} exit={done.returncode}: "
            + done.stderr.decode("utf-8", "replace").strip()[:300]
        )
    return done.stdout


def verify_online(
    case_path: str | Path,
    *,
    download: bool = False,
    fetch: Fetch = gh_fetch,
) -> dict[str, Any]:
    raw = json.loads(Path(case_path).read_text(encoding="utf-8"))
    refusals: list[str] = []
    checked: list[str] = []
    runs: dict[tuple[str, int], dict[str, Any]] = {}
    validators: dict[tuple[str, str, str], str] = {}
    for item in raw["evidence"]:
        eid = item["evidence_id"]
        prov = item.get("provenance") or {}
        repo = item["repository"]
        try:
            key = (repo, int(prov["run_id"]))
            if key not in runs:
                runs[key] = json.loads(
                    fetch(f"repos/{repo}/actions/runs/{key[1]}", False)
                )
            run = runs[key]
            if run.get("head_sha") != item["subject_sha"]:
                refusals.append(f"REFUSED:RUN_SUBJECT_MISMATCH:{eid}")
            elif run.get("path") != prov["workflow"]:
                refusals.append(f"REFUSED:RUN_VALIDATOR_MISMATCH:{eid}")
            elif run.get("conclusion") != "success":
                refusals.append(f"REFUSED:RUN_NOT_SUCCESS:{eid}")
            else:
                checked.append(f"run:{eid}:{key[1]}")

            artifact = json.loads(
                fetch(
                    f"repos/{repo}/actions/artifacts/{prov['artifact_id']}",
                    False,
                )
            )
            if artifact.get("expired"):
                refusals.append(f"BLOCKED:PROVENANCE_EXPIRED:{eid}")
            elif artifact.get("digest") != item["artifact_digest"]:
                refusals.append(f"REFUSED:ARTIFACT_DIGEST_MISMATCH:{eid}")
            else:
                checked.append(f"artifact-api:{eid}")
                if download:
                    body = fetch(
                        f"repos/{repo}/actions/artifacts/{prov['artifact_id']}/zip",
                        False,
                    )
                    if sha256_bytes(body) != item["artifact_digest"]:
                        refusals.append(f"REFUSED:ARTIFACT_DIGEST_MISMATCH:{eid}")
                    else:
                        checked.append(f"artifact-bytes:{eid}")

            vkey = (repo, prov["workflow"], item["subject_sha"])
            if vkey not in validators:
                validators[vkey] = sha256_bytes(
                    fetch(
                        f"repos/{repo}/contents/{prov['workflow']}"
                        f"?ref={item['subject_sha']}",
                        True,
                    )
                )
            if validators[vkey] != item["validator_digest"]:
                refusals.append(f"REFUSED:VALIDATOR_DIGEST_MISMATCH:{eid}")
            else:
                checked.append(f"validator-at-subject:{eid}")
        except (KeyError, ValueError, TypeError) as exc:
            refusals.append(f"REFUSED:PROVENANCE_MALFORMED:{eid}:{exc}")
        except LookupError as exc:
            message = str(exc)
            if " 410" in message or "expired" in message.lower():
                refusals.append(f"BLOCKED:PROVENANCE_EXPIRED:{eid}")
            else:
                refusals.append(f"BLOCKED:PROVENANCE_UNREACHABLE:{eid}:{message[:120]}")
    return {
        "mode": "online",
        "case_id": raw.get("case_id"),
        "standing": _standing(refusals),
        "refusals": sorted(set(refusals)),
        "checked": checked,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("offline", "online"))
    parser.add_argument("case")
    parser.add_argument("--receipt", help="committed court receipt to replay")
    parser.add_argument(
        "--download",
        action="store_true",
        help="online: re-download artifact zips and re-hash them",
    )
    args = parser.parse_args(argv)
    if args.mode == "offline":
        report = verify_offline(args.case, args.receipt)
    else:
        report = verify_online(args.case, download=args.download)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2 if report["standing"] == "REFUSED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
