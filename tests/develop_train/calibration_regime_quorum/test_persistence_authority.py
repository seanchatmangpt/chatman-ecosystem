import unittest
from scripts.develop_train.calibration_regime_quorum.authority_receipt import ActionClass,require_action
from scripts.develop_train.calibration_regime_quorum.persistence import PersistenceNeed,select_store
from scripts.develop_train.calibration_regime_quorum.subject import Refusal
class PersistenceAuthorityCourt(unittest.TestCase):
    def test_reversible_store_candidates_narrow_by_need(self):
        self.assertEqual(select_store(PersistenceNeed()).selected,"MEMORY"); self.assertEqual(select_store(PersistenceNeed(durable=True)).selected,"JSONL"); choice=select_store(PersistenceNeed(transactional=True)); self.assertEqual(choice.selected,"SQLITE"); self.assertEqual(choice.candidates,("MEMORY","JSONL","SQLITE"))
    def test_do_is_mechanically_refused(self):
        require_action(ActionClass.CONSTRUCT)
        with self.assertRaisesRegex(Refusal,"BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO"): require_action(ActionClass.DO)
if __name__=="__main__": unittest.main()
