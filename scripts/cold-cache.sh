#!/usr/bin/env bash
set -euo pipefail

# Cold-cache is itself an admission gate for the final Crown: it proves the
# candidate can rebuild and satisfy all pre-admission courts from an empty
# target directory. The final Crown admission is downstream of this gate, so
# an admission artifact appearing here would be circular authority rather
# than evidence. Keep this court dependency-acyclic.
rm -rf target
test ! -e target/crown/admission.json

CARGO_INCREMENTAL=0 cargo test --locked --workspace --all-features
CARGO_INCREMENTAL=0 cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- catalog validate
CARGO_INCREMENTAL=0 cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- architecture check
CARGO_INCREMENTAL=0 cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- projection check
CARGO_INCREMENTAL=0 cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- receipt verify-all
CARGO_INCREMENTAL=0 cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- storage verify

test ! -e target/crown/admission.json
