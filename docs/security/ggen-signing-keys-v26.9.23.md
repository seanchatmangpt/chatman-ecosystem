# Compromised ggen receipt-signing keys (v26.9.23)

Recorded 2026-09-24 by the single-repo migration (operator security item). These private ed25519 seeds were committed
to this PUBLIC repository's default branch, so they are compromised: every receipt signed with them carries NO signing
authority (standing of such signatures: REFUSED, broken_term R_missing_authority). The private keys are removed from the
tree by this commit (history is not rewritten; no force-push). The next `ggen` run in each directory generates a fresh
keypair, which `.gitignore` (`.ggen/`) keeps out of git; ggen itself is being fixed to write `.ggen/keys/.gitignore`.

| private key path (removed) | sha256 of the compromised private key file | sha256 of its public verifying.key |
|---|---|---|
| `platform-console/services/ggen-marketplace/ggen-packs-src/autofde-lab-capabilities-pack/.ggen/keys/signing.key` | `41d126aeea7c6ac8fe8b5042c7ae2124612f38f38177a4cc1480d6b80124ca24` | `57649332786c5cc9943d9eeac9ae542f78f2d250d8b54e65e3bec96530e5b1c5` |
| `platform-console/services/ggen-marketplace/ggen-packs-src/claude-config-max-pack/examples/consumer/.ggen/keys/signing.key` | `6eac7154c338c903d444f07bfedda0dbdfdb9ea18adf0b90e44f229ada2d9d48` | `095afd05e7422b2f83d9750059ee3fc7a65609d83f6b6b25cc8b1fc961dbaa2c` |
| `platform-console/services/ggen-marketplace/ggen-packs-src/legacy-equivalence-verifier-pack/.ggen/keys/signing.key` | `be0fbab5f9b675613e013836181f8ffd399fbb258fb86cf099d5a40e9c1db086` | `7f2e32ef64f3b5430f7fdc1fc3dea2a0bbe1b3c766b9efd7649e4ecb6d9a7a6f` |

Fleet scan (default branches) found the same class in other repositories; see the migration receipt
`FINAL-RECEIPT.json` (security.fleet_scan) for the list and their owners.
