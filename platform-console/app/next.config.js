const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  // `output: "standalone"` removed by the realtime-notification pass:
  // this app now ships its own custom server.js (WebSocket upgrade
  // handling for /ws/notifications -- see that file's header comment),
  // and the Dockerfile's runner stage copies the FULL node_modules
  // instead of standalone's pruned/traced subset, so there is no longer
  // a standalone output for this app to consume.
  reactStrictMode: true,
  // Pin the file-tracing root to this app directory -- the monorepo has
  // other lockfiles above it (pnpm-lock.yaml at the home directory) that
  // would otherwise make Next.js guess the wrong workspace root.
  outputFileTracingRoot: path.join(__dirname),
};

module.exports = nextConfig;
