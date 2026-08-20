# Case Study: Reconstituting Freedom Consulting as a Gym Empire Company Twin

**Date:** 2026-08-19  
**Subject:** Freedom Consulting Inc. as a bounded enterprise-company simulation target  
**Primary runtime:** `gymact`  
**Simulation scope:** organization + services + sales + staffing + delivery + revenue + public-presence behavior  
**Standing:** `PARTIAL_ALIVE` design/implementation path; source-company facts beyond the supplied outreach remain `UNKNOWN` until independently observed and admitted.

## Thesis

This case is not primarily about recruiting and it is not a single-client deployment exercise.

The target is to determine whether the Chatman Ecosystem, GymAct, and the wider gym empire can **reconstitute the observable behavior of an enterprise consulting company** closely enough that the simulation can be used as a bounded world for planning, benchmarking, training, economic experimentation, and deployment research.

The object being modeled is the company as a dynamical system:

`market -> attention -> lead -> qualification -> opportunity -> staffing -> engagement -> delivery -> invoice -> collection -> renewal/churn -> reputation -> market`

The simulation must preserve the causal relationships between people, services, customers, regions, utilization, delivery capacity, revenue, margin, reputation, hiring, and demand. It is not sufficient to produce a static org chart, synthetic web page, or a collection of agent personas.

The hard acceptance question is:

> Given the same bounded exogenous events, can the simulated company produce organizational, commercial, delivery, and economic trajectories that are behaviorally equivalent to the admitted real-company observations?

For identity-bearing public surfaces such as LinkedIn, the benchmark may demand human-plausible profiles, communication patterns, role distributions, posting cadence, and network behavior. Public synthetic identities, however, must remain explicitly synthetic; the benchmark tests fidelity rather than undisclosed impersonation.

---

## 1. What must be replicated

A company twin is only useful if it includes the mechanisms that produce outcomes.

### 1.1 Organization

The world must represent:

- legal/operating entities;
- regions and time zones;
- business units;
- practices and centers of excellence;
- leadership and reporting relationships;
- recruiters and talent acquisition;
- account executives and business development;
- solution architects and pre-sales roles;
- Forward Deployment Engineers / AI Deployment Engineers;
- SAP, Salesforce, supply-chain, data, AI, security, program-management, and change-management talent;
- employees, contractors, partners, candidates, clients, and prospects as different actor types;
- capacity, utilization, skills, rates, cost, availability, tenure, and assignment state.

The graph must support reorganization without rewriting the simulator.

### 1.2 Service catalog

The observed outreach names at least these service families:

- SAP transformation;
- Salesforce transformation;
- supply-chain consulting;
- enterprise AI;
- automation;
- data;
- intelligent business processes;
- Forward Deployment Engineering;
- AI Deployment Engineering;
- staffing and talent solutions;
- delivery and transformation-led consulting.

Each service must be represented as an economic/product capability with:

- prerequisites;
- compatible customer problems;
- required roles and skills;
- delivery lifecycle;
- pricing model;
- cost model;
- expected duration;
- capacity constraints;
- quality/SLA metrics;
- renewal/expansion possibilities;
- failure and recovery modes.

### 1.3 Revenue-generating motions

The twin must model the full commercial loop rather than setting `revenue = X` directly.

At minimum:

1. market/contact discovery;
2. outbound or inbound attention;
3. lead creation;
4. qualification;
5. solution discovery;
6. proposal/SOW creation;
7. commercial negotiation;
8. close/win/loss;
9. recruiting or internal staffing;
10. onboarding;
11. delivery;
12. milestone acceptance;
13. time/material or milestone billing;
14. invoicing;
15. collection;
16. gross margin realization;
17. expansion, renewal, referral, or churn.

The simulation must permit different business models simultaneously: consulting projects, managed services, staff augmentation, retained talent programs, outcome-based work, and recurring platform/service revenue where observed.

### 1.4 Delivery operations

An engagement should consume real simulated resources and produce measurable state changes.

A SAP + AI transformation engagement, for example, should require some combination of discovery, architecture, data work, integration, security/compliance, FDE activity, testing, deployment, user adoption, and support. A staffing engagement should instead traverse sourcing, qualification, submission, interview, placement, start, timesheet, invoice, and retention transitions.

The world must therefore model **process topology**, not merely labels such as `engagement.active = true`.

### 1.5 Economic state

The company world must expose at least:

