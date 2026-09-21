#!/usr/bin/env python3
"""Compile a fail-closed daily Chatman Ecosystem accomplishment log.

Only exact-subject semantic units with verified consequences and receipt-bound
PASS evidence enter the 250/hour numerator. The compiler is OBSERVE/CONSTRUCT
only: it performs no repository, issue, PR, deployment, or publication actuation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

try:
    from scripts.measure_train.identity import Subject
except ModuleNotFoundError:  # direct execution from scripts/measure_train
    from identity import Subject

HEX64 = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_STATES = {"COMPLETED", "OPEN_GAP", "BLOCKED"}
PASS = "PASS"


class AccomplishmentRefused(ValueError):
    """Typed fail-closed refusal for malformed evidence records."""

    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(f"REFUSED[{code}]: {detail}")


@dataclass(frozen=True)
class Policy:
    timezone: str
    target_per_hour: int
    review_status: str
    standing: str


def load_policy(path: Path) -> Policy:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    target = raw.get("target_verified_unique_semantic_commits_per_hour")
    if not isinstance(target, int) or target <= 0:
        raise AccomplishmentRefused("INVALID_POLICY", "target must be a positive integer")

    counting = raw.get("counting")
    required_counting = {
        "dedupe_key": "semantic_fingerprint",
        "require_exact_subject": True,
        "require_state": "COMPLETED",
        "require_verified_consequence": True,
        "require_verifier_outcome": "PASS",
        "require_receipt_identity": True,
        "require_receipt_digest": True,
        "unverified_counts_toward_target": False,
    }
    if not isinstance(counting, dict):
        raise AccomplishmentRefused("INVALID_POLICY", "counting contract is required")
    for key, expected in required_counting.items():
        if counting.get(key) != expected:
            raise AccomplishmentRefused(
                "UNSUPPORTED_POLICY_DRIFT",
                f"counting.{key} must remain {expected!r}",
            )

    timezone = raw.get("timezone")
    if not isinstance(timezone, str):
        raise AccomplishmentRefused("INVALID_POLICY", "timezone is required")
    try:
        ZoneInfo(timezone)
    except Exception as exc:  # pragma: no cover - platform tzdata failure
        raise AccomplishmentRefused("INVALID_POLICY", f"unknown timezone {timezone}") from exc
    return Policy(
        timezone=timezone,
        target_per_hour=target,
        review_status=str(raw.get("compiled_review_status", "PENDING_USER_REVIEW")),
        standing=str(raw.get("compiled_standing", "CANDIDATE")),
    )


def _parse_time(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise AccomplishmentRefused("INVALID_COMPLETION_TIME", repr(value))
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AccomplishmentRefused("INVALID_COMPLETION_TIME", value) from exc
    if parsed.tzinfo is None:
        raise AccomplishmentRefused("INVALID_COMPLETION_TIME", "naive timestamp")
    return parsed


def _required_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AccomplishmentRefused("MISSING_FIELD", key)
    return value.strip()


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    fingerprint = _required_string(record, "semantic_fingerprint")
    if not HEX64.fullmatch(fingerprint):
        raise AccomplishmentRefused("INVALID_SEMANTIC_FINGERPRINT", fingerprint)

    repository = _required_string(record, "repository")
    source_sha = _required_string(record, "source_sha")
    subject = Subject(repository, source_sha)
    completed_at = _parse_time(record.get("completed_at"))
    summary = _required_string(record, "summary")
    state = _required_string(record, "state").upper()
    if state not in ALLOWED_STATES:
        raise AccomplishmentRefused("INVALID_STATE", state)

    consequence = record.get("consequence")
    if not isinstance(consequence, dict):
        consequence = {}
    consequence_identity = str(consequence.get("identity", "")).strip()
    consequence_verified = consequence.get("verified") is True

    verification = record.get("verification")
    if not isinstance(verification, dict):
        verification = {}
    verifier = str(verification.get("verifier", "")).strip()
    outcome = str(verification.get("outcome", "UNKNOWN")).upper()
    receipt_id = str(verification.get("receipt_id", "")).strip()
    receipt_digest = str(verification.get("receipt_digest", "")).strip()
    receipt_digest_valid = bool(HEX64.fullmatch(receipt_digest))

    blocker = str(record.get("blocker", "")).strip()

    normalized = {
        "semantic_fingerprint": fingerprint,
        "repository": repository,
        "source_sha": source_sha,
        "subject": subject.identity,
        "completed_at": completed_at,
        "summary": summary,
        "state": state,
        "consequence_identity": consequence_identity,
        "consequence_verified": consequence_verified,
        "verifier": verifier,
        "verifier_outcome": outcome,
        "receipt_id": receipt_id,
        "receipt_digest": receipt_digest,
        "receipt_digest_valid": receipt_digest_valid,
        "blocker": blocker,
    }
    normalized["verification_gaps"] = verification_gaps(normalized)
    return normalized


def verification_gaps(record: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    if record["state"] != "COMPLETED":
        gaps.append(f"STATE_{record['state']}")
    if not record["consequence_identity"]:
        gaps.append("MISSING_CONSEQUENCE_IDENTITY")
    if not record["consequence_verified"]:
        gaps.append("CONSEQUENCE_UNVERIFIED")
    if not record["verifier"]:
        gaps.append("MISSING_VERIFIER")
    if record["verifier_outcome"] != PASS:
        gaps.append(f"VERIFIER_{record['verifier_outcome']}")
    if not record["receipt_id"]:
        gaps.append("MISSING_RECEIPT_ID")
    if not record["receipt_digest_valid"]:
        gaps.append("INVALID_OR_MISSING_RECEIPT_DIGEST")
    return gaps


def is_countable(record: dict[str, Any]) -> bool:
    return record["state"] == "COMPLETED" and not record["verification_gaps"]


def _dedupe(records: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_fingerprint: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_fingerprint.setdefault(record["semantic_fingerprint"], []).append(record)

    admitted: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    identity_fields = (
        "repository",
        "source_sha",
        "consequence_identity",
        "summary",
    )
    for fingerprint, group in sorted(by_fingerprint.items()):
        canonical = group[0]
        if any(any(row[field] != canonical[field] for field in identity_fields) for row in group[1:]):
            conflicts.append(
                {
                    **canonical,
                    "verification_gaps": ["CONFLICTING_SEMANTIC_FINGERPRINT"],
                    "conflict_count": len(group),
                }
            )
            continue
        chosen = next((row for row in group if is_countable(row)), canonical)
        admitted.append(chosen)

    # A plant credit is a unique semantic Git commit, not an arbitrary number
    # of semantic fingerprints packed into one source SHA. If multiple distinct
    # semantic fingerprints claim the same exact Git subject, fail closed and
    # exclude that subject from the throughput numerator until reconciled.
    by_subject: dict[str, list[dict[str, Any]]] = {}
    for record in admitted:
        by_subject.setdefault(record["subject"], []).append(record)
    unique_subjects: list[dict[str, Any]] = []
    for subject, group in sorted(by_subject.items()):
        if len(group) == 1:
            unique_subjects.append(group[0])
            continue
        conflicts.append(
            {
                **group[0],
                "verification_gaps": ["MULTIPLE_SEMANTIC_FINGERPRINTS_FOR_SUBJECT"],
                "conflict_count": len(group),
            }
        )
    return unique_subjects, conflicts


def _public_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "semantic_fingerprint": record["semantic_fingerprint"],
        "subject": record["subject"],
        "completed_at": record["completed_at"].isoformat(),
        "summary": record["summary"],
        "state": record["state"],
        "consequence_identity": record["consequence_identity"],
        "consequence_verified": record["consequence_verified"],
        "verifier": record["verifier"],
        "verifier_outcome": record["verifier_outcome"],
        "receipt_id": record["receipt_id"],
        "receipt_digest": record["receipt_digest"],
        "verification_gaps": list(record["verification_gaps"]),
        "blocker": record["blocker"],
    }


def compile_log(records: Iterable[dict[str, Any]], policy: Policy, day: date) -> dict[str, Any]:
    tz = ZoneInfo(policy.timezone)
    normalized = [normalize_record(record) for record in records]
    in_day = [record for record in normalized if record["completed_at"].astimezone(tz).date() == day]
    deduped, conflicts = _dedupe(in_day)

    completed = sorted((r for r in deduped if is_countable(r)), key=lambda r: (r["completed_at"], r["semantic_fingerprint"]))
    blocked = sorted((r for r in deduped if r["state"] == "BLOCKED"), key=lambda r: (r["completed_at"], r["semantic_fingerprint"]))
    open_gaps = sorted(
        [r for r in deduped if not is_countable(r) and r["state"] != "BLOCKED"] + conflicts,
        key=lambda r: (r["completed_at"], r["semantic_fingerprint"]),
    )

    hourly: dict[str, int] = {}
    for record in completed:
        local = record["completed_at"].astimezone(tz)
        bucket = local.strftime("%Y-%m-%dT%H:00%z")
        hourly[bucket] = hourly.get(bucket, 0) + 1

    peak_hour = None
    peak_count = 0
    if hourly:
        peak_hour, peak_count = max(sorted(hourly.items()), key=lambda item: item[1])

    evidence = [
        {
            "semantic_fingerprint": r["semantic_fingerprint"],
            "subject": r["subject"],
            "verifier": r["verifier"],
            "verifier_outcome": r["verifier_outcome"],
            "receipt_id": r["receipt_id"],
            "receipt_digest": r["receipt_digest"],
            "counted": is_countable(r),
        }
        for r in sorted(deduped + conflicts, key=lambda r: (r["completed_at"], r["semantic_fingerprint"]))
    ]

    report_core = {
        "schema": "chatman.accomplishment-log.v1",
        "day": day.isoformat(),
        "timezone": policy.timezone,
        "review": {"status": policy.review_status},
        "standing": policy.standing,
        "target": {
            "verified_unique_semantic_commits_per_hour": policy.target_per_hour,
            "daily_verified_unique_semantic_commits": len(completed),
            "peak_verified_unique_semantic_commits_per_hour": peak_count,
            "peak_hour": peak_hour,
            "peak_target_fraction": peak_count / policy.target_per_hour,
            "hours_at_or_above_target": sum(count >= policy.target_per_hour for count in hourly.values()),
            "hourly_counts": dict(sorted(hourly.items())),
        },
        "completed": [_public_record(r) for r in completed],
        "evidence": evidence,
        "open_gaps": [_public_record(r) for r in open_gaps],
        "blocked": [_public_record(r) for r in blocked],
        "unverified_count": len(open_gaps),
        "blocked_count": len(blocked),
        "counting_rule": "Only unique exact-subject COMPLETED semantic units with verified consequence, PASS verifier, receipt identity, and valid receipt digest count toward 250/hour.",
        "evidence_ceiling": "CANDIDATE pending user review; no merge, publication, deployment, runtime standing, or cross-repository ALIVE claim is inferred.",
    }
    digest_body = json.dumps(report_core, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    report_core["report_digest"] = hashlib.sha256(digest_body).hexdigest()
    return report_core


def render_markdown(report: dict[str, Any]) -> str:
    target = report["target"]
    pct = target["peak_target_fraction"] * 100
    lines = [
        f"# Chatman Ecosystem Daily Accomplishment Log — {report['day']}",
        "",
        f"- Review: **{report['review']['status']}**",
        f"- Standing: **{report['standing']}**",
        f"- Verified unique semantic commits: **{target['daily_verified_unique_semantic_commits']}**",
        f"- Peak verified rate: **{target['peak_verified_unique_semantic_commits_per_hour']}/{target['verified_unique_semantic_commits_per_hour']} per hour ({pct:.1f}%)**",
        f"- Peak hour: **{target['peak_hour'] or 'none'}**",
        f"- Unverified/open gaps: **{report['unverified_count']}**",
        f"- Blocked: **{report['blocked_count']}**",
        "",
        "## Completed work",
    ]
    if report["completed"]:
        for row in report["completed"]:
            lines.append(f"- `{row['semantic_fingerprint'][:12]}` {row['subject']} — {row['summary']} → `{row['consequence_identity']}`")
    else:
        lines.append("- None with verified consequence.")

    lines.extend(["", "## Receipts / evidence"])
    if report["evidence"]:
        for row in report["evidence"]:
            counted = "COUNTED" if row["counted"] else "NOT_COUNTED"
            receipt = row["receipt_id"] or "missing"
            digest = row["receipt_digest"][:12] if row["receipt_digest"] else "missing"
            verifier = row["verifier"] or "missing"
            lines.append(f"- **{counted}** `{row['semantic_fingerprint'][:12]}` {row['subject']} — verifier `{verifier}` = `{row['verifier_outcome']}`; receipt `{receipt}`; digest `{digest}`")
    else:
        lines.append("- No evidence records observed for this day.")

    lines.extend(["", "## Open gaps"])
    if report["open_gaps"]:
        for row in report["open_gaps"]:
            gaps = ", ".join(row["verification_gaps"])
            lines.append(f"- `{row['semantic_fingerprint'][:12]}` {row['subject']} — {row['summary']} — **UNVERIFIED**: {gaps}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Blocked items"])
    if report["blocked"]:
        for row in report["blocked"]:
            blocker = row["blocker"] or "BLOCKED_WITHOUT_DETAIL"
            lines.append(f"- `{row['semantic_fingerprint'][:12]}` {row['subject']} — {row['summary']} — `{blocker}`")
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Evidence ceiling",
            "",
            report["counting_rule"],
            "",
            report["evidence_ceiling"],
            "",
            f"Report digest: `{report['report_digest']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def read_jsonl(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            raise AccomplishmentRefused("INPUT_NOT_FOUND", str(path))
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AccomplishmentRefused("INVALID_JSONL", f"{path}:{line_number}") from exc
            if not isinstance(value, dict):
                raise AccomplishmentRefused("INVALID_RECORD", f"{path}:{line_number}")
            rows.append(value)
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=Path("catalog/accomplishment-log.toml"))
    parser.add_argument("--input", type=Path, action="append", default=[])
    parser.add_argument("--date", type=date.fromisoformat)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    policy = load_policy(args.policy)
    tz = ZoneInfo(policy.timezone)
    report_day = args.date or datetime.now(tz).date()
    report = compile_log(read_jsonl(args.input), policy, report_day)
    rendered = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n" if args.format == "json" else render_markdown(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AccomplishmentRefused as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
