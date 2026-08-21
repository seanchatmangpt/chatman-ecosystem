# v26.8.20 — mdBook Plan: "Engineering XaaS Applications" (BEAMOps 2nd Edition)

> Not started as an implementation ticket — this is the mdBook structure plan the user asked for,
> combining real source material already on disk. No chapter prose is written here; this is the
> `SUMMARY.md`-shaped table of contents plus the mapping of every chapter to its real source and
> its real target in this ecosystem (`platform-console` / `autofde-lab` / `~/dev/beamops`).

## Decision context (carried forward, not re-litigated)

- **Pure Erlang is deprioritized until a proven need exists** — supersedes
  [`02-ERLANG-RUST-LANGUAGE-SPLIT.md`](02-ERLANG-RUST-LANGUAGE-SPLIT.md)'s framing. Elixir + Ash is
  the working substrate; this doc plans content on that basis, not pure OTP/Erlang.
- "XaaS" is the name for the three real layers established in
  [`03-XAAS-ASH-ECOSYSTEM-MAP.md`](03-XAAS-ASH-ECOSYSTEM-MAP.md): capability ontology, planner
  (`autofde-lab`), compliance/entitlement surface (`platform-console`). This book teaches how to
  build that shape from scratch in Elixir/Ash/Phoenix, using `~/dev/beamops` as the running
  substrate.
- The user fetched the final Ash Framework edition mid-session: `~/Downloads/ash-framework_P1.0.pdf`
  (Pragmatic, Le & Daniel, book version P1.0—August 2025, the print release superseding the B3/B4/B5
  betas also on disk). Its TOC is structurally identical to B5.0's (10 chapters, same order; ch. 7
  renamed "Testing Your Application" from "All About Testing") — the chapter plan below needed no
  restructuring, only this citation update.
- Two more Pragmatic titles landed alongside it, also real source material for later chapters:
  `~/Downloads/designing-elixir-systems-with-otp_P1.0 (1).pdf` and
  `~/Downloads/concurrent-data-processing-in-elixir_P1.0.pdf`.
- **Explore phase closed.** Per the user's own framing: `~/cns` (679 top-level entries) and
  `~/chatmangpt` (including `BusinessOS`) are this account's prior wide-exploration record — the
  research-on-myself survey stops here, not because more isn't there, but because the user named
  this the pivot point from Explore to Exploit. This doc and `03-XAAS-ASH-ECOSYSTEM-MAP.md` are
  the convergence artifacts; the next real step is scaffolding, not more surveying.

## Real source material found on disk

