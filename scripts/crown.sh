#!/usr/bin/env bash
set -euo pipefail

for tool in cargo-deny cargo-machete; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    echo "required admission tool not found: ${tool}" >&2
    exit 2
  fi
done

cargo fmt --all -- --check
cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
cargo test --locked --workspace --all-features
RUSTDOCFLAGS="-D warnings" cargo doc --locked --workspace --all-features --no-deps
cargo deny check
cargo machete
cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- catalog validate
cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- receipt verify-all
cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- projection check
cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- architecture check
cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- storage verify
cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- crown --verify
