class Refused(RuntimeError):
    """Typed fail-closed refusal for inadmissible replicated-state transitions."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"REFUSED[{code}]" + (f": {detail}" if detail else ""))
