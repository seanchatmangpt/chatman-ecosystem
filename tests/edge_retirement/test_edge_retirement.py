import unittest
from scripts.edge_retirement.edge_retirement import Edge, admit, replay
S="a"*40
class Court(unittest.TestCase):
 def test_replay_and_canonicalization(self):
  e=Edge("E-REP-01",S,("machine","machine"),"typed repair demand")
  self.assertTrue(replay(e,admit(e)))
 def test_recurring_intelligence_refused(self):
  for o in (("machine","human"),("machine","llm"),("human",)):
   with self.assertRaises(ValueError): admit(Edge("E",S,o,"c"))
 def test_subject_and_authority_refused(self):
  with self.assertRaises(ValueError): admit(Edge("E","main",("machine",),"c"))
  with self.assertRaises(ValueError): admit(Edge("E",S,("machine",),"c","DO"))
 def test_semantic_change_changes_receipt(self):
  self.assertNotEqual(admit(Edge("E",S,("machine",),"a")).digest,admit(Edge("E",S,("machine",),"b")).digest)
if __name__=="__main__": unittest.main()
