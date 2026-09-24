"""CE23-7 court probe: audit_run.py records what a tool reads and court.audit() judges it.

Chicago style: every case runs a real script under the real audit_run.py probe as a
subprocess, on real files in a temporary tree, and judges the real audit log with the
court's own audit() (release/v26.9.23/courts/ce23_7/court.py). No collaborator is
replaced; the one local HTTP port used is a closed 127.0.0.1 port (the request is
refused by the kernel, which is all the URL case needs).
"""

from __future__ import annotations

import importlib.util
import socket
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURT_DIR = ROOT / "release" / "v26.9.23" / "courts" / "ce23_7"
AUDIT_RUN = COURT_DIR / "audit_run.py"
SPEC = importlib.util.spec_from_file_location("ce23_7_court", COURT_DIR / "court.py")
assert SPEC is not None and SPEC.loader is not None
court = importlib.util.module_from_spec(SPEC)
sys.modules["ce23_7_court"] = court
SPEC.loader.exec_module(court)

PRED = court.PRED  # the predecessor line, read from fence.toml
TARGET = court.TARGET


def closed_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ProbeCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def probe(self, body: str) -> tuple[list[str], list[str], subprocess.CompletedProcess[str]]:
        """Run ``body`` as a tool under audit_run.py in self.root; return (reads, blind, proc)."""
        script = self.root / "tool.py"
        script.write_text(textwrap.dedent(body), encoding="utf-8")
        log = self.root / "audit.log"
        proc = subprocess.run([sys.executable, str(AUDIT_RUN), str(log), str(script)], cwd=self.root,
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertTrue(court.probe_fired(log, script), "the probe must log the tool's own source")
        reads, blind = court.audit(log)
        return reads, blind, proc

    def line_file(self, line: str, rel: str = "manifest.toml", data: bytes = b"x = 1\n") -> Path:
        path = self.root / "release" / line / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path


class ProbeReadTests(ProbeCase):
    def test_a_clean_target_read_is_neither_read_nor_blind(self) -> None:
        self.line_file(TARGET)
        reads, blind, _ = self.probe(f'open("release/{TARGET}/manifest.toml").read()\n')
        self.assertEqual(([], []), (reads, blind))

    def test_an_open_under_the_predecessor_line_is_a_read_wherever_it_lives(self) -> None:
        legacy = self.line_file(PRED)
        reads, _, _ = self.probe(f"open({str(legacy)!r}).read()\n")
        self.assertEqual([f"opened {legacy}"], reads)

    def test_any_component_naming_the_predecessor_is_a_read(self) -> None:
        doc = self.root / "docs" / PRED / "notes.md"
        doc.parent.mkdir(parents=True)
        doc.write_text("n\n", encoding="utf-8")
        reads, _, _ = self.probe(f"open({str(doc)!r}).read()\n")
        self.assertEqual([f"opened {doc}"], reads)

    def test_a_directory_listing_of_the_predecessor_is_a_read(self) -> None:
        self.line_file(PRED)
        reads, _, _ = self.probe(f'import os\nos.listdir("release/{PRED}")\n')
        self.assertIn(f"read the directory {self.root / 'release' / PRED}", reads)

    def test_a_byte_copy_of_a_predecessor_file_is_a_read_outside_the_target_line(self) -> None:
        data = (ROOT / "release" / PRED / "manifest.toml").read_bytes()
        copy = self.root / "vendor" / "legacy.toml"
        copy.parent.mkdir()
        copy.write_bytes(data)
        self.line_file(TARGET, data=data)
        reads, _, _ = self.probe(f'open("vendor/legacy.toml", "rb").read()\nopen("release/{TARGET}/manifest.toml", "rb").read()\n')
        self.assertEqual([f"opened {copy}, a byte copy of a release/{PRED} file"], reads)

    def test_a_child_process_naming_the_predecessor_is_a_read(self) -> None:
        legacy = self.line_file(PRED)
        reads, _, _ = self.probe(f'import subprocess\nsubprocess.run(["cat", {str(legacy)!r}], capture_output=True)\n')
        self.assertEqual(1, len(reads), reads)
        self.assertTrue(reads[0].startswith(f"spawned a child process naming {PRED}: "), reads)

    def test_a_url_naming_the_predecessor_is_a_read(self) -> None:
        url = f"http://127.0.0.1:{closed_port()}/release/{PRED}/manifest.toml"
        reads, blind, _ = self.probe(textwrap.dedent(f"""\
            import urllib.request
            try:
                urllib.request.urlopen({url!r}, timeout=2)
            except OSError:
                pass
            """))
        self.assertEqual(([f"requested {url}"], []), (reads, blind))


class ProbeBlindTests(ProbeCase):
    def test_an_unrelated_child_process_is_blind(self) -> None:
        reads, blind, _ = self.probe('import subprocess\nsubprocess.run(["true"])\n')
        self.assertEqual([], reads)
        self.assertEqual(1, len(blind), blind)
        self.assertTrue(blind[0].startswith("spawned a child process the audit hook cannot see into: "), blind)

    def test_native_code_is_blind(self) -> None:
        reads, blind, _ = self.probe("import ctypes\nctypes.CDLL(None)\n")
        self.assertEqual([], reads)
        self.assertTrue(blind and blind[0].startswith("ran native code (ctypes) the audit hook cannot see into: "), blind)

    def test_a_git_object_store_open_is_blind(self) -> None:
        head = self.root / "repo" / ".git" / "HEAD"
        head.parent.mkdir(parents=True)
        head.write_text("ref: refs/heads/main\n", encoding="utf-8")
        reads, blind, _ = self.probe(f"open({str(head)!r}).read()\n")
        self.assertEqual(([], [f"opened {head} in a git object store; a {PRED} blob read cannot be excluded"]), (reads, blind))

    def test_an_off_host_socket_is_blind(self) -> None:
        reads, blind, _ = self.probe(textwrap.dedent("""\
            import socket
            with socket.socket(socket.AF_UNIX) as sock:
                sock.connect_ex("/nonexistent-ce23-7.sock")
            """))
        self.assertEqual([], reads)
        self.assertTrue(blind and blind[0].startswith("connected off-host the audit hook cannot see into: "), blind)

    def test_judge_reads_refuses_a_read_before_it_reports_a_blind_spot(self) -> None:
        legacy = self.line_file(PRED)
        script = self.root / "tool.py"
        script.write_text(f'import subprocess\nsubprocess.run(["true"])\nopen({str(legacy)!r}).read()\n', encoding="utf-8")
        log = self.root / "audit.log"
        subprocess.run([sys.executable, str(AUDIT_RUN), str(log), str(script)], cwd=self.root, check=True, timeout=120)
        refused, unknown = len(court.V.refused), len(court.V.unknown)
        self.assertFalse(court.judge_reads("tool", "T", log, script))
        new_refused, new_unknown = court.V.refused[refused:], court.V.unknown[unknown:]
        self.assertEqual(1, len(new_refused), new_refused)
        self.assertTrue(new_refused[0].startswith("REFUSED[SILENT_V26_9_1_READ] T: tool targeting"), new_refused)
        self.assertEqual([], new_unknown)


if __name__ == "__main__":
    unittest.main()
