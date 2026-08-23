class Refused(ValueError):
    pass

def refuse(code: str):
    raise Refused(f"REFUSED[{code}]")
