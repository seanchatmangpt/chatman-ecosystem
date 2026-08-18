# 63. The State Algebra

Post-AGI systems need more than one boolean called `success`.

The evidence model should preserve orthogonal facts about what happened.

## Observed

`observed(x)` means the system directly acquired evidence of `x` under the declared observation method.

## Admitted

`admitted(x,s)` means the observation or proposition has been accepted for exact subject `s` within a bounded context.

## Executed

`executed(a,s)` means the operation actually ran against the subject. It does not imply the intended consequence occurred.

## Changed

`changed(s,\Delta)` means post-execution observation identified a state difference.

## Verified

`verified(p,s)` means a declared verifier established proposition `p` about the subject within its scope.

## Inferred

`inferred(p)` preserves conclusions produced by reasoning that have not been promoted to observation or admission.

## Refused

`refused(a,\tau)` records that transition `a` was evaluated and rejected with typed reason `τ`.

## Blocked

`blocked(a,d)` means a known dependency prevents advancement. The transition may remain lawful if the dependency is later satisfied.

## Unsupported

`unsupported(c)` means the required capability is absent or not represented. It is not evidence that the capability is impossible or forbidden.

## Why orthogonality matters

An action can be executed but unchanged. It can change the world but fail verification. A candidate can be admitted for CONSTRUCT but refused for DO. A verifier can be ALIVE while the subject remains UNKNOWN.

Flattening these dimensions into one status bit destroys diagnostic information.

## Standing is derived

Standing values such as `PARTIAL_ALIVE` and `ALIVE` should be calculated from required predicates over this state algebra, not assigned by narrative.

## Falsifier

The algebra is insufficient if two materially different operational histories collapse to the same state and that loss prevents correct authority or standing decisions.

## Operational exercise

Take a failed deployment and classify each fact using the state algebra. Avoid the word “failed” until the end. The resulting typed description should make the repair path more obvious.