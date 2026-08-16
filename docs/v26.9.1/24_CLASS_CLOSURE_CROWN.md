# Class Closure Crown

## Crown claim

Class closure establishes that a solved instance has been transformed into reusable executable class knowledge such that a distinct lawful future instance closes without rediscovering the solution.

The condition is:

\[
\exists x'\in[x]_\Gamma,\quad x'\neq x,
\]

such that:

\[
InstanceClosed(x')\land Rediscovery(x')=0.
\]

## Why replay is insufficient

Replaying the original \(x\) proves reproduction. It can demonstrate deterministic execution, receipt validity, or preservation of the original solution. It does not establish that the encoded structure captures the solution class rather than the training instance.

Therefore the evidentiary hierarchy is:

\[
Replay(x)<Transfer(x')<ClassClosure([x]_\Gamma).
\]

## Class identity

The class relation must itself be admitted and normalized. Let:

\[
c_\Gamma:X\rightarrow\mathcal C.
\]

Then:

\[
x\sim_\Gamma y\iff c_\Gamma(x)=c_\Gamma(y).
\]

The crown must show that \(x'\) belongs to the same bounded class under the relevant context. A conveniently similar instance outside the admitted class does not count.

## Rediscovery information

`Rediscovery(x')=0` means the next instance does not require reconstruction of the class solution as new reasoning. Contextual values, observations, and ordinary admission are still allowed and expected. Class closure eliminates rediscovery, not novelty and not local authority.

A strong metric can represent newly introduced solution information after instantiation as \(I(x';S_{[x]})\). The crown requires:

\[
I(x';S_{[x]})=0.
\]

## Candidate pack versus closure

Encoding a reusable package, ontology, generator, verifier, or workflow is only the candidate for class closure:

\[
PackCreated\neq ClassClosed.
\]

The reusable structure earns class standing only when transfer succeeds on a distinct instance.

## Future applicability

Even a class-closed structure does not become ambient authority. On future use it is projected through contextual applicability and admission. A law may change, authority may be revoked, or a capability may disappear without falsifying the historical class solution.

```mermaid
flowchart LR
  X["closed instance x"] --> N["normalize class"] --> S["S_[x]"] --> XP["distinct x' in [x]_Γ"] --> I["instantiate"] --> C["InstanceClosed(x')"] --> Z["Rediscovery=0"] --> CC["ClassClosed"]
```
