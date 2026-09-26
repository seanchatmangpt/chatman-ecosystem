"""Chicago-style tests for topology.py: real git repositories built in the lane fixtures directory (fixtures, not shadows),
real snapshots, real pushes to a local bare 'origin', real archive-based restore drills. No test doubles of any kind.

Every gate rule R1..R17 gets a PASS baseline on a real world and a mutant that the rule must refuse.
Linked worktrees are built from their on-disk structure (admin dir + .git file) rather than `git worktree add`, so the
fixture never invokes the command the topology guard forbids; git treats them exactly like any linked worktree.
"""

import json
import os
import shutil
import subprocess
import sys
import unittest
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.environ.get("TOPO_FIXTURES", "/private/tmp/claude-501/-Users-sac/90d06f90-3c25-4b15-bede-3d0e7e58ac78/scratchpad/v26925/lanes/topo/fixtures")
sys.path.insert(0, os.path.dirname(HERE))


def sh(*a, cwd=None, check=True, env=None):
    e = dict(os.environ, GIT_AUTHOR_NAME="fx", GIT_AUTHOR_EMAIL="fx@x", GIT_COMMITTER_NAME="fx", GIT_COMMITTER_EMAIL="fx@x")
    e.update(env or {})
    p = subprocess.run(list(a), cwd=cwd, capture_output=True, text=True, env=e)
    if check and p.returncode:
        raise AssertionError(f"{a}: {p.stderr}")
    return p.stdout.strip()


class World:
    def __init__(self, name):
        self.root = os.path.realpath(os.path.join(FIX, f"{name}-{uuid.uuid4().hex[:8]}"))
        os.makedirs(self.root)
        self.home = os.path.join(self.root, "state")
        self.scratch = os.path.join(self.root, "scratch")
        self.trash = os.path.join(self.root, "trash")
        for d in (self.home, self.scratch, self.trash, os.path.join(self.home, "verify")):
            os.makedirs(d, exist_ok=True)
        self.origin = os.path.join(self.root, "origin.git")
        sh("git", "init", "-q", "--bare", "-b", "main", self.origin)
        self.K = os.path.join(self.root, "K")
        os.makedirs(self.K)
        sh("git", "init", "-q", "-b", "main", cwd=self.K)
        self.write(self.K, "a.txt", "alpha\n")
        self.write(self.K, "src/b.py", "print('b')\n")
        self.write(self.K, ".gitignore", "*.log\n/target/\n")
        sh("git", "add", "-A", cwd=self.K)
        sh("git", "commit", "-q", "-m", "init", cwd=self.K)
        sh("git", "remote", "add", "origin", self.origin, cwd=self.K)
        sh("git", "push", "-q", "origin", "main", cwd=self.K)
        sh("git", "fetch", "-q", "origin", cwd=self.K)
        self.scope = {
            "canonicals": {"fx": self.K},
            "extra_copies": [],
            "owned_remote_patterns": ["local:" + self.root],
            "refs_only_repos": [],
            "revoked_blobs": [],
        }

    @staticmethod
    def write(base, rel, text, mode="w"):
        p = os.path.join(base, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, mode) as f:
            f.write(text)
        return p

    def linked_worktree(self, name, branch):
        sh("git", "branch", branch, cwd=self.K)
        admin = os.path.join(self.K, ".git", "worktrees", name)
        os.makedirs(admin)
        W = os.path.join(self.K, ".claude", "worktrees", name)
        os.makedirs(W)
        self.write(admin, "HEAD", f"ref: refs/heads/{branch}\n")
        self.write(admin, "commondir", "../..\n")
        self.write(admin, "gitdir", W + "/.git\n")
        self.write(W, ".git", f"gitdir: {admin}\n")
        sh("git", "read-tree", "HEAD", cwd=W)
        sh("git", "checkout-index", "-a", "-f", cwd=W)
        return W

    def prunable(self, name, branch):
        W = self.linked_worktree(name, branch)
        shutil.rmtree(W)
        return W

    def clone(self, name):
        C = os.path.join(self.root, name)
        sh("git", "clone", "-q", self.origin, C)
        return C

    def save_scope(self):
        with open(os.path.join(self.home, "scope.json"), "w") as f:
            json.dump(self.scope, f)

    def T(self):
        """topology module bound to this world's state dirs (fresh import per world: module-level config)."""
        os.environ.update(TOPO_HOME=self.home, TOPO_SCRATCH=self.scratch, TOPO_TRASH=self.trash)
        import importlib
        import topology

        importlib.reload(topology)
        return topology

    def run(self, *argv):
        self.save_scope()
        t = self.T()
        return t, t.main([*argv, "--scope", os.path.join(self.home, "scope.json")])

    def full(self, push=True):
        self.run("freeze")
        self.run("inventory")
        self.run("preserve", *(["--push"] if push else []))
        self.run("drill")
        t = self.T()
        return t

    def gate(self, cid, lock=True):
        t = self.T()
        scope = t.load_scope(os.path.join(self.home, "scope.json"))
        g = t.Gate(
            scope,
            t.jload("INVENTORY.json"),
            t.load_parts("PRESERVE", {"records": {}}),
            t.load_parts("verify/drill", {}),
            t.jload("RUN.json")["run_id"],
        )
        inv = t.jload("INVENTORY.json")
        for n in t.gate_order(inv, [x for x in inv["copies"] if inv["copies"][x]["kind"] in t.RETIRABLE]):
            if n == cid:
                break
            if lock:
                with t.Lock("fx"):
                    g.cache[n] = g.check(n)
        if lock:
            with t.Lock("fx"):
                return g.check(cid)
        return g.check(cid)

    def cid(self, path):
        return self.T().slug(path)


