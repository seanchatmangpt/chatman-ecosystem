# 79. Measurement System for the Autonomous Software Factory

A production system changes what it optimizes. Metrics must therefore distinguish activity, value flow, standing, waste, autonomy, and safety. No single scalar—commits, tests, tokens, issues, or releases—can represent the factory.

## 79.1 Measurement vector

Define

\[
M_t=(\lambda_v,\lambda_c,W,L,\sigma,\eta,\chi,\delta,\rho_h,\kappa,G,D_r).
\]

Where:

- \(\lambda_v\): valuable admitted transition rate;
- \(\lambda_c\): verified closure rate;
- \(W\): WIP;
- \(L\): lead-time distribution;
- \(\sigma\): standing-preservation yield;
- \(\eta\): ALIVE transitions per human intervention;
- \(\chi\): cross-repo fanout per semantic source change;
- \(\delta\): post-promotion defect escape;
- \(\rho_h\): human touches per completed piece;
- \(\kappa\): kaizen leverage;
- \(G\): generated-from-canonical fraction;
- \(D_r\): dependency closure ratio.

## 79.2 Commit velocity

Let \(C_d\) be commits per day. Treat it as a **production-load indicator**. Normalize by eligible or active repository count:

\[
C_{repo}=\frac{C_d}{R}.
\]

A rising \(C_d\) is useful evidence that the factory is processing more transitions. Its interpretation depends on whether \(\sigma,\eta,\delta\), and lead time improve or degrade.

Do not erase the signal because it is imperfect. Contextualize it.

## 79.3 Closure ratio

Define

\[
CR=\frac{\lambda_c}{\lambda_v}.
\]

For sustained load, \(CR\approx1\) is desirable. If \(CR<1\), WIP grows. The improvement response is to locate the constrained service center and increase closure capacity or eliminate avoidable arrivals.

## 79.4 Human-touch intensity

Define

\[
HTI=\frac{human\ touches}{verified\ completed\ pieces}.
\]

The core TPS/autonomy prediction is

\[
HTI\downarrow
\]

as throughput increases.

Touches should be typed: novel intent, policy, exception, manual scheduling, manual repair, manual verification, manual release. This reveals which categories remain removable.

## 79.5 Standing yield

Not every generated transition becomes valid standing. Define

\[
SY=\frac{ALIVE+typed\ terminal\ refusals}{admitted\ executions}.
\]

A typed, evidence-backed refusal is preferable to ambiguous limbo. Therefore terminality matters alongside success.

## 79.6 WIP age spectrum

Average WIP can hide old stranded work. Track percentiles and maximum age:

\[
W_{50},W_{90},W_{99},W_{max}.
\]

Also segment by blocker class. A healthy recovery engine should reduce the long tail of capability-solvable WIP.

## 79.7 Fanout quality

High \(\chi\) can be good or catastrophic. Add verified fanout yield

\[
FY=\frac{verified\ generated\ consequences}{all\ generated\ consequences}.
\]

The factory wants both \(\chi\uparrow\) and \(FY\rightarrow1\).

## 79.8 Recovery yield

For dormant repositories re-evaluated in a period, define

\[
RY=\frac{repositories\ moved\ to\ viable/ALIVE}{repositories\ re-evaluated}.
\]

Track separate causes for refusal. This measures whether capability improvements are actually harvesting historical option value.

## 79.9 Constraint observability

For each service center record utilization, queue depth, lead time, failure rate, and refusal cause. The current bottleneck should be queryable directly:

\[
K_t=arg\max_k\;constraint\_pressure(k).
\]

If the factory cannot name its current constraint from evidence, it is still being managed impressionistically.

## 79.10 North-star relation

The strongest compact relation is

\[
\boxed{
\lambda_c\uparrow,
\quad
HTI\downarrow,
\quad
\delta\downarrow,
\quad
FY\uparrow,
\quad
L\downarrow\text{ or bounded}
}
\]

under increasing valuable load.

That combination would demonstrate manufacturing capacity rather than activity inflation.