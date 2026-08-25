class Refused(ValueError):
    """Typed fail-closed refusal with a stable machine code."""
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"REFUSED[{code}]" + (f": {detail}" if detail else ""))

def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise Refused(code, detail)
