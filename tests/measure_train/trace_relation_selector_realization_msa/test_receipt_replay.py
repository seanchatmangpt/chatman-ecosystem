import unittest
from datetime import datetime,timezone
from scripts.measure_train.trace_relation_selector_realization_msa.subject import Subject,Refused
from scripts.measure_train.trace_relation_selector_realization_msa.selector import Selector,SelectorIdentity
from scripts.measure_train.trace_relation_selector_realization_msa.relation import Relation
from scripts.measure_train.trace_relation_selector_realization_msa.decision import Decision
from scripts.measure_train.trace_relation_selector_realization_msa.census import deterministic_census
from scripts.measure_train.trace_relation_selector_realization_msa.receipt import manufacture
from scripts.measure_train.trace_relation_selector_realization_msa.replay import replay
class T(unittest.TestCase):
 def test_tamper_refuses(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); i=SelectorIdentity(Selector.MINIMAX_ERROR,1,"c"*64)
  ds=[Decision(s,i,str(n),(Relation.EXACT,),(Relation.EXACT,),100000,1,now) for n in range(5)]
  c=deterministic_census(ds,{d.decision_id:False for d in ds}); r=manufacture(s,c,"PARTIAL_ALIVE",[0],False)
  self.assertEqual(replay(r),"REPLAY_MATCH"); r["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused): replay(r)
