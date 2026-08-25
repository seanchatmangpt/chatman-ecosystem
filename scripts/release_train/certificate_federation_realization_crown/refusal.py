class Refused(ValueError):
    """Typed fail-closed refusal carrying a stable machine code."""
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"REFUSED[{code}]" + (f": {detail}" if detail else ""))
