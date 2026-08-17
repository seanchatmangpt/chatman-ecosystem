# 25. Receipt(A)

A post-AGI system can produce explanations faster than any human audit function can read them. Narrative therefore cannot be the primary evidence format for consequence.

The ecosystem uses receipts to bind claims to exact operations.

\[
R = Receipt(A)
\]

The notation does not mean every artifact automatically has a receipt. It means that consequential manufacture and actuation should produce an evidence object whose semantics can be verified independently of the story told about the action.

## What a receipt must bind

A useful receipt identifies at least:

- the exact admitted subject;
- the operation or transition requested;
- the authority under which it advanced;
- the actor or execution principal;
- the toolchain and environment identities that matter;
- the inputs and relevant content digests;
- the observed result;
- the expected and observed postconditions;
- parent receipts or causal predecessors;
- replay information;
- time and policy context.

Different domains may require additional fields.

## Receipt is a type, not a filename

A JSON object named `receipt.json` is not a constitutional receipt merely because it contains a timestamp and a hash.

The system must be able to answer what proposition the receipt supports and verify the bindings required by that proposition.

This prevents evidence theater: artifacts that look auditable but do not establish identity, authority, or consequence.

## Construction receipts and actuation receipts

CONSTRUCT and DO should not be collapsed.

A construction receipt can establish how an artifact was manufactured, which semantic source and toolchain produced it, and which validations were performed.

An actuation receipt establishes that a consequential transition actually crossed the BRCE boundary and what postcondition was observed.

The second should be able to reference the first without pretending they are the same event.

## Receipts make machine review tractable

At post-AGI throughput, humans cannot review every generated diff or event. Receipts let machines evaluate standing through explicit predicates rather than prose summaries.

The human can inspect exceptions, falsifiers, policy changes, and high-consequence transitions while routine evidence is mechanically checked.

## Falsifier

A receipt fails if the exact subject or consequence it claims to cover can change while the receipt still verifies as though nothing changed.

## Operational exercise

Take one existing deployment or publication log and attempt to reconstruct a constitutional receipt from it. Every missing identity or postcondition reveals evidence that the current system does not persist.