from .refusal import Refused
def admit_semantic(fixed_point,monotone,semilattice,final_distance,tolerance):
 if min(final_distance,tolerance)<0: raise Refused("REFUSED[INVALID_SEMANTIC_DISTANCE]")
 if not monotone or not semilattice: raise Refused("REFUSED[SEMANTIC_LAW_FAILURE]")
 if not fixed_point or final_distance>tolerance: raise Refused("REFUSED[SEMANTIC_NONCONVERGENCE]")
 return True
