from fractions import Fraction
from .sensitivity import Interval
from .refusal import refuse

def manski_mean(observed_rewards, total_count:int):
    vals=tuple(observed_rewards)
    if total_count < len(vals) or total_count<=0: refuse("INVALID_IDENTIFICATION_DOMAIN")
    if any(v<0 or v>1 for v in vals): refuse("INVALID_REWARD")
    missing=total_count-len(vals); s=sum(vals,Fraction(0))
    return Interval(s/total_count,(s+missing)/total_count)
