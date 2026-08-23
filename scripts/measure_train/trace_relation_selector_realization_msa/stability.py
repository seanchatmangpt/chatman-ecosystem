from fractions import Fraction

def jaccard(left,right):
    a=set(left); b=set(right)
    if not a and not b:
        return Fraction(1)
    return Fraction(len(a&b),len(a|b))

def churn(decisions):
    rows=tuple(decisions)
    if len(rows)<2:
        return Fraction(0)
    changed=sum(1 for a,b in zip(rows,rows[1:]) if set(a.chosen)!=set(b.chosen))
    return Fraction(changed,len(rows)-1)
