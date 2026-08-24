import unittest
from datetime import datetime, timezone, timedelta
from scripts.develop_train.certificate_federation_observability import *
C=Certificate(7,"c"*64,"d"*64,"e"*64,"f"*64); NOW=datetime.now(timezone.utc); T1=Transport("gh-api","impl-a","model-a","domain-a")
def resolved(i,rel=Relation.EXACT): return Observation(f"o{i}",T1.transport_id,7,TransportState.RESOLVED,rel,"a"*40,"b"*64,C.digest,NOW-timedelta(seconds=1),10+i)
class T(unittest.TestCase):
 def test_censoring(self):
  o=Observation("c","gh-api",7,TransportState.TIMEOUT,Relation.CENSORED,None,None,None,NOW-timedelta(seconds=1),100)
  self.assertEqual(summarize([resolved(1),o]).censored,1); self.assertEqual(classify_lineage([resolved(1),o]).diverged,0)
 def test_diverged(self):
  with self.assertRaises(Refused): require_no_divergence(classify_lineage([resolved(1,Relation.DIVERGED)]))
