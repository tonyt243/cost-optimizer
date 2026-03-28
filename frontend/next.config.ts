import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://35.85.216.208:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;