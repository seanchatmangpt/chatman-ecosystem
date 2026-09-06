"""Chatman Ecosystem West extensions.

These commands are intentionally SELECT/CONSTRUCT only. They never grant or exercise
external DO authority. Consequential actuation remains behind the repository's BRCE
boundary.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from west.commands import WestCommand


def _project_record(project: Any) -> dict[str, Any]:
    userdata = project.userdata if isinstance(project.userdata, dict) else {}
    return {
        "name": project.name,
        "path": project.path,
        "revision": project.revision,
        "url": project.url,
        "groups": list(project.groups or []),
        "description": project.description,
        "userdata": userdata,
    }


def _is_dirty(project: Any) -> bool:
    abspath = getattr(project, "abspath", None)
    if not abspath or not Path(abspath).is_dir():
        return False
    proc = subprocess.run(
        ["git", "-C", str(abspath), "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0 and bool(proc.stdout.strip())


class DfcmPlan(WestCommand):
    def __init__(self) -> None:
        super().__init__(
            "dfcm-plan",
            "select a reversible workspace frontier without actuation",
            "Select and inspect the largest bounded lawful West project frontier.",
            accepts_unknown_args=False,
        )

    def do_add_parser(self, parser_adder: Any) -> Any:
        parser = parser_adder.add_parser(
            self.name,
            help=self.help,
            description=self.description,
        )
        parser.add_argument("projects", nargs="*", help="optional project names")
        parser.add_argument(
            "--group",
            action="append",
            default=[],
            help="retain projects belonging to this group; repeatable",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="include inactive projects instead of honoring the manifest group filter",
        )
        parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
        return parser

    def do_run(self, args: Any, unknown_args: list[str]) -> None:
        projects = list(self.manifest.projects)[1:]
        requested = set(args.projects)
        groups = set(args.group)

        if requested:
            projects = [project for project in projects if project.name in requested]

        if groups:
            projects = [
                project
                for project in projects
                if groups.intersection(set(project.groups or []))
            ]

        if not args.all:
            projects = [
                project
                for project in projects
                if self.manifest.is_active(project)
            ]

        records = [_project_record(project) for project in projects]
        payload = {
            "status": "PARTIAL_ALIVE",
            "authority": "SELECT_ONLY",
            "actuation": "none",
            "project_count": len(records),
            "projects": records,
        }

        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
            return

        print("PARTIAL_ALIVE SELECT_ONLY actuation=none")
        for record in records:
            group_text = ",".join(record["groups"])
            print(f"{record['name']:32} {record['path']:48} [{group_text}]")


class DfcmFreeze(WestCommand):
    def __init__(self) -> None:
        super().__init__(
            "dfcm-freeze",
            "construct an exact-SHA frozen manifest and local receipt",
            "Freeze cloned projects to exact SHAs without external actuation.",
            accepts_unknown_args=False,
        )

    def do_add_parser(self, parser_adder: Any) -> Any:
        parser = parser_adder.add_parser(
            self.name,
            help=self.help,
            description=self.description,
        )
        parser.add_argument(
            "--output",
            default=".artifacts/west/frozen.yml",
            help="frozen manifest output path relative to the workspace topdir",
        )
        parser.add_argument(
            "--receipt",
            default=".artifacts/west/freeze-receipt.json",
            help="receipt output path relative to the workspace topdir",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="freeze inactive projects too; requires them to be cloned",
        )
        parser.add_argument(
            "--allow-dirty",
            action="store_true",
            help="allow a frozen snapshot when a cloned project has uncommitted changes",
        )
        return parser

    def do_run(self, args: Any, unknown_args: list[str]) -> None:
        projects = list(self.manifest.projects)[1:]
        selected = projects if args.all else [p for p in projects if self.manifest.is_active(p)]
        dirty = [project.name for project in selected if _is_dirty(project)]
        if dirty and not args.allow_dirty:
            joined = ",".join(sorted(dirty))
            raise RuntimeError(f"REFUSED:DIRTY_WORKSPACE:{joined}")

        frozen = self.manifest.as_frozen_yaml(active_only=not args.all)
        topdir = Path(self.topdir)
        output = topdir / args.output
        receipt = topdir / args.receipt
        output.parent.mkdir(parents=True, exist_ok=True)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(frozen, encoding="utf-8")

        digest = hashlib.sha256(frozen.encode("utf-8")).hexdigest()
        receipt_payload = {
            "schema": "chateco-west-freeze-receipt/v1",
            "status": "PARTIAL_ALIVE",
            "authority": "CONSTRUCT_ONLY",
            "actuation": "none",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "workspace_topdir": str(topdir),
            "project_count": len(selected),
            "frozen_manifest": str(output),
            "sha256": digest,
            "dirty_projects": sorted(dirty),
        }
        receipt.write_text(
            json.dumps(receipt_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(receipt_payload, indent=2, sort_keys=True))
