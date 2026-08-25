class Refused(ValueError):
    """Typed fail-closed refusal for certificate-realization admission."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        suffix = f": {detail}" if detail else ""
        super().__init__(f"REFUSED[{code}]{suffix}")
