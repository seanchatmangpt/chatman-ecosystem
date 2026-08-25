from dataclasses import dataclass
from .subject import Refused
KINDS={"GITHUB_ACTION","GITHUB_STATUS","ARTIFACT","RUNTIME","RECEIPT","DEPENDENCY"}
@dataclass(frozen=True, order=True)
class Source:
    kind: str
    locator: str
    def __post_init__(self):
        if self.kind not in KINDS: raise Refused("REFUSED[UNKNOWN_SOURCE_KIND]")
        if not self.locator.strip(): raise Refused("REFUSED[EMPTY_SOURCE_LOCATOR]")
