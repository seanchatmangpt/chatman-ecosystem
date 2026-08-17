# 17. GymAct: Executable Counterfactual Reality

Before a post-AGI intelligence changes the world, it should be able to manufacture worlds in which the proposed change can fail safely.

GymAct is therefore more than a benchmark adapter. Its general role is **executable counterfactual reality**.

## A gym is a world model with actuation semantics

A useful gym defines:

- objects and their identities;
- observable state;
- legal and illegal actions;
- transition semantics;
- resource and time constraints;
- reward or objective functions where appropriate;
- refusal and failure states;
- evidence emitted by execution.

The system can then ask what happens when a candidate construction becomes kinetic without crossing the real DO boundary.

\[
CONSTRUCT(World) \rightarrow Execute_{synthetic}(A) \rightarrow Evidence
\]

## Counterfactuals are not mocks

A mock often exists to make a test convenient. A gym exists to preserve the relevant causal structure of the domain.

The distinction matters. If the synthetic world omits the exact constraint that makes production difficult, success in the gym has little standing.

Gym quality therefore depends on correspondence evidence between the synthetic world and the real class of systems it represents.

## Manufacture the gym too

The post-AGI move is not to hand-build a gym for every domain. Ontology and ggen can manufacture executable world definitions from shared semantic classes.

A cloud ontology can project to several provider gyms. A process ontology can project to POWL or BPMN execution environments. A security goal model can project to defensive reachability scenarios. An infrastructure capability can project to both Terraform construction and a synthetic execution substrate.

## Evidence before reality

GymAct narrows DfCM's construction graph empirically.

Candidates that satisfy static constraints may still fail due to interaction effects, timing, resource contention, or unmodeled behavior. Synthetic execution provides evidence about those dynamic properties before real-world authority is considered.

## No promotion by leaderboard alone

A high score is not operational standing. Benchmark performance establishes evidence about a bounded task distribution.

To advance toward DO, the system still needs exact-subject admission, authority, and runtime postcondition evidence.

## Falsifier

A gym is insufficient if it rewards behavior that would violate the real system's constitutional boundaries or if its success can be promoted directly to production authority.

## Operational exercise

Take one cloud deployment class. Define its object model, actions, constraints, postconditions, and failure states independently of a vendor API. Then project the same semantics into a GymAct environment and a real provider adapter. Compare the evidence each produces.