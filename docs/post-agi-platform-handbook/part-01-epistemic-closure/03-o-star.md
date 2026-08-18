# 3. O*.toml and the Admitted Subject

A post-AGI platform needs a concrete carrier for the exact subject it is about to manufacture or actuate against. In the Chatman Ecosystem vocabulary, `O*.toml` is the archetype of that carrier.

The file is not important because TOML is special. TOML is merely a readable deterministic serialization. The constitutional object is the admitted subject.

## What the carrier must bind

An admitted subject should make accidental scope widening difficult. A useful carrier binds at least:

- subject identity;
- repository, artifact, resource, or external object coordinate;
- exact revision or digest where available;
- observation evidence and timestamps;
- policy and ontology versions;
- environment and toolchain identities when execution depends on them;
- allowed authority class;
- expected postconditions;
- refusal conditions;
- replay identity.

A conceptual profile might look like:

```toml
[subject]
id = "service:payments-api"
repository = "owner/payments"
commit = "<40-character-sha>"

[admission]
state = "CANDIDATE"
ontology = "platform:v3"
policy = "prod-deploy:v9"

[authority]
class = "CONSTRUCT"
allow_do = false

[verification]
expected = ["tests", "policy", "integration"]
```

The example is intentionally incomplete. A real profile is domain-specific and must be validated by its owning schema.

## Deterministic tickets

A human ticket can say, “Deploy the latest safe version.” That is useful intent but not a deterministic operational subject.

A deterministic ticket resolves “latest,” “safe,” “version,” target environment, admissible evidence, and required authority before DO.

This prevents a common post-AGI failure mode: a highly capable system satisfies the semantics of a sentence while changing a different exact object than the requester intended.

## Environment identity matters

Software standing is contextual. A verifier proven against one source SHA, toolchain, configuration, and environment does not automatically crown another.

A Capsule ALIVE model therefore separates:

\[
Source \times Validator \times Toolchain \times Config \times Environment
\]

Reusing a verifier is lawful only when the identities required by that verifier remain equivalent. The subject still needs its own execution evidence.

## O* is not a permission slip

The most important property of the admitted carrier is what it does **not** do.

It does not grant ambient DO authority.

`O*` makes the subject precise enough to reason about. The authority broker still decides whether a consequential operation is lawful. This preserves the separation between epistemic admission and operational admission.

## Falsifier

If changing a branch name, deployment UID, account, or digest can leave the admitted subject apparently unchanged, the carrier is too weak for exact-subject actuation.

## Operational exercise

Take the most consequential command in a platform workflow and ask whether its exact subject could be reconstructed from the inputs and receipt six months later. If not, design the missing admitted carrier before adding more automation.