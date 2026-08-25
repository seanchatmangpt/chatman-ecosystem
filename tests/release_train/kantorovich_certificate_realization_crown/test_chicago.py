import unittest
from fractions import Fraction
from scripts.release_train.kantorovich_certificate_realization_crown import Subject,Certificate,Observation,qualify,replay
METHODS=('discovery','conformance','simulation','prediction','optimization','intervention','monitoring','event-centric','object-centric','declarative','procedural')
WORLDS=('node','partition','latency','loss','version','certificate','ambiguous-do')
class T(unittest.TestCase):
    def corpus(self):
        out=[]; i=0
        for m in METHODS:
            for w in WORLDS:
                out.append(Observation(str(i),'b'*64,7,Fraction(1),Fraction(1),Fraction(1),'impl'+str(i%2),'model'+str(i%2),'root'+str(i%2),m,'BEAM' if i%2==0 else 'WASM','us-east' if i%2==0 else 'eu-west',w)); i+=1
        return tuple(out)
    def test_chicago_realization_and_failure_dominance(self):
        s=Subject.parse('seanchatmangpt/chatman-ecosystem@'+'a'*40); c=Certificate('b'*64,7,Fraction(1),Fraction(1)); obs=self.corpus()
        standing,r=qualify(s,c,obs,{'root':['release-control']},{'release-control':'ALIVE'})
        self.assertEqual(standing,'PARTIAL_ALIVE'); self.assertEqual(replay(r),'REPLAY_MATCH')
        standing,r=qualify(s,c,obs,{'root':['qlever']},{'qlever':'BUILD_BROKEN'})
        self.assertEqual(standing,'BUILD_BROKEN'); self.assertIsNone(r)
if __name__=='__main__': unittest.main()
