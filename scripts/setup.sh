#!/bin/bash
set -e

# Hugging Face Token Setup Script
# One-command setup for Hugging Face deployment
# Usage: HF_TOKEN=your_token ./scripts/setup.sh

echo "🚀 Hugging Face Token Integration Setup"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
HF_SPACE="Really-amin/ultichat-hugginigfae"
REQUIRED_TOKEN="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"

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
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

print_header() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

# Check if HF_TOKEN is provided
check_token() {
    print_header "Checking Hugging Face Token"
    
    if [ -z "$HF_TOKEN" ]; then
        print_error "HF_TOKEN environment variable is not set!"
        echo ""
        echo "Please provide your Hugging Face token:"
        echo "HF_TOKEN=$REQUIRED_TOKEN ./scripts/setup.sh"
        echo ""
        echo "Or export it first:"
        echo "export HF_TOKEN=$REQUIRED_TOKEN"
        echo "./scripts/setup.sh"
        exit 1
    fi
    
    # Validate token format
    if ! echo "$HF_TOKEN" | grep -q "^hf_"; then
        print_error "Invalid HF_TOKEN format. Token should start with 'hf_'"
        exit 1
    fi
    
    print_success "HF_TOKEN is set and has correct format"
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    # Check if pip is available
    if ! command -v pip &> /dev/null; then
        print_error "pip not found. Please install Python and pip first."
        exit 1
    fi
    
    # Install Hugging Face CLI
    print_status "Installing Hugging Face CLI..."
    pip install -U huggingface_hub
    
    # Install additional dependencies if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        print_status "Installing project requirements..."
        pip install -r requirements.txt
    fi
    
    print_success "Dependencies installed successfully"
}

