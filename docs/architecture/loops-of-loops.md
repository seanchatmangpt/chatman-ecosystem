# Architecture Specification: The Loops of Loops

**System Scope:** `ash_a2a` $\times$ `ash_r2rml` $\times$ `ash_graphlaw` $\times$ `ash_affidavit` $\times$ `ash_pplan` $\times$ `xaas` $\times$ `ggen_igniter` $\times$ `ggen-marketplace`  
**Framework:** C4 Architectural Model (Context, Container, Component, Dynamic Loops) & The Chatman Recursive Semantic Loop  
**Core Invariant:** $A_t = \mu(O_t^*), \quad R_t = \text{receipt}(A_t), \quad O_{t+1}^* = \text{admit}(\text{observe}(S_t) \cup R_t)$

---

## 1. Executive Summary: The Recursive Control Fabric

In a deterministic, cryptographically attested semantic control architecture, systems do not operate via flat request-reply RPCs or open-loop task execution. Instead, the architecture is structured as a hierarchy of **three nested, self-closing recursive feedback loops**:

1. **The Inner Micro-Actuation Loop (Gate & Execution):**  
   `ash_a2a` $\to$ `ash_r2rml` $\to$ `ash_graphlaw` $\to$ `ash_affidavit` $\to$ `xaas`  
   Validates pre-conditions, cryptographically bounds authority with Ed25519 leases, admits transitions through branchless WASM kernels, executes provider tasks, and stamps immutable receipt records.
2. **The Outer Goal-Convergence Loop (Planning & State Reconciliation):**  
   `ash_pplan` $\to$ `ash_a2a` $\to$ `ash_affidavit` $\to$ `ggen_igniter`  
   Translates declarative work orders into FOND/HTN action trees, checks post-conditions against relational and RDF state, and reconciles state transitions through append-only event sourcing logs.
3. **The Meta Ontological Evolution Loop (Synthesis & Self-Hosting):**  
   `ggen-marketplace` $\to$ `ggen_igniter` $\to$ `ash_*` Artifacts $\to$ Conformance Mining $\to$ `ggen-marketplace`  
   Compiles W3C RDF/OWL ontologies into executable Spark DSL extensions, Ash resources, and validation shapes, feeding runtime process-mining metrics back into ontology refinement.

---

## 2. C4 Level 1: System Context Diagram

The System Context diagram establishes the boundary between human intent, autonomous agent coordination, and the deterministic execution fabric.

```mermaid
flowchart TD
    Operator["🧑 Human Operator / Enterprise Client"]
    Agent["🤖 Autonomous Multi-Agent Fabric"]

    subgraph Fabric["Chatman Ecosystem Semantic Execution Fabric"]
        direction TB
        PlanningEngine["Planning & Task Formulation\n(ash_pplan, ggen_igniter)"]
        AdmissionMesh["Two-Port Semantic Mesh & Gate\n(ash_a2a, ash_r2rml, ash_graphlaw)"]
        AttestationEngine["Cryptographic Attestation & Replay\n(ash_affidavit)"]
        ProviderFabric["Provider Execution Boundary\n(xaas)"]
    end

    Marketplace["📦 Ontology Marketplace\n(ggen-marketplace)"]

    Operator -->|"1. Ingests Goals / Policies / FIBO Rules"| PlanningEngine
    Agent -->|"2. Submits WorkOrders & Commands"| AdmissionMesh
    Marketplace -->|"0. Injects Ontology Packs & SHACL Shapes"| PlanningEngine
    PlanningEngine -->|"3. Dispatches Admitted Plans"| AdmissionMesh
    AdmissionMesh -->|"4. Leases & Kernel Admissions"| ProviderFabric
    ProviderFabric -->|"5. Execution Telemetry & Artifacts"| AttestationEngine
    AttestationEngine -->|"6. Signed Receipts & State Updates"| PlanningEngine
    AttestationEngine -->|"7. Cryptographic Audit Proofs"| Operator
```

---

## 3. C4 Level 2: Container Diagram (Repository Boundaries & Interfaces)

The Container diagram illustrates the eight target repositories, their runtime boundaries, communication interfaces, and data models.

