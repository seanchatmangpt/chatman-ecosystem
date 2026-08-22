import unittest
from scripts.release_train.ack_discharge_promotion.subject import Subject
from scripts.release_train.ack_discharge_promotion.strategy import Strategy
A=Subject.parse("o/a@"+"a"*40); B=Subject.parse("o/b@"+"b"*40); C=Subject.parse("o/c@"+"c"*40)
class T(unittest.TestCase):
    def test_all(self): self.assertFalse(Strategy("ALL").complete({B},(B,C)))
    def test_quorum(self): self.assertTrue(Strategy("QUORUM",1).complete({B},(B,C)))
    def test_critical(self): self.assertTrue(Strategy("CRITICAL_PATH",critical=(B,)).complete({B},(B,C)))
