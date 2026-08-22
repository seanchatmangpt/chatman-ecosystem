import unittest
from scripts.release_train.dependency_qualification import DependencySubject, Refusal
from scripts.release_train.dependency_qualification.candidate import Candidate, select
class T(unittest.TestCase):
 def test_rank(self):
  a=Candidate(DependencySubject('o/a','a'*40),5,2,'exact-head-partial'); b=Candidate(DependencySubject('o/b','b'*40),6,1,'exact-head-success'); self.assertEqual(select([a,b]),b)
 def test_no_evidence(self):
  with self.assertRaises(Refusal): select([Candidate(DependencySubject('o/a','a'*40),9,9,'unknown')])
