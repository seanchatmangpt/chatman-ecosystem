# Qualification fixtures — receipt-provenance-unification-pack

Real receipts and one-mutation variants of them, run by `generated/qualification_runner.py`
(generated from the `rp:QualificationSuite` facts in `ontology.ttl`). Naming law in every
suite: `pos-*.json` must exit 0; `neg-*.json` must exit 1 and print a broken_term matching the
suite's `rp:refusalTermPattern`. No output may contain a traceback.

Base receipt: xaas `docs/sjira/v26.9.23/receipts/GC23-4.json` (worktree
`/Users/sac/wt/v26922/fri/xaas-int`, blob at commit `295e0200a9f61b78d4a631c667e4851cff7b8bb1`),
sha256 `628a1eaf90bfc14f84262a50d798a52a1bd86ffaddba012ba1fb72a8978ced43`.
Mutants are re-serialized with sorted keys and 2-space indent.

| suite | args | parity with validate_receipt.py |
|---|---|---|
| `dfcm_fleet_v1/` | `--contract=dfcm_fleet_v1` | yes |
| `durable/` | `--contract=dfcm_fleet_v1 --require-durable --repo-map seanchatmangpt/xaas=<xaas checkout>` | no (profile is stricter by design) |
| `durable_standing/` | same as `durable/` | no |

Run: `python3 generated/qualification_runner.py --repo-map seanchatmangpt/xaas=/Users/sac/wt/v26922/fri/xaas-int`
(from any cwd; fixtures with `identity.repo = "."` resolve against the pack directory, which must be
inside a ggen-marketplace checkout that holds commit `420bc91e7c1e291be73ab749b7e443252bc7bab8`).

## Derivation of every fixture

