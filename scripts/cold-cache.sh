#!/usr/bin/env bash
set -euo pipefail

# Cold-cache is itself an admission gate for the final Crown. It must prove that
# the exact subject passes from an empty target directory, but it cannot verify
# the Crown before the downstream crown job has assembled target/crown/admission.json.
# Keep this court dependency-acyclic: cold-cache proves clean-build behavior;
# the Crown job later binds this successful gate into the exact-subject admission.
rm -rf target
CARGO_INCREMENTAL=0 cargo test --locked --workspace --all-features
