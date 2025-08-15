#!/bin/bash

# Vercel Deployment Script for Multi-Agent Code Generation System
# This script deploys the application to Vercel

set -e

echo "🚀 Starting Vercel deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    print_error "Vercel CLI is not installed. Please install it first:"
    echo "npm install -g vercel"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "api/index.py" ] || [ ! -f "vercel.json" ]; then
    print_error "Missing required Vercel files. Please ensure you're in the project root."
    exit 1
fi

print_status "Verifying Vercel configuration..."

# Test the Vercel app locally
print_status "Testing Vercel app locally..."
if python3 -c "import sys; sys.path.insert(0, '.'); from api.vercel_app import app; print('✅ Vercel app test passed')" 2>/dev/null; then
    print_success "Vercel app test passed"
else
    print_error "Vercel app test failed"
    exit 1
fi

# Check if user is logged in to Vercel
print_status "Checking Vercel authentication..."
if ! vercel whoami &> /dev/null; then
    print_warning "Not logged in to Vercel. Please log in:"
    vercel login
fi

# Deploy to Vercel
print_status "Deploying to Vercel..."
if vercel --prod; then
    print_success "Deployment completed successfully!"
    print_status "Your application should be available at the URL shown above."
else
    print_error "Deployment failed!"
    exit 1
fi

print_success "🎉 Vercel deployment completed!"
print_status "Check the URL above to access your application."