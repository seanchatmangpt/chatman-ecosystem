"""Pure-Python git identities recompute the real v26.9.25 tag, commit and trees from bytes.

Real collaborators only: the committed raw objects under release/v26.9.25/hardening and
the checked-out payload. The synthetic tree's expected id was computed once by real git
(``git add -A && git write-tree`` over the same files) and is pinned here.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from _support import REPO, RELEASE

from scripts.release_train.root_crown import gitobj

HARDENING = REPO / "release" / RELEASE / "hardening"
OBJECTS = HARDENING / "inputs" / "objects"
TAG = "337e839937c247de4ee58b744c8b8e43950d18e3"
COMMIT = "68bacd8dcc9ae12e4e97727a284c14abdc7520c5"
ROOT_TREE = "8553eb9ea7ab45227169eec1f57204f2ff12ad53"
PAYLOAD_TREE = "a01b914de2e4b3503dc2126ce233654af764c362"


@unittest.skipUnless(OBJECTS.is_dir(), "hardening raw objects not committed")
class TagObjectsTest(unittest.TestCase):
    def test_tag_object_recomputes_337e8399_and_targets_68bacd8d(self):
        body = (OBJECTS / f"{TAG}.tag.raw").read_bytes()
        self.assertEqual(gitobj.object_sha("tag", body), TAG)
        tag = gitobj.parse_tag(body)
        self.assertEqual((tag["object"], tag["type"], tag["tag"]), (COMMIT, "commit", RELEASE))
        self.assertIn("crown receipt sha256:2323f877", tag["message"])

    def test_commit_object_recomputes_68bacd8d(self):
        body = (OBJECTS / f"{COMMIT}.commit.raw").read_bytes()
        self.assertEqual(gitobj.object_sha("commit", body), COMMIT)
        commit = gitobj.parse_commit(body)
        self.assertEqual(commit["tree"], ROOT_TREE)
        self.assertEqual(len(commit["parents"]), 2)

    def test_every_committed_raw_object_recomputes(self):
        objects = gitobj.RawObjects(OBJECTS)
        self.assertEqual(objects.mismatches, [])
        self.assertIn(TAG, objects.bodies)
        for sha, (kind, body) in objects.bodies.items():
            with self.subTest(sha=sha):
                self.assertEqual(gitobj.object_sha(kind, body), sha)

    def test_tree_chain_reaches_the_payload_tree(self):
        chain = gitobj.tree_chain(gitobj.RawObjects(OBJECTS), COMMIT, f"release/{RELEASE}")
        self.assertEqual(chain[0], ("", ROOT_TREE))
        self.assertEqual(chain[-1], (f"release/{RELEASE}", PAYLOAD_TREE))

    def test_tree_bodies_reencode_byte_identically(self):
        for sha, (kind, body) in gitobj.RawObjects(OBJECTS).bodies.items():
            if kind == "tree":
                with self.subTest(sha=sha):
                    self.assertEqual(gitobj.tree_body(gitobj.parse_tree(body)), body)

    def test_checked_out_payload_minus_post_tag_dirs_is_the_tagged_tree(self):
        payload = REPO / "release" / RELEASE
        self.assertEqual(gitobj.tree_sha_of_dir(payload, exclude=("hardening", "autonomy")), PAYLOAD_TREE)
        self.assertNotEqual(gitobj.tree_sha_of_dir(payload), PAYLOAD_TREE, "hardening/ is a post-tag addition")

    def test_flipped_raw_byte_is_a_recorded_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / f"{TAG}.tag.raw"
            body = bytearray((OBJECTS / f"{TAG}.tag.raw").read_bytes())
            body[-2] ^= 0x01
            target.write_bytes(bytes(body))
            objects = gitobj.RawObjects(Path(tmp))
        self.assertEqual(len(objects.mismatches), 1)
        self.assertNotIn(TAG, objects.bodies)
        with self.assertRaises(gitobj.GitObjectError):
            objects.get(TAG, "tag")


class SyntheticTreeTest(unittest.TestCase):
    """Exec bit, symlink, empty dir and git's dir-sort rule ("d-" < "d/")."""

    EXPECTED = "36c862673728a4675758e9c32f4059a846506aaa"  # real `git write-tree`

    def build(self, root: Path) -> None:
        (root / "d").mkdir()
        (root / "empty").mkdir()
        (root / "a").write_bytes(b"x\n")
        os.chmod(root / "a", 0o755)
        os.symlink("a", root / "l")
        (root / "d" / "f").write_bytes(b"plain\n")
        (root / "d-").write_bytes(b"b\n")

    def test_matches_real_git_write_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.build(Path(tmp))
            self.assertEqual(gitobj.tree_sha_of_dir(Path(tmp)), self.EXPECTED)

    def test_mode_and_link_changes_change_the_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build(root)
            os.chmod(root / "a", 0o644)
            self.assertNotEqual(gitobj.tree_sha_of_dir(root), self.EXPECTED)
            os.chmod(root / "a", 0o755)
            os.remove(root / "l")
            shutil.copyfile(root / "a", root / "l")
            self.assertNotEqual(gitobj.tree_sha_of_dir(root), self.EXPECTED)

    def test_blob_sha_matches_git_hash_object(self):
        self.assertEqual(gitobj.blob_sha(b"x\n"), "587be6b4c3f93f93c489c0111bba5596147a26cb")

    def test_unknown_object_type_is_refused(self):
        with self.assertRaises(gitobj.GitObjectError):
            gitobj.object_sha("note", b"")


if __name__ == "__main__":
    unittest.main()
