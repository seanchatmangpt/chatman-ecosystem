def signature(rows):
    seq=[]
    for r in rows:
        if not seq or seq[-1]!=r.state: seq.append(r.state)
    toggles=max(0,len(seq)-1); recurrent=len(set(seq))<len(seq)
    return {'sequence':tuple(seq),'toggles':toggles,'recurrent':recurrent,'oscillating':recurrent and toggles>=2}
