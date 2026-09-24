# Signing-key rotation (v26.9.24)

Recorded 2026-09-24 (fleet key scan after the single-repo migration). Base `57f4bf2998eb` of `chatman-ecosystem`.
Every private key listed here was committed to this repository and is therefore compromised: every receipt or
attestation signed with it carries no signing authority (standing REFUSED, broken_term R_missing_authority).
The keys leave the tree (history is not rewritten; no force-push), and each key directory's `.gitignore` now
covers both halves. Every checkout keeps its own pair: ggen generates one on first use, and a tracked public
half without its private half would make that first `ggen sync` refuse [FM-KEY-010/011]. The canonical
checkout's new public key is published below for anyone verifying its future receipts.

| key dir | removed private key sha256 | removed public key sha256 | new public key (canonical checkout) |
|---|---|---|---|
| `platform-console/services/ggen-marketplace/ggen-packs-src/autofde-lab-capabilities-pack/.ggen/keys` | removed earlier | `57649332786c5cc9943d9eeac9ae542f78f2d250d8b54e65e3bec96530e5b1c5` | `216bcc4a020f4000ef0bb200dd018b66adab262f3e41aed8a4f16c7c2bbcdbc8` |
| `platform-console/services/ggen-marketplace/ggen-packs-src/claude-config-max-pack/examples/consumer/.ggen/keys` | removed earlier | `095afd05e7422b2f83d9750059ee3fc7a65609d83f6b6b25cc8b1fc961dbaa2c` | `70319f1275270064616c005b0fea066b62e4466ab9d9ccef8d9822af657b00e3` |
| `platform-console/services/ggen-marketplace/ggen-packs-src/legacy-equivalence-verifier-pack/.ggen/keys` | removed earlier | `7f2e32ef64f3b5430f7fdc1fc3dea2a0bbe1b3c766b9efd7649e4ecb6d9a7a6f` | `7241e0b557dfc3feaa9c3811e6b7d51f4135e439ae58eb3ff60dfb3e78b19d9e` |
