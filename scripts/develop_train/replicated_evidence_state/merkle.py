import hashlib
from .errors import Refused

def merkle_root(digests: list[str]) -> str:
    if not digests: raise Refused("EMPTY_MERKLE_SET")
    level=[bytes.fromhex(d) for d in sorted(digests)]
    while len(level)>1:
        if len(level)%2: level.append(level[-1])
        level=[hashlib.sha256(level[i]+level[i+1]).digest() for i in range(0,len(level),2)]
    return level[0].hex()
