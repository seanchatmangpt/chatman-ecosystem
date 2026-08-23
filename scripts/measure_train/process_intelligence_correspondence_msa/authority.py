from .subject import Refused
def admit_authority(path, actuation_performed):
    expected=("SEMANTIC_ADMISSION","REACTOR_CONSTRUCT","BRCE_DO","POSTCONDITION","RECEIPT")
    if tuple(path)!=expected: raise Refused("REFUSED[BRCE_CORRESPONDENCE_BROKEN]")
    if actuation_performed is not True: raise Refused("REFUSED[NO_OBSERVED_BRCE_ACTUATION]")
    return "CORRESPONDENT"
def measurement_authority():
    return {"authority":"OBSERVE|VERIFY","actuation_performed":False}
