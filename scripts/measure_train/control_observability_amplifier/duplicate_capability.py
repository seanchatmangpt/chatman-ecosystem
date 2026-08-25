from collections import defaultdict
def observe(rows):
 g=defaultdict(list)
 for r in rows:g[r['semantic_digest']].append(r['subject'])
 dup={k:sorted(v) for k,v in g.items() if len(v)>1}
 return {"sensor":"duplicate_capability","duplicates":dup,"groups":len(dup)}
