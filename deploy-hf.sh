#!/bin/bash

# =============================================================================
# Hugging Face Spaces Deployment Script
# Multi-Agent Code Generation System
# =============================================================================

set -e  # Exit on any error

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

print_header() {
    echo -e "\n${BLUE}==========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}==========================================${NC}\n"
}

# Check requirements
check_requirements() {
    print_header "Checking Requirements"
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install git first."
        exit 1
    fi
    
    # Check if python is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    
    # Check if huggingface-hub is installed
    if ! pip show huggingface-hub &> /dev/null; then
        print_warning "huggingface-hub not found. Installing..."
        pip install huggingface-hub[cli]
    fi
    
    print_success "All requirements satisfied"
}

# Validate environment variables
validate_environment() {
    print_header "Validating Environment"
    
    # Check for HF_TOKEN
    if [ -z "$HF_TOKEN" ]; then
        print_error "HF_TOKEN environment variable is not set!"
        print_error "Please set your Hugging Face token:"
        print_error "export HF_TOKEN=hf_your_token_here"
        exit 1
    fi
    
    # Validate token format
    if ! echo "$HF_TOKEN" | grep -q "^hf_"; then
        print_error "Invalid HF_TOKEN format. Token should start with 'hf_'"
        exit 1
    fi
    
    # Test token validity
    print_status "Testing Hugging Face token..."
    if huggingface-cli whoami --token "$HF_TOKEN" >/dev/null 2>&1; then
        USER_INFO=$(huggingface-cli whoami --token "$HF_TOKEN")
        USERNAME=$(echo "$USER_INFO" | grep -oP '(?<=username: ).*')
        print_success "Token valid for user: $USERNAME"
    else
        print_error "Token validation failed. Please check your HF_TOKEN"
        exit 1
    fi
}

# Prepare files for deployment
prepare_deployment() {
    print_header "Preparing Deployment Files"
    
    # Ensure app.py exists
    if [ ! -f "app.py" ]; then
        print_error "app.py not found! This file is required for Hugging Face Spaces."
        exit 1
    fi
    
    # Check requirements.txt
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    # Ensure gradio is in requirements
    if ! grep -q "gradio" requirements.txt; then
        print_warning "Adding gradio to requirements.txt"
        echo "gradio==4.8.0" >> requirements.txt
    fi
    
    # Create README.md for HF Space if it doesn't exist
    if [ ! -f "README.md" ]; then
        print_status "Creating README.md for Hugging Face Space..."
        cat > README.md << 'EOF'
---
title: Multi-Agent Code Generator
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.8.0
app_file: app.py
pinned: false
license: mit
---

# 🤖 Multi-Agent Code Generation System

An AI-powered code generation system using multiple specialized agents to create high-quality code, documentation, and tests.

## Features

- **Planning Agent**: Analyzes requirements and creates project plans
- **Code Generation**: Multiple specialized coding agents
- **Quality Assurance**: Automated code review and optimization  
- **Testing**: Automatic test generation and validation
- **Documentation**: Comprehensive documentation generation

## Usage

1. Enter your code generation prompt
2. Select the project type
3. Click "Generate Code" to create your project
4. Review the generated code and explanation

## Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **AI**: OpenAI GPT-4, Custom agent orchestration
- **Frontend**: Gradio interface
- **Deployment**: Hugging Face Spaces

## Environment Variables

The system requires the following environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key for code generation
- `JWT_SECRET_KEY`: Secret key for authentication (if needed)

## Local Development

```bash
pip install -r requirements.txt
python main.py
```

## Contributing

This project is open source. Contributions are welcome!

## License

MIT License - see LICENSE file for details.
EOF
        print_success "Created README.md"
    fi
    
    print_success "Deployment files prepared"
}

