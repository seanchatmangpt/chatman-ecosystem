# 27. Design by Admission and Truth Debt

**Executive thesis:** Design by contract becomes stronger when the contract includes what may enter the manufacturing system, what must be refused, and what evidence can support each claim.

## Beyond preconditions

Traditional preconditions and postconditions describe program behavior. Admission adds identity, provenance, authority, semantic shape, and evidence freshness. A valid value from the wrong subject or stale observation can be just as dangerous as an invalid value.

## Truth debt

Broken windows in a deterministic enterprise are stale claims: docs that describe deleted behavior, green badges for unrelated heads, receipts that cannot replay, “supported” capabilities that have never crossed the named boundary, and manual side paths that bypass the factory. These create truth debt because future operators act on false state.

## Refusal is maintenance

A typed refusal prevents truth debt from being silently refinanced. It says the system knows the edge of its knowledge or authority. Refusals should therefore be designed, tested, monitored, and improved like successful behaviors.

## Operating practice

Add claim ceilings to verifiers. A parser can prove parsed. A compiler can prove compiled. A unit test can prove a local invariant. A live integration can prove the boundary it actually exercised. Do not let any court issue a stronger verdict than its evidence supports.

## Diagnostic question

Which green check in your system claims more than its verifier actually observed?
