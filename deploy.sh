#!/bin/bash

# =============================================================================
# Manual Deployment Script for Hugging Face Spaces
# Multi-Agent Code Generation System
# =============================================================================
# Usage: ./deploy.sh [commit-message] [--force]
# 
# Examples:
#   ./deploy.sh "🚀 Initial deployment"
#   ./deploy.sh "🐛 Fix authentication bug" --force
#   ./deploy.sh
#

set -e  # Exit on error

# =============================================================================
# CONFIGURATION
# =============================================================================
HF_SPACE="Really-amin/ultichat-hugginigfae"
COMMIT_MSG="${1:-🚀 Manual deployment $(date +'%Y-%m-%d %H:%M:%S')}"
FORCE_DEPLOY="${2:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
print_header() {
    echo -e "${PURPLE}"
    echo "=================================================================="
    echo "$1"
    echo "=================================================================="
    echo -e "${NC}"
}

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
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

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# =============================================================================
# PRE-DEPLOYMENT CHECKS
# =============================================================================
check_dependencies() {
    print_step "Checking dependencies..."
    
    # Check if HF_TOKEN is set
    if [ -z "$HF_TOKEN" ]; then
        print_error "HF_TOKEN environment variable not set"
        echo ""
        print_info "Please export your Hugging Face token:"
        echo "export HF_TOKEN=hf_your_token_here"
        echo ""
        print_info "Get your token from: https://huggingface.co/settings/tokens"
        exit 1
    fi
    
    # Check if huggingface-cli is installed
    if ! command -v huggingface-cli &> /dev/null; then
        print_warning "Hugging Face CLI not found. Installing..."
        pip install -U huggingface_hub
    fi
    
    # Check if git is available
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed"
        exit 1
    fi
    
    print_success "All dependencies checked"
}

check_required_files() {
    print_step "Checking required files..."
    
    required_files=("app.py" "requirements.txt" "Dockerfile" "README.md")
    missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -ne 0 ]; then
        print_error "Required files missing:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi
    
    print_success "All required files present"
}

validate_python_syntax() {
    print_step "Validating Python syntax..."
    
    python_files=("app.py")
    if [ -f "main.py" ]; then
        python_files+=("main.py")
    fi
    
    for file in "${python_files[@]}"; do
        if [ -f "$file" ]; then
            python -m py_compile "$file" || {
                print_error "Python syntax error in $file"
                exit 1
            }
        fi
    done
    
    print_success "Python syntax validation passed"
}

check_dockerfile() {
    print_step "Validating Dockerfile..."
    
    if ! grep -q "EXPOSE 7860" Dockerfile; then
        print_warning "Dockerfile doesn't expose port 7860 (required for HF Spaces)"
    fi
    
    if ! grep -q "USER user" Dockerfile; then
        print_warning "Dockerfile doesn't use non-root user (recommended for HF Spaces)"
    fi
    
    print_success "Dockerfile validation completed"
}

# =============================================================================
# DEPLOYMENT FUNCTIONS
# =============================================================================
login_to_hf() {
    print_step "Logging in to Hugging Face..."
    huggingface-cli login --token "$HF_TOKEN" || {
        print_error "Failed to login to Hugging Face"
        exit 1
    }
    print_success "Successfully logged in to Hugging Face"
}

prepare_deployment() {
    print_step "Preparing deployment files..."
    
    # Create necessary directories
    mkdir -p logs temp uploads static
    
    # Set permissions
    chmod +x app.py 2>/dev/null || true
    
    # Create .gitignore if it doesn't exist
    if [ ! -f ".gitignore" ]; then
        print_warning "Creating basic .gitignore file"
        cat > .gitignore << 'EOF'
.env
__pycache__/
*.pyc
*.log
temp/
uploads/
.DS_Store
EOF
    fi
    
    print_success "Deployment files prepared"
}

deploy_to_hf() {
    print_step "Deploying to Hugging Face Spaces..."
    
    # Build the upload command
    upload_cmd="huggingface-cli upload $HF_SPACE . --repo-type=space"
    upload_cmd="$upload_cmd --commit-message=\"$COMMIT_MSG\""
    upload_cmd="$upload_cmd --commit-description=\"Manual deployment from local environment\""
    
    # Add exclusions
    upload_cmd="$upload_cmd --exclude=\".git/*\""
    upload_cmd="$upload_cmd --exclude=\"tests/*\""
    upload_cmd="$upload_cmd --exclude=\"scripts/*\""
    upload_cmd="$upload_cmd --exclude=\"deployment/*\""
    upload_cmd="$upload_cmd --exclude=\".github/*\""
    upload_cmd="$upload_cmd --exclude=\"*.md\""
    upload_cmd="$upload_cmd --exclude=\".env*\""
    
    # Add force flag if specified
    if [ "$FORCE_DEPLOY" == "--force" ]; then
        upload_cmd="$upload_cmd --force"
        print_warning "Force deployment enabled"
    fi
    
    # Execute deployment
    eval $upload_cmd || {
        print_error "Deployment failed"
        exit 1
    }
    
    print_success "Deployment completed successfully"
}

# =============================================================================
# POST-DEPLOYMENT
# =============================================================================
show_deployment_info() {
    print_header "🎉 DEPLOYMENT SUCCESSFUL!"
    
    echo -e "${GREEN}"
    echo "Space URL: https://huggingface.co/spaces/$HF_SPACE"
    echo "API Docs: https://huggingface.co/spaces/$HF_SPACE/docs"
    echo "Commit: $COMMIT_MSG"
    echo "Timestamp: $(date)"
    echo -e "${NC}"
    
    print_info "Build Status:"
    echo "The space is now building on Hugging Face."
    echo "This may take a few minutes to complete."
    echo ""
    print_info "Monitor the build process at:"
    echo "https://huggingface.co/spaces/$HF_SPACE/logs"
    echo ""
    
    print_warning "Note:"
    echo "- First deployment may take 5-10 minutes"
    echo "- Check the logs if the space doesn't start"
    echo "- Ensure OPENAI_API_KEY is set in Space secrets"
}

show_troubleshooting() {
    print_header "🔧 TROUBLESHOOTING"
    
    echo "If deployment fails, check:"
    echo ""
    echo "1. HF_TOKEN is valid and has write permissions"
    echo "2. Space name '$HF_SPACE' is correct"
    echo "3. All required files are present"
    echo "4. Python syntax is valid"
    echo "5. Dockerfile exposes port 7860"
    echo ""
    echo "Common fixes:"
    echo "- Update huggingface_hub: pip install -U huggingface_hub"
    echo "- Re-export HF_TOKEN: export HF_TOKEN=hf_your_token"
    echo "- Use --force flag: ./deploy.sh \"message\" --force"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================
main() {
    print_header "🚀 Deploying Multi-Agent Code Generator to Hugging Face Spaces"
    
    echo "Target Space: $HF_SPACE"
    echo "Commit Message: $COMMIT_MSG"
    echo ""
    
    # Pre-deployment checks
    check_dependencies
    check_required_files
    validate_python_syntax
    check_dockerfile
    
    # Login and prepare
    login_to_hf
    prepare_deployment
    
    # Deploy
    deploy_to_hf
    
    # Post-deployment
    show_deployment_info
    
    print_success "🎊 All done! Your Multi-Agent Code Generator is now live!"
}

# =============================================================================
# ERROR HANDLING
# =============================================================================
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Deployment failed!"
        echo ""
        show_troubleshooting
    fi
}

trap cleanup EXIT

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi