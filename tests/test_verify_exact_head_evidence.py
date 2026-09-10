import datetime as dt, importlib.util, json, pathlib, tempfile, unittest

PATH = pathlib.Path(__file__).parents[1] / "scripts" / "verify_exact_head_evidence.py"
spec = importlib.util.spec_from_file_location("court", PATH)
court = importlib.util.module_from_spec(spec); spec.loader.exec_module(court)
SHA = "a" * 40
NOW = dt.datetime(2026, 8, 22, 0, 0, tzinfo=dt.timezone.utc)

def doc(rows):
    return {"schema": court.SCHEMA, "subjects": [{"repo": "seanchatmangpt/example", "head_sha": SHA, "evidence": rows}]}

def row(**kw):
    base = {"kind":"ci","source_id":"run-1","subject_sha":SHA,"status":"SUCCESS","observed_at":"2026-08-21T23:30:00Z"}
    base.update(kw); return base

class CourtTests(unittest.TestCase):
    def test_fresh_exact_head_is_alive_and_digest_replays(self):
        a = court.verify(doc([row()]), NOW, 3600); b = court.verify(doc([row()]), NOW, 3600)
        self.assertEqual("ALIVE", a["subjects"][0]["standing"]); self.assertEqual(a["digest_sha256"], b["digest_sha256"])
    def test_stale_evidence_refuses(self):
        with self.assertRaisesRegex(court.Refusal, "EVIDENCE_STALE"): court.verify(doc([row(observed_at="2026-08-21T20:00:00Z")]), NOW, 3600)
    def test_wrong_head_refuses(self):
        with self.assertRaisesRegex(court.Refusal, "EVIDENCE_WRONG_HEAD"): court.verify(doc([row(subject_sha="b"*40)]), NOW, 3600)
    def test_future_evidence_refuses(self):
        with self.assertRaisesRegex(court.Refusal, "EVIDENCE_FROM_FUTURE"): court.verify(doc([row(observed_at="2026-08-22T00:00:01Z")]), NOW, 3600)
    def test_duplicate_source_refuses(self):
        with self.assertRaisesRegex(court.Refusal, "EVIDENCE_SOURCE_DUPLICATE"): court.verify(doc([row(), row()]), NOW, 3600)
    def test_failure_is_observed_but_not_alive(self):
        receipt = court.verify(doc([row(status="FAILURE")]), NOW, 3600)
        self.assertEqual("PARTIAL_ALIVE", receipt["subjects"][0]["standing"])
    def test_empty_evidence_is_unknown(self):
        receipt = court.verify(doc([]), NOW, 3600); self.assertEqual("UNKNOWN", receipt["subjects"][0]["standing"])
    def test_cli_refusal_is_machine_readable(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td)/"e.json"; p.write_text(json.dumps(doc([row(subject_sha="b"*40)])))
            self.assertEqual(2, court.main([str(p), "--now", "2026-08-22T00:00:00Z", "--max-age-seconds", "3600"]))

if __name__ == "__main__": unittest.main()
