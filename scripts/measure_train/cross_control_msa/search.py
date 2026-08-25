from .refusal import Refused
def admit_search(expansions,cost,depth,max_expansions,max_cost,max_depth,regret):
 if min(expansions,depth,max_expansions,max_depth)<0 or min(cost,max_cost,regret)<0: raise Refused("REFUSED[INVALID_SEARCH_MEASUREMENT]")
 if expansions>max_expansions or cost>max_cost or depth>max_depth: raise Refused("REFUSED[SEARCH_BUDGET_ESCAPE]")
 return True
