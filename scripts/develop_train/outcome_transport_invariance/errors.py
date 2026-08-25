class Refused(ValueError):
    def __init__(self, code, detail=""):
        self.code = code
        super().__init__(f"REFUSED[{code}]" + (f": {detail}" if detail else ""))
