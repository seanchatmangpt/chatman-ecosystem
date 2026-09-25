"""Pure-Python git object identities (stdlib only; no subprocess, no .git access).

The post-tag crown binds the immutable release tag to bytes it can recompute: raw git
object bodies committed under ``release/<v>/hardening/inputs/objects/<sha>.<type>.raw``
(the output of ``git cat-file <type> <sha>``) and a materialized subject directory
(``git archive <commit> <paths> | tar -x``). Every identity here is the git SHA-1 object
id: ``sha1(b"<type> <len>\\0" + body)``.
"""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

OBJECT_TYPES = ("blob", "tree", "commit", "tag")
MODE_TREE = "40000"
MODE_FILE = "100644"
MODE_EXEC = "100755"
MODE_LINK = "120000"


class GitObjectError(ValueError):
    """A raw object that does not parse, or a path that does not resolve."""


def object_sha(kind: str, body: bytes) -> str:
    if kind not in OBJECT_TYPES:
        raise GitObjectError(f"unknown object type {kind!r}")
    return hashlib.sha1(b"%s %d\0" % (kind.encode("ascii"), len(body)) + body).hexdigest()


def blob_sha(body: bytes) -> str:
    return object_sha("blob", body)


def _headers(body: bytes) -> tuple[list[tuple[str, str]], str]:
    """RFC-822-ish git headers (continuation lines start with a space) + message."""
    text = body.decode("utf-8", errors="surrogateescape")
    head, _, message = text.partition("\n\n")
    headers: list[tuple[str, str]] = []
    for line in head.split("\n"):
        if line.startswith(" ") and headers:
            key, value = headers[-1]
            headers[-1] = (key, value + "\n" + line[1:])
        elif line:
            key, _, value = line.partition(" ")
            headers.append((key, value))
    return headers, message


def parse_tag(body: bytes) -> dict[str, str]:
    headers, message = _headers(body)
    fields = dict(headers)
    missing = [k for k in ("object", "type", "tag") if k not in fields]
    if missing:
        raise GitObjectError(f"tag object lacks {','.join(missing)}")
    return {
        "object": fields["object"],
        "type": fields["type"],
        "tag": fields["tag"],
        "tagger": fields.get("tagger", ""),
        "message": message,
    }


def parse_commit(body: bytes) -> dict[str, object]:
    headers, message = _headers(body)
    trees = [v for k, v in headers if k == "tree"]
    if len(trees) != 1:
        raise GitObjectError(f"commit has {len(trees)} tree headers")
    return {
        "tree": trees[0],
        "parents": [v for k, v in headers if k == "parent"],
        "author": next((v for k, v in headers if k == "author"), ""),
        "committer": next((v for k, v in headers if k == "committer"), ""),
        "message": message,
    }


@dataclass(frozen=True, slots=True)
class TreeEntry:
    mode: str
    name: str
    sha: str


def parse_tree(body: bytes) -> tuple[TreeEntry, ...]:
    entries: list[TreeEntry] = []
    i = 0
    while i < len(body):
        space = body.index(b" ", i)
        nul = body.index(b"\0", space)
        if nul + 21 > len(body):
            raise GitObjectError("truncated tree entry")
        mode = body[i:space].decode("ascii")
        name = body[space + 1 : nul].decode("utf-8", errors="surrogateescape")
        entries.append(TreeEntry(mode, name, body[nul + 1 : nul + 21].hex()))
        i = nul + 21
    return tuple(entries)


def _sort_key(entry: TreeEntry) -> bytes:
    name = entry.name.encode("utf-8", errors="surrogateescape")
    return name + b"/" if entry.mode == MODE_TREE else name


def tree_body(entries: Iterable[TreeEntry]) -> bytes:
    out = bytearray()
    for e in sorted(entries, key=_sort_key):
        out += e.mode.encode("ascii") + b" " + e.name.encode("utf-8", errors="surrogateescape") + b"\0"
        out += bytes.fromhex(e.sha)
    return bytes(out)


def tree_sha_of_dir(path: Path, exclude: Iterable[str] = ()) -> str | None:
    """Git tree id of a materialized directory (None when it holds no trackable entry).

    Modes follow git: 100755 when the owner-exec bit is set, 120000 for a symlink (its
    target is the blob), 40000 for a non-empty subdirectory; empty directories vanish.
    ``exclude`` names top-level entries to omit (post-tag additions under the payload).
    """
    skip = set(exclude)
    entries: list[TreeEntry] = []
    for name in sorted(os.listdir(path)):
        if name in skip:
            continue
        child = path / name
        st = os.lstat(child)
        if stat.S_ISLNK(st.st_mode):
            entries.append(TreeEntry(MODE_LINK, name, blob_sha(os.readlink(child).encode("utf-8"))))
        elif stat.S_ISDIR(st.st_mode):
            sub = tree_sha_of_dir(child)
            if sub is not None:
                entries.append(TreeEntry(MODE_TREE, name, sub))
        elif stat.S_ISREG(st.st_mode):
            mode = MODE_EXEC if st.st_mode & stat.S_IXUSR else MODE_FILE
            entries.append(TreeEntry(mode, name, blob_sha(child.read_bytes())))
    if not entries:
        return None
    return object_sha("tree", tree_body(entries))


class RawObjects:
    """Committed raw object bodies, each re-verified against its file-name identity."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.bodies: dict[str, tuple[str, bytes]] = {}
        self.mismatches: list[str] = []
        if not directory.is_dir():
            return
        for path in sorted(directory.glob("*.raw")):
            sha, _, rest = path.name.partition(".")
            kind = rest[: -len(".raw")]
            body = path.read_bytes()
            try:
                actual = object_sha(kind, body)
            except GitObjectError:
                self.mismatches.append(f"{path.name}:unknown-type")
                continue
            if actual != sha:
                self.mismatches.append(f"{path.name}:recomputed={actual}")
                continue
            self.bodies[sha] = (kind, body)

    def get(self, sha: str, kind: str) -> bytes:
        found = self.bodies.get(sha)
        if found is None:
            raise GitObjectError(f"raw {kind} {sha} not committed")
        if found[0] != kind:
            raise GitObjectError(f"raw {sha} is a {found[0]}, not a {kind}")
        return found[1]


def tree_chain(objects: RawObjects, commit_sha: str, path: str) -> list[tuple[str, str]]:
    """[(path-prefix, tree sha), ...] from the commit's root tree down to ``path``.

    Only the final component may be missing from the committed raw objects: its sha is
    read from its parent tree's entry.
    """
    commit = parse_commit(objects.get(commit_sha, "commit"))
    chain = [("", str(commit["tree"]))]
    current = str(commit["tree"])
    parts = [p for p in path.split("/") if p]
    for depth, part in enumerate(parts):
        entries = parse_tree(objects.get(current, "tree"))
        hit = next((e for e in entries if e.name == part), None)
        if hit is None or hit.mode != MODE_TREE:
            raise GitObjectError(f"{'/'.join(parts[: depth + 1])} is not a tree in {current}")
        current = hit.sha
        chain.append(("/".join(parts[: depth + 1]), current))
    return chain
