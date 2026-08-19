# Deterministic Dynamic UI federation

This directory is the composition-root contract for ecosystem-wide Deterministic Dynamic UI (DDUI).

`chatman-ecosystem` does not own component implementation. Each participating repository owns its bounded `dd-ui/world.json` observations. `federation.json` pins those observations to exact repository SHAs and pins the shared projection engine to one exact wasm4pm DDUI v2 SHA.

The federation law is:

`UI_t = P(union(G_component,t), alpha, kappa, rho, Gamma)`

The union is observation composition only. Component standing remains scoped to the owning repository and exact subject. No red edge is allowed to erase evidence for unrelated components, and no `UNKNOWN` component may be promoted by composition.

DfCM preserves reversible presentation candidates before deterministic presentation selection. Every projection must retain `irreversibleUiSelections = 0`; runtime AI has no render authority; rendering has no direct actuation authority; projected controls are unselected intents; DO remains behind the owning BRCE/broker boundary.

The federation verifier materializes every pinned component profile and the exact DDUI engine, checks those identities, unions the event worlds, projects all 5 admitted avatars across all 4 admitted contexts, and requires receipt replay for all 20 executive/system views.
