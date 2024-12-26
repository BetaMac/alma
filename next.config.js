module.exports = {
  async rewrites() {
    return [
      {
        source: '/ws/:path*',
        destination: 'http://127.0.0.1:8000/ws/:path*'
      }
    ]
  }
}