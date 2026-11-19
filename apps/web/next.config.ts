import type { NextConfig } from "next";

const apiInternalUrl =
  process.env.API_INTERNAL_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiInternalUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