```mermaid
flowchart LR
    subgraph MetaLayer["Ontology & Synthesis Tier"]
        MKT["ggen-marketplace\n[RDF / TTL / SHACL Packs]"]
        IGN["ggen_igniter\n[Elixir / Igniter Synthesizer]\nSemantic Jira Kernel & Reconciler"]
    end

    subgraph PlanningLayer["Goal & Strategy Tier"]
        PPLAN["ash_pplan\n[Elixir / Rust FOND Planner]\nHTN / PDDL Domain Compiler"]
    end

    subgraph ProtocolLayer["Mesh & Identity Tier"]
        A2A["ash_a2a\n[Elixir / Ash Extension]\nCommandBus & Two-Port Gate"]
        R2RML["ash_r2rml\n[Elixir / W3C OBDA Engine]\nRelational-to-RDF Mapper"]
    end

    subgraph KernelLayer["Deterministic Admission Tier"]
        GLAW["ash_graphlaw\n[Wasmex / Wasmtime NIF]\nRDFC-1.0 & LawState Kernel"]
        AFF["ash_affidavit\n[Elixir / Wasm Engine]\nReceipt Log & Attestation Store"]
    end

    subgraph ActuationLayer["Provider Execution Tier"]
        XAAS["xaas\n[Elixir / OTP Provider Layer]\nTask Execution & Sandboxing"]
    end

    MKT -->|"Turtle Packs / Shapes"| IGN
    IGN -->|"Generated Ash Resources & WorkOrders"| PPLAN
    IGN -->|"Synthesizes DSL Extensions"| A2A

    PPLAN -->|"Goal Regression & Action Sequence"| A2A
    A2A -->|"Relational State Query"| R2RML
    R2RML -->|"RDFC-1.0 Canonical Graph"| GLAW
    A2A -->|"Signed Ed25519 Lease"| GLAW
    GLAW -->|"Formal Admission / Refusal"| A2A

    A2A -->|"Admitted Command"| XAAS
    XAAS -->|"Execution Telemetry & Side Effects"| AFF
    AFF -->|"Signed Receipt Hash Chain"| IGN
    AFF -->|"Verified State Receipts"| PPLAN
```

---

## 4. C4 Level 3: Component Diagram (Internal Engine Mechanics)

A focused view on the core components inside `ash_a2a`, `ash_graphlaw`, `ash_affidavit`, and `ggen_igniter`.

```mermaid
flowchart TB
    subgraph ash_a2a["ash_a2a Internals"]
        CmdBus["CommandBus"]
        Dispatcher["A2A.Dispatcher"]
        TwoPortGate["Two-Port Identity Validator"]
        CapabilityIndex["CapabilityIndex Compiler"]
    end

    subgraph ash_graphlaw["ash_graphlaw Internals"]
        WasmPool["Wasmex Pool"]
        DigestEngine["RDFC-1.0 Canonicalizer"]
        ShaclValidator["W3C SHACL Validator"]
        LeaseVerifier["Ed25519 Lease Verifier"]
    end

    subgraph ash_affidavit["ash_affidavit Internals"]
        ReceiptStore["ReceiptStore (EKV / Memory)"]
        ChainHasher["Blake3 / SHA256 Chain Hasher"]
        Attestor["Offline Verify Engine"]
    end

    subgraph ggen_igniter["ggen_igniter Internals"]
        Reconciler["SemanticJira.Reconciler"]
        TransitionLog["TransitionLog (ETS/Postgres)"]
        CodeGenerator["Ggen.Igniter Code Generator"]
    end

    Dispatcher --> CmdBus
    CmdBus --> TwoPortGate
    TwoPortGate -->|"Verify Digest Parity"| CapabilityIndex

    TwoPortGate --> LeaseVerifier
    LeaseVerifier --> WasmPool
    DigestEngine --> WasmPool
    ShaclValidator --> WasmPool

    CmdBus -->|"On Success"| ReceiptStore
    ReceiptStore --> ChainHasher
    ChainHasher --> Attestor

    Attestor --> TransitionLog
    TransitionLog --> Reconciler
    Reconciler -->|"Trigger Repair / Generation"| CodeGenerator
```

---

## 5. C4 Dynamic: The Loops of Loops in Motion

### 5.1 Loop 1: The Inner Actuation & Admission Loop (Micro Cycle)

*Frequency: Milliseconds to seconds*  
*Invariant: Zero unreceipted actuation. Real collaborators only.*

```mermaid
sequenceDiagram
    autonumber
    participant Agent as 🤖 Agent / Command Source
    participant A2A as 🛡️ ash_a2a (CommandBus)
    participant R2RML as 🗄️ ash_r2rml (OBDA)
    participant GLAW as ⚖️ ash_graphlaw (WASM)
    participant XAAS as ⚙️ xaas (Provider)
    participant AFF as 📜 ash_affidavit (Receipt)

    Agent->>A2A: Submit Command with Ed25519 Lease
    A2A->>R2RML: Fetch Relational State as RDF Graph
    R2RML-->>A2A: Canonical Graph Digest
    A2A->>A2A: Assert Two-Port Invariant (work_order == state)
    A2A->>GLAW: Transition Check (data, shapes, lease)
    alt Invalid State or Ceiling Exceeded
        GLAW-->>A2A: {:error, %AshGraphLaw.Refusal{code: "LeaseRefused"}}
        A2A-->>Agent: Refusal (Closed, Non-Actuated)
    else State Compliant & Signed
        GLAW-->>A2A: {:ok, %Admitted{subject_sha256: hash}}
        A2A->>XAAS: Execute Admitted Command
        XAAS-->>AFF: Emit Telemetry & Transition Delta
        AFF->>AFF: Append to Hash Chain & Sign Receipt
        AFF-->>A2A: Receipt Token
        A2A-->>Agent: {:ok, Result, Receipt}
    end
```