class Base(unittest.TestCase):
    def world(self, name):
        w = World(name)
        self.addCleanup(lambda: None)
        return w

    def assertRefuses(self, res, rule):
        self.assertEqual(res["verdict"], "REFUSED", res)
        self.assertIn(rule, res["failed_rules"], res)

    def assertPass(self, res):
        self.assertEqual(res["verdict"], "PASS", json.dumps(res, indent=1)[:3000])


def dirty_linked(w):
    W = w.linked_worktree("agent-1", "worktree-agent-1")
    w.write(W, "a.txt", "alpha changed\n")
    w.write(W, 'new dir/odd "name".txt', "untracked\n")
    w.write(W, "notes.log", "ignored evidence\n")
    return W


class TestGateRules(Base):
    def setUp(self):
        self.w = self.world("gate")
        self.W = dirty_linked(self.w)
        self.C = self.w.clone("C")
        self.w.write(self.C, "c.txt", "clone wip\n")
        sh("git", "checkout", "-q", "-b", "feature", cwd=self.C)
        self.w.write(self.C, "f.txt", "feature\n")
        sh("git", "add", "f.txt", cwd=self.C)
        sh("git", "commit", "-q", "-m", "feature commit", cwd=self.C)
        self.w.scope["extra_copies"] = [{"path": self.C, "owner": "fx"}]
        self.w.full()
        self.cw, self.cc = self.w.cid(self.W), self.w.cid(self.C)

    def test_baseline_pass(self):
        self.assertPass(self.w.gate(self.cw))
        self.assertPass(self.w.gate(self.cc))

    def test_R1_frozen(self):
        self.w.write(self.W, "src/b.py", "changed after freeze\n")
        self.assertRefuses(self.w.gate(self.cw), "R1")

    def test_R2_ref_resolves(self):
        t = self.w.T()
        sh("git", "update-ref", "-d", f"{t.NS}/{self.cc}/heads/feature", cwd=self.w.K)
        self.assertRefuses(self.w.gate(self.cc), "R2")

    def test_R3_commit_reachable(self):
        t = self.w.T()
        # remove every anchor of the clone's commits: preserve refs, the pushed backup branch and its remote-tracking ref
        for r in sh("git", "for-each-ref", "--format=%(refname)", f"{t.NS}/{self.cc}", "refs/remotes/origin/backup", cwd=self.w.K).split():
            sh("git", "update-ref", "-d", r, cwd=self.w.K)
        for r in sh("git", "for-each-ref", "--format=%(refname)", "refs/heads/backup", cwd=self.w.origin).split():
            sh("git", "update-ref", "-d", r, cwd=self.w.origin)
        self.assertRefuses(self.w.gate(self.cc), "R3")

    def test_R4_dirty_archived(self):
        t = self.w.T()
        p = t.load_parts("PRESERVE", {"records": {}})
        rec = p["records"][self.cw]
        base = sh("git", "rev-parse", f"{rec['refs'][t.NS + '/' + self.cw + '/dirty']}^1", cwd=self.w.K)
        sh("git", "update-ref", f"{t.NS}/{self.cw}/dirty", base, cwd=self.w.K)
        rec["refs"][f"{t.NS}/{self.cw}/dirty"] = base
        t.save_part("PRESERVE", "fx", p)
        self.assertRefuses(self.w.gate(self.cw), "R4")

    def test_R5_ignored_evidence(self):
        self.w.write(self.W, "notes.log", "ignored evidence mutated\n")
        res = self.w.gate(self.cw)
        self.assertRefuses(res, "R5")
        self.assertNotIn("R1", res["failed_rules"])  # ignored files are outside the fingerprint; R5 alone catches it

    def test_R6_stash(self):
        self.w.write(self.C, "f.txt", "stash me\n")
        sh("git", "stash", "-q", cwd=self.C)
        self.assertRefuses(self.w.gate(self.cc), "R6")

    def test_R7_snapshot_fresh(self):
        t = self.w.T()
        p = t.load_parts("PRESERVE", {"records": {}})
        p["records"][self.cw]["snapshot_tree"] = t.EMPTY_TREE
        t.save_part("PRESERVE", "fx", p)
        res = self.w.gate(self.cw)
        self.assertRefuses(res, "R7")
        self.assertEqual(res["failed_rules"], ["R7"])

    def test_R8_remote_durable(self):
        t = self.w.T()
        rec = t.load_parts("PRESERVE", {"records": {}})["records"][self.cw]
        self.assertTrue(rec["remote_verified_sha"])
        sh("git", "update-ref", "-d", f"refs/heads/{rec['remote_ref']}", cwd=self.w.origin)
        res = self.w.gate(self.cw)
        self.assertRefuses(res, "R8")

    def test_R9_no_key_material_pushed(self):
        t = self.w.T()
        blob = sh("git", "rev-parse", f"{t.NS}/{self.cw}/dirty:a.txt", cwd=self.w.K)
        self.w.scope["revoked_blobs"] = [blob]
        self.w.save_scope()
        self.assertRefuses(self.w.gate(self.cw), "R9")

    def test_R10_not_canonical(self):
        self.w.scope["canonicals"]["fx2"] = self.C
        self.w.save_scope()
        self.assertRefuses(self.w.gate(self.cc), "R10")

    def test_R11_no_nested_ungated(self):
        n = os.path.join(self.C, "vendor", "inner")
        os.makedirs(n)
        sh("git", "init", "-q", n)
        self.assertRefuses(self.w.gate(self.cc), "R11")

    def test_R12_rollback_qualified(self):
        t = self.w.T()
        d = t.load_parts("verify/drill", {})
        d[self.cw]["ok"] = False
        t.save_part("verify/drill", "all", d)
        self.assertRefuses(self.w.gate(self.cw), "R12")

    def test_R13_lock_held(self):
        self.assertRefuses(self.w.gate(self.cw, lock=False), "R13")

    def test_R14_not_live(self):
        p = subprocess.Popen(["sleep", "30"], cwd=self.W)
        try:
            self.assertRefuses(self.w.gate(self.cw), "R14")
        finally:
            p.kill()
            p.wait()

    def test_R17_owner_resolved(self):
        t = self.w.T()
        inv = t.jload("INVENTORY.json")
        inv["copies"][self.cc]["foreign"] = True
        inv["copies"][self.cc]["signed_off"] = False
        t.jdump("INVENTORY.json", inv)
        self.assertRefuses(self.w.gate(self.cc), "R17")


