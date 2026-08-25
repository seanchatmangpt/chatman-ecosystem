import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.federation_epistemic_capital_msa.subject import Subject
from scripts.measure_train.federation_epistemic_capital_msa.transport import Transport
from scripts.measure_train.federation_epistemic_capital_msa.observation import TrialObservation
from scripts.measure_train.federation_epistemic_capital_msa.association import associations
from scripts.measure_train.federation_epistemic_capital_msa.correlation import matrix
from scripts.measure_train.federation_epistemic_capital_msa.effective_sample import effective_sample
from scripts.measure_train.federation_epistemic_capital_msa.clusters import clusters
from scripts.measure_train.federation_epistemic_capital_msa.capital import capitalize
class T(unittest.TestCase):
 def test_duplicates_collapse_capital(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40,"b"*64); rows=[]
  for tid in ("x","y","z"):
   t=Transport(tid,(tid*64)[:64],((tid+"m")*64)[:64],"d"+tid,1)
   for i,v in enumerate([0,1,0,1,0,1]): rows.append(TrialObservation(s,t,str(i),bool(v),True,True,now+timedelta(seconds=i),"DISCOVERY","e","r","root"))
  a=associations(rows); ids=sorted({r.transport.transport_id for r in rows}); cap=capitalize(effective_sample(matrix(ids,a)),clusters(ids,a)); self.assertLessEqual(cap.effective_n,1.01); self.assertGreater(cap.duplication_ratio,.6)
