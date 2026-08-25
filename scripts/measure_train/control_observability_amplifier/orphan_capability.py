def observe(capabilities, consumers):
 used={c['capability'] for c in consumers}; orphan=sorted(set(capabilities)-used)
 return {"sensor":"orphan_capability","orphan":orphan,"count":len(orphan)}
