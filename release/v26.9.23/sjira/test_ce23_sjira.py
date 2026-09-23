#!/usr/bin/env python3
"""Chicago tests for the CE23 first mile (lane CE-INTAKE, wave CE0).

Real files, real subprocesses, real tools: the committed goal graph and prose,
corrections.py, unit_goal.py, the frozen xaas prose_spans.py and -- when a
ggen_igniter checkout with the pinned toolchain is present -- the real
`mix semantic_jira.compile_prose` and the oxigraph stop witness. Mutations run
on copies in temporary directories; nothing in the repository is written. No
mock, patch or stub of any collaborator.

  python3 -m unittest discover -s release/v26.9.23/sjira -p 'test_*.py' -v

Env: GGEN_IGNITER_DIR, PROSE_SPANS, ELIXIR_BIN, ERLANG_BIN (same defaults as
compile_check.sh). The compiler/oxigraph tests skip with a named reason when
that checkout or toolchain is absent; they are never replaced by a fake.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REL = "release/v26.9.23/sjira"
SJ = Namespace("https://ggen-igniter.dev/ontology/semantic-jira#")
DCT = Namespace("http://purl.org/dc/terms/")
CE = Namespace("https://ggen-igniter.dev/sjira/chatman-26.9.23#")
NS = str(CE)
UNITS = ("chatman-ce23", "chatman-ce23-12-bench", "chatman-ce23-12-standings")
CROWN = (
    "CE23-0 CE23-1 CE23-2 CE23-3 CE23-4 CE23-5 CE23-6 CE23-7 CE23-8 CE23-9 CE23-10 "
    "CE23-12 CE23-12-BenchmarkDesign CE23-12-MSAContract CE23-12-GeneratedQualificationPlan"
).split()
GI = Path(os.environ.get("GGEN_IGNITER_DIR", "/Users/sac/wt/v26922/fri/ggen_igniter-int"))
SPANS = Path(os.environ.get("PROSE_SPANS", "/Users/sac/wt/v26922/fri/xaas-int/scripts/sjira/prose_spans.py"))
ELIXIR_BIN = Path(os.environ.get("ELIXIR_BIN", "/Users/sac/.asdf/installs/elixir/1.18.4-otp-27/bin"))
ERLANG_BIN = Path(os.environ.get("ERLANG_BIN", "/Users/sac/.asdf/installs/erlang/27.2.4/bin"))


def py(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True)


def copy_tree(dst: Path) -> Path:
    """Copy release/v26.9.23 into dst (same relative layout) and return the new root."""
    shutil.copytree(ROOT / "release/v26.9.23", dst / "release/v26.9.23")
    return dst


def goal_graph(path: Path = ROOT / REL / "goal.ttl") -> Graph:
    graph = Graph()
    graph.parse(path, format="turtle")
    return graph


def stop(graph: Graph) -> bool:
    query = str(graph.value(CE["GC-CE-26.9.23"], SJ.stopQuery))
    return bool(graph.query(query).askAnswer)


def with_alive(graph: Graph, ids, standing: str = "ALIVE") -> Graph:
    out = Graph()
    for triple in graph:
        out.add(triple)
    for gate in list(out.subjects(RDF.type, SJ.GoalCheckpoint)):
        ident = str(out.value(gate, DCT.identifier))
        if ident in ids:
            receipt = URIRef("urn:test:receipt:" + ident)
            out.add((gate, SJ.receipt, receipt))
            out.add((receipt, RDF.type, SJ.Receipt))
            out.add((receipt, SJ.standing, Literal(standing)))
    return out


class StopQueryTest(unittest.TestCase):
    """The root sj:stopQuery computes CHATMAN_STOP over the crown gates (rdflib)."""

    @classmethod
    def setUpClass(cls):
        cls.goal = goal_graph()

    def test_goal_asserts_no_receipt_and_stop_is_false(self):
        self.assertEqual(list(self.goal.subject_objects(SJ.receipt)), [])
        self.assertEqual(list(self.goal.subjects(RDF.type, SJ.WorkOrder)), [])
        self.assertFalse(stop(self.goal))

    def test_all_crown_gates_alive_is_true(self):
        self.assertTrue(stop(with_alive(self.goal, CROWN)))

    def test_each_missing_crown_gate_makes_stop_false(self):
        for gate in CROWN:
            with self.subTest(gate=gate):
                self.assertFalse(stop(with_alive(self.goal, [g for g in CROWN if g != gate])))

    def test_non_alive_receipt_does_not_count(self):
        graph = with_alive(self.goal, [g for g in CROWN if g != "CE23-8"])
        self.assertFalse(stop(with_alive(graph, ["CE23-8"], standing="UNKNOWN")))

    def test_tag_gate_is_a_consequence_not_a_term(self):
        self.assertFalse(stop(with_alive(self.goal, [g for g in CROWN if g != "CE23-9"] + ["CE23-11"])))

    def test_deleted_crown_gate_makes_stop_false(self):
        graph = with_alive(self.goal, CROWN)
        gate = CE["CE23-12-MSAContract"]
        for triple in list(graph.triples((gate, None, None))):
            graph.remove(triple)
        self.assertFalse(stop(graph))

    def test_open_order_under_a_crown_gate_keeps_stop_false(self):
        graph = with_alive(self.goal, CROWN)
        order = URIRef("urn:test:order")
        graph.add((order, RDF.type, SJ.WorkOrder))
        graph.add((order, SJ.checkpointOf, CE["CE23-12-MSAContract"]))
        self.assertFalse(stop(graph))
        graph.add((order, SJ.boundaryClass, SJ.Successor))
        self.assertTrue(stop(graph))

    def test_terminal_order_receipt_closes_and_tag_orders_are_outside(self):
        graph = with_alive(self.goal, CROWN)
        order = URIRef("urn:test:order")
        graph.add((order, RDF.type, SJ.WorkOrder))
        graph.add((order, SJ.checkpointOf, CE["CE23-3"]))
        receipt = URIRef("urn:test:order-receipt")
        graph.add((order, SJ.receipt, receipt))
        graph.add((receipt, RDF.type, SJ.Receipt))
        graph.add((receipt, SJ.standing, Literal("UNKNOWN")))
        self.assertFalse(stop(graph))
        graph.set((receipt, SJ.standing, Literal("BLOCKED:operator_acceptance")))
        self.assertTrue(stop(graph))
        tag = URIRef("urn:test:tag-order")
        graph.add((tag, RDF.type, SJ.WorkOrder))
        graph.add((tag, SJ.checkpointOf, CE["CE23-11"]))
        self.assertTrue(stop(graph))


class CorrectionsTest(unittest.TestCase):
    """candidates/<unit>.extract.json is apply(raw, corrections.json), and nothing else."""

    def args(self, root: Path):
        return [
            "--raw-dir", str(root / REL / "candidates/raw"),
            "--corrections", str(root / REL / "candidates/corrections.json"),
            "--out-dir", str(root / REL / "candidates"),
        ]

    def test_committed_extractions_recompute(self):
        result = py(str(HERE / "corrections.py"), "check", *self.args(ROOT))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("chatman-ce23=0 chatman-ce23-12-bench=0 chatman-ce23-12-standings=24", result.stdout)

    def test_raw_extractions_are_the_recorded_llm_edge(self):
        for unit in UNITS:
            items = json.loads((ROOT / REL / "candidates/raw" / f"{unit}.extract.json").read_text("utf-8"))
            self.assertTrue(items and all("quote" in i and "kind" in i for i in items), unit)

    def mutate(self, edit) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_tree(Path(tmp))
            edit(root)
            return py(str(HERE / "corrections.py"), "check", *self.args(root))

    def test_hand_edit_of_a_generated_extraction_is_refused(self):
        def edit(root):
            path = root / REL / "candidates/chatman-ce23-12-standings.extract.json"
            items = json.loads(path.read_text("utf-8"))
            items[3]["required_by"] = "CE23-12"
            path.write_text(json.dumps(items, indent=1, sort_keys=True, ensure_ascii=False) + "\n", "utf-8")

        result = self.mutate(edit)
        self.assertEqual(result.returncode, 1)
        self.assertIn("output_drift", result.stdout)

    def test_dropping_the_corrections_is_refused(self):
        def edit(root):
            path = root / REL / "candidates/corrections.json"
            doc = json.loads(path.read_text("utf-8"))
            doc["corrections"] = []
            path.write_text(json.dumps(doc), "utf-8")

        result = self.mutate(edit)
        self.assertEqual(result.returncode, 1)
        self.assertIn("REFUSED chatman-ce23-12-standings: output_drift", result.stdout)
        # the bench unit carries no correction: its extraction is the raw LLM edge as recorded
        self.assertNotIn("REFUSED chatman-ce23-12-bench", result.stdout)

    def test_quote_guard_and_uncorrectable_fields_are_refused(self):
        def edit(root):
            path = root / REL / "candidates/corrections.json"
            doc = json.loads(path.read_text("utf-8"))
            doc["corrections"][0]["quote"] = "not the raw quote"
            doc["corrections"][1]["field"] = "statement"
            path.write_text(json.dumps(doc), "utf-8")

        result = self.mutate(edit)
        self.assertEqual(result.returncode, 1)
        self.assertIn("quote_guard", result.stdout)
        self.assertIn("field_not_correctable", result.stdout)


class DesignObligationTest(unittest.TestCase):
    """CE23-12 keeps every benchmark design obligation, and every candidate names its extraction run.

    chatman-ce23-12-standings.md: BenchmarkDesign A = 'experiment, DOE, corpus, statistics and
    qualification rules defined', with acceptance 'near-miss/UNKNOWN falsifiers identified' and 'DOE
    support matrix generated'. The standings rule keeps NON_LLM_OPERATIONAL standing out of the design
    crown, so no bench item (B1..B6: DOE, typed fault states, near-miss UNKNOWN, ...) is demoted off
    CE23-12 by a correction. Real committed files only.
    """

    BENCH = "chatman-ce23-12-bench"
    RUN_ID = re.compile(r"^llm:claude-opus-5-5@wf_[0-9a-f]{8}-[0-9a-f]{3}/\S+$")

    def test_no_correction_touches_a_bench_item(self):
        doc = json.loads((ROOT / REL / "candidates/corrections.json").read_text("utf-8"))
        touched = [(e["index"], e["field"]) for e in doc["corrections"] if e["unit"] == self.BENCH]
        self.assertEqual(touched, [])

    def test_bench_extraction_is_the_raw_llm_edge(self):
        generated = (ROOT / REL / "candidates" / f"{self.BENCH}.extract.json").read_bytes()
        raw = (ROOT / REL / "candidates/raw" / f"{self.BENCH}.extract.json").read_bytes()
        self.assertEqual(generated, raw)

    def test_every_raw_ce23_12_bench_item_stays_required_by_ce23_12(self):
        raw = json.loads((ROOT / REL / "candidates/raw" / f"{self.BENCH}.extract.json").read_text("utf-8"))
        wanted = {i["quote"] for i in raw if i.get("required_by") == "CE23-12"}
        self.assertEqual(len(wanted), 17)
        graph = Graph()
        graph.parse(ROOT / REL / "candidates" / f"{self.BENCH}.ttl", format="turtle")
        required = {
            str(graph.value(s, SJ.sourceText))
            for s in graph.subjects(SJ.requiredBy, CE["CE23-12"])
        }
        for quote in ("Run a designed experiment rather than random chaos.", "not uncontrolled continuation."):
            self.assertIn(quote, required)
        self.assertEqual(len(required), 17)

    def test_bench_unit_compiles_to_nine_design_orders(self):
        graph = Graph()
        graph.parse(ROOT / REL / "compiled" / self.BENCH / "orders.ttl", format="turtle")
        self.assertEqual(len(set(graph.subjects(RDF.type, SJ.WorkOrder))), 9)

    def test_every_candidate_names_its_extraction_run(self):
        for unit in UNITS:
            with self.subTest(unit=unit):
                graph = Graph()
                graph.parse(ROOT / REL / "candidates" / f"{unit}.ttl", format="turtle")
                ids = {str(o) for o in graph.objects(None, SJ.extractedBy)}
                self.assertEqual(len(ids), 1, ids)
                self.assertRegex(ids.pop(), self.RUN_ID)


class UnitGoalTest(unittest.TestCase):
    """The three unit views are projections of goal.ttl and partition its 16 gates."""

    def partition(self, root: Path) -> subprocess.CompletedProcess:
        units = []
        for unit in UNITS:
            units += ["--unit", f"{REL}/{unit}.md"]
        return py(str(HERE / "unit_goal.py"), "partition", "--goal", f"{REL}/goal.ttl", *units, cwd=root)

    def view(self, root: Path, unit: str, cmd: str = "check") -> subprocess.CompletedProcess:
        return py(
            str(HERE / "unit_goal.py"), cmd, "--goal", f"{REL}/goal.ttl", "--unit", f"{REL}/{unit}.md",
            "--source", f"{REL}/{unit}.md", "--out", f"{REL}/units/{unit}.goal.ttl", cwd=root,
        )

    def test_committed_views_and_partition_hold(self):
        result = self.partition(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("16 GoalCheckpoints", result.stdout)
        for unit in UNITS:
            with self.subTest(unit=unit):
                self.assertEqual(self.view(ROOT, unit).returncode, 0)

    def test_view_roots_and_gates(self):
        expect = {
            "chatman-ce23": ("GC-CE-26.9.23", 12),
            "chatman-ce23-12-bench": ("GC-CE-26.9.23", 1),
            "chatman-ce23-12-standings": ("CE23-12", 3),
        }
        for unit, (root_id, n) in expect.items():
            graph = goal_graph(ROOT / REL / "units" / f"{unit}.goal.ttl")
            roots = [s for s in graph.subjects(RDF.type, SJ.GoalCheckpoint) if graph.value(s, SJ.checkpointOf) is None]
            self.assertEqual([str(graph.value(r, DCT.identifier)) for r in roots], [root_id], unit)
            self.assertEqual(len(list(graph.subjects(SJ.checkpointOf, roots[0]))), n, unit)

    def rewrite_goal(self, root: Path, old: str, new: str) -> None:
        path = root / REL / "goal.ttl"
        text = path.read_text("utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), "utf-8")

    def test_gate_without_a_unit_is_a_partition_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_tree(Path(tmp))
            self.rewrite_goal(
                root,
                'sj:checkpointOf ce:CE23-12 ;\n    sj:boundaryClass sj:LastMile ;\n'
                '    dcterms:source "release/v26.9.23/sjira/chatman-ce23-12-standings.md" ;\n'
                '    sj:sourceSha256 "sha256:80091c45b16d6afbf0bfa5717726c9221f35905f5650fad03b8cd81cbcb5b2d2" ;\n'
                '    sj:courtCommand "sh release/v26.9.23/courts/CE23-12-MSAContract.sh"',
                'sj:checkpointOf ce:CE23-12 ;\n    sj:boundaryClass sj:LastMile ;\n'
                '    sj:courtCommand "sh release/v26.9.23/courts/CE23-12-MSAContract.sh"',
            )
            result = self.partition(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("partition_gap", result.stdout)
            self.assertIn("CE23-12-MSAContract", result.stdout)
            self.assertIn("output_drift", self.view(root, "chatman-ce23-12-standings").stdout)

    def test_gate_pinned_to_other_bytes_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_tree(Path(tmp))
            path = root / REL / "chatman-ce23-12-bench.md"
            path.write_bytes(path.read_bytes() + b"\n")
            result = self.view(root, "chatman-ce23-12-bench", cmd="emit")
            self.assertEqual(result.returncode, 1)
            self.assertIn("source_sha256_mismatch", result.stdout)

    def test_hand_edited_view_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_tree(Path(tmp))
            path = root / REL / "units/chatman-ce23.goal.ttl"
            path.write_text(path.read_text("utf-8").replace('"CE23-10"', '"CE23-10b"', 1), "utf-8")
            result = self.view(root, "chatman-ce23")
            self.assertEqual(result.returncode, 1)
            self.assertIn("output_drift", result.stdout)


@unittest.skipUnless(SPANS.is_file(), f"prose_spans.py not found at {SPANS}")
class CandidatesTest(unittest.TestCase):
    """Candidates re-verify against the committed prose bytes (the frozen xaas tool)."""

    def check(self, root: Path, unit: str) -> subprocess.CompletedProcess:
        return py(
            str(SPANS), "check", "--source", f"{REL}/{unit}.md", "--candidates", f"{REL}/candidates/{unit}.ttl",
            "--namespace", NS, "--prefix", "ce", "--extract", f"{REL}/candidates/{unit}.extract.json", cwd=root,
        )

    def test_committed_candidates_verify(self):
        for unit in UNITS:
            with self.subTest(unit=unit):
                result = self.check(ROOT, unit)
                self.assertEqual(result.returncode, 0, result.stdout)

    def test_one_byte_of_prose_changed_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_tree(Path(tmp))
            path = root / REL / "chatman-ce23.md"
            data = bytearray(path.read_bytes())
            at = data.index(b"CHATMAN")
            data[at] = ord("X")
            path.write_bytes(bytes(data))
            result = self.check(root, "chatman-ce23")
            self.assertEqual(result.returncode, 1)
            self.assertIn("source_sha256_mismatch", result.stdout)


def toolchain_ready() -> str | None:
    if not (GI / "mix.exs").is_file():
        return f"no ggen_igniter checkout at {GI}"
    if not (GI / "_build/test").is_dir():
        return f"{GI} has no _build/test"
    if not (ELIXIR_BIN / "mix").exists() or not (ERLANG_BIN / "erl").exists():
        return "pinned Elixir/Erlang toolchain not installed"
    if not SPANS.is_file():
        return f"prose_spans.py not found at {SPANS}"
    return None


SKIP = toolchain_ready()


@unittest.skipIf(SKIP is not None, SKIP or "")
class CompilerTest(unittest.TestCase):
    """The real ggen_igniter compiler refuses the inputs the unit design must refuse."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        base = Path(cls.tmp.name)
        cls.build = base / "build-test"
        subprocess.run(["cp", "-cRp", str(GI / "_build/test"), str(cls.build)], check=True)
        (base / "home").mkdir()
        user_base = subprocess.run([sys.executable, "-m", "site", "--user-base"], capture_output=True, text=True)
        cls.env = {
            "HOME": str(base / "home"),
            "PATH": f"{ELIXIR_BIN}:{ERLANG_BIN}:{Path(sys.executable).parent}:/usr/bin:/bin",
            "MIX_HOME": os.environ.get("MIX_HOME", str(Path.home() / ".mix")),
            "HEX_HOME": os.environ.get("HEX_HOME", str(Path.home() / ".hex")),
            "LANG": "en_US.UTF-8",
            "MIX_ENV": "test",
            "MIX_BUILD_PATH": str(cls.build),
            "PYTHONUSERBASE": user_base.stdout.strip(),
        }

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def mix(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["mix", *args], cwd=GI, env=self.env, capture_output=True, text=True, timeout=900)

    def compile(self, root: Path, unit: str, candidates: Path, goal_unit: str | None = None) -> subprocess.CompletedProcess:
        return self.mix(
            "semantic_jira.compile_prose",
            "--source", str(root / REL / f"{unit}.md"),
            "--candidates", str(candidates),
            "--goal", str(root / REL / "units" / f"{goal_unit or unit}.goal.ttl"),
            "--out-dir", str(root / "out" / unit),
        )

    def emit(self, root: Path, unit: str, items: list, extracted_by: str) -> Path:
        extract = root / f"{unit}.mutant.extract.json"
        extract.write_text(json.dumps(items, indent=1, sort_keys=True, ensure_ascii=False) + "\n", "utf-8")
        out = root / f"{unit}.mutant.ttl"
        result = py(
            str(SPANS), "emit", "--source", f"{REL}/{unit}.md", "--extract", str(extract), "--out", str(out),
            "--source-path", f"{REL}/{unit}.md", "--extracted-by", extracted_by, "--namespace", NS, "--prefix", "ce",
            cwd=root,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        return out

    def test_committed_units_compile_and_recompute(self):
        for unit in UNITS:
            with self.subTest(unit=unit):
                result = self.mix(
                    "semantic_jira.compile_prose", "--source", str(ROOT / REL / f"{unit}.md"),
                    "--candidates", str(ROOT / REL / "candidates" / f"{unit}.ttl"),
                    "--goal", str(ROOT / REL / "units" / f"{unit}.goal.ttl"),
                    "--out-dir", str(ROOT / REL / "compiled" / unit), "--check",
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("recompute byte-identically", result.stdout)

    def test_gate_without_a_required_proposition_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_tree(Path(tmp))
            items = json.loads((ROOT / REL / "candidates/chatman-ce23.extract.json").read_text("utf-8"))
            kept = [i for i in items if i.get("required_by") != "CE23-10"]
            self.assertEqual(len(items) - len(kept), 1)
            ttl = self.emit(root, "chatman-ce23", kept, "test:mutant")
            result = self.compile(root, "chatman-ce23", ttl)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("uncovered_gate", result.stdout + result.stderr)
            self.assertIn("CE23-10", result.stdout + result.stderr)

    def test_uncorrected_standings_extraction_leaves_conjuncts_uncovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_tree(Path(tmp))
            raw = json.loads((ROOT / REL / "candidates/raw/chatman-ce23-12-standings.extract.json").read_text("utf-8"))
            ttl = self.emit(root, "chatman-ce23-12-standings", raw, "test:raw")
            result = self.compile(root, "chatman-ce23-12-standings", ttl)
            output = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0)
            for gate in ("CE23-12-BenchmarkDesign", "CE23-12-MSAContract", "CE23-12-GeneratedQualificationPlan"):
                self.assertIn(gate, output)
            self.assertIn("uncovered_gate", output)

    def test_candidates_of_another_prose_are_refused_by_the_view_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = copy_tree(Path(tmp))
            result = self.mix(
                "semantic_jira.compile_prose", "--source", str(root / REL / "chatman-ce23-12-bench.md"),
                "--candidates", str(root / REL / "candidates/chatman-ce23-12-bench.ttl"),
                "--goal", str(root / REL / "units/chatman-ce23.goal.ttl"),
                "--out-dir", str(root / "out"),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("provenance_mismatch", result.stdout + result.stderr)

    def test_oxigraph_stop_witness_agrees_with_the_crown(self):
        goal = str(ROOT / REL / "goal.ttl")
        witness = str(HERE / "stop_witness.exs")
        full = self.mix("run", witness, goal, *CROWN)
        self.assertIn("STOP=true (ALIVE gates: 15)", full.stdout, full.stderr)
        partial = self.mix("run", witness, goal, *[g for g in CROWN if g != "CE23-12-MSAContract"], "CE23-11")
        self.assertIn("STOP=false (ALIVE gates: 15)", partial.stdout, partial.stderr)


if __name__ == "__main__":
    unittest.main()
