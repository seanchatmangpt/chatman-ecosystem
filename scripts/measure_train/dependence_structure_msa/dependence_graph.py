def components(pair_verdicts):
    adjacency={}
    for left,right,verdict in pair_verdicts:
        adjacency.setdefault(left,set()); adjacency.setdefault(right,set())
        if verdict=="DEPENDENT":
            adjacency[left].add(right); adjacency[right].add(left)
    seen=set(); result=[]
    for node in sorted(adjacency):
        if node in seen: continue
        stack=[node]; comp=[]
        while stack:
            cur=stack.pop()
            if cur in seen: continue
            seen.add(cur); comp.append(cur)
            stack.extend(sorted(adjacency[cur]-seen, reverse=True))
        result.append(tuple(sorted(comp)))
    return tuple(sorted(result))
