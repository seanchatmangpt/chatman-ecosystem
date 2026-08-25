def clusters(ids,assoc,phi_threshold=0.8,mi_threshold=0.5):
    g={x:set() for x in ids}
    for a in assoc:
        if abs(a.phi)>=phi_threshold or a.mutual_information_bits>=mi_threshold:
            g[a.left].add(a.right); g[a.right].add(a.left)
    seen=set(); out=[]
    for x in sorted(g):
        if x in seen: continue
        stack=[x]; c=set()
        while stack:
            y=stack.pop()
            if y in seen: continue
            seen.add(y); c.add(y); stack.extend(g[y]-seen)
        out.append(tuple(sorted(c)))
    return tuple(out)
