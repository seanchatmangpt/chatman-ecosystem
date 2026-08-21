# ggen ↔ Igniter ↔ Ash: Real Pipeline Diagrams

These four diagrams are grounded in this session's real, verified work: a real source-code
audit of ggen-engine's `sync.rs` (`run_shell_hook`, ~line 1839) and `shell_safety.rs` (16-substring
denylist, self-documented as "not a sandbox"); real deep-research on Igniter/Ash with cited
sources (ash-project.github.io/igniter, github.com/ash-project/igniter, Ash's
`generators.md` doc); the real artifacts `ash-igniter-gen-pipeline-pack` and
`ash-subproject-pack-generator`; and the real `MATURITY-MATRIX.md` 5-level×7-metric scoring
(including the cited Idempotency L5 evidence of 34 written → 34/34 skipped on repeat runs,
and the still-open Safety/Authorization L1 finding). Each diagram's caption states exactly
which edges are documented/verified versus inferred/open, matching how they were drafted.

## 1. Igniter internals

This diagram traces Igniter's generator-composition flow for `mix igniter.install ash` — CLI
invocation through `Mix.Task` wrapping, `Igniter.compose_task/3` fan-out to sub-generators, and
AST-aware semantic patching — sourced from this session's deep-research citations
(ash-project.github.io/igniter, github.com/ash-project/igniter, Ash's `generators.md` doc). It
also distinguishes the three real entry tasks (`igniter.install` / `igniter.new` /
`igniter.upgrade`) per that same documentation.

```mermaid
sequenceDiagram
    actor Dev as Developer/CLI
    participant Mix as Mix.Task runner
    participant IT as Igniter task<br/>(e.g. Igniter.Install)
    participant Compose as Igniter.compose_task/3
    participant Sub1 as Sub-generator A<br/>(e.g. ash.gen.resource)
    participant Sub2 as Sub-generator B<br/>(e.g. ash.gen.domain)
    participant AST as Igniter AST engine<br/>(semantic patch)
    participant FS as Project source files

    Dev->>Mix: mix igniter.install ash
    Note over Mix,IT: Igniter task wraps Mix.Task<br/>(documented: ash-project.github.io/igniter,<br/>github.com/ash-project/igniter)
    Mix->>IT: dispatch to Igniter-backed task
    IT->>Compose: compose_task/3(igniter, task_name, argv)
    Note right of Compose: Internal call graph of<br/>compose_task/3 is INFERRED —<br/>exact fan-out/ordering logic was an<br/>OPEN question in this session's<br/>deep-research (not yet verified)

    Compose->>Sub1: invoke sub-generator (composed)
    Compose->>Sub2: invoke sub-generator (composed)
    Note over Sub1,Sub2: Backs Ash's 8 documented<br/>ash.gen.* tasks: resource, domain, enum,<br/>base_resource, change, validation,<br/>preparation, custom_expression<br/>(source: ash generators.md)

    Sub1->>AST: propose code change (add resource module)
    Sub2->>AST: propose code change (register in domain)
    Note over AST,FS: AST-aware semantic patching —<br/>NOT naive file overwrite/stamping<br/>(documented distinction, igniter.install)
    AST->>FS: apply merged patch (preserves existing code structure)
    FS-->>Dev: modified project files

    Note over Dev,FS: Three real Igniter entry points (documented, distinct):<br/>igniter.install = add + configure a new dependency<br/>igniter.new = scaffold a brand-new Mix project<br/>igniter.upgrade = migrate an existing dependency across versions
```

## 2. Ash's `ash.gen.*` family

```mermaid
flowchart TD
    subgraph Igniter["Igniter (AST-aware codegen engine)"]
        C["Igniter.compose_task/3"]
    end

    T1["mix ash.gen.resource"] --> C
    T2["mix ash.gen.domain"] --> C
    T3["mix ash.gen.enum"] --> C
    T4["mix ash.gen.base_resource"] --> C
    T5["mix ash.gen.change"] --> C
    T6["mix ash.gen.validation"] --> C
    T7["mix ash.gen.preparation"] --> C
    T8["mix ash.gen.custom_expression"] --> C

    C -->|semantic patch| R1["Resource module\n(e.g. MyApp.Blog.Post)"]
    C -->|semantic patch| R2["Domain module\n(e.g. MyApp.Blog)"]
    C -->|semantic patch| R3["Enum/type module"]
    C -->|semantic patch| R4["Base resource module"]
    C -->|inject into resource| R5["Change module"]
    C -->|inject into resource| R6["Validation module"]
    C -->|inject into resource| R7["Preparation module"]
    C -->|inject into resource| R8["Custom expression module"]

    R1 -->|"registered in"| R2
    R3 -->|"registered in"| R2
    R4 -.->|"used as behaviour by"| R1
    R5 -.->|"attached to actions on"| R1
    R6 -.->|"attached to actions on"| R1
    R7 -.->|"attached to actions on"| R1
    R8 -.->|"used in calculations on"| R1

    R2 -->|"interact via domain API"| App["Calling app code\n(Ash.read/create/etc via Domain)"]
```

This diagram reflects only the real, documented mechanics established this session: Igniter's
`Igniter.compose_task/3` composition point wraps `Mix.Task` and performs AST-aware (not
file-stamping) codegen, per ash-project.github.io/igniter and github.com/ash-project/igniter;
the 8 `ash.gen.*` tasks are the ones documented in
github.com/ash-project/ash/documentation/topics/development/generators.md; and the "resources
are tied together by a domain module used to interact with them" relationship is the
deep-research's stated fact, not invented. The finer edges (e.g. exactly which AST insertion
points each generator targets, whether `base_resource`/`change`/`validation`/`preparation`/
`custom_expression` write new files vs. patch existing ones) are not yet verified this session
and are shown only at the level of granularity the research actually confirmed.