| Source | Location | What it real-covers |
|---|---|---|
| *Engineering Elixir Applications* (BEAMOps, 1st ed.) | `~/Downloads/engineering-elixir-applications_P1.0.pdf` | 12 ch.: Terraform/GH issues, Docker/OTP releases, GH Actions CI, Docker Compose, Packer AMIs, CD+secrets(SOPS), multinode Swarm, Distributed Erlang, autoscaling, PromEx/Grafana/Loki metrics, custom alerts |
| *The Platform Engineer's Handbook* | `~/Downloads/_OceanofPDF.com_The_Platform_Engineers_Handbook_-_Ajay_Chankramath.pdf` (Packt, 2026) | 14 ch. + setup appendix: K8s/service-mesh runtime, OAuth/RBAC platform security, Prometheus/Loki/Tempo/Grafana observability, Backstage developer portal, self-service onboarding, CI/CD-as-platform-service, self-service infra with **Crossplane**, starter kits, OPA policy-as-code, FinOps/cost/autoscaling, chaos/DR resilience, agentic/AI-augmented platforms |
| *Ash Framework* | `~/Downloads/ash-framework_P1.0.pdf` (Pragmatic, Le & Daniel, **P1.0, final print release, August 2025**) | 10 ch.: first resource, business logic, search UI, JSON:API/GraphQL generation, `AshAuthentication`, policy-based authorization, testing, nested forms, many-to-many relationships, PubSub/real-time |
| Phoenix/LiveView material | `~/Downloads/programming-phoenix-14-...pdf`, `~/Downloads/real-time-phoenix-...pdf`, `~/Documents/Papers/BEAM/programming-phoenix-liveview_B12.0.pdf` | Phoenix fundamentals, channels/PubSub real-time patterns, LiveView |
| OTP design / concurrency depth | `~/Downloads/designing-elixir-systems-with-otp_P1.0 (1).pdf`, `~/Downloads/concurrent-data-processing-in-elixir_P1.0.pdf` | Candidate source for Part IV's Ch. 26 (Distributed Elixir / control-plane clustering) and any GenStage/Flow-shaped capability-actuation pipeline work |
| `~/dev/beamops` | verified runnable this session (`mix compile`/`ecto.migrate`/`phx.server` → real `200`) | The actual worked-example substrate — real Terraform/Packer/Swarm/PromEx/DNSCluster already implementing BEAMOps ch. 1–12 |
| `~/chatmangpt/BusinessOS` | negative comparator, reviewed not adopted | A real prior XaaS-shaped attempt (Go+SvelteKit, agent-first, has `deploy/k8s/multi-tenant/`) with no capability ontology, no receipt/broker discipline, no planner/actuator boundary — cited in the book's own argument for why ontology-first beats UI-first |
| `docs/jira/v26.8.20/03-XAAS-ASH-ECOSYSTEM-MAP.md` | this repo | The real Ash-package-to-layer coverage map (all ~127 hex.pm ash-dependent packages reviewed) this book's Part III draws its extension chapters from |

## Proposed structure — "Engineering XaaS Applications: Navigate Each Stage of Delivering an Ash/Phoenix Platform"

