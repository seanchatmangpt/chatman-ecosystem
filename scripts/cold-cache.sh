#!/usr/bin/env bash
set -euo pipefail

rm -rf target
CARGO_INCREMENTAL=0 cargo test --locked --workspace --all-features
CARGO_INCREMENTAL=0 cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- crown --verify
