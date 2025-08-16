#!/bin/bash

# Vercel Deployment Fixes Script
# This script automates the deployment process with all the fixes applied

set -e  # Exit on any error

echo "🚀 Starting Vercel Deployment Fixes..."

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

# Check if we're in the right directory
if [ ! -f "next.config.js" ] || [ ! -f "vercel.json" ]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

print_status "Verifying project structure..."

# Check for required files
required_files=("next.config.js" "vercel.json" "package.json" "requirements.txt")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Missing required file: $file"
        exit 1
    fi
done

print_success "Project structure verified"

# Check if .env.local exists, create if not
if [ ! -f ".env.local" ]; then
    print_warning ".env.local not found, creating with default values..."
    cat > .env.local << EOF
# Next.js Frontend Environment Variables
NEXT_PUBLIC_API_URL=http://localhost:8000
API_DESTINATION=http://localhost:8000

# Backend Configuration
BACKEND_URL=http://localhost:8000

# Development Settings
NODE_ENV=development
NEXT_PUBLIC_VERCEL_ENV=development
EOF
    print_success "Created .env.local"
fi

# Check if .env.production exists, create if not
if [ ! -f ".env.production" ]; then
    print_warning ".env.production not found, creating template..."
    cat > .env.production << EOF
# Production Environment Variables for Vercel
# IMPORTANT: Set these in your Vercel dashboard

# API Configuration - Replace with your actual backend URL
NEXT_PUBLIC_API_URL=https://your-backend-api.vercel.app
API_DESTINATION=https://your-backend-api.vercel.app

# Backend Configuration
BACKEND_URL=https://your-backend-api.vercel.app

# Production Settings
NODE_ENV=production
NEXT_PUBLIC_VERCEL_ENV=production

# AI Configuration (if using separate AI service)
OPENAI_API_KEY=your-openai-api-key-here
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-min-32-chars
EOF
    print_success "Created .env.production template"
fi

print_status "Checking Next.js configuration..."

# Verify next.config.js has the fixes
if grep -q "destination.*undefined" next.config.js; then
    print_error "next.config.js still contains 'undefined' destination"
    exit 1
fi

if grep -q "experimental.*appDir" next.config.js; then
    print_error "next.config.js still contains deprecated experimental.appDir"
    exit 1
fi

print_success "Next.js configuration verified"

print_status "Checking Vercel configuration..."

# Verify vercel.json has the fixes
if ! grep -q "NODE_ENV.*production" vercel.json; then
    print_error "vercel.json missing NODE_ENV=production"
    exit 1
fi

print_success "Vercel configuration verified"

print_status "Installing dependencies..."

# Install Node.js dependencies
if [ -f "package-lock.json" ]; then
    npm ci
else
    npm install
fi

print_success "Dependencies installed"

print_status "Building Next.js application..."

# Build the Next.js application
npm run build

print_success "Next.js build completed"

print_status "Checking for Vercel CLI..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    print_warning "Vercel CLI not found, installing..."
    npm install -g vercel
fi

print_success "Vercel CLI available"

# Ask user for deployment preference
echo ""
print_status "Choose deployment method:"
echo "1) Deploy to Vercel (recommended)"
echo "2) Push to Git and let Vercel auto-deploy"
echo "3) Just verify configuration (no deployment)"
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        print_status "Deploying to Vercel..."
        vercel --prod
        ;;
    2)
        print_status "Preparing for Git deployment..."
        git add .
        git commit -m "Fix Vercel deployment issues: update next.config.js, vercel.json, and environment variables"
        git push
        print_success "Code pushed to Git. Vercel will auto-deploy if connected."
        ;;
    3)
        print_success "Configuration verification completed. No deployment performed."
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
print_success "🎉 Deployment process completed!"
echo ""
print_status "IMPORTANT: Don't forget to set environment variables in your Vercel dashboard:"
echo ""
echo "Required Environment Variables:"
echo "- NEXT_PUBLIC_API_URL = https://your-backend-api.vercel.app"
echo "- API_DESTINATION = https://your-backend-api.vercel.app"
echo "- NODE_ENV = production"
echo "- OPENAI_API_KEY = your_actual_openai_api_key"
echo "- JWT_SECRET_KEY = your_secure_jwt_secret"
echo ""
print_status "To set these variables:"
echo "1. Go to your Vercel project dashboard"
echo "2. Navigate to Settings → Environment Variables"
echo "3. Add each variable with the appropriate value"
echo ""
print_status "Test your deployment:"
echo "- Frontend: https://your-app.vercel.app"
echo "- API Health: https://your-app.vercel.app/api/health"
echo "- API Root: https://your-app.vercel.app/api"
echo ""
print_success "Deployment fixes applied successfully! 🚀"