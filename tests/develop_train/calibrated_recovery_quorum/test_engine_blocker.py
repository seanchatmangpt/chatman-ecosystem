from datetime import datetime, timezone
from fractions import Fraction
import unittest

from scripts.develop_train.calibrated_recovery_quorum.calibration_model import CalibrationModel
from scripts.develop_train.calibrated_recovery_quorum.dependency import DependencyGraph
from scripts.develop_train.calibrated_recovery_quorum.engine import qualify
from scripts.develop_train.calibrated_recovery_quorum.evidence_source import EvidenceSource
from scripts.develop_train.calibrated_recovery_quorum.persistence import PersistenceNeed
from scripts.develop_train.calibrated_recovery_quorum.subject import Subject
from scripts.develop_train.calibrated_recovery_quorum.witness import RecoveryWitness


class TestEngineBlocker(unittest.TestCase):
    def test_dependency_red_dominates(self):
        now = datetime.now(timezone.utc)
        source = EvidenceSource("p", "r", "a", "f")
        witness = RecoveryWitness("att", source.fingerprint, "PASS", now, "repo")
        model = CalibrationModel(
            source.fingerprint,
            10,
            Fraction(9, 10),
            Fraction(1, 10),
            Fraction(0),
            Fraction(1, 2),
        )
        qualification = qualify(
            subject=Subject("a/b", "a" * 40),
            attempt_id="att",
            sources=(source,),
            witnesses=(witness,),
            calibrations={source.fingerprint: model},
            proofs=(),
            now=now,
            min_trials=4,
            required_clusters=1,
            dependency_graph=DependencyGraph((("root", "dep"),)),
            dependency_standings={"dep": "BUILD_BROKEN"},
            dependency_root="root",
            persistence=PersistenceNeed(),
        )
        self.assertEqual(qualification.standing, "BLOCKED")
        self.assertEqual(qualification.receipt.blockers, ("dep",))
