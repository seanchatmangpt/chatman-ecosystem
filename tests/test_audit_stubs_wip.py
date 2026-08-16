from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_stubs_wip", ROOT / "scripts" / "audit_stubs_wip.py"
)
audit_stubs_wip = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = audit_stubs_wip
SPEC.loader.exec_module(audit_stubs_wip)


def make_git_repo(files: dict[str, str]) -> Path:
    """Build a real, tracked git repo on disk containing the given files.

    Chicago-style: audit_stubs_wip.scan() shells out to `git ls-files`, so the
    test exercises a real git repository and real files rather than mocking
    subprocess or the filesystem.
    """
    tmpdir = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=tmpdir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmpdir, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, check=True)
    for rel_path, content in files.items():
        path = tmpdir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmpdir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmpdir, check=True)
    return tmpdir


class AuditStubsWipTests(unittest.TestCase):
    def scan_repo(self, files: dict[str, str]):
        repo = make_git_repo(files)
        original_root = audit_stubs_wip.ROOT
        audit_stubs_wip.ROOT = repo
        try:
            return audit_stubs_wip.scan()
        finally:
            audit_stubs_wip.ROOT = original_root

    def test_finds_todo_marker_in_source_file(self) -> None:
        markers, mock_hits = self.scan_repo({"src/lib.rs": "fn f() {\n    // TODO: fix this\n}\n"})
        self.assertEqual(1, len(markers))
        rel_path, lineno, content = markers[0]
        self.assertEqual("src/lib.rs", rel_path)
        self.assertEqual(2, lineno)
        self.assertIn("TODO", content)
        self.assertEqual([], mock_hits)

    def test_finds_rust_stub_macros(self) -> None:
        markers, _ = self.scan_repo(
            {"src/lib.rs": "fn a() { unimplemented!() }\nfn b() { todo!() }\nfn c() { stub!() }\n"}
        )
        self.assertEqual(3, len(markers))

    def test_ignores_non_source_suffixes(self) -> None:
        markers, _ = self.scan_repo({"notes.txt": "TODO: not scanned, wrong suffix\n"})
        self.assertEqual([], markers)

    def test_excludes_self_and_audits_dir(self) -> None:
        markers, _ = self.scan_repo(
            {
                "scripts/audit_stubs_wip.py": "# TODO marker inside the scanner itself\n",
                "docs/audits/2026-08-01-stubs-wip.md": "TODO appears in a prior audit report\n",
                "src/real.py": "# TODO real finding\n",
            }
        )
        self.assertEqual(1, len(markers))
        self.assertEqual("src/real.py", markers[0][0])

    def test_finds_mock_pattern_only_under_tests_dir(self) -> None:
        markers, mock_hits = self.scan_repo(
            {
                "tests/test_foo.py": "from unittest.mock import MagicMock\nm = MagicMock()\n",
                "src/foo.py": "from unittest.mock import MagicMock\n",
            }
        )
        self.assertEqual([], markers)
        self.assertEqual(2, len(mock_hits))
        self.assertTrue(all(rel_path == "tests/test_foo.py" for rel_path, _, _ in mock_hits))

    def test_clean_tree_produces_no_findings(self) -> None:
        markers, mock_hits = self.scan_repo({"src/clean.py": "def f():\n    return 1\n"})
        self.assertEqual([], markers)
        self.assertEqual([], mock_hits)

    def test_render_reports_alive_status_when_clean(self) -> None:
        content = audit_stubs_wip.render([], [])
        self.assertIn("Status: `ALIVE`", content)
        self.assertIn("WIP-STUB-MARKERS — none found", content)
        self.assertIn("WIP-MOCK-DOUBLES — none found", content)

    def test_render_reports_partial_alive_and_lists_findings(self) -> None:
        markers = [("src/lib.rs", 2, "// TODO: fix this")]
        mock_hits = [("tests/test_foo.py", 1, "MagicMock()")]
        content = audit_stubs_wip.render(markers, mock_hits)
        self.assertIn("Status: `PARTIAL_ALIVE`", content)
        self.assertIn("src/lib.rs:2", content)
        self.assertIn("tests/test_foo.py:1", content)
        self.assertIn("WIP-STUB-MARKERS — 1 marker(s) found", content)
        self.assertIn("WIP-MOCK-DOUBLES — 1 banned mock pattern(s) found", content)


if __name__ == "__main__":
    unittest.main()
