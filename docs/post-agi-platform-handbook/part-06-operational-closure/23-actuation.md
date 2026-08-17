# 23. Actuating Computational Worlds

The post-AGI platform should not confuse its constitutional execution model with any particular substrate.

Cloud, Kubernetes, WASM, operating systems, SaaS, networks, edge devices, and physical systems are all potential actuation targets.

## Adapters terminate semantics

An adapter translates a bounded semantic intent into the operations understood by a target runtime.

\[
Intent_{semantic} \xrightarrow{adapter} Operation_{substrate}
\]

The adapter should not invent new authority or business semantics. Its job is to preserve the admitted meaning across the substrate boundary.

## Cloud

Cloud adapters may create, update, or delete managed resources. Provider differences belong in projection and capability mapping, not in the constitutional definition of resources such as identity, storage, compute, network policy, or data residency.

## Kubernetes

Kubernetes is a reconciliation substrate. It is excellent at maintaining desired resource state inside its domain. That does not make Kubernetes the authority root for the wider ecosystem.

The admitted graph may project to Kubernetes objects, and observed cluster state returns as evidence.

## WASM and local runtimes

WASM can provide portable bounded execution for constructed logic and process components. Local runtimes may be preferred when they produce faster deterministic evidence than hosted CI or remote infrastructure.

## SaaS and organizational systems

A platform may actuate issue trackers, calendars, email, documents, billing, identity systems, or procurement workflows. These operations have consequences even when they do not look like infrastructure.

BRCE applies equally.

## Physical systems

When software reaches actuators, robots, factories, vehicles, or other physical systems, postconditions become even more important. A command acknowledgment is not necessarily evidence that the physical world reached the intended state.

Sensors and observations must close the loop.

## Reality is heterogeneous

The architecture should embrace heterogeneous substrates while preserving one execution calculus:

\[
O^* \rightarrow Construct \rightarrow Admit_{DO} \rightarrow Adapter_i \rightarrow Consequence \rightarrow Receipt
\]

The runtime can change without changing the constitutional path.

## Falsifier

If adding a new substrate requires bypassing identity, authority, receipt, or replay semantics because “this API works differently,” substrate independence has failed at the wrong layer.

## Operational exercise

Model one capability and project it to two different substrates. Identify which semantics stay invariant and which details belong only to the adapter. Any authority rule that changes merely because the provider changes deserves scrutiny.