from collections import defaultdict

def contradictions(witnesses):
    grouped=defaultdict(set)
    for w in witnesses:
        if w.kind in {"DISCHARGE","RECOVERY"}:
            grouped[(w.consumer,w.producer,w.generation,w.event_id,w.kind)].add(w.outcome)
    return tuple(sorted((k[0].repo,k[0].sha,k[2],k[3],k[4],tuple(sorted(v))) for k,v in grouped.items() if len(v)>1))