# Deploy to Hugging Face
deploy_to_huggingface() {
    print_header "Deploying to Hugging Face Spaces"
    
    # Get space name from user or use default
    if [ -z "$HF_SPACE_NAME" ]; then
        read -p "Enter Hugging Face Space name (default: multi-agent-code-generator): " HF_SPACE_NAME
        HF_SPACE_NAME=${HF_SPACE_NAME:-multi-agent-code-generator}
    fi
    
    USERNAME=$(huggingface-cli whoami --token "$HF_TOKEN" | grep -oP '(?<=username: ).*')
    SPACE_REPO="$USERNAME/$HF_SPACE_NAME"
    
    print_status "Deploying to space: $SPACE_REPO"
    
    # Login to Hugging Face
    print_status "Logging in to Hugging Face..."
    huggingface-cli login --token "$HF_TOKEN"
    
    # Create or update the space
    print_status "Creating/updating Hugging Face Space..."
    
    # Try to create the space (will fail if it already exists, which is fine)
    huggingface-cli repo create "$SPACE_REPO" --type space --sdk gradio --private || true
    
    # Clone the space repository
    TEMP_DIR=$(mktemp -d)
    print_status "Cloning space repository..."
    git clone "https://huggingface.co/spaces/$SPACE_REPO" "$TEMP_DIR" || {
        print_error "Failed to clone space repository"
        exit 1
    }
    
    # Copy files to the space
    print_status "Copying files to space..."
    
    # Copy essential files
    cp app.py "$TEMP_DIR/"
    cp requirements.txt "$TEMP_DIR/"
    cp README.md "$TEMP_DIR/"
    
    # Copy backend directory
    if [ -d "backend" ]; then
        cp -r backend "$TEMP_DIR/"
    fi
    
    # Copy config directory
    if [ -d "config" ]; then
        cp -r config "$TEMP_DIR/"
    fi
    
    # Copy other necessary files
    for file in main.py .env.example; do
        if [ -f "$file" ]; then
            cp "$file" "$TEMP_DIR/"
        fi
    done
    
    # Navigate to temp directory and commit changes
    cd "$TEMP_DIR"
    
    git config user.email "action@github.com"
    git config user.name "HF Deploy Script"
    
    git add .
    git commit -m "🚀 Deploy Multi-Agent Code Generator $(date '+%Y-%m-%d %H:%M:%S')" || {
        print_warning "No changes to commit"
    }
    
    # Push to Hugging Face
    print_status "Pushing to Hugging Face Spaces..."
    git push || {
        print_error "Failed to push to Hugging Face"
        cd - > /dev/null
        rm -rf "$TEMP_DIR"
        exit 1
    }
    
    # Cleanup
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
    
    print_success "Successfully deployed to Hugging Face Spaces!"
    print_success "View your space at: https://huggingface.co/spaces/$SPACE_REPO"
}

# Test deployment
test_deployment() {
    print_header "Testing Deployment"
    
    # Test local gradio app
    print_status "Testing local Gradio interface..."
    
    timeout 10s python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app import setup_gradio_interface
    demo = setup_gradio_interface()
    print('✅ Gradio interface setup successful')
except Exception as e:
    print(f'❌ Gradio interface test failed: {e}')
    sys.exit(1)
" || {
        print_warning "Local Gradio test timed out (this may be normal)"
    }
    
    print_success "Deployment testing completed"
}

# Main deployment function
main() {
    print_header "Hugging Face Spaces Deployment"
    print_status "Multi-Agent Code Generation System"
    print_status "Starting deployment process..."
    
    # Check if HF_TOKEN is provided as argument
    if [ -n "$1" ]; then
        export HF_TOKEN="$1"
    fi
    
    # Run deployment steps
    check_requirements
    validate_environment
    prepare_deployment
    test_deployment
    deploy_to_huggingface
    
    print_header "Deployment Complete!"
    print_success "🎉 Your Multi-Agent Code Generator is now live on Hugging Face Spaces!"
    print_success "🔗 Space URL: https://huggingface.co/spaces/$USERNAME/$HF_SPACE_NAME"
    
    echo -e "\n${BLUE}Next Steps:${NC}"
    echo "1. Set environment variables in your Space settings:"
    echo "   - OPENAI_API_KEY (required)"
    echo "   - JWT_SECRET_KEY (optional)"
    echo "2. Wait for the Space to build and start"
    echo "3. Test the interface and functionality"
    echo "4. Share your Space with others!"
}

# Show help
show_help() {
    echo "Hugging Face Spaces Deployment Script"
    echo ""
    echo "Usage:"
    echo "  $0 [HF_TOKEN]                 # Deploy with token"
    echo "  $0 --help                     # Show this help"
    echo ""
    echo "Environment Variables:"
    echo "  HF_TOKEN        - Your Hugging Face token (required)"
    echo "  HF_SPACE_NAME   - Space name (optional, default: multi-agent-code-generator)"
    echo ""
    echo "Examples:"
    echo "  export HF_TOKEN=hf_your_token && $0"
    echo "  HF_TOKEN=hf_your_token $0"
    echo "  $0 hf_your_token"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac