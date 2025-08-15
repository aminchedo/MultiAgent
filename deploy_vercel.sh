#!/bin/bash

echo "🚀 Vercel Deployment Script"
echo "=========================="

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Please install it first:"
    echo "npm i -g vercel"
    exit 1
fi

# Check environment variables
echo "📋 Checking environment variables..."

JWT_SECRET_SET=false
OPENAI_KEY_SET=false

# Check if we're in a Vercel environment
if [ -n "$VERCEL" ]; then
    echo "✅ Running in Vercel environment"
    
    if [ -n "$JWT_SECRET_KEY" ]; then
        if [ "$JWT_SECRET_KEY" != "default-secret-key-for-development-only" ]; then
            echo "✅ JWT_SECRET_KEY is set"
            JWT_SECRET_SET=true
        else
            echo "⚠️  JWT_SECRET_KEY is using default value (insecure for production)"
        fi
    else
        echo "❌ JWT_SECRET_KEY not set"
    fi
    
    if [ -n "$OPENAI_API_KEY" ]; then
        echo "✅ OPENAI_API_KEY is set"
        OPENAI_KEY_SET=true
    else
        echo "❌ OPENAI_API_KEY not set"
    fi
else
    echo "ℹ️  Running locally - environment variables will be checked on Vercel"
fi

# Generate JWT secret if needed
if [ "$JWT_SECRET_SET" = false ]; then
    echo ""
    echo "🔑 JWT_SECRET_KEY Setup:"
    echo "   Generate a secure key with: openssl rand -hex 32"
    echo "   Set it in Vercel dashboard under Environment Variables"
    echo ""
fi

# Deploy to Vercel
echo "🌐 Deploying to Vercel..."

if [ "$1" = "--prod" ]; then
    echo "   Deploying to production..."
    vercel --prod
else
    echo "   Deploying to preview..."
    vercel
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "🔗 Test your endpoints:"
    echo "   - Health: https://your-app.vercel.app/health"
    echo "   - Root: https://your-app.vercel.app/"
    echo "   - API Health: https://your-app.vercel.app/api/health"
    echo ""
    echo "🧪 Run tests:"
    echo "   python test_vercel_fixes.py https://your-app.vercel.app"
    echo ""
else
    echo "❌ Deployment failed!"
    exit 1
fi