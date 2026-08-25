def observe(edges, cleared):
 unlocked=sorted({child for parent,child in edges if parent in set(cleared)})
 return {"sensor":"dependency_unlock","cleared":sorted(cleared),"unlocked":unlocked,"fanout":len(unlocked)}
