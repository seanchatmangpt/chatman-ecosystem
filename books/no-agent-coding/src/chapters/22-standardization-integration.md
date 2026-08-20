# 22. Standardization, Integration, and the Right Kind of Reuse

**Executive thesis:** Reuse is valuable when it preserves meaning; copying implementation without shared semantics often multiplies future integration work.

## Two enterprise axes

Integration answers how much business units must share state and coordinate transactions. Standardization answers how similarly they should operate. No Agent Coding adds a third practical question: which decisions can be compiled once and projected everywhere without erasing legitimate variation?

## Semantic reuse beats snippet reuse

A copied library can still be configured differently, wrapped inconsistently, or used under divergent assumptions. A reusable semantic contract states the capability, constraints, authority, inputs, outputs, refusals, evidence, and projection rules. Multiple implementations can satisfy it without losing interoperability.

## Class closure is the leverage point

The highest-value reuse closes a class. A marketplace pack, ontology profile, or generator can encode what the enterprise has learned so that new instances inherit the invariant. This is closer to an operating standard than to a code template.

## Operating practice

When teams ask for a shared library, first ask whether they actually need shared semantics, shared implementation, or both. Standardize the smallest layer that must remain invariant; project or implement the rest locally.

## Diagnostic question

Are teams asking for shared code when what they really need is a shared contract?
