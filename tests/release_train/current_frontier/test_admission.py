import unittest
from datetime import datetime, timezone
from scripts.release_train.current_frontier.admission import admit_subject
from scripts.release_train.current_frontier.evidence import Evidence
from scripts.release_train.current_frontier.frontier import Frontier
from scripts.release_train.current_frontier.obligation import Obligation
from scripts.release_train.current_frontier.subject import Subject
class T(unittest.TestCase):
 def test_current_pass_promotable(self):
  s=Subject.parse("o/r@"+"a"*40); e=Evidence("x",s,"REPOSITORY","PASS",datetime.now(timezone.utc),"1"); a=admit_subject(s.canonical(),Frontier((e,),()),(Obligation("repo","REPOSITORY"),)); self.assertTrue(a.promotable); self.assertEqual(a.standing,"PARTIAL_ALIVE")