## 3. The ggen ↔ Igniter bridge (the safety-relevant one)

```mermaid
sequenceDiagram
    participant TTL as ontology.ttl (RDF facts)
    participant SPARQL as ggen SPARQL for_each
    participant Tera as Tera template renderer
    participant Safety as check_shell_command_safe (16-substring denylist)
    participant Shell as sh -c (std::process::Command)
    participant Mix as mix ash.gen.*/ash.extend process
    participant Igniter as Igniter (AST-aware codemod, inside Mix process)
    participant Receipt as .agp-receipts/*.txt

    TTL->>SPARQL: agp:CodegenTarget rows (moduleName, domainModule, mixTask, mixArgs, ...)
    SPARQL->>Tera: for_each row -> bind row fields into template context
    Tera->>Tera: render sh_after string, interpolating row fields verbatim
    Tera->>Safety: pass fully-interpolated sh_after string
    Safety->>Safety: scan string against 16 denylist substrings (sync.rs shell_safety.rs)
    Note over Safety: Disclosed gap: denylist checks the ALREADY-interpolated<br/>string. A malicious or malformed ontology field is rendered in<br/>BEFORE this check, so an injected second command that avoids<br/>all 16 substrings is not caught. shell_safety.rs's own doc<br/>comment states it is not a sandbox.
    alt denylist match found
        Safety-->>Tera: reject, run_shell_hook fails closed
    else no match
        Safety->>Shell: approved sh_after string
        Shell->>Mix: spawn "sh -c '<sh_after>'" with current_dir(root)
        Mix->>Igniter: Igniter.compose_task/3 invoked inside mix task
        Igniter->>Igniter: AST-aware semantic patch of target .ex files
        Note over Shell,Igniter: Boundary: ggen has ZERO visibility into what Igniter<br/>actually changes inside this process. It only observes<br/>the process's exit code and captured stdout/stderr.<br/>No diff, no AST, no file list crosses back to ggen.
        Mix-->>Shell: exit code + stdout/stderr
        Shell-->>Safety: process result
    end
    Safety-->>SPARQL: run_shell_hook returns (fail-closed on non-zero exit)
    SPARQL->>Receipt: write receipt (to: field) — records ggen's own action, not Igniter's diff
```

