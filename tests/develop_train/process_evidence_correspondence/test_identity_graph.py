import unittest
from scripts.develop_train.process_evidence_correspondence import *
class T(unittest.TestCase):
 def test_identity_and_cycle(self):
  s=Subject.parse("o/r@"+"a"*40+"#"+"b"*64); self.assertEqual(s.repo,"o/r")
  with self.assertRaises(Refused): Subject.parse("o/r@short")
  p=Provenance("i","m","d"); a=Evidence("a",1,"SEMANTIC",Interval(.8,.9),p,"1"*64)
  b=Evidence("b",1,"TRACE",Interval(.7,.8),p,"2"*64,("a",)); self.assertEqual(EvidenceGraph([b,a]).order,("a","b"))
  c=Evidence("c",1,"TRACE",Interval(.7,.8),p,"3"*64,("d",)); d=Evidence("d",1,"TRACE",Interval(.7,.8),p,"4"*64,("c",))
  with self.assertRaises(Refused): EvidenceGraph([c,d])
if __name__=="__main__": unittest.main()
