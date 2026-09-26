"""Workflow scan (stdlib, line-based; no YAML dependency): U-13, U-16 exit policy, U-17.

U-13 (RFC-0005 §7, §9): every ``uses:`` pinned by a 40-hex commit; no floating runner
label (``*-latest``, or a hosted image label that the provider updates in place --
RFC-0005 §12 asks for an image digest); every ``python-version`` exact ``X.Y.Z``; every
``container``/``image`` pinned by ``@sha256:``.

U-16 gap (§12): an exit policy that turns a typed BLOCKED (exit 3) into a warning.

U-17 (§7 note 4): the controller survives removal of the primary schedule only if an
unconditional machine trigger remains (``push`` without ``paths``, ``workflow_run``,
``repository_dispatch``). ``workflow_dispatch`` is a human trigger; ``pull_request`` is
not a controller cycle; a path-filtered ``push`` fires only on matching changes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_USES = re.compile(r"^\s*(?:-\s+)?uses:\s*['\"]?([^\s'\"#]+)")
_RUNS_ON = re.compile(r"^\s*runs-on:\s*['\"]?([^\s'\"#]+)")
_PYTHON = re.compile(r"^\s*python-version:\s*['\"]?([^\s'\"#]+)")
_IMAGE = re.compile(r"^\s*(?:image|container):\s*['\"]?([^\s'\"#{}]+)")
_CRON = re.compile(r"^\s*-\s*cron:\s*")
_WARN_ON_BLOCKED = re.compile(r"^\s*3\)\s*echo\s+\"::warning")
_SHA_REF = re.compile(r"@[0-9a-f]{40}$")
_EXACT_PY = re.compile(r"^\d+\.\d+\.\d+$")
# Hosted runner labels: the provider replaces the image behind the label (floating).
_HOSTED = re.compile(r"^(ubuntu|windows|macos)-")
MACHINE_TRIGGERS = ("push", "workflow_run", "repository_dispatch")


@dataclass
class Scan:
    violations: list[str] = field(default_factory=list)  # U-13 "<code>:<line>:<value>"
    schedulers: int = 0
    triggers: dict[str, dict[str, bool]] = field(default_factory=dict)  # name -> {"paths": bool}
    warns_on_blocked: bool = False

    @property
    def independent_triggers(self) -> list[str]:
        return sorted(t for t, f in self.triggers.items() if t in MACHINE_TRIGGERS and not f["paths"])

    def as_dict(self) -> dict[str, object]:
        return {
            "violations": list(self.violations),
            "schedulers": self.schedulers,
            "triggers": {k: dict(v) for k, v in sorted(self.triggers.items())},
            "independent_triggers": self.independent_triggers,
            "warns_on_blocked": self.warns_on_blocked,
        }


def scan(text: str) -> Scan:
    out = Scan()
    in_on = False
    current: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.rstrip()
        if re.match(r"^on:\s*$", line):
            in_on = True
            continue
        if in_on:
            if line and not line.startswith(" "):
                in_on = False
            else:
                top = re.match(r"^  ([a-z_]+):", line)
                if top:
                    current = top.group(1)
                    out.triggers.setdefault(current, {"paths": False})
                elif current and re.match(r"^\s{4,}paths(-ignore)?:", line):
                    out.triggers[current]["paths"] = True
                if _CRON.match(line):
                    out.schedulers += 1
                continue
        m = _USES.match(stripped)
        if m and not m.group(1).startswith("./") and not _SHA_REF.search(m.group(1)):
            out.violations.append(f"UNPINNED_ACTION:{number}:{m.group(1)}")
        m = _RUNS_ON.match(stripped)
        if m:
            label = m.group(1)
            if label.endswith("-latest"):
                out.violations.append(f"FLOATING_RUNNER:{number}:{label}")
            elif _HOSTED.match(label):
                out.violations.append(f"HOSTED_RUNNER_IMAGE_MUTABLE:{number}:{label}")
        m = _PYTHON.match(stripped)
        if m and not _EXACT_PY.match(m.group(1)):
            out.violations.append(f"INEXACT_TOOLCHAIN:{number}:{m.group(1)}")
        m = _IMAGE.match(stripped)
        if m and "@sha256:" not in m.group(1):
            out.violations.append(f"UNPINNED_CONTAINER:{number}:{m.group(1)}")
        if _WARN_ON_BLOCKED.match(line):
            out.warns_on_blocked = True
    return out
