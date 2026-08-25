import math
def total_variation(p,q):
    keys=set(p)|set(q)
    return 0.5*sum(abs(float(p.get(k,0))-float(q.get(k,0))) for k in keys)
def jensen_shannon(p,q):
    keys=set(p)|set(q); m={k:(float(p.get(k,0))+float(q.get(k,0)))/2 for k in keys}
    def kl(a,b):
        return sum(float(a.get(k,0))*math.log2(float(a.get(k,0))/b[k]) for k in keys if float(a.get(k,0))>0 and b[k]>0)
    return 0.5*kl(p,m)+0.5*kl(q,m)
