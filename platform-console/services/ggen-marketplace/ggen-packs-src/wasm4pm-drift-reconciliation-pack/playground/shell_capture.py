#!/usr/bin/env python3
"""Shared shell-capture helper.

Extracted from verify.py's `check_command_output_matches` to de-duplicate the
`subprocess.run(cmd, shell=True, cwd=repo, capture_output=True, text=True,
timeout=...)` + stdout/stderr-combine pattern that also appears, independently,
in ggen-legacy's tools/v26.8.20/observe_contract.py.

ggen-legacy requires ticket-gated admission for new executable/imported code
(AGENTS.md: "Nothing executable is admitted without a deterministic ticket").
No such ticket exists for this refactor, so observe_contract.py is left
un-imported from here -- a cross-repo `sys.path` import into a ticket-gated
repo would itself be a new admission, not a cleanup. This module lives only in
wasm4pm-drift-reconciliation-pack, which has no such restriction, and is the
single real implementation `verify.py` now uses.
"""
import subprocess


def run_shell_capture(cmd: str, cwd, timeout: int) -> tuple[int, str]:
    """Run `cmd` via the shell with cwd=cwd, return (exit_code, combined_stdout_stderr)."""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )
    return result.returncode, result.stdout + result.stderr