Four parts, mirroring BEAMOps' own "journey through delivery stages" structure but widened to
cover resource modeling (Ash) and platform-team concerns (Platform Engineer's Handbook) BEAMOps
never touched, and narrowed to Elixir/Ash/Phoenix per this session's Erlang-deprioritization
decision.

```text
# Summary

[Introduction: From BEAMOps to XaaS](introduction.md)

---

# Part I: Model the Domain (new — from Ash Framework)

- [Ch 1: Building Your First Ash Resource](ch01-ash-resource.md)
- [Ch 2: Extending Resources with Business Logic](ch02-ash-business-logic.md)
- [Ch 3: Generating APIs Without Writing Code (JSON:API + GraphQL)](ch03-ash-apis.md)
- [Ch 4: Authentication with AshAuthentication](ch04-ash-authentication.md)
- [Ch 5: Authorization Policies for Capability-Gated Actions](ch05-ash-authorization.md)

---

# Part II: Ship It (BEAMOps ch. 2-8, retargeted at an Ash/Phoenix app)

- [Ch 6: Terraform for Project Management (GitHub Issues/Milestones)](ch06-terraform-pm.md)
- [Ch 7: Build and Dockerize Your Ash/Phoenix Application](ch07-dockerize.md)
- [Ch 8: CI Pipelines with GitHub Actions](ch08-ci.md)
- [Ch 9: The Dev Environment with Docker Compose](ch09-compose.md)
- [Ch 10: The Production Environment and Packer](ch10-packer.md)
- [Ch 11: Continuous Deployment and Secrets (SOPS)](ch11-cd-secrets.md)
- [Ch 12: Multinode Docker Swarm](ch12-swarm.md)

---

# Part III: Operate It as a Platform (new — from Platform Engineer's Handbook)

- [Ch 13: Kubernetes Runtime and Service Mesh](ch13-k8s-mesh.md)
- [Ch 14: Securing Platform Access (OAuth/RBAC)](ch14-platform-security.md)
- [Ch 15: Observability with Prometheus/Loki/Tempo/Grafana](ch15-observability.md)
- [Ch 16: A Backstage Developer Portal for Your Capability Catalog](ch16-backstage.md)
- [Ch 17: Self-Service Onboarding](ch17-onboarding.md)
- [Ch 18: CI/CD as a Platform Service](ch18-cicd-platform.md)
- [Ch 19: Self-Service Infrastructure with Crossplane](ch19-crossplane.md)
- [Ch 20: Publishing Starter Kits](ch20-starter-kits.md)

---

# Part IV: Prove It's Governed (new — the XaaS/capability-ontology synthesis)

- [Ch 21: Policy-as-Code with OPA, Meets ce:Capability](ch21-opa-capability.md)
- [Ch 22: Receipts, Idempotency, and ash_onetime](ch22-receipts.md)
- [Ch 23: Audit Chains — ash_paper_trail, ash_event_log, ash_carbonite](ch23-audit-chains.md)
- [Ch 24: FinOps, Autoscaling, and Cost Governance](ch24-finops.md)
- [Ch 25: Chaos Engineering and Disaster Recovery](ch25-chaos-dr.md)
- [Ch 26: Distributed Elixir — Clustering the Control Plane](ch26-distributed-elixir.md)
- [Ch 27: Agentic and AI-Augmented Platforms](ch27-agentic-platforms.md)

---

[Appendix A: Comprehensive Installation Guide](appendix-a-install.md)
[Appendix B: Ash Package Reference (the full coverage map)](appendix-b-ash-packages.md)
```

## Appendix A's real content plan — "installation information for all of these"

Per the user's explicit ask, Appendix A is the single chapter that must be genuinely comprehensive
and dependency-ordered, following *The Platform Engineer's Handbook*'s own Appendix A pattern
(per-chapter install sections, `⚠ Common pitfalls` callouts). Real, verified-on-this-machine
version pins to seed it with (not fabricated — checked this session):

| Tool | Verified version on this machine | Source |
|---|---|---|
| Erlang/OTP | 28 (`erts-16.2`) | `elixir --version` output, this session |
| Elixir | 1.19.5 | `elixir --version` output, this session |
| PostgreSQL | running, `pg_isready` confirmed accepting connections | this session |
| `ggen` | 26.8.18 | `ggen --version`, this session |

Plus, from the two handbooks' own appendices/tool lists (not yet installed/verified on this
machine — real follow-on work, not silently assumed present): `mix igniter` / `mix ash.install`
(Ash project scaffolding), Docker/Docker Compose/Docker Swarm, Terraform, Packer, SOPS+age,
Kubernetes (Kind, per the Handbook's local-MVP choice), Istio or the Handbook's chosen service
mesh, Auth0 (Handbook's OAuth choice) or `AshAuthentication`'s own providers, Backstage, Crossplane,
OPA Gatekeeper, Prometheus/Loki/Tempo/Grafana, KubeCost, Sloth, Velero.

## What this doc does not do

No chapter prose is written. No mdBook skeleton has been scaffolded on disk yet — this is the
structure plan for review before that scaffolding step, per this session's "confirm the scoping
decision before code" pattern from doc 03. Next real step, once this structure is confirmed: create
the actual `book.toml`/`src/SUMMARY.md`/stub chapter files (mirroring `~/jotp/books/jotpops`'s
existing, working `mdbook` convention — `book.toml`, `[output.html] theme = "ayu"`, `outline.md`,
`CHAPTERS_NN.md` grouping files), sourced content-by-content from the real PDFs and the real
`~/dev/beamops`/`platform-console` code as each chapter is actually written.

## See Also

- [`01-ROADMAP-TODAY.md`](01-ROADMAP-TODAY.md), [`02-ERLANG-RUST-LANGUAGE-SPLIT.md`](02-ERLANG-RUST-LANGUAGE-SPLIT.md)
  (superseded per the decision context above), [`03-XAAS-ASH-ECOSYSTEM-MAP.md`](03-XAAS-ASH-ECOSYSTEM-MAP.md)
- `~/jotp/books/jotpops/book.toml`, `src/SUMMARY.md` — the existing, working mdBook convention
  this plan's Appendix A and chapter-file structure follows
- `~/chatmangpt/BusinessOS` — the negative comparator informing Part IV's governance argument
