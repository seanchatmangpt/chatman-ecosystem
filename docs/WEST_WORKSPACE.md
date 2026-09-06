# Zephyr West federated workspace

`chatman-ecosystem` is the manifest repository for a Zephyr West workspace. West supplies the multi-repository materialization layer; it does not collapse repository identities and it does not grant actuation authority.

## Boundaries

The workspace has three different identity surfaces:

1. `west.yml` — development/workspace membership and floating revisions.
2. `release/v26.9.1/manifest.toml` — admitted release components and exact release SHAs.
3. receipts/Crown — execution evidence and standing.

Therefore:

```text
workspace HEAD != admitted release SHA != ALIVE
```

A West update is source materialization. A West freeze is construction of an exact snapshot. Neither operation grants external DO authority or standing.

## Workspace shape

Initialize with the manifest repository as a local manifest:

```bash
mkdir chatman-workspace
cd chatman-workspace
git clone https://github.com/seanchatmangpt/chatman-ecosystem.git
west init -l chatman-ecosystem
west update
```

The resulting topology is:

```text
chatman-workspace/
  .west/
  chatman-ecosystem/       # manifest/control-plane repository
  projects/                # canonical independently owned Git repositories
  portfolio/               # inactive-by-default public owned portfolio
  corpus/                  # external pattern/candidate repositories
```

Every `projects/*` and `corpus/*` checkout is an ordinary independent Git repository.

## DfCM group topology

The manifest preserves more possibilities than it materializes by default. `portfolio`, `external`, `rejected`, and `unsupported` are disabled through West's group filter. They remain represented and can be selected explicitly.

Examples:

```bash
west list
west list --all
west config manifest.group-filter +portfolio,-external,-rejected,-unsupported
west update
west config manifest.group-filter +portfolio,+external,-rejected,-unsupported
west update
```

The same project can belong to multiple orthogonal groups such as `core`, `manufacture`, `gym`, `process`, `formal`, or `release-v26-9-1`; directory placement is not the ontology.

## West feature surface

The manifest deliberately exercises West's mature composition features where they preserve lawful options:

- manifest schema versioning;
- repository-local `self` imports for federated graph layers;
- remotes and defaults;
- project descriptions;
- `repo-path` for names that differ from GitHub coordinates;
- shallow clone depth for external corpus repositories;
- group filters and multi-group membership;
- project `userdata` for Chateco/release correspondence;
- project submodule recursion for a nested composition root;
- manifest repository `self.path` and extension commands;
- built-in `list`, `status`, `diff`, `compare`, `grep`, `forall`, `manifest --resolve`, and `manifest --freeze` flows.

Repository-local `self` imports are deliberately used to preserve a larger reversible graph without making it the default hydration set. `west/20-public-portfolio.yml` + `west/21-public-portfolio.yml` records the observed public owned portfolio behind the disabled `portfolio` group; `west/30-external-corpus.yml` records donor/candidate/rejected/unsupported external topology behind disabled corpus groups. The root keeps release-bearing and catalog-owned composition projects. Maximum feature usage is therefore bounded by semantic preservation rather than feature-count theater.

## Public and private portfolio boundary

The public GitHub inventory observed on 2026-09-06 contains 308 public repositories. West preserves that public surface without hydrating it by default. Repositories not already represented as canonical root projects are imported as `portfolio-*` projects under `portfolio/<repo>`.

Private repository discovery is deliberately **not projected into this public repository**. Private composition belongs in a local/private extension manifest and must be admitted under an authority boundary that can publish those names. Observation of a private repository is not authority to disclose it.

## SELECT: inspect the frontier

The extension command is non-actuating:

```bash
west dfcm-plan
west dfcm-plan --group manufacture
west dfcm-plan --all --json
```

It emits `PARTIAL_ALIVE` because workspace selection is not execution proof.

## CONSTRUCT: freeze an exact workspace

After the desired projects are cloned:

```bash
west dfcm-freeze
```

By default the command refuses a dirty workspace and writes:

```text
.artifacts/west/frozen.yml
.artifacts/west/freeze-receipt.json
```

The receipt binds the frozen manifest SHA-256 and records `CONSTRUCT_ONLY`, `actuation=none`. Use `west manifest --freeze` directly when no Chateco receipt is required.

## Built-in cross-repository operations

Examples:

```bash
west status
west diff
west compare
west grep 'Brokered Receipted Consequence Execution'
west forall -c 'git status --short --branch'
west manifest --resolve
west manifest --freeze -o .artifacts/west/native-frozen.yml
```

These are observations or workspace-local operations. Any consequential external mutation must still traverse the repository's BRCE path and produce the appropriate receipt.

## Existing Git submodules

The two `platform-console/services/*` submodules remain because they currently encode a component-local composition dependency. West now provides workspace membership in parallel:

```text
West project = workspace membership/materialization
Git submodule = intrinsic component source-composition edge
```

Removing or relocating those gitlinks requires separate evidence that `platform-console` no longer depends on their existing paths.

## Verification

Install West and run:

```bash
python3 scripts/verify_west_workspace.py
```

The verifier checks:

- every release component has a corresponding West project;
- each embedded release SHA agrees with the admitted release manifest;
- project names and paths are unique;
- existing submodule repositories are represented in West;
- DfCM/West feature policy remains explicit;
- import, submodule, shallow-clone, and `repo-path` features are actually exercised;
- all 308 public repositories observed on 2026-09-06 remain represented either as `self`, canonical projects, or inactive portfolio projects;
- the default active frontier remains release-bounded rather than expanding merely because more possibilities are known.

This proves the workspace correspondence boundary only. It does not promote ecosystem Crown standing.
