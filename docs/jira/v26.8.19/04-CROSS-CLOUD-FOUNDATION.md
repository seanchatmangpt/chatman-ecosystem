# Cross-Cloud Foundation — Shared P0 Work + Non-Engineering Blockers

## Backward from finished

Every cloud-specific ticket (`01-AWS-MARKETPLACE.md`, `02-AZURE-MARKETPLACE.md`,
`03-GCP-MARKETPLACE.md`) depends on three engineering artifacts existing once, not three times,
plus a set of business/legal artifacts that block submission on every cloud equally. All of it
is finished: the entitlement state machine accepts events from any source, the Helm chart is
fully `.Values`-parameterized, the CI scan-gate runs for real against real registries, and the
EULA/listing-legal content exists and has been adapted to each cloud's format.

## Real state today

### Engineering

- `plan-state.ts` derives state from Stripe subscription state only (per its own documentation)
  — no generic entrypoint for a non-Stripe entitlement event exists yet.
- `chart/platform-console/templates/*.yaml` are real, verified (`helm lint` 0 failures,
  `helm template` renders all 1,599 lines) static copies of the 6 cited raw manifests — but
  `values.yaml`'s `image`/`service`/`ingress`/`autoscaling` keys are placeholders consumed by
  nothing (confirmed by inspection this session, disclosed in the file's own header).
- `.github/workflows/marketplace-scan-publish.yml` exists (generated via `ggen-marketplace`'s
  `marketplace-listing-scaffold-pack`, this session) with build→scan→publish-ECR→publish-ACR
  stages correctly ordered and real GHA `${{ }}` syntax (confirmed by grep), but has never
  executed — `AWS_ECR_PUBLISH_ROLE_ARN` and `AZURE_CREDENTIALS` are referenced secrets that
  don't exist.

### Legal/business

- No EULA text exists anywhere in the repo. `grep -ri "EULA\|end user license"` across the full
  tree returns only unrelated OWL ontology terms and vendored third-party license files —
  checked this session, not assumed.
- No marketing/listing copy (description, categories, support contact) exists in a
  cloud-listing-ready format.

## Backward-chained work items

### 1. `plan-state.ts` generic entitlement adapter — P0, highest leverage
- **Finished:** a real `applyEntitlementEvent(source: 'stripe' | 'aws' | 'azure' | 'gcp',
  event: EntitlementEvent)` entrypoint, with the existing Stripe path refactored to call through
  it rather than special-cased separately, so a fourth cloud's onboarding never means a fourth
  parallel state machine.
- **Gap:** does not exist. Estimated 3-5 days — the single highest-leverage item in the entire
  ticket set, because every one of the nine per-cloud items across `01`/`02`/`03` that touch
  entitlement state depends on this landing first. Build this before any cloud-specific
  adapter's stub methods are filled in.

### 2. Helm chart `.Values` parameterization
- **Finished:** `image.repository`/`.tag`, `service.*`, `ingress.*`, `autoscaling.*` are
  consumed by the 6 templates via real `{{ .Values.* }}` substitution, replacing the current
  static copy.
- **Gap:** the chart wraps all 6 manifests (done this session) but consumes none of
  `values.yaml`'s keys yet. Estimated 1-1.5 weeks given the largest wrapped file
  (`services-and-deployments.yaml`) is 957 raw lines — this is real templating labor across a
  large surface, not a quick pass. This item unblocks Azure's CNAB wrapping and GCP's
  Application CRD wrapping equally; build it once here, not per cloud.

### 3. CI vulnerability-scan + dual-registry publish pipeline
- **Finished:** the generated workflow runs for real in GitHub Actions, with `Trivy` (or
  equivalent) scanning the built image, and real `AWS_ECR_PUBLISH_ROLE_ARN`/`AZURE_CREDENTIALS`
  secrets provisioned, publishing to both a Marketplace-owned ECR repo and a publisher ACR.
- **Gap:** the workflow file's shape is real and generated; the secrets and the actual first run
  do not exist. Estimated 3-4 days once the underlying cloud accounts (item 4 below) exist to
  provision credentials against — this item is gated on the non-engineering track, not purely
  an engineering estimate in isolation.

### 4. Non-engineering blockers — run in parallel with items 1-3, starting day one

Named separately because no amount of code changes this repo's timeline for these:

- **AWS**: AMMP seller profile, W-9 tax interview, Marketplace-specific bank disbursement
  account (distinct from the existing Stripe payout rail), KYC business verification.
- **Azure**: Partner Center account, program enrollment (tax/payout/identity/MPN
  verification).
- **GCP**: MVA partner status, Payments Center banking/tax registration, then Producer Portal
  access request (sequentially gated on partner status, unlike AWS/Azure which can each start
  cold).
- **All three**: EULA drafted by legal (zero starting point exists in this repo today) and
  adapted to each cloud's listing-content format; marketing/support-contact copy.

**Critical parallelization point, carried forward from the original research and unchanged by
anything built this session:** none of the four business-registration processes depend on any
engineering item above completing first, and none of items 1-3 depend on business registration
completing first. Start both tracks simultaneously.

## Revised honest timeline, backward-chained from "finished"

Per this session's own measured ledger on `ggen-marketplace`'s `marketplace-listing-scaffold-pack`
(see that pack's `generated/README.md` and this session's transcript): code-scaffolding
generation compresses from days to under a minute, but that compression applies to a few days
of interface/skeleton authorship at the front of the critical path — not to items 1-3 above (real
implementation labor, not scaffolding) and not at all to the non-engineering track. The
honest total, unchanged in kind from the original research and only revised in scope by what
this session actually closed:

- Items 1-3 (shared engineering): ~2.5-3.5 weeks combined, sequenced roughly 1 → 2/3 in
  parallel.
- Per-cloud engineering (from `01`/`02`/`03`): Azure cheapest (~1.5-2 weeks), AWS next
  (~1-3 weeks), GCP most (~2-6 weeks, plus the disclosed EnvoyFilter decision in `03`).
- Non-engineering, parallel: ~2-4 weeks (business/legal) to ~several weeks (GCP's sequential
  partner-status-then-portal-access gate is the slowest single external step).
- Review queues, sequential to a complete submission per cloud: ~2-6 weeks each, external,
  not compressible.

**Total, all three clouds, engineering run mostly in parallel with the legal/business track:
roughly 6-12 weeks**, matching the figure this session's `ggen-marketplace` speedrun ledger
already arrived at independently — this ticket set is that same number decomposed into concrete,
ordered work items rather than a fresh estimate.

## What gymact/autofde-lab can actuate here today

Nothing in items 1-4. See `05-GYMACT-AUTOFDE-ACTUATION-SCOPE.md` for the one real actuation
surface that does exist (Castle verb execution against the already-shipped platform) and why it
doesn't reach this ticket's work.
