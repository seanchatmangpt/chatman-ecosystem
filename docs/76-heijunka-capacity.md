# 76. Heijunka, Capacity, and Graph-Level Load Distribution

Heijunka is production leveling. In a software ecosystem it should not be translated into making every repository equally active or suppressing bursts. The purpose is to prevent avoidable oscillation, starvation, and bottleneck overload while preserving real demand variation.

## 76.1 Demand vector

Let repository demand at time \(t\) be

\[
D_t=(d_1,d_2,\ldots,d_n).
\]

Each \(d_i\) may contain novel work, recovery work, dependency fanout, repair, release closure, or maintenance.

The scheduler maps demand to service capacity

\[
C_t=(c_1,c_2,\ldots,c_m)
\]

across build runners, generators, verifiers, graph engines, release channels, providers, and other constrained resources.

## 76.2 Level the bottleneck, not the imagination

The leveling problem is

\[
\min variance(load_k)
\]

subject to value priority, dependency order, authority, and deadline constraints.

It is not

\[
\min \Lambda_v.
\]

High valuable arrival rates are compatible with heijunka if capacity is allocated so no service center experiences pathological burst/starvation cycles.

## 76.3 Takt reinterpretation

Manufacturing takt is customer-demand pace. In a software factory, define value takt for a work class \(j\) as

\[
T_j=\frac{available\ service\ time}{required\ completed\ value\ units_j}.
\]

Not every repository shares a takt. Release-critical dependency repair may require minutes, while dormant-POC archaeology may tolerate days.

The useful artifact is a class-specific service-level objective, not one global cadence.

## 76.4 Capacity pools

A large ecosystem benefits from explicit capacity pools:

- semantic manufacture;
- compile/test;
- benchmark/gym execution;
- formal proof/admission;
- graph query;
- consequential actuation;
- release publication;
- archaeological recovery.

A work token declares which pools it needs. Scheduling can then avoid sending more work into a saturated pool while independent work continues elsewhere.

## 76.5 Dependency-aware leveling

If repository \(r_b\) depends on \(r_a\), finishing \(r_a\) can unlock many downstream cells. Define unlock leverage

\[
U(r)=|descendants(r)\cap blocked|.
\]

Heijunka should account for this topology. Leveling is not blind fairness; a high-unlock node can deserve disproportionate capacity because it reduces global queueing.

## 76.6 Recovery work as background pull

Dormant POC recovery is ideal for spare capacity when it does not compete with urgent customer/release demand. Let \(s_k\) be slack in capacity pool \(k\). A recovery scheduler can consume slack when

\[
s_k>\theta_k
\]

and the candidate's required pools are available.

This turns idle machine capacity into option-value harvesting without overloading critical paths.

## 76.7 Burst absorption

Canonical semantic changes can create legitimate fanout bursts. The system should absorb them with queues, batching where semantics allow, parallelism where dependencies allow, and admission backpressure at the actual constrained pool.

The important property is that backpressure remains local and typed.

## 76.8 Leveling metrics

Track:

- service-center utilization;
- queue depth by class;
- queue age percentiles;
- starvation count;
- blocked-descendant count;
- burst recovery time;
- human scheduling interventions;
- capacity lost to rework;
- spare capacity harvested by recovery work.

A healthy graph-level heijunka system raises throughput while reducing starvation and operator scheduling.

## 76.9 Falsifier

If graph-aware leveling consistently increases total lead time or reduces valuable closure compared with simpler priority scheduling under matched demand, the added control complexity is unjustified. Heijunka is a production hypothesis, not a ritual.