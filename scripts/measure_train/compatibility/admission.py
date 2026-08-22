from .contradiction import contradictions
def admit(vector):
    c=contradictions(vector)
    if c: return {"admitted":False,"refusal":"REFUSED[CONTRADICTORY_AXIS]","contradictions":c}
    return {"admitted":True,"refusal":None,"contradictions":()}
