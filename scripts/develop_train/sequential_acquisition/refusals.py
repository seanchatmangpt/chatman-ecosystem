class Refused(ValueError):
    """Typed fail-closed refusal used by the sequential acquisition capsule."""

    def __init__(self, code: str):
        if not code or not code.startswith("REFUSED_"):
            raise ValueError("refusal code must start with REFUSED_")
        self.code = code
        super().__init__(code)
