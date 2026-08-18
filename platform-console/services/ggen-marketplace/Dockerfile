# Build context for this Dockerfile is the parent `services/` directory (not this
# directory alone), so the builder stage can reach the real ggen source snapshot
# already staged at `services/ggen/ggen-src/` (populated by services/ggen/prep.sh's
# own upstream snapshot step) without duplicating a second ~150MB copy of the same
# workspace here. Build with:
#   docker build -f services/ggen-marketplace/Dockerfile -t <tag> services/
FROM rustlang/rust:nightly-slim AS builder

# Same rationale as services/ggen/Dockerfile: the host's compiled ggen binaries
# (Mach-O, macOS) cannot run inside this Linux container -- confirmed this pass
# ("Exec format error" running the macOS release build directly in a python:3.12-slim
# container). This stage compiles the real `ggen-cli-lib` crate (the one with the
# `pack list`/`pack query` subcommands this service's app.py shells out to) from the
# real workspace source for the container's own OS/arch, via the checked-in Cargo.lock
# -- a real build of real source, not a simulated one.
WORKDIR /src
COPY ggen/ggen-src/ /src/
# The sibling ggen-src snapshot has no top-level packs/ dir, but ggen-cli-lib's build
# embeds real pack catalog JSON via include_str!(CARGO_MANIFEST_DIR/../../packs/...) --
# confirmed by a real failed build this pass. ggen-marketplace/prep.sh separately
# snapshots the real packs/ tree for this COPY.
COPY ggen-marketplace/ggen-packs-src/ /src/packs/
RUN apt-get update && apt-get install -y --no-install-recommends pkg-config libssl-dev clang && rm -rf /var/lib/apt/lists/*
RUN cargo build --release -p ggen-cli-lib --locked \
    && cp target/release/ggen /usr/local/bin/ggen-built

FROM python:3.12-slim

WORKDIR /app

# facts.json and packs-registry/ must already exist -- produced by
# ggen-marketplace/prep.sh against the real, live project checkouts BEFORE
# `docker build` runs. The container itself never has access to the host repos.
COPY ggen-marketplace/facts.json /app/facts.json
COPY ggen-marketplace/packs-registry/ /app/packs-registry/
COPY ggen-marketplace/app.py /app/app.py
COPY --from=builder /usr/local/bin/ggen-built /usr/local/bin/ggen

RUN chmod +x /usr/local/bin/ggen

ENV FACTS_PATH=/app/facts.json
ENV GGEN_BIN=/usr/local/bin/ggen
ENV GGEN_PACKS_DIR=/app/packs-registry
ENV PORT=8080
EXPOSE 8080

USER nobody

CMD ["python3", "/app/app.py"]
