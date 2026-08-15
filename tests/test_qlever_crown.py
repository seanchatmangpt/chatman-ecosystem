from __future__ import annotations
import importlib.util, json, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"release"/"v26.9.1"/"qlever"
def load(name):
    s=importlib.util.spec_from_file_location(name,ROOT/f"{name}.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

class QLeverCrownTests(unittest.TestCase):
    def test_fixture_is_byte_deterministic(self):
        g=load("generate_fixture")
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.nt",Path(td)/"b.nt"
            ma=g.generate(a,64,10,32); mb=g.generate(b,64,10,32)
            self.assertEqual(a.read_bytes(),b.read_bytes()); self.assertEqual(ma,mb); self.assertEqual(ma["triples"],640)
    def test_expected_structural_ties_are_deterministic(self):
        v=load("verify_qlever_crown")
        self.assertEqual(v.expected_candidates(200_000,32,3),["<urn:chatman:subject:100000>","<urn:chatman:subject:100032>","<urn:chatman:subject:100064>"])
    def test_scale_floor_refuses_small_fixture(self):
        v=load("verify_qlever_crown")
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); (p/"fixture.json").write_text(json.dumps({"schema":"chatman.qlever.fixture/v1","subjects":64,"width":10,"predicate_universe":32,"triples":640,"sha256":"0"*64}))
            for n in ["ranking.tsv","replay.tsv"]: (p/n).write_text("?candidate\t?overlap\n<urn:chatman:subject:32>\t10\n")
            (p/"count.tsv").write_text("?triples\n640\n")
            with self.assertRaisesRegex(ValueError,"QLEVER_SCALE_BELOW_2M"):
                v.verify(p/"fixture.json",p/"ranking.tsv",p/"replay.tsv",p/"count.tsv","a"*40)
if __name__=="__main__": unittest.main()
