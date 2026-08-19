# Appendix T — Reconstitution Protocol

This appendix is a reference surface for the Chateco doctoral program. Its source correspondence is **16.10 Rust Typestates for the Chatman Equation**.

The Rust implementation turns the law-state chain into a protocol enforced by ownership and method availability. The central type is:

```rust
pub struct Stage<T, S> {
    value: T,
    context: Context,
    _state: PhantomData<S>,
}
```

`T` is the domain payload. `S` is a zero-sized marker such as `Observed`, `Admitted`, `Diagnosed`, `Planned`, `Authorized`, `Actuated`, `Receipted`, or `Replayed`. A transition consumes `self` and returns a new `Stage` with a different marker. Because the original value has moved, authority-bearing states cannot be reused accidentally.

### Method availability as law

Rust implements a method only for the state from which the transition is lawful:

```rust
impl<T> Stage<T, Observed> {
    pub fn admit<L>(self, law: &L)
        -> Result<Stage<T, Admitted>, TransitionError<T, Observed, L::Error>>
    where
        L: AdmissionLaw<T>;
}
```

The planner is available only after diagnosis. Authorization is available only after planning. Actuation is available only after authorization. Receipt is available only after actuation. Replay is available only after receipt.

This is stronger than a runtime enum with a switch statement. A caller holding `Stage<P, Planned>` cannot call `actuate` because no such method exists. The compiler therefore rejects the illegal program before any runtime policy branch can be forgotten or bypassed.

### Domain traits

The crate avoids hard-coding one domain. Traits supply the native law:

-   `AdmissionLaw<T>` returns an `AdmissionCertificate` and `Boundary`.
-   `Diagnoser<T>` returns a finding.
-   `Planner<F>` returns a plan.
-   `Authorizer<P>` returns a grant.
-   `Actuator<P, G>` returns an artifact.
-   `ReceiptLaw<A>` creates and verifies a receipt.
-   `Replayer<A>` reconstructs or checks the consequence.

Each fallible trait classifies its errors into a `RefusalKind`. The error retains the source stage, allowing lawful repair or retry without inventing a new observation.

### Evidence and limits

The typestate crate establishes protocol properties: order, ownership consumption, authority separation, typed failure, and receipt-before-replay. It does not prove domain theorems, planner soundness, or cryptographic security. Those obligations remain with Lean, planner verification, domain validators, and production digest implementations. The crate is therefore a projection of the equation, not a replacement for every admission mechanism.

## Standing rule

Entries in this appendix are descriptive until bound to exact repository, ref/SHA or artifact digest, owning verifier, and receipt/replay evidence. Registry membership is not operational standing.