class TestSizeSecretOrphan(Base):
    def test_R15_size(self):
        w = self.world("size")
        W = w.linked_worktree("agent-big", "wt-big")
        with open(os.path.join(W, "blob.bin"), "wb") as f:
            f.write(os.urandom(4096))
        os.environ["TOPO_BIG"] = "1024"
        try:
            w.full()
            res = w.gate(w.cid(W))
        finally:
            os.environ.pop("TOPO_BIG")
        self.assertRefuses(res, "R15")

    def test_R16_secret_unpreservable_and_dedup(self):
        w = self.world("secret")
        W = w.linked_worktree("agent-sec", "wt-sec")
        w.write(W, ".env", "API=sk-ant-" + "x" * 40 + "\n")
        w.full()
        self.assertRefuses(w.gate(w.cid(W)), "R16")
        # same secret byte-identical in the canonical checkout: deduplicated, nothing is lost by retiring the copy
        w2 = self.world("secretdedup")
        W2 = w2.linked_worktree("agent-sec", "wt-sec")
        w2.write(W2, ".env", "API=sk-ant-" + "y" * 40 + "\n")
        w2.write(w2.K, ".env", "API=sk-ant-" + "y" * 40 + "\n")
        with open(os.path.join(w2.K, ".git", "info", "exclude"), "a") as f:
            f.write(".env\n")
        w2.full()
        self.assertPass(w2.gate(w2.cid(W2)))

    def test_revoked_key_redacted_and_passes(self):
        w = self.world("revoked")
        w.write(w.K, ".ggen/keys/signing.key", "-----BEGIN PRIVATE KEY-----\nREVOKED\n-----END PRIVATE KEY-----\n")
        sh("git", "add", "-f", ".ggen/keys/signing.key", cwd=w.K)
        sh("git", "commit", "-q", "-m", "key (revoked later)", cwd=w.K)
        sh("git", "push", "-q", "origin", "main", cwd=w.K)
        sh("git", "fetch", "-q", "origin", cwd=w.K)
        blob = sh("git", "rev-parse", "HEAD:.ggen/keys/signing.key", cwd=w.K)
        w.scope["revoked_blobs"] = [blob]
        W = w.linked_worktree("agent-key", "wt-key")
        w.write(W, "wip.txt", "wip\n")
        w.full()
        t = w.T()
        rec = t.load_parts("PRESERVE", {"records": {}})["records"][w.cid(W)]
        self.assertEqual([r["path"] for r in rec["redacted"]], [".ggen/keys/signing.key"])
        tree = sh("git", "ls-tree", "-r", "--name-only", f"{t.NS}/{w.cid(W)}/dirty", cwd=w.K)
        self.assertNotIn(".ggen/keys/signing.key", tree.split("\n"))
        self.assertTrue(rec["remote_verified_sha"])
        self.assertPass(w.gate(w.cid(W)))

    def test_orphan_and_prunable(self):
        w = self.world("orphan")
        O = os.path.join(w.K, ".claude", "worktrees", "agent-orphan")
        os.makedirs(O)
        w.write(O, ".git", "gitdir: /nonexistent/scikit-decide/.git/worktrees/agent-orphan\n")
        for i in range(30):
            w.write(w.K, f"lib/m{i}.txt", f"module {i}\n")
            w.write(O, f"lib/m{i}.txt", f"module {i}\n")
        sh("git", "add", "lib", cwd=w.K)
        sh("git", "commit", "-q", "-m", "lib", cwd=w.K)
        sh("git", "push", "-q", "origin", "main", cwd=w.K)
        w.write(O, "a.txt", "alpha\n")
        w.write(O, ".gitignore", "*.log\n/target/\n")
        w.write(O, "src/b.py", "print('b') orphan edit\n")
        w.write(O, "target/big.o", "regen\n")
        P = w.prunable("stale-1", "stale-branch")
        w.full()
        t = w.T()
        inv = t.jload("INVENTORY.json")
        self.assertEqual(inv["copies"][w.cid(O)]["kind"], "ORPHAN_WORKTREE")
        self.assertEqual(inv["copies"][w.cid(P)]["kind"], "PRUNABLE_RECORD")
        self.assertPass(w.gate(w.cid(O)))
        self.assertPass(w.gate(w.cid(P)))


