# 18. Perfect Information and Adversarial Worlds

Many planning systems were developed for environments with hidden information. Infrastructure and synthetic operational worlds can sometimes do better: the gym can expose the complete modeled state to the evaluating intelligence.

This does not mean the real world offers perfect information. It means the experimental world can make its assumptions explicit and remove accidental uncertainty from the benchmark.

## Perfect modeled state

Given a GymAct world `W`, define the evaluator's observation as the full represented state:

\[
Obs_{gym}(W_t)=W_t
\]

This allows experiments to measure planning and construction quality rather than tool-discovery noise.

A second evaluation can deliberately restrict observations to test behavior under partial information.

The two modes answer different scientific questions and should not be conflated.

## Model the adversary's goals

Defensive systems often start from known exploit catalogs. A post-AGI system can reason one level higher by modeling unacceptable goals as reachability problems.

For example, a defensive goal might be to ensure that an untrusted principal cannot reach a state representing unauthorized data access, persistent authority, or irreversible destructive control.

The emphasis is not on enumerating attack instructions. It is on proving or empirically testing non-reachability of prohibited states.

\[
principal \not\leadsto forbidden\_state
\]

## Perfect information about the synthetic adversary

In a gym, the system may know the adversary's modeled capabilities, objectives, and reachable transitions exactly. That creates a useful upper-bound experiment: if the defense fails even with complete state knowledge, uncertainty is not the root cause.

Conversely, if a defense succeeds only under perfect knowledge, the gap to real operation becomes an explicit observation problem.

## DfCM over defensive topology

One failed defensive control is not the whole graph. The system can construct alternative boundaries, isolate authority, remove reachability, alter network topology, rotate identities, or change process structure in the synthetic world.

The goal is to discover classes of configurations in which forbidden goals are structurally unreachable, not merely to patch one known path.

## Falsifier

A “perfect information” claim is false if the gym hides material state from the evaluator while the benchmark interprets failures as planning failures rather than observation failures.

## Operational exercise

Define one prohibited operational state in terms of objects and authority relationships. Build two gym modes: full modeled state and bounded realistic observation. Compare whether the proposed defense depends on hidden knowledge.