/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,  // 关闭严格模式避免开发环境重复请求
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  },
}

module.exports = nextConfig

