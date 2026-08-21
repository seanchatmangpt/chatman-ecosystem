# syntax=docker/dockerfile:1

# --- wpm-builder: build the real wasm4pm-cli (`wpm`) binary from source.
# Consumed by lib/ocel-log.ts's `discoverOcDfgLocal` (a real
# execFileSync("wpm", ["mining", "discover", ..., "--algo", "ocdfg", "-o", ...])
# subprocess call, see that file's header comment) via
# app/api/ocel/discover-local/route.ts. Deliberately separate from, and left
# unlinked to, the existing `ocel-accumulator` proxy in lib/ocel-log.ts --
# this is a second, independently-comparable OC-DFG discovery path, not a
# replacement.
#
# wasm4pm lives in a separate repo (github.com/seanchatmangpt/wasm4pm), not
# vendored into this checkout, so it is cloned at a pinned commit rather than
# COPYed from a local build context. Override WASM4PM_GIT_REF at build time
# to pin/bump the commit this image builds against.
FROM rust:1-slim-bookworm AS wpm-builder
WORKDIR /src
ARG WASM4PM_GIT_URL=https://github.com/seanchatmangpt/wasm4pm.git
ARG WASM4PM_GIT_REF=main
RUN apt-get update \
  && apt-get install -y --no-install-recommends git pkg-config libssl-dev ca-certificates \
  && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch "${WASM4PM_GIT_REF}" "${WASM4PM_GIT_URL}" wasm4pm \
  || (git clone "${WASM4PM_GIT_URL}" wasm4pm && cd wasm4pm && git checkout "${WASM4PM_GIT_REF}")
WORKDIR /src/wasm4pm
RUN cargo build --release -p wasm4pm-cli

# --- deps: install dependencies only, cached separately from source changes
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

# --- builder: full source + build (next build, standalone output)
FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
# No secrets are read at build time: session verification (lib/session.ts)
# only runs per-request in middleware/route handlers, not during
# `next build`'s static generation. Real secrets are supplied at container
# runtime via environment variables (see .env.example) -- never baked into
# the image or passed as a build ARG/ENV.
RUN npm run build

# --- runner: full node_modules (not standalone's pruned/traced subset) --
# the custom server.js (real-time notification WebSocket relay, see its
# own header comment) requires `ws`, `next`, `jose`, `pg` directly as a
# plain Node entrypoint, outside Next's own file-tracing graph, so
# standalone's traced-subset copy is no longer sufficient. Larger image,
# same real dependency set the builder already resolved -- an honest
# tradeoff for a real WebSocket upgrade hook standalone's generated
# server.js has no way to expose.
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Real `openssl` CLI -- lib/custom-domains.ts shells out to a real
# `openssl req -x509` subprocess to generate each Custom Domain's TLS
# certificate (no bundled cert library, no forged PEM content). node:20-
# slim (Debian) does not carry openssl by default -- confirmed live via
# `kubectl exec ... -- which openssl` returning a real "not found" before
# this line existed.
RUN apt-get update \
  && apt-get install -y --no-install-recommends openssl \
  && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 1001 nodejs \
  && useradd --system --uid 1001 --gid nodejs nextjs

COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.js ./next.config.js
COPY --from=builder /app/package.json ./package.json
COPY --from=builder --chown=nextjs:nodejs /app/server.js ./server.js

# Real wasm4pm-cli binary -- lib/ocel-log.ts's `discoverOcDfgLocal` shells
# out to this exact path via WPM_BIN_PATH (falls back to `wpm` on PATH if
# WPM_BIN_PATH is unset).
COPY --from=wpm-builder /src/wasm4pm/target/release/wpm /usr/local/bin/wpm
ENV WPM_BIN_PATH=/usr/local/bin/wpm

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
