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


class TestEngineUnderCalibrated(unittest.TestCase):
    def test_under_calibrated_positive_stays_unknown(self):
        now = datetime.now(timezone.utc)
        source = EvidenceSource("p", "r", "a", "f")
        witness = RecoveryWitness("att", source.fingerprint, "PASS", now, "repo")
        model = CalibrationModel(
            source.fingerprint,
            2,
            Fraction(9, 10),
            Fraction(1, 10),
            Fraction(0),
            Fraction(0),
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
            dependency_graph=DependencyGraph(()),
            dependency_standings={},
            dependency_root="root",
            persistence=PersistenceNeed(),
        )
        self.assertEqual(qualification.standing, "UNKNOWN")
