# Chatman Ecosystem Capabilities

> Generated from `catalog/capabilities-decision-graph.toml`. Do not edit manually.

| Capability | Class | Authority | Broker | Receipt | Standing | Interfaces |
|---|---|---|---|---|---|---|
| `capability:admit-capability-plan` | `SELECT` | `classify` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:admit-planner-policy-role-separation` | `SELECT` | `classify` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:attest-affidavit-standing` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:bound-ww3gym-simulation` | `SELECT` | `classify` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:broker-consequential-do` | `DO` | `modify_external_object` | true | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:compile-bounded-oracle` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:compute-bounded-cmca` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:distribute-ggen-pack` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:enforce-live-azure-authority` | `SELECT` | `classify` | false | true | `BLOCKED` | cli, api, mcp, a2a |
| `capability:execute-bounded-domain-gym` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:execute-gym-world` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:falsify-candidate-plan` | `SELECT` | `classify` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:manufacture-with-ggen` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:orchestrate-manufacturing-work` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:persist-autofde-runtime` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:plan-decision-frontier` | `SELECT` | `classify` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:reconstitute-project-protocol-suite` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |

## Dependency graph

- `capability:admit-capability-plan` ← `capability:falsify-candidate-plan`
- `capability:admit-planner-policy-role-separation` ← `capability:admit-public-custom-ontology`
- `capability:attest-affidavit-standing` ← `capability:replay-manufacture`, `capability:observe-exact-github-subject`
- `capability:bound-ww3gym-simulation` ← `capability:execute-bounded-domain-gym`
- `capability:broker-consequential-do` ← `capability:persist-autofde-runtime`, `capability:enforce-authority-ceiling`
- `capability:compile-bounded-oracle` ← `capability:admit-public-custom-ontology`
- `capability:compute-bounded-cmca` ← `capability:admit-capability-plan`
- `capability:distribute-ggen-pack` ← `capability:manufacture-with-ggen`, `capability:replay-manufacture`
- `capability:enforce-live-azure-authority` ← `capability:enforce-authority-ceiling`
- `capability:execute-bounded-domain-gym` ← `capability:execute-gym-world`
- `capability:execute-gym-world` ← `capability:orchestrate-manufacturing-work`, `capability:enforce-authority-ceiling`
- `capability:falsify-candidate-plan` ← `capability:plan-decision-frontier`
- `capability:manufacture-with-ggen` ← `capability:admit-capability-plan`, `capability:admit-public-custom-ontology`
- `capability:orchestrate-manufacturing-work` ← `capability:compute-bounded-cmca`, `capability:admit-capability-plan`
- `capability:persist-autofde-runtime` ← `capability:admit-capability-plan`, `capability:orchestrate-manufacturing-work`
- `capability:plan-decision-frontier` ← `capability:admit-planner-policy-role-separation`, `capability:enforce-authority-ceiling`
- `capability:reconstitute-project-protocol-suite` ← `capability:reconstitute-with-ggen-legacy`, `capability:project-interface-surfaces`, `capability:admit-public-custom-ontology`