- pipeline value;
- probability-weighted pipeline;
- bookings;
- backlog;
- recognized revenue;
- invoiced revenue;
- cash collected;
- accounts receivable;
- delivery cost;
- recruiting cost;
- sales cost;
- gross margin;
- contribution margin where data allows;
- headcount;
- billable headcount;
- utilization;
- bench;
- average bill rate;
- average cost rate;
- days sales outstanding;
- win rate;
- time to staff;
- time to revenue;
- renewal rate;
- churn;
- regional and practice-level performance.

Economic outputs must emerge from transitions in the world. They may not be fabricated as post-hoc dashboard values.

---

## 2. GymAct execution model

GymAct is the bounded execution kernel for one company-world episode.

The company twin must respect GymAct's consequence law:

`request accepted != world changed != objective verified != benchmark scored`

The provider exposes company capabilities as `sosa:Procedure`-like runtime capabilities and routes consequential transitions through GymAct receipts and authority controls.

The initial provider implementation is `gymact.gyms.enterprise_company.EnterpriseCompanyProvider` on the isolated `gymact` branch `feat/enterprise-company-gym`.

Initial executable capabilities are:

- `create_lead`;
- `qualify_lead`;
- `close_engagement`;
- `hire_persona`;
- `staff_engagement`;
- `deliver_milestone`;
- `invoice`;
- `collect`;
- `renew`;
- `churn`;
- `publish_profile`;
- `score_company`.

This is the first executable economic loop, not the final company ontology.

### Consequence boundary

Every state-changing capability is `DO`. `score_company` is `READ`.

Synthetic company worlds are still consequential benchmark worlds: their state transitions must produce receipts, support checkpoint/restore, and remain replayable. Simulation is not an excuse to bypass the execution kernel.

---

## 3. Gym empire composition

A complete company cannot be represented by one monolithic provider. The gym empire should compose specialized worlds around the company graph.

A target composition is:

`CompanyGym × PeopleGym × MarketGym × SalesGym × RecruitingGym × DeliveryGym × FinanceGym × SocialPresenceGym × EnterpriseTechnologyGyms`

where each factor retains its own observations, actions, constraints, authority, evidence, and verifier.

### CompanyGym

Owns organizational structure, business units, practices, regions, capacity, engagement portfolio, and aggregate economic state.

### PeopleGym

Owns synthetic worker/candidate actors, skill graphs, availability, compensation/cost, learning, assignment, turnover, and role transitions.

### MarketGym

Owns prospect populations, demand generation, macro conditions, competitive alternatives, inbound/outbound events, referrals, and regional demand.

### SalesGym

Owns lead/opportunity lifecycle, account strategy, discovery, proposals, commercial terms, probability updates, win/loss, and expansion.

### RecruitingGym

Owns requisitions, sourcing, outreach, response, screening, submission, interviews, offers, placement, start, retention, and recruiting economics.

### DeliveryGym

Owns projects, milestones, dependencies, defects, customer acceptance, staffing consumption, delays, rework, quality, SLA/SLO state, and delivery evidence.

### FinanceGym

Owns contracts, rates, time/milestones, invoices, AR, collection, cost allocation, recognition, margin, cash, and financial controls.

### SocialPresenceGym

Owns professional-profile projection, posting cadence, content topics, reactions, connection/follow relationships, recruiter outreach, candidate responses, and business-development signals.

For public external surfaces, synthetic identity disclosure is a hard fence. Internal/blind benchmark views may suppress the disclosure marker from evaluators when testing behavioral realism, but the underlying artifact retains synthetic provenance.

### EnterpriseTechnologyGyms

Compose SAP, Salesforce, cloud, Kubernetes, data, supply-chain, security, workflow, and AI-agent gyms so delivery engagements exercise the technology stack they claim to deliver.

This is how "Freedom Consulting can deliver SAP + Salesforce + supply chain + AI" becomes executable rather than a sentence in a profile.

---

## 4. The LinkedIn-style fidelity benchmark

The user's desired intuition is useful: if avatars replaced photographs, the simulated company should look operationally like a real consulting company.

The defensible benchmark is **blind behavioral indistinguishability under disclosed synthetic provenance**, not covert impersonation.

### Observable surface

A blinded evaluator can be shown:

- organization size and role distribution;
- employee-like synthetic profiles;
- titles, tenure, skills, and regions;
- posting cadence and content themes;
- recruiter outreach patterns;
- job/requisition activity;
- candidate conversations;
- account-development conversations;
- hiring and attrition patterns;
- staffing changes;
- public announcements derived from simulated company events;
- service mix and client-safe case-study activity.

