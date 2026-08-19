FROM rustlang/rust:nightly-slim AS builder

# The host ggen-bin snapshot (Mach-O, built on macOS) cannot run inside this Linux
# container -- confirmed this pass (`file ggen-bin` -> "Mach-O 64-bit executable arm64").
# So instead of COPYing a host binary, this stage compiles the real `ggen` CLI from the
# real workspace source for the container's own OS/arch. The workspace pins a nightly
# toolchain (see /Users/sac/ggen/rust-toolchain.toml); rustlang/rust:nightly-slim tracks
# a recent nightly and `cargo build` resolves via the checked-in Cargo.lock, so this stays
# a real build of the real source, not a simulated one.
WORKDIR /src
# ggen-cli-lib's build uses include_str! against sibling packs/ content
# (e.g. packs/ggen-self-pack/templates/*, packs/fortune5-deployment-blocks-pack/
# catalog/*.json) -- these live inside the same ggen-src/ snapshot (packs/ is a
# real subdirectory of the source repo, not a separate sibling checkout), so a
# single COPY of the whole snapshot is sufficient; this comment documents why
# `packs/` must be present in that snapshot (a prior build failed with real
# "No such file or directory" errors when ggen-src/ was stale and missing it --
# see services/ggen/prep.sh's sibling re-sync step).
COPY ggen-src/ /src/
RUN apt-get update && apt-get install -y --no-install-recommends pkg-config libssl-dev clang && rm -rf /var/lib/apt/lists/*
RUN cargo build --release -p ggen-cli-lib --locked \
    && cp target/release/ggen /usr/local/bin/ggen-built

FROM python:3.12-slim

WORKDIR /app

# facts.json must already exist -- produced by ./prep.sh against the real, live project
# checkout BEFORE `docker build` runs. The container itself never has access to the host
# repos beyond the ggen-src/ source snapshot staged for the builder above.
COPY facts.json /app/facts.json
COPY --from=builder /usr/local/bin/ggen-built /usr/local/bin/ggen
COPY app.py /app/app.py

RUN chmod +x /usr/local/bin/ggen \
    && mkdir -p /app/state/runs /app/state/keys \
    && chown -R nobody:nogroup /app/state

ENV FACTS_PATH=/app/facts.json
ENV GGEN_BIN=/usr/local/bin/ggen
ENV WORKSPACE_ROOT=/app/state/runs
ENV SIGNING_KEY_PATH=/app/state/keys/signing.key
ENV PORT=8080
EXPOSE 8080

USER nobody

CMD ["python3", "/app/app.py"]