# Validate token with Hugging Face
validate_token() {
    print_header "Validating Token with Hugging Face"
    
    if ! command -v huggingface-cli &> /dev/null; then
        print_error "huggingface-cli not found after installation"
        exit 1
    fi
    
    print_status "Testing token with Hugging Face API..."
    if huggingface-cli whoami --token "$HF_TOKEN" >/dev/null 2>&1; then
        USER_INFO=$(huggingface-cli whoami --token "$HF_TOKEN")
        USERNAME=$(echo "$USER_INFO" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
        EMAIL=$(echo "$USER_INFO" | grep -o '"email":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "N/A")
        
        print_success "Token is valid!"
        echo "  👤 User: $USERNAME"
        echo "  📧 Email: $EMAIL"
    else
        print_error "Token validation failed. Please check your HF_TOKEN"
        exit 1
    fi
}

# Create environment file
create_env_file() {
    print_header "Creating Environment Configuration"
    
    if [ -f ".env" ]; then
        print_warning ".env file already exists"
        read -p "Do you want to backup and recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mv .env ".env.backup.$(date +%Y%m%d_%H%M%S)"
            print_status "Backed up existing .env file"
        else
            print_status "Keeping existing .env file, updating HF_TOKEN only"
            # Update only HF_TOKEN in existing file
            if grep -q "^HF_TOKEN=" .env; then
                sed -i "s/^HF_TOKEN=.*/HF_TOKEN=$HF_TOKEN/" .env
            else
                echo "HF_TOKEN=$HF_TOKEN" >> .env
            fi
            print_success "Updated HF_TOKEN in existing .env file"
            return
        fi
    fi
    
    print_status "Creating .env file from template..."
    
    if [ ! -f ".env.example" ]; then
        print_error ".env.example not found!"
        exit 1
    fi
    
    # Copy template and update with actual token
    cp .env.example .env
    sed -i "s/HF_TOKEN=hf_your_hugging_face_token_here/HF_TOKEN=$HF_TOKEN/" .env
    
    print_success ".env file created successfully"
    print_warning "Please edit .env and set your other configuration values:"
    echo "  - OPENAI_API_KEY: Your OpenAI API key"
    echo "  - JWT_SECRET_KEY: A secure random string"
    echo "  - DATABASE_URL: Your database connection string"
}

# Test deployment preparation
test_deployment() {
    print_header "Testing Deployment Preparation"
    
    # Make deploy script executable
    if [ -f "deploy.sh" ]; then
        chmod +x deploy.sh
        print_success "Made deploy.sh executable"
    else
        print_warning "deploy.sh not found"
    fi
    
    # Test token validation script
    if [ -f "scripts/validate-token.py" ]; then
        print_status "Testing token validation script..."
        export HF_TOKEN="$HF_TOKEN"
        if python scripts/validate-token.py; then
            print_success "Token validation script works correctly"
        else
            print_warning "Token validation script test failed"
        fi
    fi
    
    # Check if we can prepare deployment
    if [ -f "deploy.sh" ]; then
        print_status "Testing deployment preparation..."
        if ./deploy.sh prepare; then
            print_success "Deployment preparation test successful"
        else
            print_warning "Deployment preparation test failed"
        fi
    fi
}

# Create GitHub setup instructions
create_github_instructions() {
    print_header "GitHub Repository Setup"
    
    cat > GITHUB_SETUP.md << EOF
# GitHub Repository Setup for Hugging Face Deployment

## 🔐 Add HF_TOKEN to GitHub Secrets

1. **Go to your GitHub repository**
   - Navigate to: \`https://github.com/YOUR_USERNAME/YOUR_REPO\`

2. **Access Repository Settings**
   - Click on "Settings" tab (top right of repo)

3. **Navigate to Secrets**
   - In left sidebar, click "Secrets and variables" → "Actions"

4. **Add New Secret**
   - Click "New repository secret"
   - **Name**: \`HF_TOKEN\`
   - **Value**: \`$HF_TOKEN\`
   - Click "Add secret"

## ✅ Verify Setup

After adding the secret, you can verify by:

1. **Check Secrets List**
   - You should see \`HF_TOKEN\` in the list of repository secrets

2. **Test Deployment**
   - Push any commit to \`main\` branch
   - GitHub Actions will automatically deploy to Hugging Face

3. **Monitor Deployment**
   - Go to "Actions" tab in your repository
   - Watch the "🚀 Deploy to Hugging Face Spaces" workflow

## 🌐 Deployment URL

Your application will be deployed to:
**https://huggingface.co/spaces/$HF_SPACE**

## 🔄 Automatic Deployment

- **Trigger**: Every push to \`main\` or \`master\` branch
- **Manual**: Use "Actions" → "🚀 Deploy to Hugging Face Spaces" → "Run workflow"

## 🛠️ Manual Deployment

You can also deploy manually using:

\`\`\`bash
export HF_TOKEN=$HF_TOKEN
./deploy.sh "Your commit message"
\`\`\`

## 📋 Troubleshooting

- **Secret not found**: Make sure you added \`HF_TOKEN\` exactly as shown
- **Invalid token**: Verify your token starts with \`hf_\` and is valid
- **Permission denied**: Ensure you have push access to the Hugging Face space

EOF

    print_success "Created GITHUB_SETUP.md with instructions"
}

# Show final instructions
show_completion() {
    echo ""
    print_success "🎉 Hugging Face Token Integration Setup Complete!"
    echo ""
    echo "📊 Setup Summary:"
    echo "├─ 🔐 Token validated and configured"
    echo "├─ 📁 Environment file created"
    echo "├─ 📦 Dependencies installed" 
    echo "├─ 🚀 Deployment scripts ready"
    echo "└─ 📋 GitHub instructions generated"
    echo ""
    print_status "🌐 Your Hugging Face Space: https://huggingface.co/spaces/$HF_SPACE"
    echo ""
    print_header "Next Steps:"
    echo ""
    echo "1. 📝 **Edit .env file** with your other configuration:"
    echo "   - Set OPENAI_API_KEY"
    echo "   - Set JWT_SECRET_KEY" 
    echo "   - Configure database settings"
    echo ""
    echo "2. 🔐 **Add HF_TOKEN to GitHub Secrets** (see GITHUB_SETUP.md):"
    echo "   - Go to repository Settings → Secrets and variables → Actions"
    echo "   - Add new secret: HF_TOKEN = $HF_TOKEN"
    echo ""
    echo "3. 🚀 **Test deployment**:"
    echo "   - Manual: ./deploy.sh \"Test deployment\""
    echo "   - Auto: git push origin main"
    echo ""
    echo "4. ✅ **Verify deployment**:"
    echo "   - Check GitHub Actions tab for workflow status"
    echo "   - Visit https://huggingface.co/spaces/$HF_SPACE"
    echo ""
    print_warning "Security Reminder:"
    echo "- Never commit .env file to git"
    echo "- Keep your tokens secure"
    echo "- Rotate tokens regularly"
    echo ""
}

# Main setup process
main() {
    case "${1:-setup}" in
        "setup")
            check_token
            install_dependencies
            validate_token
            create_env_file
            test_deployment
            create_github_instructions
            show_completion
            ;;
        "validate-only")
            check_token
            install_dependencies
            validate_token
            print_success "Token validation completed"
            ;;
        "env-only")
            check_token
            create_env_file
            print_success "Environment file setup completed"
            ;;
        "help")
            echo "Usage: HF_TOKEN=your_token $0 [command]"
            echo ""
            echo "Commands:"
            echo "  setup        - Full setup process (default)"
            echo "  validate-only - Only validate the token"
            echo "  env-only     - Only create environment file"
            echo "  help         - Show this help"
            echo ""
            echo "Environment variables:"
            echo "  HF_TOKEN     - Your Hugging Face token (required)"
            echo ""
            echo "Examples:"
            echo "  HF_TOKEN=$REQUIRED_TOKEN $0"
            echo "  export HF_TOKEN=$REQUIRED_TOKEN && $0 setup"
            echo "  HF_TOKEN=$REQUIRED_TOKEN $0 validate-only"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
}

# Make script executable and run
chmod +x "$0" 2>/dev/null || true
main "$@"