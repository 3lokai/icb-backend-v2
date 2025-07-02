#!/bin/bash

# Deployment script for Fly.io
# This script automates the deployment process

set -e  # Exit on any error

echo "🚀 Starting deployment to Fly.io..."

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Please install it first:"
    echo "   macOS: brew install flyctl"
    echo "   Windows: powershell -Command \"iwr https://fly.io/install.ps1 -useb | iex\""
    echo "   Linux: curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if user is logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Please run: flyctl auth login"
    exit 1
fi

# Check if app exists, create if it doesn't
if ! flyctl apps list | grep -q "icb-backend-v2"; then
    echo "📱 Creating new app: icb-backend-v2"
    flyctl apps create icb-backend-v2
else
    echo "✅ App icb-backend-v2 already exists"
fi

# Check if required secrets are set
echo "🔐 Checking environment variables..."

# Check for required Supabase variables
if ! flyctl secrets list | grep -q "SUPABASE_URL"; then
    echo "⚠️  SUPABASE_URL not set. Please set it with:"
    echo "   fly secrets set SUPABASE_URL=your_supabase_url"
    echo "   fly secrets set SUPABASE_KEY=your_supabase_key"
    echo ""
    read -p "Continue with deployment anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 1
    fi
fi

# Deploy the application
echo "🚀 Deploying to Fly.io..."
flyctl deploy

# Check deployment status
echo "📊 Checking deployment status..."
flyctl status

echo "✅ Deployment completed!"
echo ""
echo "🌐 Your application is available at:"
echo "   https://icb-backend-v2.fly.dev"
echo ""
echo "📚 API Documentation:"
echo "   https://icb-backend-v2.fly.dev/docs"
echo ""
echo "💚 Health Check:"
echo "   https://icb-backend-v2.fly.dev/health"
echo ""
echo "📋 Useful commands:"
echo "   fly logs --follow          # View real-time logs"
echo "   fly status                 # Check app status"
echo "   fly ssh console            # SSH into container"
echo "   fly apps restart           # Restart the app" 