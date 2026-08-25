from math import sqrt
def confidence_interval(successes:int,n:int,z:float=1.96):
    if n<=0 or not 0<=successes<=n: raise ValueError("invalid support")
    p=successes/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d
    h=z*sqrt((p*(1-p)+z*z/(4*n))/n)/d
    return max(0.0,c-h),min(1.0,c+h)
