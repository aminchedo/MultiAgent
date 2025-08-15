#!/bin/bash

# Vercel Deployment Fixes Script
# This script helps deploy the fixes for the Vercel deployment issues

set -e  # Exit on any error

echo "🚀 Deploying Vercel Fixes"
echo "=========================="

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
if [ ! -f "api/vercel_app.py" ]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    print_error "Git is not installed or not in PATH"
    exit 1
fi

# Check if vercel CLI is available
if ! command -v vercel &> /dev/null; then
    print_warning "Vercel CLI not found. You can still deploy using git push."
fi

print_status "Checking current git status..."

# Check if there are uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    print_warning "You have uncommitted changes. Please commit them first:"
    git status --short
    echo ""
    read -p "Do you want to commit all changes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Committing changes..."
        git add .
        git commit -m "Fix Vercel deployment issues: add root endpoint, favicon handling, and JWT_SECRET_KEY defaults"
        print_success "Changes committed"
    else
        print_error "Please commit your changes before deploying"
        exit 1
    fi
else
    print_success "No uncommitted changes found"
fi

# Verify the fixes are in place
print_status "Verifying fixes are in place..."

# Check if root endpoint exists
if ! grep -q "@app.get(\"/\")" api/vercel_app.py; then
    print_error "Root endpoint not found in api/vercel_app.py"
    exit 1
fi

# Check if favicon endpoints exist
if ! grep -q "@app.get(\"/favicon.ico\")" api/vercel_app.py; then
    print_error "Favicon.ico endpoint not found in api/vercel_app.py"
    exit 1
fi

if ! grep -q "@app.get(\"/favicon.png\")" api/vercel_app.py; then
    print_error "Favicon.png endpoint not found in api/vercel_app.py"
    exit 1
fi

# Check if static directory exists
if [ ! -d "static" ]; then
    print_error "Static directory not found"
    exit 1
fi

# Check if favicon files exist
if [ ! -f "static/favicon.ico" ]; then
    print_warning "static/favicon.ico not found"
fi

if [ ! -f "static/favicon.png" ]; then
    print_warning "static/favicon.png not found"
fi

# Check if vercel.json has the right routes
if ! grep -q "\"/favicon.ico\"" vercel.json; then
    print_error "Favicon routes not found in vercel.json"
    exit 1
fi

print_success "All fixes verified"

# Show current branch
current_branch=$(git branch --show-current)
print_status "Current branch: $current_branch"

# Ask for deployment method
echo ""
echo "Choose deployment method:"
echo "1. Git push (recommended for Vercel)"
echo "2. Vercel CLI deploy"
echo "3. Just verify and exit"

read -p "Enter your choice (1-3): " -n 1 -r
echo

case $REPLY in
    1)
        print_status "Deploying via git push..."
        
        # Check if remote exists
        if ! git remote get-url origin &> /dev/null; then
            print_error "No remote 'origin' found. Please add your git remote first."
            exit 1
        fi
        
        # Push to remote
        print_status "Pushing to remote..."
        git push origin "$current_branch"
        print_success "Deployment initiated via git push"
        print_status "Vercel will automatically deploy from your git repository"
        ;;
    2)
        if ! command -v vercel &> /dev/null; then
            print_error "Vercel CLI not found. Please install it first: npm i -g vercel"
            exit 1
        fi
        
        print_status "Deploying via Vercel CLI..."
        vercel --prod
        print_success "Deployment completed via Vercel CLI"
        ;;
    3)
        print_success "Verification completed. No deployment performed."
        exit 0
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

# Environment variables reminder
echo ""
print_warning "IMPORTANT: Don't forget to set environment variables in Vercel dashboard:"
echo "  1. Go to your Vercel project dashboard"
echo "  2. Navigate to Settings → Environment Variables"
echo "  3. Add the following variables:"
echo "     - OPENAI_API_KEY: Your OpenAI API key"
echo "     - JWT_SECRET_KEY: A secure random string (recommended for production)"
echo ""

print_success "Deployment script completed!"
print_status "Monitor your Vercel deployment logs for any issues."
print_status "You can test the endpoints once deployment is complete."