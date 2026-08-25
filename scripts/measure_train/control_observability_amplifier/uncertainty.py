import math
def observe(successes,n,z=1.96):
 if n<=0:return {'sensor':'uncertainty','standing':'UNKNOWN'}
 p=successes/n; se=math.sqrt(p*(1-p)/n); lo=max(0,p-z*se); hi=min(1,p+z*se)
 return {'sensor':'uncertainty','estimate':p,'lower':lo,'upper':hi,'width':hi-lo,'support':n}
