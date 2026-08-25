from .subject import Refused

CLASSES=frozenset({"OBSERVE","SELECT","CONSTRUCT","VERIFY","DO"})

def admit_authority(action,brce_receipt=None):
    if action not in CLASSES: raise Refused("REFUSED[UNKNOWN_AUTHORITY_CLASS]")
    if action=="DO":
        if not brce_receipt: raise Refused("REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]")
        if brce_receipt.get("authority")!="BRCE" or brce_receipt.get("actuation_performed") is not True:
            raise Refused("REFUSED[INVALID_BRCE_RECEIPT]")
    return "ADMITTED"
