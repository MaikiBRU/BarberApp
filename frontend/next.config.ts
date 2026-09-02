import type { NextConfig } from "next";

/**
 * Origin the API is actually served from.
 *
 * In production the browser only ever calls `/api/...` on this same
 * origin; the rewrite below forwards those to the backend. That keeps
 * the request same-origin (no CORS at all) and keeps the shared backend
 * host out of the published bundle.
 */
const apiOrigin = process.env.API_ORIGIN?.replace(/\/$/, "");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Emits a self-contained server bundle so the production image does not
  // need node_modules at runtime.
  output: "standalone",
  async rewrites() {
    if (!apiOrigin) {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
