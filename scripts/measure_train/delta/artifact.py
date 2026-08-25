from dataclasses import dataclass
HEX=set("0123456789abcdef")
@dataclass(frozen=True)
class ArtifactEvidence:
    name:str; sha256:str; subject_sha:str
    def __post_init__(self):
        if len(self.sha256)!=64 or any(c not in HEX for c in self.sha256): raise ValueError("REFUSED[INVALID_ARTIFACT_DIGEST]")
        if len(self.subject_sha)!=40 or any(c not in HEX for c in self.subject_sha): raise ValueError("REFUSED[INVALID_ARTIFACT_SUBJECT]")
    def binds(self,subject_sha): return self.subject_sha==subject_sha
