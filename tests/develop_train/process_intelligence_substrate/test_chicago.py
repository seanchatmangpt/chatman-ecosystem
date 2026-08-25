import unittest
from scripts.develop_train.process_intelligence_substrate import ActionClass, Engine, Methodology, MethodologySet, Projection, Subject, qualify, replay

class ChicagoTest(unittest.TestCase):
    def test_full_methodology_projection_receipt_path(self):
        subject = Subject.parse("seanchatmangpt/chatman-ecosystem@" + "d" * 40)
        methods = MethodologySet(frozenset(Methodology))
        digest = "e" * 64
        obligations = frozenset({"events","objects","powl","reactor","receipt"})
        projections = (
            Projection(Engine.BEAM, digest, obligations),
            Projection(Engine.WASM, digest, obligations),
        )
        q = qualify(subject, methods, projections, ("SEMANTIC","POWL","REACTOR","PROJECTION","REPLAY","BRCE"), ActionClass.VERIFY)
        self.assertEqual(q.standing, "PARTIAL_ALIVE")
        self.assertEqual(q.missing, ())
        self.assertIsNotNone(q.receipt)
        self.assertTrue(replay(q.receipt, q.receipt.digest()))
        self.assertFalse(q.receipt.actuation_performed)

if __name__ == "__main__": unittest.main()