---

### 5.2 Loop 2: The Outer Goal-Convergence Loop (Macro Cycle)

*Frequency: Seconds to minutes*  
*Invariant: Goals formulated in FOND/HTN must reach deterministic goal states or emit explicit BLOCKED / UNSUPPORTED receipts.*

```mermaid
sequenceDiagram
    autonumber
    participant Client as 🧑 Enterprise Client
    participant IGN as 📋 ggen_igniter (Semantic Jira)
    participant PPLAN as 🧭 ash_pplan (Planner)
    participant A2A as 🛡️ ash_a2a (Mesh)
    participant AFF as 📜 ash_affidavit (Receipts)

    Client->>IGN: Create WorkOrder (Origin Authority, Scope)
    IGN->>IGN: Validate Origin Authority & Hash WorkOrder
    IGN->>PPLAN: Formulate Plan (PDDL Goals / Pre-conditions)
    PPLAN->>PPLAN: FOND Search & HTN Task Decomposition
    loop For Each Step in Plan
        PPLAN->>A2A: Dispatch Subtask via Inner Loop
        A2A-->>PPLAN: Step Receipt or Typed Refusal
        PPLAN->>AFF: Verify Step Receipt on Disk
    end
    PPLAN->>IGN: Complete WorkOrder Transition
    IGN->>IGN: Reconciler Reconciles TransitionLog
    IGN-->>Client: Final Verified Receipt Chain (graphlaw-verify compatible)
```

---

### 5.3 Loop 3: The Meta Synthesis & Evolution Loop (Meta Cycle)

*Frequency: Hours to days / Release Cadence*  
*Invariant: No handwritten boilerplate. Ontology is source; generated code is projection.*

```mermaid
sequenceDiagram
    autonumber
    participant Domain as 🌐 W3C Standards / FIBO / DCAT
    participant MKT as 📦 ggen-marketplace
    participant IGN as ⚙️ ggen_igniter
    participant Code as 💻 Core Repositories (ash_*)
    participant Mining as 📊 Process Mining & Drift (wasm4pm)

    Domain->>MKT: Ingest Public Ontology (TTL / OWL / SHACL)
    MKT->>IGN: Update Pack Dependencies
    IGN->>IGN: Run Synchronous 5-Stage Sync Pipeline
    IGN->>Code: Project Spark DSLs, Schema Modules, Resources
    Code->>Mining: Telemetry Output (OCEL 2.0 Streams)
    Mining->>Mining: Conformance Checking & Fitness Mining
    Mining-->>MKT: Feedback on Drift, Violations & New Constraints
```

---

## 6. Matrix of Repository Responsibilities

| Repository | Primary Loop | Input Artifact | Produced Artifact | Falsifier / Kill Criterion |
|---|---|---|---|---|
| `ash_a2a` | Inner | Signed Commands & Leases | Admitted Actions / Dispatch | Two-Port digest mismatch or expired lease survives. |
| `ash_r2rml` | Inner | PostgreSQL / Relational Tables | RDFC-1.0 Canonical Triples | Unmapped relational change alters state without RDF trace. |
| `ash_graphlaw` | Inner | RDF Data + SHACL Shapes | Typed Refusal or `%Admitted{}` | Invalid state or ceiling breach fails to emit refusal. |
| `ash_affidavit` | Inner / Outer | Telemetry & Execution Proofs | Append-Only Receipt Chain | Receipt chain verifies with missing intermediate hash. |
| `ash_pplan` | Outer | FOND Goals & Preconditions | Action Plans (HDDL / PDDL) | Action plan executes out of topological dependency order. |
| `xaas` | Inner | Admitted Task Execution Request | Isolated Process Output | Provider execution breaches container isolation boundary. |
| `ggen_igniter` | Outer / Meta | RDF WorkOrders & Manifests | Reconciled Event Logs & Code | Reconciler drops unhandled state transition event. |
| `ggen-marketplace` | Meta | Ontological Source Graphs | Versioned Packs & Shape Bundles | Pack contains ungrounded or non-canonical RDF terms. |

---

## 7. Architectural Guarantees

1. **Topological Closure:** No state transition can be applied to persistent storage without traversing both `ash_graphlaw` (WASM semantic admission) and `ash_affidavit` (receipt attestation).
2. **Deterministic Replay:** Any state $S_t$ can be bit-for-bit reconstructed by running `graphlaw-verify` across the receipt logs generated by `ash_affidavit` and `ggen_igniter`.
3. **Mocks Excluded Structurally:** Because all loops exchange cryptographically signed digests and compiled WASM outputs, synthetic mocks (`Mox`, `:meck`) cannot satisfy downstream mathematical verifiers.
