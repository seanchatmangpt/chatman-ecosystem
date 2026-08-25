from .relation import maximal

def select_strongest_defensible(admitted_relations):
    return maximal(admitted_relations)