class TestDrillAndCleanup(Base):
    def test_drill_byte_exact_and_mutant(self):
        w = self.world("drill")
        W = dirty_linked(w)
        with open(os.path.join(W, "bin.dat"), "wb") as f:
            f.write(bytes(range(256)) * 16)
        os.symlink("a.txt", os.path.join(W, "link-to-a"))
        w.full()
        t = w.T()
        d = t.load_parts("verify/drill", {})[w.cid(W)]
        self.assertTrue(d["ok"], d)
        self.assertGreaterEqual(d["files"], 6)
        # mutant: live file changes after preserve -> drill must fail with the exact path
        w.write(W, "bin.dat", "tampered")
        w.run("drill")
        d = t.load_parts("verify/drill", {})[w.cid(W)]
        self.assertFalse(d["ok"])
        self.assertIn("bin.dat", d["mismatch"])

    def test_staged_state_recorded_separately(self):
        w = self.world("staged")
        W = w.linked_worktree("agent-st", "wt-st")
        w.write(W, "a.txt", "staged version\n")
        sh("git", "add", "a.txt", cwd=W)
        w.write(W, "a.txt", "worktree version\n")
        w.full()
        t = w.T()
        snap = f"{t.NS}/{w.cid(W)}/dirty"
        self.assertEqual(sh("git", "show", f"{snap}:a.txt", cwd=w.K), "worktree version")
        self.assertEqual(sh("git", "show", f"{snap}^2:a.txt", cwd=w.K), "staged version")
        self.assertPass(w.gate(w.cid(W)))

    def test_cleanup_moves_to_trash_and_is_reversible(self):
        w = self.world("cleanup")
        W = dirty_linked(w)
        C = w.clone("C2")
        w.scope["extra_copies"] = [{"path": C, "owner": "fx"}]
        w.full()
        w.run("cleanup")
        t = w.T()
        self.assertFalse(os.path.exists(W))
        self.assertFalse(os.path.exists(C))
        listed = sh("git", "worktree", "list", "--porcelain", cwd=w.K)
        self.assertNotIn(W, listed)
        trashed = sorted(os.listdir(w.trash))
        self.assertIn(f"{w.cid(W)}-retired-{t.TS}", trashed)
        self.assertIn(f"{w.cid(W)}-admin-retired-{t.TS}", trashed)
        # tier-2 rollback: move both back, git sees the worktree again, bytes intact
        os.rename(os.path.join(w.trash, f"{w.cid(W)}-retired-{t.TS}"), W)
        os.rename(os.path.join(w.trash, f"{w.cid(W)}-admin-retired-{t.TS}"), os.path.join(w.K, ".git", "worktrees", "agent-1"))
        self.assertIn(W, sh("git", "worktree", "list", "--porcelain", cwd=w.K))
        with open(os.path.join(W, "a.txt")) as f:
            self.assertEqual(f.read(), "alpha changed\n")
        w.run("verify")
        m = t.jload("verify/m_term.json")
        self.assertIn("holds", m)

    def test_cleanup_refuses_without_drill(self):
        w = self.world("nodrill")
        W = dirty_linked(w)
        w.run("freeze")
        w.run("inventory")
        w.run("preserve", "--push")
        w.run("cleanup")
        self.assertTrue(os.path.exists(W))


