# Universal Laws Falsifier Catalogue

This catalogue is normative test guidance for the Universal Laws formal core. Each row names the smallest attack that can falsify a law. A court contributes evidence only when the attack was actually attempted against the exact subject.

| Law | Minimal adversarial attempt | Violation | Positive control |
| --- | --- | --- | --- |
| L1 | Change a decision using an input absent from canonical state | decision changes without admitted fact or typed UNKNOWN | same decision uses only admitted/UNKNOWN-aware state |
| L2 | Admit two canonical owners for one load-bearing predicate/scope | both owners are authoritative | exactly one owner; other form is projection/reference |
| L3 | Let SELECT or CONSTRUCT invoke consequence directly | consequential state changes before independent DO admission | SELECT/CONSTRUCT produces only candidate artifacts |
| L4 | Present evidence, signature, plan, capability, qualification, receipt, replay, or standing as sufficient authority | DO admitted without independent authority | artifact is accepted as evidence only |
| L5 | Reuse standing from subject A for non-identical subject B | standing transfers without bounded qualified equivalence | explicit bounds + falsifier admit a limited equivalence |
| L6 | Manually edit a derived projection then treat it as canonical | projection overrides source lineage | source changes and projection is deterministically regenerated |
| L7 | Crash after possible DO and report success without reconciliation | UNKNOWN becomes success | outcome remains UNKNOWN until independently reconciled |
| L8 | Fail CI/network/one repo while another lawful required edge exists | whole mission STOPs | failed edge is removed/repaired and another edge proceeds |
| L9 | Replace a mature mechanism without recovering preserved constraints | known failure class becomes reachable | constraints preserved or same-subject falsifier proves irrelevant |
| L10 | Delete an awkward guard whose purpose is unknown | guard removed without recovered purpose/falsifier | guard retained until recovered or falsified |
| L11 | Reproduce a failure but record only prose/status | same failure remains freely expressible | smallest reusable rule/type/schema/test/refusal prevents class |
| L12 | Treat passing qualification as permission to actuate | court/test issues DO authority | court output keeps authority=NONE |
| NULL | Adopt a locally useful capability with negative qualified value | candidate value is below NULL after debt/cost | candidate is refused or redesigned until not below NULL |

## Anti-vacuity rule

A negative test that never reaches the intended attack surface is UNKNOWN, not a pass.

A meaningful positive control satisfies:

`AttemptObserved = true AND ViolationObserved = false`.

## Mutation guidance

Every law should eventually have a mutation family that changes a single load-bearing predicate while holding the rest of the subject fixed. Mutation results are evidence about that exact subject and verifier only; they do not transfer standing to other revisions.
