# 15. Thermodynamics

> **Part 4: Physics Is the Type System.** This part places physics above software preference. Orbital dynamics, energy, thermodynamics, materials, and information limits act like non-negotiable types that candidate designs must inhabit.

## Thesis

Thermodynamics is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.

Every useful energy conversion ends as heat. A collector that absorbs stellar power must either radiate comparable power, export energy, store it temporarily, or fail thermally. Radiative disposal scales as P=εσAT⁴, making radiator area and operating temperature architectural variables. The T⁴ dependence rewards hotter radiators with compact area, but material limits, conversion efficiency, computation density, and component lifetime constrain that choice.

## Chatman-Ecosystem realization

The operational path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

## Chapter map

- [Every Collector Is Also a Radiator](15-01-every-collector-is-also-a-radiator.md)
- [Waste Heat](15-02-waste-heat.md)
- [Operating Temperature](15-03-operating-temperature.md)
- [Radiator Area](15-04-radiator-area.md)
- [Carnot Limits](15-05-carnot-limits.md)
- [Thermal Failure Domains](15-06-thermal-failure-domains.md)

## Acceptance boundary

This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.

## Falsifiers

- A required physical ledger does not close.
- The subject identity is ambiguous or stale.
- A simulation result is presented as physical execution evidence.
- A proof is about a model that was never admitted as the operational subject.
- An actuator can be reached outside the brokered receipt path.
- Replay cannot reconstruct the transition that supposedly established standing.
