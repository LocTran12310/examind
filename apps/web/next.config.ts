import type { NextConfig } from "next";

const apiInternal = process.env.API_INTERNAL_URL ?? "http://localhost:58100";

const nextConfig: NextConfig = {
  output: "standalone",
  // In production Caddy routes /api to the api container; this rewrite makes `next dev` work alone.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiInternal}/api/:path*` }];
  },
};

export default nextConfig;
