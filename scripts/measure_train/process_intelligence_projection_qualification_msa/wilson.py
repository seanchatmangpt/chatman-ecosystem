import math
def wilson_upper(errors,n,z=1.959963984540054):
    if n<=0:return 1.0
    p=errors/n; den=1+z*z/n; center=(p+z*z/(2*n))/den; radius=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/den
    return min(1.0,center+radius)
