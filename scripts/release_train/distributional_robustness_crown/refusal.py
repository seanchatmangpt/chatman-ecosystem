class Refused(ValueError):
    """Typed fail-closed release admission refusal."""
    def __init__(self, code: str, detail: str = ""):
        self.code, self.detail = code, detail
        super().__init__(f"REFUSED[{code}]" + (f": {detail}" if detail else ""))
