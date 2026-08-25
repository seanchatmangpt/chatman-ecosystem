import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.trace_relation_selector_realization_msa.subject import Subject
from scripts.measure_train.trace_relation_selector_realization_msa.selector import Selector,SelectorIdentity
from scripts.measure_train.trace_relation_selector_realization_msa.relation import Relation
from scripts.measure_train.trace_relation_selector_realization_msa.decision import Decision
from scripts.measure_train.trace_relation_selector_realization_msa.qualify import qualify
from scripts.measure_train.trace_relation_selector_realization_msa.replay import replay
class T(unittest.TestCase):
 def test_realized_selector_quality_never_manufactures_alive(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); i=SelectorIdentity(Selector.MINIMAX_ERROR,2,"c"*64)
  ds=[Decision(s,i,f"d{n}",(Relation.EXACT,),(Relation.EXACT,Relation.ACTIVITY),100000,10,now+timedelta(seconds=n)) for n in range(5)]
  q=qualify(s,ds,{d.decision_id:False for d in ds},[0,0,0,0,0])
  self.assertEqual(q["standing"],"PARTIAL_ALIVE"); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH"); self.assertFalse(q["actuation_performed"])
  red=qualify(s,ds,{d.decision_id:False for d in ds},[0,0,0,0,0],dependencies=("BUILD_BROKEN",))
  self.assertEqual(red["standing"],"BUILD_BROKEN")
