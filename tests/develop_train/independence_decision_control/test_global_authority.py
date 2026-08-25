import unittest

from scripts.develop_train.independence_decision_control.authority import ActionClass, admit
from scripts.develop_train.independence_decision_control.engine import EngineWitness, require_correspondence
from scripts.develop_train.independence_decision_control.errors import Refused
from scripts.develop_train.independence_decision_control.oracle import OracleWitness, require_oracles


class TestGlobalAuthority(unittest.TestCase):
    def test_engine_oracle_correspondence_and_do_refusal(self):
        engines = [
            EngineWitness("BEAM", "a", "s", "t", "o"),
            EngineWitness("WASM", "b", "s", "t", "o"),
        ]
        self.assertTrue(require_correspondence(engines))
        oracles = [
            OracleWitness("POWL", "a", "m1", "d"),
            OracleWitness("POWL", "b", "m2", "d"),
        ]
        self.assertTrue(require_oracles(oracles, "POWL"))
        with self.assertRaises(Refused):
            admit(ActionClass.DO)


if __name__ == "__main__":
    unittest.main()
