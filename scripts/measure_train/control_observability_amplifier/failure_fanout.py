from collections import Counter
def observe(rows):
 c=Counter(r['failure_root'] for r in rows if r.get('failure_root'))
 return {"sensor":"failure_fanout","roots":dict(sorted(c.items())),"max_fanout":max(c.values(),default=0)}
