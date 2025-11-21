/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: 'http://localhost:8001/api/:path*',
            },
            {
                source: '/generated_assets/:path*',
                destination: 'http://localhost:8001/generated_assets/:path*',
            },
        ]
    },
};

export default nextConfig;
