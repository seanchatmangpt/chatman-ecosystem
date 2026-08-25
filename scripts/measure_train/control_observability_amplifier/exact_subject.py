import re

def observe(repo: str, sha: str) -> dict:
    exact = bool(re.fullmatch(r"[0-9a-f]{40}", sha)) and "/" in repo
    return {"sensor":"exact_subject","repo":repo,"sha":sha,"standing":"ALIVE" if exact else "REFUSED[INEXACT_SUBJECT]"}
