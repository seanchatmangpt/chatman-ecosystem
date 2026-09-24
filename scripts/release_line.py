#!/usr/bin/env python3
"""Resolve the Chatman release line a tool targets (CE23-7 version fence).

No Chatman tool carries its own literal release directory. A tool's inputs
resolve, first match wins, from:

  1. an explicit ``--release vYY.M.D`` (canonicalized by the one calendar law,
     ``verify_calendar_release.canonical_release``: no zero padding, real date);
  2. the ``release/vYY.M.D/`` directory of an explicit ``--manifest``;
  3. the declared pointer ``catalog/west.toml [boundaries].release_manifest``.

Companion inputs (fleet policy, fan-out bootstrap, role crosswalk) resolve from
the manifest's own release directory, never from a different line.

Typed refusals (``ReleaseLineError``; the message starts with the code):

  RELEASE_LINE_INVALID     the --release value is not a calendar vYY.M.D
  RELEASE_POINTER_MISSING  catalog/west.toml declares no [boundaries].release_manifest
  RELEASE_TARGET_CONFLICT  an explicit input is bound to a line other than --release
  RELEASE_TARGET_UNBOUND   --release was given with an input outside release/vYY.M.D/
  RELEASE_INPUT_MISSING    the resolved input file does not exist
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_calendar_release import VERSION_RE, canonical_release  # noqa: E402

CATALOG = Path("catalog/west.toml")


class ReleaseLineError(ValueError):
    """A typed release-line refusal; str(error) starts with its code."""


def canonical(release: str) -> str:
    """Return the canonical directory name vYY.M.D of a release value."""
    try:
        name, _ = canonical_release(release)
    except ValueError as exc:
        raise ReleaseLineError(f"RELEASE_LINE_INVALID:{release}") from exc
    return name


def declared_manifest(root: Path = Path(".")) -> Path:
    """The manifest the catalog pointer declares, relative to ``root``."""
    policy = tomllib.loads((root / CATALOG).read_text(encoding="utf-8"))
    pointer = policy.get("boundaries", {}).get("release_manifest")
    if not isinstance(pointer, str) or not pointer:
        raise ReleaseLineError(f"RELEASE_POINTER_MISSING:{CATALOG.as_posix()}")
    return Path(pointer)


def release_dir(release: str | None = None, root: Path = Path(".")) -> Path:
    if release:
        return Path("release") / canonical(release)
    return declared_manifest(root).parent


def release_file(name: str, release: str | None = None, root: Path = Path(".")) -> Path:
    return release_dir(release, root) / name


def version_from_path(manifest_path: Path) -> str | None:
    """The YY.M.D version bound by the input's release/<vYY.M.D>/ directory, else None."""
    parent = Path(manifest_path).parent
    name = parent.name
    if parent.parent.name != "release" or not name.startswith("v") or not VERSION_RE.fullmatch(name):
        return None
    try:
        if canonical(name) != name:
            return None
    except ReleaseLineError:
        return None
    return name[1:]


def bind(path: Path, release: str | None) -> Path:
    """Admit an explicit input path against an explicit --release (if any)."""
    if release is None:
        return path
    wanted = canonical(release)[1:]
    bound = version_from_path(path)
    if bound is None:
        raise ReleaseLineError(f"RELEASE_TARGET_UNBOUND:{path.as_posix()} is not under release/v{wanted}/")
    if bound != wanted:
        raise ReleaseLineError(f"RELEASE_TARGET_CONFLICT:{path.as_posix()} is bound to v{bound}, --release is v{wanted}")
    return path


def resolve_manifest(release: str | None, manifest: Path | None, root: Path = Path(".")) -> Path:
    if manifest is not None:
        return bind(manifest, release)
    return release_file("manifest.toml", release, root)


def companion(manifest_path: Path, name: str, explicit: Path | None = None, release: str | None = None) -> Path:
    """A sibling input of the manifest: explicit (bound to --release) or the manifest's own directory.

    An explicit sibling bound to a different release directory than the manifest is a
    cross-line mix and is refused even without --release.
    """
    if explicit is None:
        return manifest_path.parent / name
    bind(explicit, release)
    line, other = version_from_path(manifest_path), version_from_path(explicit)
    if line is not None and other is not None and line != other:
        raise ReleaseLineError(
            f"RELEASE_TARGET_CONFLICT:{explicit.as_posix()} is bound to v{other}, the manifest to v{line}"
        )
    return explicit


def require(path: Path, root: Path = Path(".")) -> Path:
    if not (root / path).is_file():
        raise ReleaseLineError(f"RELEASE_INPUT_MISSING:{path.as_posix()}")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the release directory a tool would target.")
    parser.add_argument("--release")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        print(release_dir(args.release, args.root).as_posix())
    except ReleaseLineError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
