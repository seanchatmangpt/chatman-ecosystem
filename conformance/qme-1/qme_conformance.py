#!/usr/bin/env python3
import json,sys
def court(r):
 e=[]
 s=r.get("subject")
 if r.get("receipt",{}).get("subject")!=s:e.append("EXACT_SUBJECT")
 if r.get("consequence",{}).get("bounded") is not True:e.append("MXINF")
 if r.get("replay",{}).get("actuates") is not False:e.append("REPLAY_ACTUATES")
 if r.get("authority_ceiling")=="do" and r.get("observation",{}).get("independent") is not True:e.append("SELF_OBSERVED_DO")
 owners=list(r.get("canonical_owners",{}).values())
 if len(owners)!=len(set(owners)):e.append("OWNER_ALIAS_COLLISION")
 g=r.get("generated",{})
 if g.get("is_projection") and not all(g.get(k) for k in ("source","generator","digest")):e.append("HIDDEN_GENERATION")
 for n in r.get("negative_knowledge",[]):
  if n.get("subject")!=s:e.append("NEGATIVE_SUBJECT")
 return sorted(set(e))
def main():
 rc=0
 for p in sys.argv[1:]:
  r=json.load(open(p)); got=court(r); exp=r.get("_expected_errors",[])
  if sorted(exp)!=got: print(p,"FAIL",got,"expected",exp);rc=1
  else: print(p,"PASS",got)
 return rc
if __name__=="__main__":raise SystemExit(main())
