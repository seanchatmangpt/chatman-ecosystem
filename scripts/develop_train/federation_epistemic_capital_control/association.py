from dataclasses import dataclass
from math import log2,sqrt
from .errors import Refused
@dataclass(frozen=True)
class Association: paired:int; phi:float; mutual_information:float
def measure(left,right):
    if len(left)!=len(right) or len(left)<2: raise Refused("INSUFFICIENT_ASSOCIATION_SUPPORT")
    a=b=c=d=0
    for x,y in zip(left,right):
        xf,yf=bool(x.failure),bool(y.failure)
        if xf and yf:a+=1
        elif xf:b+=1
        elif yf:c+=1
        else:d+=1
    den=sqrt((a+b)*(c+d)*(a+c)*(b+d)); phi=((a*d-b*c)/den) if den else 0.0
    n=a+b+c+d; mi=0.0
    for count,row,col in ((a,a+b,a+c),(b,a+b,b+d),(c,c+d,a+c),(d,c+d,b+d)):
        if count:
            p=count/n; mi+=p*log2(p/((row/n)*(col/n)))
    return Association(n,phi,mi)
