from urllib.parse import urlparse
from . import Refusal
from .policy import DependencyPolicy

def repo_from_git_url(url: str) -> str:
    parsed=urlparse(url)
    if parsed.scheme != 'https' or parsed.netloc != 'github.com':
        raise Refusal('REFUSED[NON_GITHUB_GIT_SOURCE]')
    path=parsed.path.strip('/')
    if path.endswith('.git'): path=path[:-4]
    if path.count('/') != 1:
        raise Refusal('REFUSED[INVALID_GIT_SOURCE]')
    return path

def admit_git_source(policy: DependencyPolicy, url: str) -> str:
    repo=repo_from_git_url(url)
    policy.admit_repo(repo)
    return repo
