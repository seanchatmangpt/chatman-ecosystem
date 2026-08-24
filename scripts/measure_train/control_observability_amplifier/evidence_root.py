def observe(rows):
 roots=[r['evidence_root'] for r in rows]; unique=len(set(roots))
 return {"sensor":"evidence_root","nominal":len(roots),"independent":unique,"duplication":len(roots)-unique}
