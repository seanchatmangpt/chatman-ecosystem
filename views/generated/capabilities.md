# Chatman Ecosystem Capabilities

> Generated from `catalog/capabilities.toml`. Do not edit manually.

| Capability | Class | Authority | Broker | Receipt | Standing | Interfaces |
|---|---|---|---|---|---|---|
| `capability:admit-public-custom-ontology` | `SELECT` | `classify` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:advance-review-readiness` | `DO` | `modify_external_object` | true | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:audit-vacuity` | `OBSERVE` | `observe` | false | false | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:bounded-compatibility-repair` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:classify-branch-standing` | `SELECT` | `classify` | false | false | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:consolidate-wip-train` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:detect-base-drift` | `OBSERVE` | `observe` | false | false | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:enforce-authority-ceiling` | `SELECT` | `classify` | false | false | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:inventory-branch-pr-graph` | `OBSERVE` | `observe` | false | false | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:localize-ci-failure` | `SELECT` | `classify` | false | false | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:manufacture-deterministic-projection` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:merge-exact-head` | `DO` | `merge` | true | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:observe-exact-github-subject` | `OBSERVE` | `observe` | false | false | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:observe-exact-head-workflows` | `OBSERVE` | `observe` | false | false | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:project-interface-surfaces` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:recompose-current-base` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:reconstitute-with-ggen-legacy` | `CONSTRUCT` | `persist_control_plane` | false | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:replay-manufacture` | `OBSERVE` | `observe` | false | false | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:retire-merged-equivalent-branch` | `DO` | `delete` | true | true | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:type-blocker-standing` | `SELECT` | `classify` | false | false | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:verify-source-correspondence` | `OBSERVE` | `observe` | false | false | `CANDIDATE` | cli, api, mcp, a2a |
| `capability:write-pr-receipt` | `CONSTRUCT` | `draft` | false | false | `CANDIDATE` | cli, api, mcp, a2a |

## Dependency graph

- `capability:admit-public-custom-ontology` ← `capability:verify-source-correspondence`
- `capability:advance-review-readiness` ← `capability:write-pr-receipt`, `capability:enforce-authority-ceiling`
- `capability:audit-vacuity` ← `capability:observe-exact-head-workflows`
- `capability:bounded-compatibility-repair` ← `capability:localize-ci-failure`
- `capability:classify-branch-standing` ← `capability:inventory-branch-pr-graph`
- `capability:consolidate-wip-train` ← `capability:classify-branch-standing`, `capability:recompose-current-base`
- `capability:detect-base-drift` ← `capability:observe-exact-github-subject`
- `capability:enforce-authority-ceiling` ← `capability:project-interface-surfaces`
- `capability:inventory-branch-pr-graph` ← `capability:observe-exact-github-subject`
- `capability:localize-ci-failure` ← `capability:observe-exact-head-workflows`
- `capability:manufacture-deterministic-projection` ← `capability:verify-source-correspondence`
- `capability:merge-exact-head` ← `capability:advance-review-readiness`
- `capability:observe-exact-github-subject` ← —
- `capability:observe-exact-head-workflows` ← `capability:observe-exact-github-subject`
- `capability:project-interface-surfaces` ← `capability:admit-public-custom-ontology`
- `capability:recompose-current-base` ← `capability:detect-base-drift`, `capability:classify-branch-standing`
- `capability:reconstitute-with-ggen-legacy` ← `capability:manufacture-deterministic-projection`, `capability:replay-manufacture`
- `capability:replay-manufacture` ← `capability:manufacture-deterministic-projection`
- `capability:retire-merged-equivalent-branch` ← `capability:classify-branch-standing`
- `capability:type-blocker-standing` ← `capability:localize-ci-failure`
- `capability:verify-source-correspondence` ← `capability:observe-exact-github-subject`
- `capability:write-pr-receipt` ← `capability:observe-exact-head-workflows`, `capability:enforce-authority-ceiling`
