import unittest
from fractions import Fraction
from scripts.develop_train.validation_independence_control import ActionClass, Candidate, CompositionMode, Dependence, Evidence, EvidenceGraph, FailureWorld, Interval, Provenance, Refused, Strategy, Subject, ValidatorWitness, evaluate, replay, REQUIRED_METHODOLOGIES, admit

class ChicagoCourt(unittest.TestCase):
    def fixtures(self):
        subject=Subject.parse("seanchatmangpt/chatman-ecosystem@"+"a"*40+"#"+"b"*64)
        graph=EvidenceGraph((Evidence("oracle-a",9,(),1),Evidence("oracle-b",9,(),1)))
        va=ValidatorWitness("va","c"*64,Provenance("ia","ma","da"),"oracle-a")
        vb=ValidatorWitness("vb","d"*64,Provenance("ib","mb","db"),"oracle-b")
        dep=Dependence(Fraction(0),Fraction(0),Fraction(0),9,"e"*64)
        candidates=(Candidate("high-coverage",Fraction(99,100),Fraction(1,3),Fraction(0),Fraction(1,100),5),Candidate("low-width",Fraction(19,20),Fraction(1,8),Fraction(0),Fraction(1,40),3))
        failures=tuple(FailureWorld(x) for x in ("NODE_DOWN","PARTITION","LATENCY","LOSS","VERSION_SKEW","CERTIFICATE","AMBIGUOUS_DO"))
        return subject,graph,va,vb,dep,candidates,failures

    def test_full_current_evidence_is_bounded_and_replayable(self):
        subject,graph,va,vb,dep,candidates,failures=self.fixtures()
        ev=evaluate(subject=subject,generation=9,graph=graph,a_interval=Interval(Fraction(3,5),Fraction(9,10)),b_interval=Interval(Fraction(7,10),Fraction(19,20)),mode=CompositionMode.INDEPENDENCE_QUALIFIED,a_validator=va,b_validator=vb,dependence=dep,candidates=candidates,strategy=Strategy.MAX_COVERAGE,methodologies=REQUIRED_METHODOLOGIES,failure_worlds=failures,dependency_states=("PARTIAL_ALIVE",))
        self.assertEqual(ev.qualification.standing,"PARTIAL_ALIVE"); self.assertIsNotNone(ev.receipt)
        self.assertEqual(replay(ev.receipt,ev.receipt.digest),"REPLAY_MATCH")
        with self.assertRaises(Refused) as do: admit(ActionClass.DO)
        self.assertEqual(do.exception.code,"BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO")

    def test_hard_failure_dominates_and_suppresses_receipt(self):
        subject,graph,va,vb,dep,candidates,failures=self.fixtures()
        ev=evaluate(subject=subject,generation=9,graph=graph,a_interval=Interval(Fraction(3,5),Fraction(9,10)),b_interval=Interval(Fraction(7,10),Fraction(19,20)),mode=CompositionMode.CONSERVATIVE,a_validator=va,b_validator=vb,dependence=dep,candidates=candidates,strategy=Strategy.MIN_WIDTH,methodologies=REQUIRED_METHODOLOGIES,failure_worlds=failures,dependency_states=("PARTIAL_ALIVE","BUILD_BROKEN"))
        self.assertEqual(ev.qualification.standing,"BUILD_BROKEN"); self.assertIsNone(ev.receipt)

if __name__ == "__main__": unittest.main()
