import importlib.util
import json
import tempfile
import unittest
import sys
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "compile_accomplishment_log.py"
spec = importlib.util.spec_from_file_location("accomplishment", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def record(unit, sha, *, when="2026-09-20T10:00:00-07:00", state="COMPLETED", consequence="VERIFIED", semantic=True, evidence=None, repo="seanchatmangpt/xaas"):
    return {
        "schema": "chatman.accomplishment-evidence/1",
        "semantic_unit_id": unit,
        "repository": repo,
        "commit_sha": sha,
        "summary": f"summary {unit}",
        "completed_at": when,
        "state": state,
        "consequence_status": consequence,
        "semantic_commit": semantic,
        "receipt": {
            "identity": f"receipt:{unit}",
            "verifier": "repo-native:test",
            "consequence": f"verified consequence {unit}",
            "evidence": ["court:PASS"] if evidence is None else evidence,
        },
    }


class AccomplishmentLogTests(unittest.TestCase):
    def test_credits_only_verified_consequence(self):
        rows = [
            mod.parse_record(record("verified", "a" * 40), "a"),
            mod.parse_record(record("unverified", "b" * 40, consequence="UNVERIFIED"), "b"),
            mod.parse_record(record("no-evidence", "c" * 40, evidence=[]), "c"),
            mod.parse_record(record("not-semantic", "d" * 40, semantic=False), "d"),
        ]
        report = mod.compile_day(rows, date(2026, 9, 20))
        self.assertEqual(report["credited_count"], 1)
        self.assertEqual([r.semantic_unit_id for r in report["credited"]], ["verified"])
        self.assertEqual(len(report["unverified"]), 3)

    def test_dedupes_same_exact_commit(self):
        rows = [
            mod.parse_record(record("u1", "a" * 40), "a"),
            mod.parse_record(record("u2", "a" * 40), "b"),
        ]
        report = mod.compile_day(rows, date(2026, 9, 20))
        self.assertEqual(report["credited_count"], 1)
        self.assertEqual(len(report["duplicate_observations"]), 1)

    def test_conflicting_semantic_unit_identity_is_blocked(self):
        rows = [
            mod.parse_record(record("same", "a" * 40), "a"),
            mod.parse_record(record("same", "b" * 40), "b"),
        ]
        report = mod.compile_day(rows, date(2026, 9, 20))
        self.assertEqual(report["credited_count"], 0)
        self.assertEqual(report["conflicting_units"], {"same"})
        self.assertEqual(len(report["blocked"]), 2)

    def test_los_angeles_day_boundary(self):
        rows = [
            mod.parse_record(record("inside", "a" * 40, when="2026-09-21T06:59:59Z"), "inside"),
            mod.parse_record(record("outside", "b" * 40, when="2026-09-21T07:00:00Z"), "outside"),
        ]
        report = mod.compile_day(rows, date(2026, 9, 20))
        self.assertEqual([r.semantic_unit_id for r in report["credited"]], ["inside"])

    def test_iter_records_and_render_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = [
                record("done", "a" * 40),
                record("gap", "b" * 40, state="OPEN_GAP", consequence="UNVERIFIED"),
                record("blocked", "c" * 40, state="BLOCKED", consequence="BLOCKED"),
                record("unknown", "d" * 40, consequence="UNVERIFIED"),
            ]
            (root / "evidence.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
            report = mod.compile_day(mod.iter_records(root), date(2026, 9, 20))
            rendered = mod.render_markdown(report)
            self.assertIn("## Completed work", rendered)
            self.assertIn("## Receipts / evidence", rendered)
            self.assertIn("## Open gaps", rendered)
            self.assertIn("## Blocked items", rendered)
            self.assertIn("## Unverified / not credited", rendered)
            self.assertIn("PENDING_USER_REVIEW", rendered)
            self.assertIn("250/hour", rendered)


if __name__ == "__main__":
    unittest.main()
