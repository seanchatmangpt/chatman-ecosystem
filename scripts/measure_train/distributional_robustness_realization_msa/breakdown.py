from .refusal import Refused
def empirical_breakdown_radius(points,max_loss):
    failures=[radius for radius,loss in sorted(points,key=lambda x:x[0]) if loss>max_loss]
    if not failures: raise Refused("REFUSED[UNOBSERVED_BREAKDOWN]")
    return min(failures)
