#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = PACK_ROOT / "scripts" / "run_receipted_mix.py"


class ReceiptedMixTests(unittest.TestCase):
    def invoke(self, root: Path, child: list[str]) -> subprocess.CompletedProcess[str]:
        pending = root / ".agp-pending" / "target.txt"
        receipt = root / ".agp-receipts" / "target.txt"
        log = root / ".agp-receipts" / "target.mix.log"
        pending.parent.mkdir(parents=True, exist_ok=True)
        pending.write_text("deterministic pending intent\n", encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--pending",
                str(pending),
                "--receipt",
                str(receipt),
                "--log",
                str(log),
                "--",
                *child,
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_success_promotes_pending_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.invoke(root, [sys.executable, "-c", "print('generated')"])
            receipt = root / ".agp-receipts" / "target.txt"
            self.assertEqual(result.returncode, 0)
            self.assertIn("ALIVE[RECEIPT_PROMOTED]", result.stdout)
            self.assertEqual(receipt.read_text(), "deterministic pending intent\n")
            self.assertFalse((root / ".agp-pending" / "target.txt").exists())
            self.assertIn("generated", (root / ".agp-receipts" / "target.mix.log").read_text())

    def test_nonzero_child_cannot_manufacture_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.invoke(
                root,
                [sys.executable, "-c", "print('looks successful'); raise SystemExit(23)"],
            )
            self.assertEqual(result.returncode, 23)
            self.assertIn("REFUSED[MIX_NONZERO_EXIT]", result.stderr)
            self.assertFalse((root / ".agp-receipts" / "target.txt").exists())
            self.assertFalse((root / ".agp-pending" / "target.txt").exists())
            self.assertIn("looks successful", (root / ".agp-receipts" / "target.mix.log").read_text())

    def test_missing_executable_is_refused_without_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.invoke(root, ["definitely-not-a-real-mix-command-EXP-GEN-001"])
            self.assertEqual(result.returncode, 66)
            self.assertIn("REFUSED[MIX_EXEC_FAILED]", result.stderr)
            self.assertFalse((root / ".agp-receipts" / "target.txt").exists())

    def test_existing_receipt_is_replay_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = root / ".agp-receipts" / "target.txt"
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text("existing receipt\n", encoding="utf-8")
            sentinel = root / "child-ran"
            result = self.invoke(
                root,
                [sys.executable, "-c", f"from pathlib import Path; Path({str(sentinel)!r}).write_text('bad')"],
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("REPLAY[RECEIPT_EXISTS]", result.stdout)
            self.assertEqual(receipt.read_text(), "existing receipt\n")
            self.assertFalse(sentinel.exists())
            self.assertFalse((root / ".agp-pending" / "target.txt").exists())

    def test_success_replay_preserves_receipt_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.invoke(root, [sys.executable, "-c", "print('first')"])
            receipt = root / ".agp-receipts" / "target.txt"
            before = receipt.read_bytes()
            second = self.invoke(root, [sys.executable, "-c", "raise SystemExit(99)"])
            self.assertEqual(first.returncode, 0)
            self.assertEqual(second.returncode, 0)
            self.assertEqual(receipt.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
