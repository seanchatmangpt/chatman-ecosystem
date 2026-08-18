import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // Pin the workspace root to this directory so Next.js never infers it from
  // an unrelated lockfile elsewhere on disk (e.g. a parent monorepo) — this
  // app is standalone and must build the same way regardless of where it's
  // checked out.
  outputFileTracingRoot: path.resolve(__dirname),
};

export default nextConfig;
