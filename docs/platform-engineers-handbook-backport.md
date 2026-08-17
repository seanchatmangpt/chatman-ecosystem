# The Platform Engineer's Handbook — Ch09 Backport

> **Provenance record.** Companion to
> [`platform-engineers-handbook-ggen-packs.md`](platform-engineers-handbook-ggen-packs.md) (where
> the three Ch09 Crossplane bugs were originally found, fixed, and reverified inside the
> `ggen-marketplace` pack) and
> [`platform-engineers-handbook-colima-runtime.md`](platform-engineers-handbook-colima-runtime.md)
> (the live-cluster runtime record). This document records porting those same three proven fixes
> out of the downstream ggen-marketplace pack and into the real upstream
> [`seanchatmangpt/Platform-Engineer-s-Handbook`](https://github.com/seanchatmangpt/Platform-Engineer-s-Handbook)
> GitHub repository, on a new branch, with a pull request opened.

## Why a backport, not just a pack fix

The three Ch09 bugs (apply-order, RBAC, XRD schema) were found, fixed, and re-verified inside
the `platform-engineers-handbook` ggen pack — see "Pack update (v0.2.0)" and "Pack update
(v0.3.0)" in `platform-engineers-handbook-ggen-packs.md`. That fixed the pack a marketplace
consumer would pull, but left the actual upstream book repository — the thing readers of *The
Platform Engineer's Handbook* clone directly — still shipping the original bugs. This pass ports
the same three fixes upstream.

## Result

**Push access:** yes — authenticated as `seanchatmangpt` with `ADMIN` permission on
`seanchatmangpt/Platform-Engineer-s-Handbook`.

**Branch:** `fix/ch09-crossplane-apply-order-rbac-schema`, branched off `main`, pushed to
`origin`. `main` itself was never checked out or modified directly.

**Commit:** `e441b5e2297665c63f2a5242af19cf98fde0cd66` —
"fix(ch09): resolve Crossplane apply-order, RBAC, and XRD schema bugs"

**PR:** opened at
[github.com/seanchatmangpt/Platform-Engineer-s-Handbook/pull/1](https://github.com/seanchatmangpt/Platform-Engineer-s-Handbook/pull/1).

**Scope:** 5 files changed, 102 insertions(+), 16 deletions(-), all under `Ch09/`.
`git diff --stat` confirmed no files outside `Ch09/` were touched.

## Diff summary per fix

**a. `Ch09/xrd-postgresql.yaml`** (bug: XRD schema out of sync with the claim that uses it) —
added only the `publishConnectionDetailsTo` schema block under `spec.properties`; rest of the
file untouched. Diffed byte-for-byte identical to the `/tmp/pe-project/xrd-postgresql.yaml`
reference after the edit (`diff` returned no output).

**b. `Ch09/crossplane-providers.yaml` + `Ch09/crossplane-provider-configs.yaml`** (bug: apply
order — `Provider` and `ProviderConfig` bundled in one file, `ProviderConfig` failing on first
apply) — replaced the original bundled file (which mixed `Provider`/`ProviderConfig`/
`Function`/`DeploymentRuntimeConfig`) with the fixed version containing only `Provider`/
`DeploymentRuntimeConfig`/`Function`, including the apply-order header comment and `kubectl
wait` commands. Added new `Ch09/crossplane-provider-configs.yaml` holding the two
`ProviderConfig` resources, also with its own header comment. Both files verified
byte-identical to the `/tmp/pe-project/` references.

**c. `Ch09/provider-kubernetes-rbac.yaml`** (bug: missing RBAC for `provider-kubernetes`'s
service account) — new file, copied verbatim from
`/tmp/pe-project/provider-kubernetes-rbac.yaml`, verified byte-identical: a declarative
`ClusterRoleBinding` binding `cluster-admin` to the `system:serviceaccounts:crossplane-system`
group (the same declarative, no-runtime-name-lookup shape shipped in the pack's v0.2.0 update).

**`Ch09/README.md`** — added a "Known Issues Fixed in This Branch" section (placed before
"Code-to-Chapter Mapping") documenting all three fixes in plain language: the exact error
messages a reader hits without the fixes, the apply-order commands for the provider split, and
a note that the book's existing manual workarounds (Step 2.4's `kubectl create
clusterrolebinding`, and the "apply providers file twice" instruction in Phase 2) are the
imperative versions of fixes 1 and 3 and remain compatible with the declarative fix now shipped
alongside them.

## Fixes ported (bug numbering matches the ggen-pack record)

| # | File(s) | Bug | Fix ported |
|---|---|---|---|
| 1 | `crossplane-providers.yaml`, `crossplane-provider-configs.yaml` | `ProviderConfig` applied before its `Provider`'s CRD exists — `no matches for kind "ProviderConfig"` on first apply | Split into two files with documented apply order |
| 2 | `xrd-postgresql.yaml` | Claim schema missing `publishConnectionDetailsTo`, rejected with `strict decoding error: unknown field "spec.publishConnectionDetailsTo"` | Added the field to the XRD's OpenAPI schema |
| 3 | `provider-kubernetes-rbac.yaml` (new) | `provider-kubernetes`'s service account has no RBAC to manage composed resource kinds — `cannot get object: ... is forbidden` | Declarative `ClusterRoleBinding` on the service-account group, no revision-hash lookup needed |

Bug 4 from the ggen-pack record (missing `connectionDetails`-aggregation function for the
pinned `function-patch-and-transform:v0.7.0`) was **not** ported — it was never fixed in the
pack either (see "Not yet done" in `platform-engineers-handbook-ggen-packs.md`); porting an
unfixed bug forward would add nothing.

## What this backport did not do

- Did not install or exercise Crossplane against any live cluster as part of this pass — this
  is a source-repository backport, not a runtime validation. The runtime validation of these
  same three fixes happened separately, against disposable Kind clusters, and is recorded in
  `platform-engineers-handbook-ggen-packs.md` ("Scripts run for real" / "Pack update" sections).
  Crossplane has not been installed on the `kind-platform-eng-colima` cluster that
  `platform-engineers-handbook-colima-runtime.md` documents.
- Did not merge the PR — it was opened, not merged; `main` is unchanged.
- Did not touch any file outside `Ch09/`.

## See also

- [The Platform Engineer's Handbook — ggen Pack](platform-engineers-handbook-ggen-packs.md)
- [The Platform Engineer's Handbook — Running on Colima](platform-engineers-handbook-colima-runtime.md)
