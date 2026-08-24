class Refused(ValueError):
    pass
def refuse(code, detail=""):
    raise Refused(f"REFUSED[{code}]" + (f": {detail}" if detail else ""))
