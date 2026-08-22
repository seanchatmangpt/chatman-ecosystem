#!/usr/bin/env python3
import argparse, datetime as dt, hashlib, json, re, sys
from pathlib import Path

SCHEMA = "chatman.exact-head-evidence/1"
RECEIPT_SCHEMA = "chatman.exact-head-evidence-receipt/1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_STATUS = {"SUCCESS", "FAILURE", "CANCELLED", "SKIPPED", "UNKNOWN"}

class Refusal(Exception):
    def __init__(self, code, detail):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")

def parse_time(value):
    if not isinstance(value, str):
        raise Refusal("REFUSED[EVIDENCE_TIME_INVALID]", repr(value))
    try:
        t = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Refusal("REFUSED[EVIDENCE_TIME_INVALID]", value) from exc
    if t.tzinfo is None:
        raise Refusal("REFUSED[EVIDENCE_TIME_UNZONED]", value)
    return t.astimezone(dt.timezone.utc)

def canonical_digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()

def verify(doc, now, max_age_seconds):
    if doc.get("schema") != SCHEMA:
        raise Refusal("REFUSED[EVIDENCE_SCHEMA]", str(doc.get("schema")))
    subjects = doc.get("subjects")
    if not isinstance(subjects, list) or not subjects:
        raise Refusal("REFUSED[SUBJECTS_EMPTY]", "subjects must be non-empty")
    seen_subjects = set()
    result_rows = []
    for subject in subjects:
        repo = subject.get("repo")
        sha = subject.get("head_sha")
        if not isinstance(repo, str) or "/" not in repo:
            raise Refusal("REFUSED[SUBJECT_REPO_INVALID]", repr(repo))
        if not isinstance(sha, str) or not SHA40.fullmatch(sha):
            raise Refusal("REFUSED[SUBJECT_SHA_INVALID]", repr(sha))
        key = (repo, sha)
        if key in seen_subjects:
            raise Refusal("REFUSED[SUBJECT_DUPLICATE]", f"{repo}@{sha}")
        seen_subjects.add(key)
        evidence = subject.get("evidence")
        if not isinstance(evidence, list):
            raise Refusal("REFUSED[EVIDENCE_NOT_LIST]", repo)
        source_ids = set()
        admitted = []
        for row in evidence:
            source_id = row.get("source_id")
            if not isinstance(source_id, str) or not source_id.strip():
                raise Refusal("REFUSED[EVIDENCE_SOURCE_ID_INVALID]", repo)
            if source_id in source_ids:
                raise Refusal("REFUSED[EVIDENCE_SOURCE_DUPLICATE]", f"{repo}:{source_id}")
            source_ids.add(source_id)
            observed_sha = row.get("subject_sha")
            if observed_sha != sha:
                raise Refusal("REFUSED[EVIDENCE_WRONG_HEAD]", f"{repo}:{source_id}:{observed_sha}!={sha}")
            status = row.get("status")
            if status not in ALLOWED_STATUS:
                raise Refusal("REFUSED[EVIDENCE_STATUS_INVALID]", f"{repo}:{source_id}:{status}")
            observed_at = parse_time(row.get("observed_at"))
            age = (now - observed_at).total_seconds()
            if age < 0:
                raise Refusal("REFUSED[EVIDENCE_FROM_FUTURE]", f"{repo}:{source_id}:{int(age)}")
            if age > max_age_seconds:
                raise Refusal("REFUSED[EVIDENCE_STALE]", f"{repo}:{source_id}:{int(age)}>{max_age_seconds}")
            admitted.append({
                "kind": row.get("kind", "unspecified"),
                "source_id": source_id,
                "status": status,
                "observed_at": observed_at.isoformat().replace("+00:00", "Z"),
                "age_seconds": int(age),
            })
        success_count = sum(r["status"] == "SUCCESS" for r in admitted)
        standing = "ALIVE" if admitted and success_count == len(admitted) else ("PARTIAL_ALIVE" if admitted else "UNKNOWN")
        result_rows.append({
            "repo": repo,
            "head_sha": sha,
            "standing": standing,
            "evidence_count": len(admitted),
            "success_count": success_count,
            "evidence": sorted(admitted, key=lambda r: (r["kind"], r["source_id"])),
        })
    result_rows.sort(key=lambda r: (r["repo"], r["head_sha"]))
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "measurement_schema": SCHEMA,
        "observed_at": now.isoformat().replace("+00:00", "Z"),
        "max_age_seconds": max_age_seconds,
        "subjects": result_rows,
    }
    receipt["digest_sha256"] = canonical_digest(receipt)
    return receipt

def main(argv=None):
    p = argparse.ArgumentParser(description="Verify exact-head freshness of engineering evidence")
    p.add_argument("evidence", type=Path)
    p.add_argument("--now", required=True, help="UTC/Z or offset timestamp; explicit for deterministic replay")
    p.add_argument("--max-age-seconds", type=int, default=86400)
    args = p.parse_args(argv)
    try:
        if args.max_age_seconds < 0:
            raise Refusal("REFUSED[MAX_AGE_INVALID]", str(args.max_age_seconds))
        doc = json.loads(args.evidence.read_text())
        receipt = verify(doc, parse_time(args.now), args.max_age_seconds)
    except (OSError, json.JSONDecodeError, Refusal) as exc:
        if isinstance(exc, Refusal):
            out = {"standing": "REFUSED", "refusal": exc.code, "detail": exc.detail}
        else:
            out = {"standing": "REFUSED", "refusal": "REFUSED[EVIDENCE_INPUT]", "detail": str(exc)}
        print(json.dumps(out, sort_keys=True))
        return 2
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
