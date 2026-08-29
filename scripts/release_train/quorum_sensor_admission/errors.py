from __future__ import annotations


class Refused(ValueError):
    """Typed fail-closed release admission refusal."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        message = f"REFUSED[{code}]" + (f": {detail}" if detail else "")
        super().__init__(message)