| fixture | sha256 | derivation |
|---|---|---|
| `dfcm_fleet_v1/pos-base-GC23-4.json` | `628a1eaf90bfc14f` | unmodified copy (re-serialized, sorted keys) of /Users/sac/wt/v26922/fri/xaas-int/docs/sjira/v26.9.23/receipts/GC23-4.json sha256:628a1eaf90bfc14f84262a50d798a52a1bd86ffaddba012ba1fb72a8978ced43 |
| `dfcm_fleet_v1/pos-exit-integral-float.json` | `c8bf17bd2c9f6799` | replay exit 75 -> 75.0 (JSON Schema draft 4+ integer admits an integral float) |
| `dfcm_fleet_v1/pos-durable-location-empty.json` | `c8a7289c4465381d` | replay.durable_location -> "" (schema: type string, no minLength) |
| `dfcm_fleet_v1/pos-files-changed-empty-string.json` | `3cfc7d7aa59a9d1b` | consequence.files_changed -> [""] (items type string, no minLength) |
| `dfcm_fleet_v1/pos-alive-exit0.json` | `fa07763e8f292b7c` | standing.value -> ALIVE and replay exit -> 0 |
| `dfcm_fleet_v1/pos-local-repo-known-commit.json` | `7ce5ae9bf8fd16f1` | identity.repo -> "." and subject_sha -> 420bc91e7c1e291be73ab749b7e443252bc7bab8 (marketplace commit; validate_receipt.py:20-25 probes it) |
| `dfcm_fleet_v1/neg-notasha.json` | `b937dd23c0b3c2cd` | identity.subject_sha -> NOTASHA |
| `dfcm_fleet_v1/neg-no-standing-value.json` | `76da636224d677bc` | standing.value deleted |
| `dfcm_fleet_v1/neg-alive-nonzero-exit.json` | `2e2f5735eebe8609` | standing.value -> ALIVE with the replay exit 75 kept (admission_vacuous, validate_receipt.py:18) |
| `dfcm_fleet_v1/pos-alive-trailing-newline-exit75.json` | `f60896c89358c216` | standing.value -> "ALIVE\n": passes the schema pattern ($) but is not == ALIVE, so validate_receipt.py admits it |
| `dfcm_fleet_v1/neg-empty-replay.json` | `18e522910609487f` | replay.commands -> [] (minItems 1) |
| `dfcm_fleet_v1/neg-no-consequence.json` | `ab566510a8e347db` | consequence deleted |
| `dfcm_fleet_v1/neg-commits-not-array.json` | `f0a68e507b28a215` | consequence.commits -> "abc1234" (type array) |
| `dfcm_fleet_v1/neg-commit-bad-item.json` | `412c5f78f118863f` | consequence.commits -> [NOTASHA] (items pattern) |
| `dfcm_fleet_v1/neg-files-changed-int-item.json` | `cd6abd788cd95511` | consequence.files_changed -> [1] (items type string) |
| `dfcm_fleet_v1/neg-blocked-no-broken-term.json` | `b019669cab0a9324` | standing.value -> BLOCKED:operator without broken_term (allOf if/then) |
| `dfcm_fleet_v1/neg-bad-broken-term.json` | `28b256495987e371` | standing.broken_term -> R_missing_everything (enum) |
| `dfcm_fleet_v1/neg-bad-ceiling.json` | `ecfa74f685ec83a9` | authority.ceiling -> ROOT (enum) |
| `dfcm_fleet_v1/neg-ceiling-trailing-newline.json` | `541c71680eef61c3` | authority.ceiling -> "DO\n" (enum equality refuses the newline) |
| `dfcm_fleet_v1/neg-bad-output-sha.json` | `24105db43ce075f0` | replay output_sha256 -> xyz (pattern) |
| `dfcm_fleet_v1/neg-graph-hash-null.json` | `9a63247715a2185a` | identity.graph_hash -> null (optional but typed string) |
| `dfcm_fleet_v1/neg-summary-int.json` | `c91bf6c50c13ac17` | replay summary -> 5 (type string) |
| `dfcm_fleet_v1/neg-exit-bool.json` | `e397f64a598cfa3c` | replay exit -> true (bool is not an integer) |
| `dfcm_fleet_v1/neg-exit-fractional.json` | `6134dc7fe1202411` | replay exit -> 0.5 |
| `dfcm_fleet_v1/neg-grant-empty.json` | `e98017f59836abe3` | authority.grant -> "" (minLength 1) |
| `dfcm_fleet_v1/pos-subject-newline-only.json` | `8dc8cc5de5e9b22a` | identity.subject -> "\n": minLength 1 passes |
| `dfcm_fleet_v1/neg-local-repo-missing-commit.json` | `300c92bf5e78da4b` | identity.repo -> "." and subject_sha -> 000..0 (validate_receipt.py:20-25 refuses: not a commit) |
| `dfcm_fleet_v1/neg-standing-not-object.json` | `b756b63b24a3735c` | standing -> "ALIVE" (type object) |
| `dfcm_fleet_v1/neg-root-array.json` | `37517e5f3dc66819` | document -> [] (type object) |
| `durable/neg-forged-GC23-4.json` | `5fbf448d56fb7c32` | byte copy of /private/tmp/claude-501/v23-scratch/SCAN-stale-evidence/forged-GC23-4.json sha256:5fbf448d56fb7c3293dd742c28bfd06caa1e822a7663478fede355a27dea7739 |
| `durable/neg-forged-slug-notes-sha0.json` | `9e2a5970946e6f1f` | byte copy of /private/tmp/claude-501/v23-scratch/SCAN-CE23-9-validator-durable-identity-profile/forged-slug-notes-sha0.json sha256:9e2a5970946e6f1ff8c9af1e4706bf81ebc9bd23bffcf33e60a87f24e9d6d42f |
| `durable/pos-git-blob.json` | `b33ed69f4c4d5c1a` | GC23-4 with identity.repo -> seanchatmangpt/xaas and durable_location -> git:seanchatmangpt/xaas@295e0200a9f61b78d4a631c667e4851cff7b8bb1:docs/sjira/v26.9.23/receipts/GC23-4.json (blob exists there; subject 11a24fb is its ancestor) |
| `durable/pos-https-form-only.json` | `969391db5c34be29` | GC23-4 with slug repo and an https durable_location (accepted by form only; the VALID output says so) |
| `durable/neg-blob-not-descendant.json` | `6c4a2751d1f9ea44` | durable_location -> git:...@bd1efb165f625e3505953b2c242196838d4311b6:mix.exs: the blob exists but that commit is the subject's base, not a descendant (ancestor_of fails) |
| `durable/neg-blob-missing-path.json` | `5c4e01e555fed705` | durable_location names a path absent at that commit (blob_at_commit fails) |
| `durable/neg-relative-path.json` | `5f3d69667a0b9d52` | durable_location left as the committed relative path docs/sjira/.../GC23-4.json: names no repository and no commit |
| `durable/neg-tmp-location.json` | `1537bfe0d1941de9` | durable_location -> /tmp/GC23-4.json (ephemeral local path) |
| `durable/neg-var-folders-location.json` | `57c9b127c2043137` | durable_location -> /var/folders/... (ephemeral local path) |
| `durable/neg-unmapped-slug.json` | `b39590fe89a34637` | identity.repo and the location repo -> seanchatmangpt/not-mapped (no --repo-map entry) |
| `durable/neg-subject-not-in-repo.json` | `9a5aa767e8ca699b` | identity.subject_sha -> 420bc91e7c1e291be73ab749b7e443252bc7bab8 (a real commit, but of ggen-marketplace, not of the mapped xaas repository) |
| `durable/neg-dotdot-slug.json` | `b4ca797ca7f7d6f9` | identity.repo -> ../xaas (path segment, not a slug) |
| `durable_standing/neg-alive-trailing-newline.json` | `750ef42f881cfac7` | pos-git-blob.json with standing.value -> "ALIVE\n" and the replay exit 75 kept: admitted by the default profile (schema $), refused by the durable profile (\Z) |
| `durable_standing/pos-unknown-exact.json` | `b33ed69f4c4d5c1a` | same receipt as durable/pos-git-blob.json (standing UNKNOWN, exact): the strict standing binding admits it |
| `durable/neg-sha0-https.json` | `c2dbcd911b9c8877` | slug repo, subject_sha -> 000..0, https durable_location: only the durable subject_commit probe can refuse it (R_missing_identity) |
