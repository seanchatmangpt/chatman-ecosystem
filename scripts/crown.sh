#!/usr/bin/env bash
set -euo pipefail

cargo fmt --all -- --check
cargo clippy --workspace --all-targets --all-features
cargo test --workspace --all-features
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --all-features --no-deps
cargo run --quiet -p ecosystem-cli --bin ecosystem -- catalog validate
cargo run --quiet -p ecosystem-cli --bin ecosystem -- receipt verify-all
cargo run --quiet -p ecosystem-cli --bin ecosystem -- projection check
cargo run --quiet -p ecosystem-cli --bin ecosystem -- architecture check
cargo run --quiet -p ecosystem-cli --bin ecosystem -- storage verify
cargo run --quiet -p ecosystem-cli --bin ecosystem -- crown --verify
