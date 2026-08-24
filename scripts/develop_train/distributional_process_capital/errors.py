class Refused(ValueError):
    """Typed fail-closed boundary for distributional process capital."""
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"REFUSED[{code}]" + (f": {detail}" if detail else ""))
