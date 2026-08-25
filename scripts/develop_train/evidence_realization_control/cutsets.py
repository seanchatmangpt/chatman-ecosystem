def minimal_blocker_cutsets(blocked, dependencies):
    blocked=set(blocked); deps={k:set(v) for k,v in dependencies.items()}
    raw=[]
    for node in sorted(blocked):
        s={node}|{d for d in deps.get(node,set()) if d in blocked}; raw.append(frozenset(s))
    return tuple(sorted((s for s in raw if not any(t < s for t in raw)), key=lambda s:(len(s),tuple(sorted(s)))))
