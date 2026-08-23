class Refused(ValueError):
    """Typed fail-closed release admission refusal."""
    def __init__(self, code: str):
        if not code or not code.replace("_", "").isalnum():
            raise ValueError("invalid refusal code")
        self.code = code
        super().__init__(f"REFUSED[{code}]")
