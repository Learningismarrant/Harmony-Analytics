/** @type {import('next').NextConfig} */
const nextConfig = {
  // Transpile internal workspace packages (source TypeScript — no pre-build needed)
  transpilePackages: [
    "@harmony/api", "@harmony/types", "@harmony/ui",
    // d3-force and deps are ESM-only — must transpile for Jest + Next.js bundler
    "d3-force", "d3-dispatch", "d3-quadtree", "d3-timer",
  ],

  // Allow Next.js to resolve files outside of apps/web (monorepo packages)
  experimental: {
    externalDir: true,
  },

  // Strict security headers
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline'", // Next.js needs unsafe-eval in dev
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: blob: https:",
              "connect-src 'self' http://localhost:8000 https://api.harmony.app",
              "frame-ancestors 'none'",
            ].join("; "),
          },
        ],
      },
    ];
  },

  // API rewrites — proxy in dev to avoid CORS
  async rewrites() {
    return process.env.NODE_ENV === "development"
      ? [
          {
            source: "/api/:path*",
            destination: "http://localhost:8000/:path*",
          },
        ]
      : [];
  },
};

module.exports = nextConfig;
