# syntax=docker/dockerfile:1

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

# --- runner: minimal runtime image using Next.js standalone output
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

RUN groupadd --system --gid 1001 nodejs \
  && useradd --system --uid 1001 --gid nodejs nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
