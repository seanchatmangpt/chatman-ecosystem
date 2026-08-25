REQUIRED=("DISCOVERY","CONFORMANCE","SIMULATION","PREDICTION","OPTIMIZATION","INTERVENTION","MONITORING","EVENT_CENTRIC","OBJECT_CENTRIC","DECLARATIVE","PROCEDURAL")
def coverage(methodologies):
    got=set(methodologies)
    missing=tuple(sorted(set(REQUIRED)-got))
    return {"covered":len(set(REQUIRED)&got),"required":len(REQUIRED),"missing":missing,"complete":not missing}
