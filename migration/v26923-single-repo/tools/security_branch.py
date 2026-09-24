#!/usr/bin/env python3
"""Build the key-rotation commit on origin/<default> without touching the working tree (temp index + commit-tree).

usage: security_branch.py <repo> <default_ref> <branch>
Removes every tracked `.ggen/keys/signing.key`, ensures `.gitignore` ignores `.ggen/keys/signing.key`, adds
docs/security/ggen-signing-keys-v26.9.23.md (fingerprints + reclassification), and points refs/heads/<branch> at the commit.
"""
import hashlib
import os
import subprocess
import sys


def git(repo, *a, env=None, input=None):
    p = subprocess.run(["git", "-C", repo, *a], capture_output=True, env=env, input=input)
    return p.returncode, p.stdout.decode(errors="replace").rstrip(), p.stderr.decode(errors="replace").strip(), p.stdout


def main():
    repo, base, branch = sys.argv[1:4]
    name = os.path.basename(repo)
    idx = f"/private/tmp/claude-501/secbranch-{name}.index"
    if os.path.exists(idx):
        os.remove(idx)
    env = dict(os.environ, GIT_INDEX_FILE=idx)
    git(repo, "read-tree", base, env=env)
    files = git(repo, "ls-tree", "-r", "--name-only", base)[1].splitlines()
    keys = [f for f in files if f.endswith(".ggen/keys/signing.key")]
    rows = []
    for k in keys:
        blob = git(repo, "show", f"{base}:{k}")[3]
        v = k[: -len("signing.key")] + "verifying.key"
        vb = git(repo, "show", f"{base}:{v}")[3] if v in files else b""
        rows.append(f"| `{k}` | `{hashlib.sha256(blob).hexdigest()}` | `{hashlib.sha256(vb).hexdigest() if vb else '-'}` |")
        git(repo, "rm", "-q", "--cached", "--", k, env=env)
    gi = git(repo, "show", f"{base}:.gitignore")[3].decode() if ".gitignore" in files else ""
    rule = ".ggen/keys/signing.key"
    probe = subprocess.run(["git", "-C", repo, "check-ignore", "--no-index", "-q", rule], capture_output=True)
    if rule not in gi:
        gi = gi + ("" if gi.endswith("\n") or not gi else "\n") + (
            "# ggen receipt-signing private keys are per-checkout credentials: never commit them (security, 2026-09-24)\n"
            ".ggen/keys/signing.key\n**/.ggen/keys/signing.key\n")
        sha = git(repo, "hash-object", "-w", "--stdin", input=gi.encode())[1]
        git(repo, "update-index", "--add", "--cacheinfo", f"100644,{sha},.gitignore", env=env)
    note = ("# Compromised ggen receipt-signing keys (v26.9.23)\n\n"
            "Recorded 2026-09-24 (operator security item, single-repo migration). These private ed25519 seeds were committed to this\n"
            "PUBLIC repository's default branch, so they are compromised: every receipt signed with them carries NO signing authority\n"
            "(standing of such signatures: REFUSED, broken_term R_missing_authority). This commit removes them from the tree (history is\n"
            "not rewritten; no force-push) and ignores `.ggen/keys/signing.key`; the next `ggen` run generates a fresh, untracked\n"
            "keypair (rotation). ggen is being fixed to write `.ggen/keys/.gitignore` itself so the class cannot recur.\n\n"
            "| private key path (removed) | sha256 of the compromised private key file | sha256 of its public verifying.key |\n|---|---|---|\n"
            + "\n".join(rows) + "\n")
    nsha = git(repo, "hash-object", "-w", "--stdin", input=note.encode())[1]
    git(repo, "update-index", "--add", "--cacheinfo", f"100644,{nsha},docs/security/ggen-signing-keys-v26.9.23.md", env=env)
    tree = git(repo, "write-tree", env=env)[1]
    msg = ("security(v26.9.23): rotate out the committed ggen receipt-signing private key\n\n"
           f"{len(keys)} tracked .ggen/keys/signing.key file(s) (ed25519 private seed) on the default branch of this public repository\n"
           "are removed (history not rewritten, no force-push), .gitignore now ignores .ggen/keys/signing.key, and the key\n"
           "fingerprints plus the reclassification of the receipts they signed (no signing authority) are recorded in\n"
           "docs/security/ggen-signing-keys-v26.9.23.md. Built on the default branch without touching the working tree.\n")
    c = git(repo, "commit-tree", tree, "-p", git(repo, "rev-parse", base)[1], "-m", msg)[1]
    git(repo, "update-ref", f"refs/heads/{branch}", c)
    os.remove(idx)
    changed = git(repo, "diff", "--name-status", base, c)[1]
    print(f"{name}: {branch} -> {c[:10]}\n{changed}")


if __name__ == "__main__":
    main()
