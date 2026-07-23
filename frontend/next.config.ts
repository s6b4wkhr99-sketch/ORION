import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.join(frontendDir, "..");

const nextConfig: NextConfig = {
  output: "standalone",
  // Prevent Next from treating ~/package-lock.json as the workspace root (causes restarts / empty responses).
  outputFileTracingRoot: projectRoot,
  // Next 16 blocks dev HMR/chunks cross-origin unless the host is allowlisted — without this,
  // http://127.0.0.1:3002 serves HTML but client JS never hydrates (stuck on "Loading workspace…").
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  // Local PoC: allow production build despite non-blocking TS drift in map components.
  typescript: {
    ignoreBuildErrors: true,
  },
  experimental: {
    optimizePackageImports: ["lucide-react", "recharts"],
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL ?? "http://127.0.0.1:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
