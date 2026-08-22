from dataclasses import dataclass, field
from . import Refusal

@dataclass(frozen=True)
class DependencyPolicy:
    allowed_git_repos: frozenset[str] = field(default_factory=frozenset)
    allowed_licenses: frozenset[str] = field(default_factory=frozenset)
    refused_actions: frozenset[str] = frozenset({'DO','MERGE','RELEASE','DEPLOY','MESSAGE','SPEND','DELETE','CLOUD_ACTUATE'})

    def admit_repo(self, repo: str) -> None:
        if repo not in self.allowed_git_repos:
            raise Refusal('REFUSED[GIT_SOURCE_NOT_ALLOWLISTED]')

    def admit_license(self, license_id: str) -> None:
        if license_id not in self.allowed_licenses:
            raise Refusal('REFUSED[LICENSE_NOT_ALLOWLISTED]')
