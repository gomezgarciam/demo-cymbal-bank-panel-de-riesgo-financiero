import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  allowedDevOrigins: ["*"],
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
