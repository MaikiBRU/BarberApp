import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Emits a self-contained server bundle so the production image
  // does not need node_modules at runtime.
  output: "standalone",
};

export default nextConfig;
