class Refused(ValueError):
    """Typed fail-closed convergence-kinetics refusal."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"REFUSED[{code}]")
