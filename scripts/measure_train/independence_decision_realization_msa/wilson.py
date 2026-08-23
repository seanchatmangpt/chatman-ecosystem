import math

def wilson_upper(successes,total,z=1.959963984540054):
    if total<=0: return 1.0
    p=successes/total; z2=z*z
    center=(p+z2/(2*total))/(1+z2/total)
    spread=z*math.sqrt((p*(1-p)+z2/(4*total))/total)/(1+z2/total)
    return min(1.0,center+spread)

def error_upper(confusion_result):
    errors=confusion_result.false_independent+confusion_result.false_dependent
    return wilson_upper(errors,confusion_result.support)
