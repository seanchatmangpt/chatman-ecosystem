# syntax=docker/dockerfile:1
#
# Real, minimal, spec-compliant OIDC provider -- a genuinely separate
# service/process/image from both platform-console itself and the GoTrue
# instance the app's second auth path already uses. See server.js's own
# module doc for the full "which real path, and why" reasoning.
#
# node:22-slim (not the rest of this repo's node:20-slim convention) --
# `oidc-provider` 9.x itself warns on anything older than Node 22 LTS
# ("Unsupported runtime"); this image uses the version it actually asks
# for rather than silently running on an unsupported one.
FROM node:22-slim AS deps
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev --no-audit --no-fund

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN groupadd --system --gid 1001 oidcidp \
  && useradd --system --uid 1001 --gid oidcidp oidcidp
COPY --from=deps /app/node_modules ./node_modules
COPY server.js ./server.js
COPY package.json ./package.json
USER oidcidp
EXPOSE 8081
CMD ["node", "server.js"]
