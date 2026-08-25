def has_cycle(digests):
    seen={}
    for i,d in enumerate(digests):
        if d in seen and i-seen[d]>1: return True
        seen[d]=i
    return False
