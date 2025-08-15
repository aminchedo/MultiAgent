#!/bin/bash

# Vercel Deployment Script for Multi-Agent Code Generation System
# This script prepares and deploys the application to Vercel

set -e

echo "🚀 Starting Vercel Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Vercel CLI is installed
check_vercel_cli() {
    print_status "Checking Vercel CLI installation..."
    if ! command -v vercel &> /dev/null; then
        print_warning "Vercel CLI not found. Installing..."
        npm install -g vercel
        print_success "Vercel CLI installed"
    else
        print_success "Vercel CLI is already installed"
    fi
}

# Verify configuration files
verify_config() {
    print_status "Verifying configuration files..."
    
    if [ ! -f "vercel.json" ]; then
        print_error "vercel.json not found!"
        exit 1
    fi
    
    if [ ! -f "requirements-vercel.txt" ]; then
        print_error "requirements-vercel.txt not found!"
        exit 1
    fi
    
    if [ ! -f "api/index.py" ]; then
        print_error "api/index.py not found!"
        exit 1
    fi
    
    if [ ! -f "api/vercel_app.py" ]; then
        print_error "api/vercel_app.py not found!"
        exit 1
    fi
    
    if [ ! -f "config/vercel_config.py" ]; then
        print_error "config/vercel_config.py not found!"
        exit 1
    fi
    
    print_success "All configuration files verified"
}

# Create .vercelignore file
create_vercelignore() {
    print_status "Creating .vercelignore file..."
    cat > .vercelignore << 'EOF'
# Ignore unnecessary files for Vercel deployment
.git/
.gitignore
README.md
*.log
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
.env.local
.env.development.local
.env.test.local
.env.production.local
npm-debug.log*
yarn-debug.log*
yarn-error.log*
temp/
tests/
docs/
deployment/
scripts/
*.sh
EOF
    print_success ".vercelignore file created"
}

# Set environment variables
setup_env() {
    print_status "Setting up environment variables..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_warning "Creating .env file with default values..."
        cat > .env << 'EOF'
# Vercel Deployment Environment Variables
DEBUG=false
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
OPENAI_API_KEY=your-openai-api-key-here
EOF
        print_warning "Please update .env file with your actual API keys"
    fi
    
    print_success "Environment variables configured"
}

# Deploy to Vercel
deploy() {
    print_status "Deploying to Vercel..."
    
    # Check if user is logged in
    if ! vercel whoami &> /dev/null; then
        print_warning "Not logged in to Vercel. Please login..."
        vercel login
    fi
    
    # Deploy
    print_status "Starting deployment..."
    vercel --prod
    
    print_success "Deployment completed!"
}

# Main deployment process
main() {
    echo "🎯 Vercel Deployment for Multi-Agent Code Generation System"
    echo "=========================================================="
    
    check_vercel_cli
    verify_config
    create_vercelignore
    setup_env
    deploy
    
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Set your environment variables in Vercel dashboard"
    echo "2. Configure your domain (if needed)"
    echo "3. Test your deployment"
    echo ""
    echo "🔗 Your application should be available at the URL provided by Vercel"
}

# Run main function
main "$@"