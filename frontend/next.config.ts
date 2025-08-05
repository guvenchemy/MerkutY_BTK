import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Production optimizations
  swcMinify: true,
  
  // Image optimization
  images: {
    domains: ['localhost'],
  },
  
  // Compression
  compress: true,
  
  // Performance optimizations
  poweredByHeader: false,
  
  // Bundle analysis (development only)
  ...(process.env.ANALYZE === 'true' && {
    webpack: (config: any) => {
      config.resolve.alias = {
        ...config.resolve.alias,
      }
      return config
    }
  })
};

export default nextConfig;
