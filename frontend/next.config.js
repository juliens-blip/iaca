/** @type {import('next').NextConfig} */
const trimTrailingSlash = (value) => value.replace(/\/+$/, "");

const buildApiRewriteDestination = (baseUrl) => {
  const normalizedBaseUrl = trimTrailingSlash(baseUrl);
  return normalizedBaseUrl.endsWith("/api")
    ? `${normalizedBaseUrl}/:path*`
    : `${normalizedBaseUrl}/api/:path*`;
};

const apiProxyTarget = trimTrailingSlash(
  process.env.INTERNAL_API_URL?.trim()
  || process.env.NEXT_PUBLIC_API_URL?.trim()
  || "http://localhost:8000"
);

const nextConfig = {
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: '/api/:path*',
          destination: buildApiRewriteDestination(apiProxyTarget),
        },
      ],
    };
  },
};

module.exports = nextConfig;
