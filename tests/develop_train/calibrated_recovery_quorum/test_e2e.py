from datetime import datetime, timezone
from fractions import Fraction
import unittest

from scripts.develop_train.calibrated_recovery_quorum.calibration_model import CalibrationModel
from scripts.develop_train.calibrated_recovery_quorum.dependency import DependencyGraph
from scripts.develop_train.calibrated_recovery_quorum.engine import qualify
from scripts.develop_train.calibrated_recovery_quorum.evidence_source import EvidenceSource
from scripts.develop_train.calibrated_recovery_quorum.independence import IndependenceProof
from scripts.develop_train.calibrated_recovery_quorum.persistence import PersistenceNeed
from scripts.develop_train.calibrated_recovery_quorum.receipt import replay
from scripts.develop_train.calibrated_recovery_quorum.subject import Subject
from scripts.develop_train.calibrated_recovery_quorum.witness import RecoveryWitness


class TestE2E(unittest.TestCase):
    def test_calibrated_independent_quorum_reaches_only_partial_alive(self):
        now = datetime.now(timezone.utc)
        left = EvidenceSource("p1", "r1", "a1", "f1")
        right = EvidenceSource("p2", "r2", "a2", "f2")
        left_witness = RecoveryWitness("att", left.fingerprint, "PASS", now, "repo")
        right_witness = RecoveryWitness("att", right.fingerprint, "PASS", now, "repo")

        def model(source_id: str) -> CalibrationModel:
            return CalibrationModel(
                source_id,
                12,
                Fraction(9, 10),
                Fraction(1, 10),
                Fraction(0),
                Fraction(1, 2),
            )

        proof = IndependenceProof(left.fingerprint, right.fingerprint, "f" * 64)
        qualification = qualify(
            subject=Subject("a/b", "a" * 40),
            attempt_id="att",
            sources=(left, right),
            witnesses=(left_witness, right_witness),
            calibrations={
                left.fingerprint: model(left.fingerprint),
                right.fingerprint: model(right.fingerprint),
            },
            proofs=(proof,),
            now=now,
            min_trials=4,
            required_clusters=2,
            dependency_graph=DependencyGraph(()),
            dependency_standings={},
            dependency_root="root",
            persistence=PersistenceNeed(transactional=True),
        )
        self.assertEqual(qualification.standing, "PARTIAL_ALIVE")
        self.assertEqual(qualification.receipt.store, "SQLITE")
        self.assertFalse(qualification.receipt.actuation_performed)
        self.assertTrue(replay(qualification.receipt, qualification.receipt.digest()))
