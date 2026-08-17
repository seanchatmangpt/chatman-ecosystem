# 20. Benchmarks as Scientific Instruments

A leaderboard is a projection. A benchmark is useful only to the extent that it measures a clearly defined capability under reproducible conditions.

Post-AGI engineering should treat benchmarks as scientific instruments.

## Define the claim first

Before selecting a benchmark, state the proposition it is supposed to test.

Examples:

- can the system recover a valid infrastructure state from a bounded incident?
- can it construct a deployment satisfying cost and policy constraints?
- can it repair a failed process without violating authority boundaries?
- can it transfer a solved class to an unseen provider?

A score without a claim is difficult to interpret.

## Benchmark identity matters

Results bind to exact benchmark version, environment, task set, toolchain, model or system version, configuration, and evaluation policy.

\[
Result = f(System, Benchmark, Config, Environment)
\]

Change one materially and the old result becomes historical evidence, not current standing.

## Gyms and benches separate concerns

The gym provides the executable world. The benchmark defines task distributions, success criteria, and measurement.

Keeping them separable lets the same world test several capabilities and lets the same capability be tested across several worlds.

## Manufacture benchmarks from ontology

Once a domain's object and transition semantics are explicit, ggen can manufacture families of benchmark instances rather than relying on a small handcrafted task set.

This reduces overfitting to fixed examples and supports DfCM-scale variation.

A cloud benchmark can vary providers, resource graphs, fault conditions, policy constraints, budgets, and migration goals while preserving the same semantic class.

## Negative behavior is part of the score

A system that completes positive tasks but violates refusal boundaries is not superior.

Evaluation should include:

- accepted valid transitions;
- correctly refused invalid transitions;
- preservation of exact subject;
- evidence quality;
- absence of ambient DO;
- replay or reconstruction behavior.

## Falsifier

A benchmark cannot support a broad capability claim if success depends on benchmark-specific affordances not present in the claimed target class.

## Operational exercise

Take one benchmark result you care about. Write the strongest claim it actually supports and three stronger claims it does **not** support. Then add at least one negative-behavior metric that would cause a high-scoring but unsafe system to fail.