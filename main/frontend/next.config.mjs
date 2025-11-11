/** @type {import('next').NextConfig} */
const nextConfig = {
  // Removed output: 'export' to enable API routes
  // API routes require Node.js server runtime (not static export)
  // Deployment must use Vercel or Node.js server (not S3 static hosting)
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
}

export default nextConfig
