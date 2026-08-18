const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  // Pin the file-tracing root to this app directory -- the monorepo has
  // other lockfiles above it (pnpm-lock.yaml at the home directory) that
  // would otherwise make Next.js guess the wrong workspace root.
  outputFileTracingRoot: path.join(__dirname),
};

module.exports = nextConfig;
