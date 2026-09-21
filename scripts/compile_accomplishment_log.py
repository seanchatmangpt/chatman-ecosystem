#!/usr/bin/env python3
"""Compile a daily Chatman Ecosystem accomplishment log from typed evidence.

The compiler is deliberately conservative: a semantic commit is credited only when
its own record says the intended consequence was verified and carries non-empty
receipt evidence. Everything else remains visible but uncredited.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

SCHEMA = "chatman.accomplishment-evidence/1"
LA = ZoneInfo("America/Los_Angeles")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_STATE = {"COMPLETED", "OPEN_GAP", "BLOCKED"}
ALLOWED_CONSEQUENCE = {"VERIFIED", "UNVERIFIED", "BLOCKED", "REFUSED", "UNSUPPORTED"}
PLANT_TARGET_PER_HOUR = 250


class EvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class Evidence:
    source: str
    semantic_unit_id: str
    repository: str
    commit_sha: str
    summary: str
    completed_at: datetime
    state: str
    consequence_status: str
    semantic_commit: bool
    receipt_identity: str
    verifier: str
    consequence: str
    evidence: tuple[str, ...]
    blockers: tuple[str, ...]

    @property
    def commit_identity(self) -> tuple[str, str]:
        return self.repository, self.commit_sha

    @property
    def creditable(self) -> bool:
        return (
            self.semantic_commit
            and self.state == "COMPLETED"
            and self.consequence_status == "VERIFIED"
            and bool(self.receipt_identity)
            and bool(self.verifier)
            and bool(self.consequence)
            and bool(self.evidence)
        )


def _parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"invalid completed_at: {value}") from exc
    if parsed.tzinfo is None:
        raise EvidenceError("completed_at must include a UTC offset")
    return parsed


def parse_record(raw: dict[str, Any], source: str) -> Evidence:
    if raw.get("schema") != SCHEMA:
        raise EvidenceError(f"{source}: schema must be {SCHEMA}")

    required = ["semantic_unit_id", "repository", "commit_sha", "summary", "completed_at", "state", "consequence_status", "semantic_commit", "receipt"]
    missing = [key for key in required if key not in raw]
    if missing:
        raise EvidenceError(f"{source}: missing required fields: {', '.join(missing)}")

    semantic_unit_id = str(raw["semantic_unit_id"]).strip()
    repository = str(raw["repository"]).strip()
    commit_sha = str(raw["commit_sha"]).strip().lower()
    summary = str(raw["summary"]).strip()
    state = str(raw["state"]).strip()
    consequence_status = str(raw["consequence_status"]).strip()
    semantic_commit = raw["semantic_commit"]
    receipt = raw["receipt"]

    if not semantic_unit_id:
        raise EvidenceError(f"{source}: semantic_unit_id must be non-empty")
    if repository.count("/") != 1 or any(not part for part in repository.split("/")):
        raise EvidenceError(f"{source}: repository must be owner/name")
    if not SHA40.fullmatch(commit_sha):
        raise EvidenceError(f"{source}: commit_sha must be 40 lowercase hex characters")
    if not summary:
        raise EvidenceError(f"{source}: summary must be non-empty")
    if state not in ALLOWED_STATE:
        raise EvidenceError(f"{source}: invalid state {state}")
    if consequence_status not in ALLOWED_CONSEQUENCE:
        raise EvidenceError(f"{source}: invalid consequence_status {consequence_status}")
    if not isinstance(semantic_commit, bool):
        raise EvidenceError(f"{source}: semantic_commit must be boolean")
    if not isinstance(receipt, dict):
        raise EvidenceError(f"{source}: receipt must be an object")

    evidence = receipt.get("evidence", [])
    if not isinstance(evidence, list) or any(not isinstance(item, str) for item in evidence):
        raise EvidenceError(f"{source}: receipt.evidence must be an array of strings")
    blockers = raw.get("blockers", [])
    if not isinstance(blockers, list) or any(not isinstance(item, str) for item in blockers):
        raise EvidenceError(f"{source}: blockers must be an array of strings")

    return Evidence(
        source=source,
        semantic_unit_id=semantic_unit_id,
        repository=repository,
        commit_sha=commit_sha,
        summary=summary,
        completed_at=_parse_time(str(raw["completed_at"])),
        state=state,
        consequence_status=consequence_status,
        semantic_commit=semantic_commit,
        receipt_identity=str(receipt.get("identity", "")).strip(),
        verifier=str(receipt.get("verifier", "")).strip(),
        consequence=str(receipt.get("consequence", "")).strip(),
        evidence=tuple(item.strip() for item in evidence if item.strip()),
        blockers=tuple(item.strip() for item in blockers if item.strip()),
    )


def iter_records(root: Path) -> Iterable[Evidence]:
    if not root.exists():
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in {".json", ".jsonl"}:
            continue
        if path.suffix == ".jsonl":
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                raw = json.loads(line)
                if not isinstance(raw, dict):
                    raise EvidenceError(f"{path}:{lineno}: JSONL entries must be objects")
                yield parse_record(raw, f"{path}:{lineno}")
        else:
            raw = json.loads(path.read_text(encoding="utf-8"))
            rows = raw if isinstance(raw, list) else [raw]
            for index, row in enumerate(rows, 1):
                if not isinstance(row, dict):
                    raise EvidenceError(f"{path}:{index}: JSON entries must be objects")
                yield parse_record(row, f"{path}:{index}")


def _day_bounds(target: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target, time.min, tzinfo=LA)
    return start, start + timedelta(days=1)


def compile_day(records: Iterable[Evidence], target: date) -> dict[str, Any]:
    start, end = _day_bounds(target)
    day_records = [r for r in records if start <= r.completed_at.astimezone(LA) < end]
    day_records.sort(key=lambda r: (r.completed_at, r.repository, r.commit_sha, r.semantic_unit_id))

    by_unit: dict[str, list[Evidence]] = {}
    for record in day_records:
        by_unit.setdefault(record.semantic_unit_id, []).append(record)

    conflicting_units: set[str] = set()
    for unit, rows in by_unit.items():
        identities = {(r.repository, r.commit_sha) for r in rows}
        if len(identities) > 1:
            conflicting_units.add(unit)

    blocked: list[tuple[Evidence, str]] = []
    open_gaps: list[Evidence] = []
    unverified: list[tuple[Evidence, str]] = []
    candidates: list[Evidence] = []

    for record in day_records:
        if record.semantic_unit_id in conflicting_units:
            blocked.append((record, "CONFLICTING_SEMANTIC_UNIT_IDENTITY"))
        elif record.state == "BLOCKED" or record.consequence_status in {"BLOCKED", "REFUSED", "UNSUPPORTED"}:
            blocked.append((record, record.consequence_status))
        elif record.state == "OPEN_GAP":
            open_gaps.append(record)
        elif record.creditable:
            candidates.append(record)
        else:
            reasons = []
            if not record.semantic_commit:
                reasons.append("NOT_SEMANTIC_COMMIT")
            if record.consequence_status != "VERIFIED":
                reasons.append(f"CONSEQUENCE_{record.consequence_status}")
            if not record.receipt_identity:
                reasons.append("MISSING_RECEIPT_IDENTITY")
            if not record.verifier:
                reasons.append("MISSING_VERIFIER")
            if not record.consequence:
                reasons.append("MISSING_CONSEQUENCE")
            if not record.evidence:
                reasons.append("MISSING_EVIDENCE")
            unverified.append((record, ",".join(reasons) or "NOT_CREDITABLE"))

    credited_by_commit: dict[tuple[str, str], Evidence] = {}
    duplicate_observations: list[Evidence] = []
    for record in candidates:
        if record.commit_identity in credited_by_commit:
            duplicate_observations.append(record)
            continue
        credited_by_commit[record.commit_identity] = record

    credited = sorted(credited_by_commit.values(), key=lambda r: (r.completed_at, r.repository, r.commit_sha))
    hourly = {hour: 0 for hour in range(24)}
    for record in credited:
        hourly[record.completed_at.astimezone(LA).hour] += 1

    peak_hour, peak_count = max(hourly.items(), key=lambda item: (item[1], -item[0]))
    credited_count = len(credited)
    daily_target = PLANT_TARGET_PER_HOUR * 24

    return {
        "date": target.isoformat(),
        "credited": credited,
        "open_gaps": open_gaps,
        "blocked": blocked,
        "unverified": unverified,
        "duplicate_observations": duplicate_observations,
        "conflicting_units": conflicting_units,
        "hourly": hourly,
        "credited_count": credited_count,
        "daily_target": daily_target,
        "daily_attainment_pct": credited_count / daily_target * 100,
        "peak_hour": peak_hour,
        "peak_count": peak_count,
        "peak_attainment_pct": peak_count / PLANT_TARGET_PER_HOUR * 100,
    }


def _short_sha(sha: str) -> str:
    return sha[:12]


def _md_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Chatman Ecosystem accomplishment log — {report['date']}",
        "",
        "**Review status:** `PENDING_USER_REVIEW`  ",
        "**Evidence ceiling:** only unique semantic commits with an explicit verified consequence and non-empty receipt evidence are credited. Commit existence, PR state, CI presence, merge, publication, deployment, and standing are not inferred.",
        "",
        "## Plant progress",
        "",
        f"- Credited unique semantic commits: **{report['credited_count']}**",
        f"- Plant target: **{PLANT_TARGET_PER_HOUR}/hour**; 24-hour equivalent: **{report['daily_target']}**",
        f"- Daily-equivalent attainment: **{report['daily_attainment_pct']:.2f}%**",
        f"- Peak verified hour: **{report['peak_hour']:02d}:00 America/Los_Angeles — {report['peak_count']} / {PLANT_TARGET_PER_HOUR} ({report['peak_attainment_pct']:.2f}%)**",
        f"- Duplicate observations excluded from credit: **{len(report['duplicate_observations'])}**",
        f"- Conflicting semantic-unit identities blocked: **{len(report['conflicting_units'])}**",
        "",
        "### Hourly verified consequence",
        "",
        "| Hour (PT) | Credited | Target | Gap |",
        "|---:|---:|---:|---:|",
    ]
    for hour, count in report["hourly"].items():
        lines.append(f"| {hour:02d}:00 | {count} | {PLANT_TARGET_PER_HOUR} | {PLANT_TARGET_PER_HOUR - count} |")

    lines.extend(["", "## Completed work", ""])
    if report["credited"]:
        lines.extend(["| Repository | Commit | Semantic unit | Consequence |", "|---|---|---|---|"])
        for r in report["credited"]:
            lines.append(f"| {_md_escape(r.repository)} | `{_short_sha(r.commit_sha)}` | `{_md_escape(r.semantic_unit_id)}` | {_md_escape(r.consequence)} |")
    else:
        lines.append("No work met the verified-consequence credit gate for this day.")

    lines.extend(["", "## Receipts / evidence", ""])
    if report["credited"]:
        for r in report["credited"]:
            lines.append(f"- `{r.semantic_unit_id}` — receipt `{_md_escape(r.receipt_identity)}`; verifier `{_md_escape(r.verifier)}`; evidence: " + "; ".join(f"`{_md_escape(e)}`" for e in r.evidence))
    else:
        lines.append("No credited receipt evidence.")

    lines.extend(["", "## Open gaps", ""])
    if report["open_gaps"]:
        for r in report["open_gaps"]:
            lines.append(f"- `{r.semantic_unit_id}` `{r.repository}@{_short_sha(r.commit_sha)}` — {_md_escape(r.summary)}")
    else:
        lines.append("None observed in admitted evidence.")

    lines.extend(["", "## Blocked items", ""])
    if report["blocked"]:
        for r, reason in report["blocked"]:
            extra = f"; blockers: {'; '.join(r.blockers)}" if r.blockers else ""
            lines.append(f"- `{r.semantic_unit_id}` `{r.repository}@{_short_sha(r.commit_sha)}` — `{_md_escape(reason)}`{_md_escape(extra)}")
    else:
        lines.append("None observed in admitted evidence.")

    lines.extend(["", "## Unverified / not credited", ""])
    if report["unverified"]:
        for r, reason in report["unverified"]:
            lines.append(f"- `{r.semantic_unit_id}` `{r.repository}@{_short_sha(r.commit_sha)}` — `{_md_escape(reason)}` — {_md_escape(r.summary)}")
    else:
        lines.append("None observed in admitted evidence.")

    lines.extend([
        "",
        "## User review",
        "",
        "This projection remains `PENDING_USER_REVIEW`. Review may accept or reject the evidence set, but review does not retroactively manufacture verification for an unverified consequence.",
        "",
    ])
    return "\n".join(lines)


def default_target_date(now: datetime | None = None) -> date:
    current = (now or datetime.now(timezone.utc)).astimezone(LA)
    return current.date() - timedelta(days=1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, default=Path("accomplishments/evidence"))
    parser.add_argument("--date", dest="target_date", help="America/Los_Angeles calendar date (YYYY-MM-DD); defaults to yesterday")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    target = date.fromisoformat(args.target_date) if args.target_date else default_target_date()
    report = compile_day(iter_records(args.evidence_dir), target)
    rendered = render_markdown(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