Real names, logos, photographs, protected marks, and false real-person claims are not required for the fidelity test.

### Target score

Define a discriminator `D` that attempts to classify a blinded trajectory as `observed-company` or `simulated-company` after brand/identity labels are removed.

A long-term target is:

`accuracy(D) -> 0.5`

while simultaneously requiring operational metric error to remain within admitted tolerances.

This prevents a trivial solution where fluent profile text looks convincing but company economics are nonsense.

### Dual acceptance

The company twin passes only when both hold:

1. **surface fidelity:** blinded evaluators cannot reliably distinguish simulated organizational/social trajectories from admitted reference trajectories; and
2. **mechanistic fidelity:** revenue, utilization, staffing, delivery, conversion, retention, and other admitted KPIs remain within tolerance under matched exogenous events.

---

## 5. Freedom Consulting reference model

The outreach is currently the only admitted source supplied in this case. From it, we can observe that the company describes itself as operating across the US, Europe, and APAC and spanning consulting, staffing, delivery, SAP, Salesforce, supply chain, AI-led digital transformation, automation, data, and intelligent business processes.

Those observations define the first public skeleton of the gym.

Everything else—headcount, revenue, customers, margins, rates, win rates, practice sizes, organizational hierarchy, exact service SKUs, delivery processes, recruiting funnels, systems of record, and geographic revenue mix—remains `UNKNOWN` until observed from lawful public evidence or otherwise provided and admitted.

Unknown does not block the simulator. It becomes a parameter/distribution boundary rather than a fabricated fact.

---

## 6. Ontology of the company world

The canonical graph should preferentially compose public ontologies rather than invent a private company metamodel.

Useful semantic families include:

- W3C ORG for organizations, units, roles, memberships, and reporting structure;
- PROV-O for provenance of observations, decisions, work, and evidence;
- P-PLAN for plans and activity structures;
- SOSA/SSN for procedures and observations;
- SKOS for service/skill/taxonomy concepts;
- OWL-Time for employment, assignment, deal, invoice, and engagement intervals;
- QUDT for currency, effort, rates, utilization, and quantitative measures;
- DCAT/DCTERMS for datasets/artifacts;
- ODRL for permissions and policy constraints;
- FIBO where appropriate for financial/business concepts;
- schema.org only as a projection where useful for public-facing organization/person/service representation.

The company twin's private implementation objects are projections of this graph, not the semantic authority.

---

## 7. Episode design

One GymAct episode should represent a bounded experiment over a specific company-world state.

Example episode:

**Objective:** maximize twelve-month gross profit while maintaining delivery quality and regional service coverage.

**Initial state:**

- admitted organization graph;
- synthetic workforce seeded from observed role/region distributions;
- service catalog;
- market/prospect distribution;
- open pipeline;
- active engagements;
- cash/AR state;
- capacity and skill constraints.

**Exogenous events:**

- inbound enterprise AI lead;
- two SAP opportunities;
- APAC staffing shortage;
- one FDE resignation;
- delayed customer milestone acceptance;
- Salesforce expansion request;
- invoice payment delay;
- competitive price pressure.

**Available actions:**

- recruit;
- hire;
- train;
- reassign;
- qualify/disqualify;
- propose;
- discount/refuse discount;
- staff;
- subcontract;
- deliver;
- remediate;
- invoice;
- collect;
- renew;
- expand;
- churn/terminate;
- publish disclosed synthetic public artifacts.

**Verifier:** checks profitability, cash, SLA/quality, staffing feasibility, receipt integrity, policy constraints, and replay.

---

## 8. Revenue-loop acceptance test

The minimum executable company twin must demonstrate this chain through actual GymAct actions:

`lead -> qualified opportunity -> won engagement -> hire -> staff -> milestone -> recognized revenue -> invoice -> collection`

The first provider implements that chain and derives:

- recognized revenue;
- cash collected;
- delivery cost;
- gross margin;
- headcount;
- staffed assignments;
- utilization;
- active engagement count.

A test scenario uses a $1.2M annual-value enterprise opportunity, staffs one synthetic Principal FDE, delivers a $50,000 milestone over 100 hours at $100/hour simulated labor cost, invoices it, and collects it. Expected derived delivery cost is $10,000 and expected gross margin on that milestone is 80%.

