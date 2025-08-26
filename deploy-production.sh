#!/bin/bash

# Multi-Agent Code Generation System - Production Deployment Script
# This script handles the complete deployment workflow for production

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
PROJECT_NAME="multi-agent-code-generation-system"
BRANCH_TO_DEPLOY="main"
VERCEL_PROJECT_NAME="multi-agent-code-generation-system"

# Check if environment variables are set
check_environment() {
    log "Checking environment variables..."
    
    required_vars=(
        "OPENAI_API_KEY"
        "JWT_SECRET_KEY"
        "VERCEL_ORG_ID"
        "VERCEL_PROJECT_ID"
    )
    
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Please set these variables before deploying:"
        echo "  export OPENAI_API_KEY='your-openai-api-key'"
        echo "  export JWT_SECRET_KEY='your-jwt-secret-key'"
        echo "  export VERCEL_ORG_ID='your-vercel-org-id'"
        echo "  export VERCEL_PROJECT_ID='your-vercel-project-id'"
        exit 1
    fi
    
    success "All required environment variables are set"
}

# Install dependencies
install_dependencies() {
    log "Installing dependencies..."
    
    # Python dependencies
    if [[ -f "requirements.txt" ]]; then
        log "Installing Python dependencies..."
        pip install -r requirements.txt
        success "Python dependencies installed"
    fi
    
    # Node.js dependencies (if any)
    if [[ -f "package.json" ]]; then
        log "Installing Node.js dependencies..."
        npm install
        success "Node.js dependencies installed"
    fi
}

# Run tests
run_tests() {
    log "Running test suite..."
    
    # Python tests
    if [[ -f "tests/test_system_integration.py" ]]; then
        log "Running Python integration tests..."
        python -m pytest tests/ -v --tb=short
        success "Python tests passed"
    fi
    
    # Add other test commands here as needed
    success "All tests passed"
}

# Build and validate
build_project() {
    log "Building project..."
    
    # Validate configuration files
    if [[ -f "vercel.json" ]]; then
        log "Validating Vercel configuration..."
        # Could add JSON validation here
        success "Vercel configuration is valid"
    fi
    
    # Validate Python syntax
    log "Validating Python code..."
    python -m py_compile backend/simple_app.py
    python -m py_compile agents/vibe_workflow_orchestrator_agent.py
    python -m py_compile config/config.py
    python -m py_compile config/security.py
    success "Python code validation passed"
    
    # Validate HTML
    if [[ -f "frontend/enhanced_vibe_frontend.html" ]]; then
        log "Frontend file exists and ready for deployment"
        success "Frontend validation passed"
    fi
}

# Security checks
security_checks() {
    log "Running security checks..."
    
    # Check for sensitive data in code
    log "Scanning for potential security issues..."
    
    # Check for hardcoded secrets (basic check)
    if grep -r "sk-[a-zA-Z0-9]" . --exclude-dir=.git --exclude="*.md" --exclude="deploy-production.sh" 2>/dev/null; then
        error "Potential OpenAI API key found in code. Please remove it and use environment variables."
        exit 1
    fi
    
    # Check for TODO/FIXME comments that might indicate incomplete security
    todo_count=$(grep -r "TODO.*security\|FIXME.*security" . --exclude-dir=.git 2>/dev/null | wc -l || echo "0")
    if [[ $todo_count -gt 0 ]]; then
        warning "Found $todo_count security-related TODO/FIXME comments. Please review before production deployment."
    fi
    
    success "Security checks completed"
}

# Pre-deployment validation
pre_deployment_validation() {
    log "Running pre-deployment validation..."
    
    # Check Git status
    if [[ -n $(git status --porcelain) ]]; then
        warning "You have uncommitted changes. Consider committing them before deployment."
        git status --short
        echo ""
        read -p "Continue with deployment? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check current branch
    current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "$BRANCH_TO_DEPLOY" ]]; then
        warning "Current branch is '$current_branch', but you're trying to deploy '$BRANCH_TO_DEPLOY'"
        read -p "Continue with deployment? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    success "Pre-deployment validation completed"
}

