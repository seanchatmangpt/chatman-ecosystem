from fractions import Fraction
def interval_iou(a,b):
    inter=max(Fraction(0), min(a.upper,b.upper)-max(a.lower,b.lower))
    union=max(a.upper,b.upper)-min(a.lower,b.lower)
    return Fraction(1) if union==0 else inter/union
def identification_value(bound, domain_width):
    if domain_width <= 0: raise ValueError("domain_width must be positive")
    width=bound.width
    if width >= domain_width: return Fraction(0)
    return Fraction(1)-width/domain_width
