# Chatman Ecosystem Constitution

## Purpose

The repository governs identities, relationships, policies, evidence, and standing across independently releasable projects. It is a control plane, not a source-code monorepo.

## Equation

`A = μ(O*)`

- `O*`: bounded and admitted observation.
- `μ`: lawful manufacturing under explicit authority.
- `A`: artifact with evidence-backed standing.

## Non-negotiable laws

1. **Zero unreceipted actuation.** Every consequential mutation produces a replayable receipt.
2. **Broker-only DO.** Adapters submit intentions; the authority broker decides whether an actuation is lawful.
3. **Exact subject.** Standing applies to a specific commit, file digest, document revision, or external artifact digest.
4. **Evidence before standing.** `ALIVE` is calculated from required gates; it is not assigned by narrative.
5. **Canonical source before projection.** TOML and source code are authoritative; generated Markdown is disposable.
6. **Framework independence.** No runtime, database, protocol, or connector framework owns constitutional identity, authority, standing, or receipts.
7. **Refusal is behavior.** Invalid, malformed, stale, duplicate, unauthorized, conflicting, and tampered inputs require typed refusal tests.
8. **Caches are acceleration.** Exact-SHA artifacts may transfer one candidate; caches never prove correctness.
9. **Repository is not project.** Program, project, repository, document, automation, transition, and receipt are distinct identities.
10. **Capability is not authority.** Tool access and credentials do not grant permission.

## Standing vocabulary

`UNKNOWN`, `OBSERVED`, `CANDIDATE`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `UNSUPPORTED`, `REJECTED`, `SUPERSEDED`.

A component is `ALIVE` only when vocabulary, positive behavior, negative behavior, integration, exact-head verification, persisted evidence, receipt integrity, replay, exclusions, and drift checks all pass.

## Crown

`CROWN = ALIVE` if and only if every required rail is `ALIVE`, every rail names the same exact subject, every receipt verifies, projections are current, architecture boundaries hold, and exact-head CI succeeds.
