from __future__ import annotations

import copy
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_portfolio import (  # noqa: E402
    PortfolioRefusal,
    build_report,
    input_digests,
    manufacture_receipt,
    replay_receipt,
)


def load(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


class PortfolioReceiptFreshnessTests(unittest.TestCase):
    def setUp(self) -> None:
        base = ROOT / "release" / "v26.9.1"
        self.policy = load(base / "fleet-policy.toml")
        self.manifest = load(base / "manifest.toml")
        self.ledger = load(base / "candidates.toml")

    def test_receipt_binds_all_three_measurement_inputs(self) -> None:
        receipt = manufacture_receipt(build_report(self.policy, self.manifest, self.ledger))
        self.assertEqual(receipt["input_digests"], input_digests(self.policy, self.manifest, self.ledger))
        self.assertEqual(replay_receipt(receipt, input_digests(self.policy, self.manifest, self.ledger)), receipt)

    def test_valid_old_receipt_is_refused_after_ledger_drift(self) -> None:
        receipt = manufacture_receipt(build_report(self.policy, self.manifest, self.ledger))
        changed = copy.deepcopy(self.ledger)
        changed["candidates"][0]["scope_standing"] = "UNKNOWN"
        with self.assertRaisesRegex(PortfolioRefusal, "PORTFOLIO_RECEIPT_STALE"):
            replay_receipt(receipt, input_digests(self.policy, self.manifest, changed))

    def test_valid_old_receipt_is_refused_after_manifest_drift(self) -> None:
        receipt = manufacture_receipt(build_report(self.policy, self.manifest, self.ledger))
        changed = copy.deepcopy(self.manifest)
        changed["release"]["version"] = "stale-falsifier"
        with self.assertRaisesRegex(PortfolioRefusal, "PORTFOLIO_RECEIPT_STALE"):
            replay_receipt(receipt, input_digests(self.policy, changed, self.ledger))

    def test_missing_input_measurement_is_refused_even_with_recomputed_outer_digest(self) -> None:
        report = build_report(self.policy, self.manifest, self.ledger)
        report.pop("input_digests")
        receipt = manufacture_receipt(report)
        with self.assertRaisesRegex(PortfolioRefusal, "PORTFOLIO_INPUT_DIGESTS_INVALID"):
            replay_receipt(receipt)


if __name__ == "__main__":
    unittest.main()
