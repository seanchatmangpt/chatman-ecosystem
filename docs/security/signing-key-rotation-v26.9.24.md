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

## Keys exposed on non-default branches (revoked 2026-09-24)

The v26.9.24 rotation scanned default branches only. A scan of every `origin/*` branch found the
private keys below committed on non-default branches only. Each is compromised and revoked: any receipt
or attestation signed with it carries no signing authority (standing REFUSED, broken_term
R_missing_authority). A disk scan of the canonical checkouts on 2026-09-24 found three of these keys in
use (ggen/packs, ignored files) and replaced them with fresh pairs. Copies in agent worktrees and tool
caches may still hold them. History is not rewritten, so the branches keep the blobs.

| path | private key sha256 | derived public key | branches (count, first) |
|---|---|---|---|
| `platform-console/services/ggen-marketplace/ggen-packs-src/autofde-lab-capabilities-pack/.ggen/keys/signing.key` | `41d126aeea7c6ac8fe8b5042c7ae2124612f38f38177a4cc1480d6b80124ca24` | `b92a6da5ef7aa011dcdb3d9aac443a7c394b4ff3dda25956027428b791d43534` | 8, `adopt/engineering-standards-v26.9.21` |
| `platform-console/services/ggen-marketplace/ggen-packs-src/claude-config-max-pack/examples/consumer/.ggen/keys/signing.key` | `6eac7154c338c903d444f07bfedda0dbdfdb9ea18adf0b90e44f229ada2d9d48` | `5c2b44448201260aa702141481598009f7851ea07578e3a64593ebde1157f23f` | 8, `adopt/engineering-standards-v26.9.21` |
| `platform-console/services/ggen-marketplace/ggen-packs-src/legacy-equivalence-verifier-pack/.ggen/keys/signing.key` | `be0fbab5f9b675613e013836181f8ffd399fbb258fb86cf099d5a40e9c1db086` | `cf1b161d57783984c61ff756d434898ecc5663366f56b2ed5a9168c0d0689a2f` | 8, `adopt/engineering-standards-v26.9.21` |