This sequence is grounded in
`~/chatman-ecosystem/platform-console/services/ggen/ggen-src/crates/ggen-engine/src/sync.rs`
(`run_shell_hook`, ~line 1839) and `shell_safety.rs` (16-substring denylist, self-documented as
"not a sandbox"), plus the frontmatter chain `sparql:` → `for_each:` → per-row Tera-rendered
`sh_after` → `run_shell_hook`. The safety-critical detail is that the denylist inspects the
string only after Tera has already interpolated ontology row values into it — a crafted field
can inject a second shell command that never matches any of the 16 substrings, and this is a
real disclosed gap, not a hypothetical. Equally important: once `sh -c` spawns the
`mix ash.gen.*`/`mix ash.extend` process, Igniter's AST-aware codemod happens entirely inside
that child process — ggen observes only the exit code and stdout/stderr, never the actual file
diff, and the receipt it writes to `.agp-receipts/*.txt` documents that ggen ran the hook, not
what Igniter changed.

## 4. The full end-to-end pipeline

```mermaid
flowchart TD
    A["hex.pm ecosystem search<br/>137 real packages depend on ash"] --> B{"admission filter<br/>>=20000 downloads"}
    B -->|34 admitted| C["asg:AshSubproject ontology facts<br/>ash-subproject-pack-generator"]
    D["2 real Igniter mix tasks proven<br/>against ~/xaas: mix ash.gen.resource,<br/>mix ash.extend"] --> E["agp:CodegenTarget ontology facts<br/>moduleName/domainModule/mixTask/mixArgs<br/>ash-igniter-gen-pipeline-pack"]

    C --> F["ggen sync: SPARQL for_each<br/>over ontology.ttl rows"]
    E --> F
    F --> G["per-row Tera-rendered<br/>sh_after string (frontmatter)"]
    G --> H["run_shell_hook (sync.rs ~L1839)<br/>check_shell_command_safe(cmd)"]
    H --> I{"shell_safety.rs<br/>16-substring denylist<br/>(not a sandbox, disclosed gap:<br/>Tera values enter cmd before check)"}
    I -->|pass| J["std::process::Command 'sh -c'<br/>current_dir(root), fail-closed on nonzero exit"]
    I -.->|open finding| N["Safety/Authorization L1<br/>still open in MATURITY-MATRIX.md"]

    J --> K["pack.toml skeleton written<br/>(scaffold_pack.tmpl, 34 rows)"]
    J --> L["real Ash resource/extension<br/>AST-aware codemod via Igniter<br/>(Igniter.compose_task/3)"]

    K --> M1["receipt/log: 34 written,<br/>then 34/34 skipped on repeat runs"]
    L --> M2["receipt/log from pipeline pack run"]

    M1 --> O["MATURITY-MATRIX.md<br/>5-level x 7-metric scoring"]
    M2 --> O
    O -->|"Idempotency L5, cited:<br/>34 written -> 34/34 skipped"| P["score feeds back:<br/>what to fix next"]
    P --> N
    N -.->|feedback loop| H
```

This traces the one real, already-built pipeline: hex.pm's 137-package ash-ecosystem search
admits 34 packages (≥20000 downloads) into `asg:AshSubproject` facts, in parallel with
`agp:CodegenTarget` facts proven against 2 real Igniter mix tasks in `~/xaas`, both consumed by
the same real ggen sync mechanism (SPARQL `for_each` → Tera `sh_after` → `run_shell_hook` in
`sync.rs`). That hook's 16-substring denylist (`shell_safety.rs`, explicitly "not a sandbox")
gates a real `sh -c` spawn — for the subproject pack, `pack.toml` skeletons written idempotently
(34 written, then 34/34 skipped on repeat runs, per the real receipt log); for the pipeline
pack, real AST-aware Igniter codemods against Ash resources/extensions. Both write receipt/log
evidence back into `MATURITY-MATRIX.md`'s 5-level×7-metric scoring — the cited Idempotency L5
example is real — and that scoring closes the loop by feeding back into what needs fixing next,
including the still-open Safety/Authorization L1 finding tied to the denylist's disclosed
shell-injection gap.
