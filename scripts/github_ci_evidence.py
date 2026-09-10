#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, sys, urllib.parse, urllib.request
from typing import Any

SCHEMA = "chatman.github-ci-evidence/1"


class Refusal(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail

    def as_dict(self) -> dict[str, str]:
        return {"standing": "REFUSED", "refusal": self.code, "detail": self.detail}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def classify_run(run: dict[str, Any], subject: str) -> dict[str, Any]:
    if run.get("head_sha") != subject:
        raise Refusal(
            "STALE_OR_FOREIGN_HEAD",
            f"run {run.get('id')} head_sha={run.get('head_sha')} expected={subject}",
        )
    status = run.get("status")
    conclusion = run.get("conclusion")
    if status == "completed":
        standing = "PASS" if conclusion == "success" else "FAIL"
    else:
        standing = "PENDING"
    return {
        "id": run.get("id"),
        "name": run.get("name"),
        "event": run.get("event"),
        "head_sha": run.get("head_sha"),
        "status": status,
        "conclusion": conclusion,
        "standing": standing,
        "html_url": run.get("html_url"),
    }


def manufacture(repo: str, subject: str, payload: dict[str, Any]) -> dict[str, Any]:
    if len(subject) != 40 or any(c not in "0123456789abcdef" for c in subject):
        raise Refusal("INVALID_SUBJECT_SHA", "subject must be lowercase 40-hex SHA")
    runs = payload.get("workflow_runs")
    if not isinstance(runs, list):
        raise Refusal("INVALID_GITHUB_PAYLOAD", "workflow_runs must be a list")
    classified = [classify_run(run, subject) for run in runs]
    classified.sort(key=lambda row: (str(row.get("name")), int(row.get("id") or 0)))
    counts = {name: sum(1 for row in classified if row["standing"] == name) for name in ("PASS", "FAIL", "PENDING")}
    standing = "BUILD_BROKEN" if counts["FAIL"] else ("UNKNOWN" if counts["PENDING"] or not classified else "PARTIAL_ALIVE")
    body = {
        "schema": SCHEMA,
        "repository": repo,
        "subject_sha": subject,
        "sensor": "github_actions_runs_exact_head",
        "runs": classified,
        "counts": counts,
        "standing": standing,
        "claim_ceiling": "CI_EVIDENCE_ONLY",
    }
    body["receipt"] = {"algorithm": "sha256", "observation_digest": digest(body)}
    return body


def verify_receipt(doc: dict[str, Any]) -> None:
    receipt = doc.get("receipt") or {}
    expected = receipt.get("observation_digest")
    if not expected:
        raise Refusal("MISSING_RECEIPT", "receipt missing")
    body = dict(doc)
    body.pop("receipt", None)
    if digest(body) != expected:
        raise Refusal("RECEIPT_MISMATCH", "observation digest mismatch")


def fetch_runs(repo: str, subject: str, token: str | None = None) -> dict[str, Any]:
    query = urllib.parse.urlencode({"head_sha": subject, "per_page": 100})
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/actions/runs?{query}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "chatman-measure-ci-evidence"},
    )
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("capture")
    capture.add_argument("--repo", required=True)
    capture.add_argument("--sha", required=True)
    capture.add_argument("--input")
    capture.add_argument("--output")
    replay = sub.add_parser("replay")
    replay.add_argument("--receipt", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            if args.input:
                with open(args.input, encoding="utf-8") as handle:
                    payload = json.load(handle)
            else:
                payload = fetch_runs(args.repo, args.sha, os.getenv("GITHUB_TOKEN"))
            doc = manufacture(args.repo, args.sha, payload)
            text = json.dumps(doc, indent=2, sort_keys=True)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as handle:
                    handle.write(text + "\n")
            else:
                print(text)
        else:
            with open(args.receipt, encoding="utf-8") as handle:
                doc = json.load(handle)
            verify_receipt(doc)
            print(json.dumps({"standing": "VERIFIED", "schema": doc.get("schema"), "subject_sha": doc.get("subject_sha")}))
        return 0
    except Refusal as exc:
        print(json.dumps(exc.as_dict(), sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
