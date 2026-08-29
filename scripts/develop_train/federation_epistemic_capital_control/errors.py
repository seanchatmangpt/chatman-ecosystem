class Refused(ValueError):
    def __init__(self, code, detail=""):
        self.code=code; self.detail=detail
        super().__init__(f"REFUSED[{code}]" + (f": {detail}" if detail else ""))