The values are test fixtures proving mechanics, not claims about Freedom Consulting's actual economics.

---

## 9. Identity and avatar rule

Synthetic people are necessary for company simulation. They may have:

- names;
- titles;
- skills;
- regions;
- histories inside the simulated world;
- generated avatars;
- professional-profile projections;
- communication styles;
- relationships;
- work histories generated from world events.

The important invariant is provenance.

For internal simulation, profiles can be rendered with maximal realism. For external/public publishing, the provider refuses publication unless `synthetic_disclosure=true`.

The target is therefore:

> indistinguishable **behavioral realism** under blind evaluation, with distinguishable **provenance** whenever the artifact enters the real public world.

This preserves the scientific/engineering benchmark without manufacturing covert real-person identity.

---

## 10. Expansion path

The first provider is intentionally one economic slice. Full Freedom-company reconstitution requires the following closure sequence:

1. **Observe public company evidence** — website, public profiles, jobs, service pages, public client stories, regional presence, technology partnerships, filings where applicable, and other lawful sources.
2. **Construct the ORG/service/role graph** with provenance and explicit unknowns.
3. **Estimate distributions, not fake facts** for values not directly observable: role mix, demand, rates, conversion, utilization, attrition, delivery duration.
4. **Add MarketGym and SalesGym** so pipeline emerges from market events.
5. **Add RecruitingGym** so staffing capacity is manufactured through a realistic funnel.
6. **Compose SAP/Salesforce/cloud/supply-chain gyms** so consulting delivery exercises real technical worlds.
7. **Add FinanceGym** with contract, time/milestone, invoice, AR, collection, margin, and cash mechanics.
8. **Add SocialPresenceGym** for human-plausible disclosed synthetic professional behavior.
9. **Calibrate against admitted historical/public observations.**
10. **Run counterfactuals**: different pricing, service mix, hiring, regional expansion, automation, AI-first delivery, and organizational design.
11. **Use DfCM** to retain multiple viable company designs before selecting operational policies.
12. **Promote standing only from executed episodes and replayable evidence.**

---

## 11. Strategic use

Once company-level simulation is credible, the gym empire can do more than mimic Freedom Consulting.

It can ask:

- What minimum organization could produce equivalent services and revenue?
- Which human roles are bottlenecks versus replaceable coordination surfaces?
- How much faster does an AI-first FDE model turn pipeline into recognized revenue?
- Which practice mix maximizes gross margin subject to delivery-quality constraints?
- What happens if recruiting, solutioning, delivery, and account management are jointly optimized rather than locally optimized?
- Can a smaller synthetic company outperform a larger traditional consulting organization on throughput, margin, quality, and response time?
- Which enterprise services are structurally profitable versus reputation/lead-generation loss leaders?
- What organizational topology survives regional, customer, staffing, or technology shocks?

That is the deeper purpose of the case: **the company becomes a gym world**.

Instead of merely automating jobs inside an organization, the Chatman Ecosystem can model the organization itself as an executable, falsifiable, replayable system.

---

## 12. Current receipt

| Dimension | State |
| --- | --- |
| Freedom Consulting outreach | `OBSERVED` |
| Stated service/geography skeleton | `OBSERVED` from supplied outreach |
| Full real-company ontology | `UNKNOWN` |
| Real headcount/revenue/margins/funnel metrics | `UNKNOWN` |
| GymAct company simulation provider | `CHANGED` on isolated `gymact` branch |
| Lead-to-cash economic loop | `CHANGED`; test authored, not yet executed here |
| Checkpoint/restore | `CHANGED`; test authored, not yet executed here |
| Synthetic public-profile disclosure fence | `CHANGED`; negative/positive tests authored, not yet executed here |
| Full gym-empire composition | `PARTIAL_ALIVE` architecture; not executed end-to-end |
| Behavioral indistinguishability benchmark | `UNKNOWN` until reference trajectories + discriminator exist |
| Production/public identity actuation | `REFUSED` when undisclosed synthetic identity is requested |

## Falsifier

The company-twin thesis is falsified for an admitted scope if, after calibration on lawful reference evidence, the simulator cannot reproduce both the causal economic trajectory and the observable organizational behavior within declared tolerances under matched exogenous events.

A convincing profile page is not sufficient. A correct revenue dashboard with unrealistic human/organizational behavior is not sufficient. The target is joint behavioral and mechanistic fidelity.
