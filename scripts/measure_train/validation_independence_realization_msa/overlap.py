from fractions import Fraction
from .graph import ancestors
def ancestry_overlap(graph,left_id,right_id):
    a=set(ancestors(graph,left_id))|{left_id}; b=set(ancestors(graph,right_id))|{right_id}
    union=a|b
    return Fraction(len(a&b),len(union)) if union else Fraction(0)
def shared_roots(graph,left_id,right_id):
    a=set(ancestors(graph,left_id))|{left_id}; b=set(ancestors(graph,right_id))|{right_id}
    return tuple(sorted(a&b))
