import type { NextConfig } from "next";

const AUTH_SERVICE_URL = process.env.AUTH_SERVICE_URL || "http://127.0.0.1:8001";
const PROJECT_SERVICE_URL = process.env.PROJECT_SERVICE_URL || "http://127.0.0.1:8002";
const DEPLOYMENT_SERVICE_URL = process.env.DEPLOYMENT_SERVICE_URL || "http://127.0.0.1:8006";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/v1/auth/:path*",
        destination: `${AUTH_SERVICE_URL}/auth/:path*`,
      },
      {
        source: "/api/v1/projects/:path*",
        destination: `${PROJECT_SERVICE_URL}/projects/:path*`,
      },
      {
        source: "/api/v1/deployments/:path*",
        destination: `${DEPLOYMENT_SERVICE_URL}/deployments/:path*`,
      },
      {
        source: "/api/v1/webhooks/:path*",
        destination: `${PROJECT_SERVICE_URL}/webhooks/:path*`,
      },
    ];
  },
};

export default nextConfig;
