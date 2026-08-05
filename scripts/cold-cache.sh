#!/usr/bin/env bash
set -euo pipefail
rm -rf target
CARGO_INCREMENTAL=0 cargo test --workspace --all-features
CARGO_INCREMENTAL=0 cargo run --quiet -p ecosystem-cli --bin ecosystem -- crown --verify