class TestV26923Fixes(Base):
    def test_is_secret_no_token_substring(self):
        t = World("fixes").T()
        self.assertFalse(t.is_secret("/nonexistent/packaging/_tokenizer.py", "packaging/_tokenizer.py"))
        self.assertFalse(t.is_secret("/nonexistent/pygments/token.py", "pygments/token.py"))
        self.assertTrue(t.is_secret("/nonexistent/.env", ".env"))
        self.assertFalse(t.is_secret("/nonexistent/.env.example", ".env.example"))
        self.assertTrue(t.is_secret("/nonexistent/keys/signing.key", ".ggen/keys/signing.key"))
        self.assertFalse(t.is_secret("/nonexistent/keys/verifying.key", ".ggen/keys/verifying.key"))

    def test_porcelain_z_odd_paths(self):
        t = World("porc").T()
        raw = b'1 .M N... 100644 100644 100644 aaa bbb dir/a b.txt\x00? new\nline "q".txt\x00'
        e = t.parse_status_z(raw)
        self.assertEqual([x["path"] for x in e], ["dir/a b.txt", 'new\nline "q".txt'])

    def test_gitlink_precedence(self):
        w = World("gitlink")
        t = w.T()
        os.makedirs(os.path.join(w.K, "plain"))
        w.write(w.K, "plain/.git", "gitdir: /nowhere\n")
        self.assertFalse(t.is_gitlink_path(w.K, "plain"))


