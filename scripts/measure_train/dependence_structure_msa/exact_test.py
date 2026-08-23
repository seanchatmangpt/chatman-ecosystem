from itertools import combinations
from math import comb
from .contingency import Contingency2x2
from .association import association
from .subject import Refused

def exact_permutation_p_value(rows, max_support=18):
    rows=tuple(rows)
    n=len(rows)
    if n == 0:
        return 1.0
    if n > max_support:
        raise Refused("REFUSED[EXACT_TEST_SUPPORT_TOO_LARGE]")
    left=[r.left for r in rows]
    right_true=sum(1 for r in rows if r.right)
    observed=abs(association(_table_from_bits(left,[r.right for r in rows])).phi)
    total=comb(n,right_true)
    extreme=0
    for positions in combinations(range(n), right_true):
        pos=set(positions)
        right=[i in pos for i in range(n)]
        if abs(association(_table_from_bits(left,right)).phi) >= observed-1e-15:
            extreme += 1
    return extreme/total

def _table_from_bits(left,right):
    counts={(False,False):0,(False,True):0,(True,False):0,(True,True):0}
    for x,y in zip(left,right):
        counts[(x,y)]+=1
    return Contingency2x2(counts[(False,False)],counts[(False,True)],counts[(True,False)],counts[(True,True)])
