#!/usr/bin/env python3
"""Exact-window repository visibility/activity sensor.

OBSERVE-only. When a token is supplied the sensor verifies the authenticated GitHub
identity and enumerates repositories owned by that identity, including private
repositories visible to the token. Without a token it explicitly degrades to the
public owner endpoint. No mutation endpoint is reachable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

API = "https://api.github.com"
SCHEMA = "chatman.repository-visibility-census/1"
PER_PAGE = 100


class VisibilityError(RuntimeError):
    """Typed refusal or measurement failure."""


@dataclass(frozen=True)
class Window:
    since: datetime
    until: datetime

    def __post_init__(self) -> None:
        if self.since.tzinfo is None or self.until.tzinfo is None:
            raise VisibilityError("REFUSED[WINDOW_TIMEZONE_REQUIRED]")
        if self.since >= self.until:
            raise VisibilityError("REFUSED[INVALID_WINDOW]")

    def contains(self, value: datetime) -> bool:
        return self.since <= value < self.until

    def to_dict(self) -> dict[str, str]:
        return {"since": iso_z(self.since), "until": iso_z(self.until)}


class Sensor(Protocol):
    def owner_repositories(self, owner: str) -> tuple[list[dict[str, Any]], dict[str, Any]]: ...


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise VisibilityError(f"REFUSED[INVALID_TIMESTAMP] value={value}") from exc
    if parsed.tzinfo is None:
        raise VisibilityError(f"REFUSED[TIMESTAMP_TIMEZONE_REQUIRED] value={value}")
    return parsed.astimezone(timezone.utc)


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


class GitHubVisibilityClient:
    """Read-only GitHub sensor; token changes visibility, never authority."""

    def __init__(self, token: str | None = None, api_url: str = API, timeout: float = 30.0) -> None:
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    def _request(self, path: str) -> Any:
        url = path if path.startswith("http") else f"{self.api_url}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "chatman-repository-visibility-census/1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise VisibilityError(f"GitHub HTTP {exc.code} for {url}: {body[:400]}") from exc
        except urllib.error.URLError as exc:
            raise VisibilityError(f"GitHub transport failed for {url}: {exc.reason}") from exc

    def _paginate(self, path: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        separator = "&" if "?" in path else "?"
        for page in range(1, 101):
            payload = self._request(f"{path}{separator}per_page={PER_PAGE}&page={page}")
            if not isinstance(payload, list):
                raise VisibilityError("REFUSED[REPOSITORY_SENSOR_NON_LIST]")
            if not payload:
                return rows
            rows.extend(row for row in payload if isinstance(row, dict))
            if len(payload) < PER_PAGE:
                return rows
        raise VisibilityError("REFUSED[REPOSITORY_PAGINATION_UNBOUNDED]")

    def owner_repositories(self, owner: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if self.token:
            identity = self._request("/user")
            login = identity.get("login") if isinstance(identity, dict) else None
            if not isinstance(login, str):
                raise VisibilityError("REFUSED[AUTHENTICATED_IDENTITY_MISSING]")
            if login.casefold() != owner.casefold():
                raise VisibilityError(
                    f"REFUSED[AUTHENTICATED_OWNER_MISMATCH] expected={owner} observed={login}"
                )
            rows = self._paginate("/user/repos?affiliation=owner&sort=full_name&direction=asc")
            return rows, {
                "visibility_scope": "AUTHENTICATED_OWNER",
                "authenticated_owner": login,
                "private_repository_visibility": "AVAILABLE_TO_TOKEN",
            }

        quoted = urllib.parse.quote(owner, safe="")
        rows = self._paginate(
            f"/users/{quoted}/repos?type=owner&sort=full_name&direction=asc"
        )
        return rows, {
            "visibility_scope": "PUBLIC_ONLY",
            "authenticated_owner": None,
            "private_repository_visibility": "UNAVAILABLE",
        }


def build_census(sensor: Sensor, *, owner: str, window: Window) -> dict[str, Any]:
    rows, scope = sensor.owner_repositories(owner)
    active: list[dict[str, Any]] = []
    malformed = 0
    private_observed = 0

    for row in rows:
        full_name = row.get("full_name")
        pushed_at = row.get("pushed_at")
        private = row.get("private")
        if not isinstance(full_name, str) or not full_name.casefold().startswith(f"{owner}/".casefold()):
            malformed += 1
            continue
        if not isinstance(private, bool):
            malformed += 1
            continue
        if private:
            private_observed += 1
        if not isinstance(pushed_at, str):
            continue
        try:
            pushed = parse_time(pushed_at)
        except VisibilityError:
            malformed += 1
            continue
        if window.contains(pushed):
            active.append(
                {
                    "full_name": full_name,
                    "private": private,
                    "pushed_at": iso_z(pushed),
                }
            )

    active.sort(key=lambda row: row["full_name"].casefold())
    authenticated = scope["visibility_scope"] == "AUTHENTICATED_OWNER"
    observation = {
        "schema": SCHEMA,
        "owner": owner,
        "window": window.to_dict(),
        "scope": scope,
        "measurement": {
            "observed_repository_rows": len(rows),
            "private_repository_rows_observed": private_observed,
            "malformed_rows": malformed,
            "active_repository_count": len(active),
            "active_private_repository_count": sum(1 for row in active if row["private"]),
            "active_repositories": active,
        },
        "standing": "PARTIAL_ALIVE" if authenticated else "OBSERVED",
        "claim_ceiling": (
            "OBSERVED_AUTHENTICATED_OWNER_PUSH_ACTIVITY"
            if authenticated
            else "OBSERVED_PUBLIC_OWNER_PUSH_ACTIVITY"
        ),
        "exclusions": [
            "issue-only activity",
            "workflow-only activity without repository push",
            "local/unpushed work",
            "repositories not visible to the admitted credential scope",
        ],
    }
    digest = hashlib.sha256(canonical_bytes(observation)).hexdigest()
    return {
        **observation,
        "receipt": {
            "algorithm": "sha256",
            "observation_digest": digest,
            "replay": "remove receipt, canonicalize JSON, and require exact digest equality",
        },
    }


def verify_receipt(census: Mapping[str, Any]) -> bool:
    receipt = census.get("receipt")
    if not isinstance(receipt, Mapping):
        return False
    expected = receipt.get("observation_digest")
    if not isinstance(expected, str):
        return False
    observation = dict(census)
    observation.pop("receipt", None)
    return hashlib.sha256(canonical_bytes(observation)).hexdigest() == expected


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", default="seanchatmangpt")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--until")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--output", type=Path, default=Path(".artifacts/repository-visibility/census.json"))
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args(argv)

    if args.replay:
        payload = json.loads(args.replay.read_text(encoding="utf-8"))
        if verify_receipt(payload):
            print(f"ALIVE:REPOSITORY_VISIBILITY_REPLAY digest={payload['receipt']['observation_digest']}")
            return 0
        print("REFUSED[REPOSITORY_VISIBILITY_REPLAY_MISMATCH]", file=sys.stderr)
        return 2
    if args.days <= 0:
        print("REFUSED[INVALID_WINDOW_DAYS]", file=sys.stderr)
        return 2

    until = parse_time(args.until) if args.until else datetime.now(timezone.utc)
    window = Window(until=until, since=until - timedelta(days=args.days))
    token = os.getenv(args.token_env) or None
    try:
        census = build_census(GitHubVisibilityClient(token=token), owner=args.owner, window=window)
    except VisibilityError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    write_json(args.output, census)
    measurement = census["measurement"]
    print(
        f"{census['standing']}:REPOSITORY_VISIBILITY_CENSUS "
        f"scope={census['scope']['visibility_scope']} "
        f"active={measurement['active_repository_count']} "
        f"active_private={measurement['active_private_repository_count']} "
        f"digest={census['receipt']['observation_digest']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