class TestFinishSignoffs(Base):
    """finish lane: operator signoffs as ledgered transitions; the gate still decides every retirement."""

    def test_secret_trash_records_sha256_only_and_secret_survives_in_trash(self):
        w = self.world("secrettrash")
        W = w.linked_worktree("agent-sec", "wt-sec")
        secret = "API=sk-ant-" + "z" * 40 + "\n"
        w.write(W, ".env", secret)
        w.full()
        self.assertRefuses(w.gate(w.cid(W)), "R16")  # anti-vacuity: without the signoff the secret blocks retirement
        w.scope["signoffs"] = [{"action": "secret_trash", "path": W, "grant": "test grant"}]
        w.run("signoff")
        res = w.gate(w.cid(W))
        self.assertPass(res)
        ev = res["evidence"]["R16_SECRET_UNPRESERVABLE"]
        self.assertNotIn("sk-ant-", json.dumps(ev))
        self.assertEqual([set(x) for x in ev["secrets"]], [{"path_sha256", "content_sha256"}])
        w.run("cleanup")
        t = w.T()
        self.assertFalse(os.path.exists(W))
        with open(os.path.join(w.trash, f"{w.cid(W)}-retired-{t.TS}", ".env")) as f:
            self.assertEqual(f.read(), secret)  # nothing lost: the secret is in the Trash, reversible
        steps = [json.loads(x) for x in open(os.path.join(w.home, "steps.jsonl"))]
        ret = [s for s in steps if s["step"] == f"retire {w.cid(W)}"][0]
        self.assertTrue(ret["ok"])
        self.assertNotIn("sk-ant-", json.dumps(ret))
        self.assertEqual(len(ret["secret_trash"]["secrets"]), 1)

    def test_m_term_unowned_identity_is_sole_copy(self):
        w = self.world("unowned")
        t = w.T()
        a, b = os.path.join(w.root, "subA"), os.path.join(w.root, "subB")
        os.makedirs(a)
        os.makedirs(b)

        def cp(path, origin):
            return {"copy_id": t.slug(path), "path": path, "kind": "SUBMODULE_ACTIVE", "writer_queue": None, "identity": {"origin_norm": origin}}

        inv = {"copies": {"a": cp(a, "github.com/x/one"), "b": cp(b, "github.com/y/two")}}
        self.assertTrue(t.m_term({}, inv)["holds"])  # two different third-party identities, one checkout each
        inv = {"copies": {"a": cp(a, "github.com/x/one"), "b": cp(b, "github.com/x/one")}}
        m = t.m_term({}, inv)
        self.assertFalse(m["holds"])  # a second copy of the same identity is a violation
        self.assertEqual(len(m["violations"]), 2)
        inv = {"copies": {"a": cp(a, None)}}
        self.assertFalse(t.m_term({}, inv)["holds"])  # no identity at all is never admitted

    def test_deinit_retire_of_active_submodule_leaves_parent_clean(self):
        w = self.world("deinit")
        P = os.path.join(w.root, "P")
        os.makedirs(P)
        sh("git", "init", "-q", "-b", "main", cwd=P)
        w.write(P, "p.txt", "parent\n")
        sh("git", "add", "-A", cwd=P)
        sh("git", "commit", "-q", "-m", "p", cwd=P)
        sh("git", "-c", "protocol.file.allow=always", "submodule", "add", "-q", w.origin, "sub", cwd=P)
        sh("git", "commit", "-q", "-m", "add sub", cwd=P)
        S = os.path.join(P, "sub")
        os.remove(os.path.join(S, "a.txt"))  # active: one tracked file deleted
        w.full()
        w.scope["signoffs"] = [{"action": "add", "path": S, "parent": P, "owner": "fx", "retire_mode": "deinit", "grant": "test"}]
        w.run("signoff")
        t = w.T()
        self.assertEqual(t.jload("INVENTORY.json")["copies"][w.cid(S)]["kind"], "SUBMODULE_ACTIVE")
        w.run("preserve", "--only", S, "--push")
        w.run("drill", "--only", S)
        w.run("cleanup", "--only", S)
        self.assertTrue(os.path.isdir(S))
        self.assertEqual(os.listdir(S), [])
        self.assertEqual(sh("git", "status", "--porcelain", "--", "sub", cwd=P), "")
        w.run("verify")
        self.assertTrue(t.jload("verify/m_term.json")["holds"])
        # rollback: the checkout comes back byte-exact from the Trash
        os.rmdir(S)
        os.rename(os.path.join(w.trash, f"{w.cid(S)}-retired-{t.TS}"), S)
        self.assertIn("D a.txt", sh("git", "status", "--porcelain", cwd=S))


if __name__ == "__main__":
    unittest.main(verbosity=2)
