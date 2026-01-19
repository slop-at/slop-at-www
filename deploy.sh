#!/bin/bash
# Deploy slop.at to Digital Ocean

set -e

echo "🚀 Deploying slop.at..."

# Build and push to Docker Hub (optional, or use DO registry)
# docker build -t yourusername/slop-at-www:latest .
# docker push yourusername/slop-at-www:latest

# Deploy with docker compose
docker compose up -d

echo "✅ Deployed!"
echo "📊 Web server: http://localhost:8080"
echo "🗄️  Oxigraph: http://localhost:7878"
