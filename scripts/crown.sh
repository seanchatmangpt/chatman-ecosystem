#!/usr/bin/env bash
set -euo pipefail

for tool in cargo-deny cargo-machete curl jq python3 sha256sum; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    echo "required admission tool not found: ${tool}" >&2
    exit 2
  fi
done

candidate_sha="$(git rev-parse HEAD)"
test "${#candidate_sha}" -eq 40

python3 scripts/verify_release.py --check-refs
python3 scripts/verify_standing_evidence.py
python3 scripts/verify_crown_edges.py

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
cargo run --locked --quiet -p chatman-ecosystem-gall --bin gall

./scripts/cold-cache.sh
cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- receipt verify-all
cargo build --locked --release -p ecosystem-cli --bin ecosystem

rm -rf target/crown-artifact
mkdir -p target/crown-artifact/receipts
cp target/release/ecosystem target/crown-artifact/ecosystem
cp target/crown/receipts/*.toml target/crown-artifact/receipts/
cat > target/crown-artifact/build-manifest.json <<JSON
{
  "source_sha": "${candidate_sha}",
  "toolchain": "$(rustc --version)",
  "target": "$(rustc -vV | sed -n 's/^host: //p')",
  "cargo_lock_sha256": "$(sha256sum Cargo.lock | awk '{print $1}')",
  "binary_sha256": "$(sha256sum target/crown-artifact/ecosystem | awk '{print $1}')"
}
JSON

test "$(jq -r '.source_sha' target/crown-artifact/build-manifest.json)" = "${candidate_sha}"
test "$(jq -r '.cargo_lock_sha256' target/crown-artifact/build-manifest.json)" = "$(sha256sum Cargo.lock | awk '{print $1}')"
test "$(jq -r '.binary_sha256' target/crown-artifact/build-manifest.json)" = "$(sha256sum target/crown-artifact/ecosystem | awk '{print $1}')"
test -s target/crown-artifact/receipts/bootstrap.toml

headers=(-H 'Accept: application/vnd.github+json')
if [[ -n "${GH_TOKEN:-}" ]]; then
  headers+=(-H "Authorization: Bearer ${GH_TOKEN}")
fi
remote_commit="$(curl --fail --silent --show-error "${headers[@]}" "https://api.github.com/repos/seanchatmangpt/chatman-ecosystem/commits/${candidate_sha}")"
test "$(jq -r '.sha' <<<"${remote_commit}")" = "${candidate_sha}"

mkdir -p target/crown
cat > target/crown/admission.json <<JSON
{
  "subject": "git:${candidate_sha}",
  "gates": [
    "release_graph",
    "standing_evidence",
    "mandatory_crown_edges",
    "format",
    "clippy",
    "tests",
    "rustdoc",
    "dependency_policy",
    "catalog",
    "receipts",
    "projection",
    "architecture",
    "storage_differential",
    "gall_sequence",
    "cold_cache",
    "github_read",
    "artifact_transfer"
  ]
}
JSON

ECOSYSTEM_SUBJECT_SHA="${candidate_sha}" cargo run --locked --quiet -p ecosystem-cli --bin ecosystem -- crown --verify