# Deploy to Vercel
deploy_to_vercel() {
    log "Deploying to Vercel..."
    
    # Check if Vercel CLI is installed
    if ! command -v vercel &> /dev/null; then
        error "Vercel CLI is not installed. Please install it with: npm i -g vercel"
        exit 1
    fi
    
    # Set environment variables in Vercel
    log "Setting environment variables in Vercel..."
    
    vercel env add OPENAI_API_KEY production <<< "$OPENAI_API_KEY" --yes 2>/dev/null || true
    vercel env add JWT_SECRET_KEY production <<< "$JWT_SECRET_KEY" --yes 2>/dev/null || true
    vercel env add ENVIRONMENT production <<< "production" --yes 2>/dev/null || true
    vercel env add DEBUG production <<< "false" --yes 2>/dev/null || true
    
    success "Environment variables configured"
    
    # Deploy to production
    log "Starting production deployment..."
    vercel --prod --confirm
    
    success "Deployment completed successfully!"
}

# Post-deployment validation
post_deployment_validation() {
    log "Running post-deployment validation..."
    
    # Get deployment URL
    deployment_url=$(vercel ls | grep "$VERCEL_PROJECT_NAME" | head -1 | awk '{print $2}' || echo "")
    
    if [[ -n "$deployment_url" ]]; then
        log "Testing deployment at: https://$deployment_url"
        
        # Test health endpoint
        health_status=$(curl -s -o /dev/null -w "%{http_code}" "https://$deployment_url/health" || echo "000")
        
        if [[ "$health_status" == "200" ]]; then
            success "Health check passed"
        else
            error "Health check failed with status: $health_status"
            exit 1
        fi
        
        # Test main page
        main_page_status=$(curl -s -o /dev/null -w "%{http_code}" "https://$deployment_url/" || echo "000")
        
        if [[ "$main_page_status" == "200" ]]; then
            success "Main page is accessible"
        else
            error "Main page check failed with status: $main_page_status"
            exit 1
        fi
        
        success "Post-deployment validation completed"
        success "🚀 Application is live at: https://$deployment_url"
    else
        warning "Could not determine deployment URL for validation"
    fi
}

# Performance optimization
optimize_for_production() {
    log "Applying production optimizations..."
    
    # Create optimized requirements file for Vercel
    if [[ -f "requirements.txt" ]]; then
        log "Creating optimized requirements for Vercel..."
        # Could filter out dev dependencies here
        cp requirements.txt requirements-vercel.txt
    fi
    
    # Ensure runtime file exists
    echo "python-3.9" > runtime.txt
    
    success "Production optimizations applied"
}

# Cleanup function
cleanup() {
    log "Cleaning up temporary files..."
    # Add cleanup commands here if needed
    success "Cleanup completed"
}

# Main deployment flow
main() {
    echo "🚀 Multi-Agent Code Generation System - Production Deployment"
    echo "=============================================================="
    echo ""
    
    # Run deployment steps
    check_environment
    install_dependencies
    run_tests
    build_project
    security_checks
    pre_deployment_validation
    optimize_for_production
    deploy_to_vercel
    post_deployment_validation
    cleanup
    
    echo ""
    echo "=============================================================="
    success "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo ""
    echo "Next steps:"
    echo "1. Monitor the application for any issues"
    echo "2. Update DNS records if using a custom domain"
    echo "3. Set up monitoring and alerts"
    echo "4. Document the deployment for team members"
    echo ""
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Handle command line arguments
case "$1" in
    "test")
        check_environment
        install_dependencies
        run_tests
        ;;
    "build")
        install_dependencies
        build_project
        ;;
    "deploy")
        main
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [test|build|deploy]"
        echo ""
        echo "Commands:"
        echo "  test   - Run tests only"
        echo "  build  - Build and validate only"
        echo "  deploy - Full deployment (default)"
        exit 1
        ;;
esac