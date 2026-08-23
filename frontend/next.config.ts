import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/v1/auth/:path*",
        destination: "http://127.0.0.1:8001/auth/:path*",
      },
      {
        source: "/api/v1/projects/:path*",
        destination: "http://127.0.0.1:8002/projects/:path*",
      },
      {
        source: "/api/v1/deployments/:path*",
        destination: "http://127.0.0.1:8006/deployments/:path*",
      },
      {
        source: "/api/v1/webhooks/:path*",
        destination: "http://127.0.0.1:8002/webhooks/:path*",
      },
    ];
  },

};

export default nextConfig;

