from fractions import Fraction
def information_inflation(conservative_width,independent_width):
    if conservative_width<=0:return Fraction(0)
    if independent_width<0: raise ValueError("negative width")
    return max(Fraction(0),Fraction(conservative_width-independent_width,conservative_width))
def duplicate_capital_multiplier(unique_roots,total_evidence):
    if unique_roots<=0 or total_evidence<unique_roots: raise ValueError("invalid evidence cardinality")
    return Fraction(total_evidence,unique_roots)
