from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.measure_train.accomplishment_log import Policy, compile_log, render_markdown


def record(
    fingerprint: str,
    *,
    hour: int = 12,
    state: str = "COMPLETED",
    verified: bool = True,
    outcome: str = "PASS",
    receipt: bool = True,
    summary: str = "verified semantic consequence",
    consequence: str = "test:semantic-edge",
    repo: str = "seanchatmangpt/example",
    sha: str | None = None,
) -> dict:
    source_sha = sha or fingerprint[-40:]
    return {
        "semantic_fingerprint": fingerprint,
        "repository": repo,
        "source_sha": source_sha,
        "completed_at": f"2026-09-20T{hour:02d}:15:00-07:00",
        "summary": summary,
        "state": state,
        "consequence": {"identity": consequence, "verified": verified},
        "verification": {
            "verifier": "repo-native:test",
            "outcome": outcome,
            "receipt_id": "receipt:1" if receipt else "",
            "receipt_digest": "c" * 64 if receipt else "",
        },
        "blocker": "DEPENDENCY_UNAVAILABLE" if state == "BLOCKED" else "",
    }


class AccomplishmentLogCourt(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = Policy("America/Los_Angeles", 250, "PENDING_USER_REVIEW", "CANDIDATE")
        self.day = date(2026, 9, 20)

    def test_only_verified_consequence_enters_numerator(self) -> None:
        report = compile_log(
            [
                record("a" * 64),
                record("b" * 64, verified=False),
                record("c" * 64, outcome="FAIL"),
                record("d" * 64, receipt=False),
            ],
            self.policy,
            self.day,
        )
        self.assertEqual(1, report["target"]["daily_verified_unique_semantic_commits"])
        self.assertEqual(3, report["unverified_count"])
        self.assertEqual({"a" * 64}, {row["semantic_fingerprint"] for row in report["completed"]})

    def test_duplicate_semantic_fingerprint_counts_once(self) -> None:
        report = compile_log([record("a" * 64), record("a" * 64)], self.policy, self.day)
        self.assertEqual(1, report["target"]["daily_verified_unique_semantic_commits"])
        self.assertEqual(1, report["target"]["peak_verified_unique_semantic_commits_per_hour"])

    def test_conflicting_duplicate_is_fail_closed_and_unverified(self) -> None:
        report = compile_log(
            [record("a" * 64, consequence="test:one"), record("a" * 64, consequence="test:two")],
            self.policy,
            self.day,
        )
        self.assertEqual(0, report["target"]["daily_verified_unique_semantic_commits"])
        self.assertEqual(1, report["unverified_count"])
        self.assertIn("CONFLICTING_SEMANTIC_FINGERPRINT", report["open_gaps"][0]["verification_gaps"])

    def test_multiple_fingerprints_on_one_git_subject_do_not_inflate_target(self) -> None:
        report = compile_log(
            [record("a" * 64, consequence="test:one", sha="f" * 40), record("b" * 64, consequence="test:two", sha="f" * 40)],
            self.policy,
            self.day,
        )
        self.assertEqual(0, report["target"]["daily_verified_unique_semantic_commits"])
        self.assertEqual(1, report["unverified_count"])
        self.assertIn("MULTIPLE_SEMANTIC_FINGERPRINTS_FOR_SUBJECT", report["open_gaps"][0]["verification_gaps"])

    def test_blocked_is_separate_and_never_counted(self) -> None:
        report = compile_log([record("a" * 64, state="BLOCKED")], self.policy, self.day)
        self.assertEqual(0, report["target"]["daily_verified_unique_semantic_commits"])
        self.assertEqual(1, report["blocked_count"])
        self.assertEqual(0, report["unverified_count"])

    def test_peak_rate_is_measured_against_250_target(self) -> None:
        rows = [record(f"{i:064x}", hour=12) for i in range(3)] + [record(f"{i + 10:064x}", hour=13) for i in range(2)]
        report = compile_log(rows, self.policy, self.day)
        self.assertEqual(3, report["target"]["peak_verified_unique_semantic_commits_per_hour"])
        self.assertAlmostEqual(3 / 250, report["target"]["peak_target_fraction"])
        self.assertEqual(0, report["target"]["hours_at_or_above_target"])

    def test_timezone_selects_local_day(self) -> None:
        row = record("a" * 64)
        row["completed_at"] = "2026-09-21T06:30:00Z"  # 2026-09-20 23:30 PDT
        report = compile_log([row], self.policy, self.day)
        self.assertEqual(1, report["target"]["daily_verified_unique_semantic_commits"])

    def test_report_remains_candidate_pending_user_review(self) -> None:
        report = compile_log([record("a" * 64)], self.policy, self.day)
        self.assertEqual("PENDING_USER_REVIEW", report["review"]["status"])
        self.assertEqual("CANDIDATE", report["standing"])
        self.assertIn("no merge, publication, deployment", report["evidence_ceiling"])

    def test_markdown_has_required_four_partitions_and_unverified_callout(self) -> None:
        report = compile_log([record("a" * 64), record("b" * 64, verified=False)], self.policy, self.day)
        rendered = render_markdown(report)
        for heading in ("## Completed work", "## Receipts / evidence", "## Open gaps", "## Blocked items"):
            self.assertIn(heading, rendered)
        self.assertIn("UNVERIFIED", rendered)

    def test_cli_compiles_jsonl(self) -> None:
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "evidence.jsonl"
            input_path.write_text(json.dumps(record("a" * 64)) + "\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "measure_train" / "accomplishment_log.py"),
                    "--policy",
                    str(root / "catalog" / "accomplishment-log.toml"),
                    "--input",
                    str(input_path),
                    "--date",
                    "2026-09-20",
                    "--format",
                    "json",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(1, payload["target"]["daily_verified_unique_semantic_commits"])


if __name__ == "__main__":
    unittest.main()
