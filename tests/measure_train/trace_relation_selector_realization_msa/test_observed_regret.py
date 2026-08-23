import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.trace_relation_selector_realization_msa.subject import Subject,Refused
from scripts.measure_train.trace_relation_selector_realization_msa.selector import Selector,SelectorIdentity
from scripts.measure_train.trace_relation_selector_realization_msa.relation import Relation
from scripts.measure_train.trace_relation_selector_realization_msa.decision import Decision
from scripts.measure_train.trace_relation_selector_realization_msa.realization import RealizedRelation
from scripts.measure_train.trace_relation_selector_realization_msa.regret import observed_only_regret
class T(unittest.TestCase):
 def test_regret_uses_only_observed_candidates(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); i=SelectorIdentity(Selector.STRONGEST_DEFENSIBLE,1,"c"*64)
  d=Decision(s,i,"d",(Relation.EXACT,),(Relation.EXACT,Relation.ACTIVITY),100000,1,now)
  rows=[RealizedRelation(s,"d",Relation.EXACT,False,2,now+timedelta(seconds=1),"e")]
  r=observed_only_regret(d,rows,lambda rel,x: 1 if not x[0].equivalent else 0); self.assertEqual(r.regret,0)
  d2=Decision(s,i,"d2",(Relation.ACTIVITY,),(Relation.EXACT,Relation.ACTIVITY),100000,1,now)
  with self.assertRaises(Refused): observed_only_regret(d2,rows,lambda rel,x:0)
