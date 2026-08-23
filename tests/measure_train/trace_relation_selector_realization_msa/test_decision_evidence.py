import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.trace_relation_selector_realization_msa.subject import Subject,Refused
from scripts.measure_train.trace_relation_selector_realization_msa.selector import Selector,SelectorIdentity
from scripts.measure_train.trace_relation_selector_realization_msa.relation import Relation
from scripts.measure_train.trace_relation_selector_realization_msa.decision import Decision
from scripts.measure_train.trace_relation_selector_realization_msa.realization import RealizedRelation
from scripts.measure_train.trace_relation_selector_realization_msa.evidence import admit_realizations
class T(unittest.TestCase):
 def test_contradictory_duplicate_refuses(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); i=SelectorIdentity(Selector.MINIMAX_ERROR,1,"c"*64)
  d=Decision(s,i,"d",(Relation.EXACT,),(Relation.EXACT,Relation.ACTIVITY),100000,10,now)
  a=RealizedRelation(s,"d",Relation.EXACT,True,10,now+timedelta(seconds=1),"x")
  b=RealizedRelation(s,"d",Relation.EXACT,False,10,now+timedelta(seconds=2),"x")
  with self.assertRaises(Refused): admit_realizations(d,[a,b])
