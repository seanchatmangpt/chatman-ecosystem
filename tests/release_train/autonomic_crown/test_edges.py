"""Edge inventory court (RFC-0005 §5, §6) and U-01..U-04 on the committed edges.json."""

from __future__ import annotations

import copy
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from _autonomic_support import AUTONOMY, committed_evaluation, committed_inputs, load

from scripts.release_train.autonomic_crown import edges
from scripts.release_train.autonomic_crown.locate import EvidenceResolver, Unresolved, git_blob_id
from scripts.release_train.autonomic_crown.model import STAGES


class EdgesTest(unittest.TestCase):
    def setUp(self):
        self.inputs = committed_inputs(self)
        self.doc = load(AUTONOMY / "edges.json")

    def check(self, doc):
        return edges.check(doc, self.inputs.source, "68bacd8dcc9ae12e4e97727a284c14abdc7520c5")

    def test_inventory_shape(self):
        rep = self.check(self.doc)
        self.assertEqual(len(rep.edges), 13)
        self.assertEqual({e["stage"] for e in rep.edges}, set(STAGES))
        self.assertTrue(all(e["recurring"] for e in rep.edges))
        self.assertEqual(sorted(rep.unresolved), ["E-CONT-01"])
        self.assertEqual(len(rep.resolved), 12)
        # Every resolved digest recomputes to the declared one.
        declared = {e["id"]: e["evidence"]["sha256"] for e in self.doc["edges"]}
        self.assertEqual({k: declared[k] for k in rep.resolved}, rep.resolved)
        self.assertEqual([(f.code, f.subject) for f in rep.findings], [("EVIDENCE_UNRESOLVED", "E-CONT-01")])

    def test_edge_gates(self):
        ev = committed_evaluation(self)
        g = {x.id: x for x in ev.gates}
        self.assertEqual((g["U-01"].state, g["U-01"].measured), ("BLOCKED", "7/11"))
        self.assertEqual(g["U-02"].findings, ["E-ADM-02", "E-CON-01", "E-OBS-02", "E-REP-01"])
        self.assertEqual(g["U-03"].findings, ["E-ADM-02", "E-CON-01", "E-REP-01"])
        self.assertEqual((g["U-04"].measured, g["U-04"].findings), ("12/13", ["E-CONT-01"]))

    def test_authority_gate_edges_are_not_operational_dependencies(self):
        by_id = {e["id"]: e for e in self.doc["edges"]}
        for eid in ("E-ADM-01", "E-ACT-01"):
            self.assertTrue(edges.is_authority_gate_only(by_id[eid]), eid)
            self.assertFalse(edges.is_operational_dependency(by_id[eid]), eid)
        self.assertIsNone(by_id["E-ACT-02"]["authority_gate"])  # absent reviewer: no enforced grant

    def test_integrity_refusals(self):
        cases = {
            "EDGE_MALFORMED": lambda d: d["edges"][0].update(owner_kind="robot", owner_kinds=["robot"]),
            "LOCATOR_NOT_DURABLE": lambda d: d["edges"][1]["evidence"].update(locator="~/obs.json"),
            "EVIDENCE_DIGEST_MISMATCH": lambda d: d["edges"][1]["evidence"].update(sha256="0" * 64),
            "OWNER_KIND_UNWITNESSED": lambda d: d["edges"][2].update(owner_kind="machine", owner_kinds=["machine"]),
            "AUTHORITY_AMPLIFICATION": lambda d: d["edges"][0].update(
                authority_gate={"grantor": "crown", "grant": "tag"}
            ),
            "STAGE_UNCOVERED": lambda d: d["edges"].pop(0),
            "SUBJECT_SPLIT": lambda d: d.update(crown_subject="a" * 40),
            "UNSUPPORTED_EVIDENCE_KIND": lambda d: d["edges"][6]["evidence"].update(kind="sbom"),
        }
        for code, fn in cases.items():
            with self.subTest(code=code):
                doc = copy.deepcopy(self.doc)
                fn(doc)
                self.assertIn(code, {f.code for f in self.check(doc).findings})

    def test_schema_refusal(self):
        self.assertEqual([f.code for f in self.check({"schema": "edges.v0", "edges": []}).findings], ["EDGE_MALFORMED"])


class ResolverTest(unittest.TestCase):
    """The production resolver against a real temporary git repository (no chatman DB needed)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.repo = root / "chatman-ecosystem"
        self.repo.mkdir()

        def git(*a):
            return subprocess.run(["git", "-C", str(self.repo), *a], check=True, capture_output=True)

        git("init", "-q")
        git("config", "user.email", "t@example.invalid")
        git("config", "user.name", "t")
        git("remote", "add", "origin", "https://github.com/seanchatmangpt/chatman-ecosystem.git")
        (self.repo / "e.json").write_bytes(b'{"x": 1}\n')
        git("add", "e.json")
        git("commit", "-q", "-m", "e")
        self.sha = git("rev-parse", "HEAD").stdout.decode().strip()
        self.root = root
        self.copy = b"# RFC\n"
        self.row = {
            "source_repo": "seanchatmangpt/engineering-standards",
            "source_sha": "1" * 40,
            "source_path": "docs/rfc.md",
            "source_blob_sha1": git_blob_id(self.copy),
        }

    def tearDown(self):
        self.tmp.cleanup()

    def resolver(self, root=None):
        return EvidenceResolver(self.root if root is None else root, [(self.row, self.copy)])

    def code(self, locator, root=None):
        try:
            self.resolver(root).resolve(locator)
        except Unresolved as exc:
            return exc.code
        return "OK"

    def test_root_repository_blob(self):
        data = self.resolver().resolve(f"git:seanchatmangpt/chatman-ecosystem@{self.sha}:e.json")
        self.assertEqual(hashlib.sha256(data).hexdigest(), hashlib.sha256(b'{"x": 1}\n').hexdigest())
        self.assertEqual(
            self.code(f"git:seanchatmangpt/chatman-ecosystem@{self.sha}:missing.json"), "EVIDENCE_UNRESOLVED"
        )

    def test_foreign_only_through_an_admitted_import(self):
        self.assertEqual(
            self.resolver().resolve("git:seanchatmangpt/engineering-standards@" + "1" * 40 + ":docs/rfc.md"), self.copy
        )
        self.assertEqual(
            self.code("git:seanchatmangpt/engineering-standards@" + "2" * 40 + ":docs/rfc.md"), "EVIDENCE_UNRESOLVED"
        )
        self.assertEqual(self.code(f"git:attacker/chatman-ecosystem@{self.sha}:e.json"), "EVIDENCE_UNRESOLVED")

    def test_non_durable_and_unfetchable(self):
        self.assertEqual(self.code("/private/tmp/x.json"), "LOCATOR_NOT_DURABLE")
        self.assertEqual(self.code("~/x.json"), "LOCATOR_NOT_DURABLE")
        self.assertEqual(self.code("https://github.com/o/r/actions/runs/1/artifacts"), "EVIDENCE_UNRESOLVED")

    def test_missing_object_database_is_transport(self):
        empty = self.root / "empty"
        empty.mkdir()
        self.assertEqual(
            self.code(f"git:seanchatmangpt/chatman-ecosystem@{self.sha}:e.json", root=empty), "TRANSPORT_UNAVAILABLE"
        )
        try:
            EvidenceResolver(None, []).resolve(f"git:seanchatmangpt/chatman-ecosystem@{self.sha}:e.json")
        except Unresolved as exc:
            self.assertEqual(exc.code, "TRANSPORT_UNAVAILABLE")
        else:
            self.fail("resolved without an object database")


if __name__ == "__main__":
    unittest.main()
