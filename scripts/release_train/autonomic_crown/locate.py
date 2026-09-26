"""Evidence resolution for the autonomic crown (read-only; no network).

Locators follow the durable grammar (CE23-9, RFC-0005 §6.4) and are parsed by
``scripts.durable_locator``. Resolution is deliberately narrow so the same inputs give
the same bytes on every runner:

* ``git:<root repo>@<sha>:<path>`` -- the root repository's own object database, through
  ``durable_locator.Resolver`` with ``allow_network=False`` (owner-checked origin remote).
* ``git:<foreign repo>@<sha>:<path>`` -- only through an admitted import: an IMPORTS.json
  row with the same (source_repo, source_sha, source_path) whose in-tree copy has git blob
  id ``source_blob_sha1``. Anything else is EVIDENCE_UNRESOLVED.
* ``https://...`` and ``git-notes:...`` -- never fetched: EVIDENCE_UNRESOLVED (not
  recomputable offline).
* anything outside the grammar (absolute, scratch, tmp, home paths) -- LOCATOR_NOT_DURABLE.

A root object database that cannot be reached is TRANSPORT_UNAVAILABLE, never a subject
failure (RFC-0004 §39).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Protocol

from scripts.durable_locator.durable_locator import Refused, Resolver, parse

from .model import ROOT_REPOSITORY


class Unresolved(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}:{detail}")
        self.code = code
        self.detail = detail


class Source(Protocol):
    name: str

    def resolve(self, locator: str) -> bytes: ...


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def load_imports(bases: list[Path]) -> list[tuple[dict[str, Any], bytes]]:
    """Admitted foreign copies: (row, bytes) for every ``<base>/imports/IMPORTS.json`` row."""
    out: list[tuple[dict[str, Any], bytes]] = []
    for base in bases:
        doc_path = base / "imports" / "IMPORTS.json"
        if not doc_path.is_file():
            continue
        for row in json.loads(doc_path.read_text(encoding="utf-8")).get("imports", []):
            copy = base / row["path"]
            if copy.is_file():
                out.append((row, copy.read_bytes()))
    return out


class EvidenceResolver:
    """The production transport: root object DB (local git, read-only) + admitted imports."""

    name = "git-object-db+imports"

    def __init__(
        self,
        repos_root: Path | None,
        imports: list[tuple[dict[str, Any], bytes]],
        root_repository: str = ROOT_REPOSITORY,
    ) -> None:
        self.repos_root = repos_root
        self.imports = imports
        self.root_repository = root_repository

    def resolve(self, locator: str) -> bytes:
        try:
            loc = parse(locator)
        except Refused as exc:
            raise Unresolved("LOCATOR_NOT_DURABLE", f"{exc.code}:{locator}") from None
        if loc.kind != "git":
            raise Unresolved("EVIDENCE_UNRESOLVED", f"{loc.kind} locators are not fetched offline: {locator}")
        assert loc.repository and loc.sha and loc.path
        if loc.repository != self.root_repository:
            for row, data in self.imports:
                if (row.get("source_repo"), row.get("source_sha"), row.get("source_path")) == (
                    loc.repository,
                    loc.sha,
                    loc.path,
                ) and git_blob_id(data) == row.get("source_blob_sha1"):
                    return data
            raise Unresolved("EVIDENCE_UNRESOLVED", f"foreign locator without an admitted import: {locator}")
        if self.repos_root is None:
            raise Unresolved("TRANSPORT_UNAVAILABLE", f"no root object database: {locator}")
        try:
            return Resolver(self.repos_root, allow_network=False).blob(loc.repository, loc.sha, loc.path)
        except Refused as exc:
            if exc.code in ("REPOSITORY_UNAVAILABLE", "OWNER_MISMATCH"):
                raise Unresolved("TRANSPORT_UNAVAILABLE", f"{exc.code}:{locator}") from None
            raise Unresolved("EVIDENCE_UNRESOLVED", f"{exc.code}:{locator}") from None


class FailingTransport:
    """A transport that is down (RFC-0005 §8 TRANSPORT_FAILURE injection): every read fails."""

    name = "transport-down"

    def resolve(self, locator: str) -> bytes:
        raise Unresolved("TRANSPORT_UNAVAILABLE", f"transport down: {locator}")


class ResolverWithOverlay:
    """A transport that serves some locators from given bytes and defers the rest.

    Used by the self-attack to present one tampered or truncated read without editing any
    file; ``reads`` counts reads per locator so a transient fault can fail once only.
    """

    def __init__(self, base: Source, overlay: dict[str, Callable[[int], bytes]], name: str) -> None:
        self.base = base
        self.overlay = overlay
        self.name = name
        self.reads: dict[str, int] = {}

    def resolve(self, locator: str) -> bytes:
        n = self.reads.get(locator, 0)
        self.reads[locator] = n + 1
        if locator in self.overlay:
            return self.overlay[locator](n)
        return self.base.resolve(locator)


class CachingSource:
    """Memoizes reads (bytes and typed failures) of an immutable, content-addressed source."""

    def __init__(self, base: Source) -> None:
        self.base = base
        self.name = base.name
        self._cache: dict[str, bytes | Unresolved] = {}

    def resolve(self, locator: str) -> bytes:
        if locator not in self._cache:
            try:
                self._cache[locator] = self.base.resolve(locator)
            except Unresolved as exc:
                self._cache[locator] = exc
        hit = self._cache[locator]
        if isinstance(hit, Unresolved):
            raise Unresolved(hit.code, hit.detail)
        return hit
