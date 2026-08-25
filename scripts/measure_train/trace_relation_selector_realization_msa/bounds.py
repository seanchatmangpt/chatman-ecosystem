import math

def wilson_upper(successes, n, z=1.959963984540054):
    if n <= 0:
        return 1.0
    p=successes/n
    z2=z*z
    center=(p+z2/(2*n))/(1+z2/n)
    radius=z*math.sqrt((p*(1-p)+z2/(4*n))/n)/(1+z2/n)
    return min(1.0,center+radius)

def wilson_lower(successes, n, z=1.959963984540054):
    if n <= 0:
        return 0.0
    p=successes/n
    z2=z*z
    center=(p+z2/(2*n))/(1+z2/n)
    radius=z*math.sqrt((p*(1-p)+z2/(4*n))/n)/(1+z2/n)
    return max(0.0,center-radius)
