#!/bin/bash
set -e

# Hugging Face Spaces Deployment Script
# Usage: ./deploy.sh [commit_message]

echo "🚀 Deploying to Hugging Face Spaces"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HF_SPACE="Really-amin/ultichat-hugginigfae"
DEFAULT_MESSAGE="🚀 Manual deployment $(date '+%Y-%m-%d %H:%M:%S')"

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

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if HF_TOKEN is set
    if [ -z "$HF_TOKEN" ]; then
        print_error "HF_TOKEN environment variable is not set!"
        echo ""
        echo "Please set your Hugging Face token:"
        echo "export HF_TOKEN=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"
        echo ""
        echo "Or source it from .env file:"
        echo "source .env"
        exit 1
    fi
    
    # Validate token format
    if ! echo "$HF_TOKEN" | grep -q "^hf_"; then
        print_error "Invalid HF_TOKEN format. Token should start with 'hf_'"
        exit 1
    fi
    
    print_success "HF_TOKEN is set and has correct format"
    
    # Check if huggingface-cli is installed
    if ! command -v huggingface-cli &> /dev/null; then
        print_warning "huggingface-cli not found. Installing..."
        pip install -U huggingface_hub
        if ! command -v huggingface-cli &> /dev/null; then
            print_error "Failed to install huggingface-cli"
            exit 1
        fi
    fi
    print_success "huggingface-cli is available"
    
    # Test token validity
    print_status "Validating HF token..."
    if huggingface-cli whoami --token "$HF_TOKEN" >/dev/null 2>&1; then
        USER_INFO=$(huggingface-cli whoami --token "$HF_TOKEN")
        print_success "Token is valid"
        echo "  User: $(echo "$USER_INFO" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)"
    else
        print_error "Token validation failed. Please check your HF_TOKEN"
        exit 1
    fi
}

# Prepare deployment files
prepare_deployment() {
    print_status "Preparing deployment files..."
    
    # Create app.py for Hugging Face Spaces if it doesn't exist
    if [ ! -f "app.py" ]; then
        print_status "Creating app.py for Hugging Face Spaces..."
        cat > app.py << 'EOF'
import gradio as gr
import subprocess
import sys
import os
from pathlib import Path
import threading
import time

# Set environment variables for Hugging Face Spaces
os.environ["PORT"] = "7860"
os.environ["HOST"] = "0.0.0.0"

def install_requirements():
    """Install requirements if needed"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return "✅ Requirements installed successfully"
    except Exception as e:
        return f"❌ Error installing requirements: {str(e)}"

def start_main_app():
    """Start the main application in background"""
    try:
        if Path("main.py").exists():
            # Start main.py in background
            proc = subprocess.Popen([sys.executable, "main.py"])
            time.sleep(2)  # Give it time to start
            if proc.poll() is None:
                return "🚀 Main application started successfully! Check the logs for details."
            else:
                return "❌ Main application failed to start"
        else:
            return "❌ main.py not found"
    except Exception as e:
        return f"❌ Error starting main application: {str(e)}"

def check_status():
    """Check application status"""
    try:
        # Try to check if main app is running on port 8000
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            return "✅ Main application is running and healthy"
        else:
            return f"⚠️ Main application responded with status {response.status_code}"
    except Exception:
        return "❌ Main application is not responding"

# Create Gradio interface
with gr.Blocks(
    title="Multi-Agent Code Generator",
    theme=gr.themes.Soft(),
    css="""
    .container { max-width: 800px; margin: auto; }
    .status-box { font-family: monospace; }
    """
) as demo:
    gr.Markdown("""
    # 🚀 Multi-Agent Code Generation System
    
    A production-ready, intelligent code generation platform powered by CrewAI and OpenAI that automatically creates complete software projects from natural language descriptions.
    
    ## 🎯 Features
    - **Multi-Agent Workflow**: Intelligent agents for planning, coding, testing, and documentation
    - **Real-time Collaboration**: Live WebSocket updates and AI chat
    - **Advanced Code Editor**: Live preview and editing capabilities
    - **Persian/Farsi UI**: RTL-supported interface with localization
    """)
    
    with gr.Row():
        with gr.Column():
            install_btn = gr.Button("📦 Install Requirements", variant="secondary", size="lg")
            start_btn = gr.Button("🚀 Start Main Application", variant="primary", size="lg")
            status_btn = gr.Button("🔍 Check Status", variant="secondary", size="lg")
    
    output = gr.Textbox(
        label="System Status", 
        lines=4, 
        elem_classes=["status-box"],
        show_copy_button=True
    )
    
    install_btn.click(install_requirements, outputs=output)
    start_btn.click(start_main_app, outputs=output)
    status_btn.click(check_status, outputs=output)
    
    gr.Markdown("""
    ## 🔧 Setup Instructions
    
    1. **Install Dependencies**: Click "📦 Install Requirements" first
    2. **Configure Environment**: Set your environment variables in Hugging Face Spaces settings:
       - `OPENAI_API_KEY`: Your OpenAI API key  
       - `JWT_SECRET_KEY`: A secure random string for JWT signing
       - `DATABASE_URL`: PostgreSQL connection string (if using external DB)
    3. **Start Application**: Click "🚀 Start Main Application"
    4. **Check Status**: Use "🔍 Check Status" to verify everything is running
    
    ## 🌐 Access Points
    
    Once the main application starts, it will be available on:
    - **Main Interface**: Port 8000 (redirected through this Gradio interface)
    - **API Endpoints**: Available at `/api/` routes
    - **WebSocket**: Real-time updates at `/ws`
    
    ## 📚 Documentation
    
    - **API Docs**: Available at `/docs` once the application starts
    - **Health Check**: Monitor at `/health`
    - **Metrics**: Performance metrics at `/metrics`
    """)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
EOF
        print_success "Created app.py for Hugging Face Spaces"
    else
        print_success "app.py already exists"
    fi
    
    # Check requirements.txt
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    print_success "requirements.txt found"
    
    # Add gradio to requirements if not present
    if ! grep -q "gradio" requirements.txt; then
        print_status "Adding gradio to requirements.txt..."
        echo "gradio>=4.0.0" >> requirements.txt
        print_success "Added gradio to requirements.txt"
    fi
}

# Deploy to Hugging Face
deploy_to_hf() {
    print_status "Deploying to Hugging Face Spaces..."
    
    # Get commit message
    COMMIT_MSG="${1:-$DEFAULT_MESSAGE}"
    
    # Login to Hugging Face
    print_status "Logging in to Hugging Face..."
    huggingface-cli login --token "$HF_TOKEN"
    print_success "Logged in to Hugging Face"
    
    # Upload files
    print_status "Uploading files to $HF_SPACE..."
    echo "Commit message: $COMMIT_MSG"
    
    huggingface-cli upload "$HF_SPACE" . \
        --repo-type=space \
        --commit-message="$COMMIT_MSG" \
        --exclude="*.git*" \
        --exclude="*/__pycache__/*" \
        --exclude="*.pyc" \
        --exclude="*/.venv/*" \
        --exclude="*/venv/*" \
        --exclude="*/node_modules/*" \
        --exclude="*.log" \
        --exclude="*/temp/*" \
        --exclude="*/logs/*" \
        --exclude="*/backups/*" \
        --exclude=".env"
    
    print_success "Upload completed successfully!"
}

# Show deployment info
show_deployment_info() {
    echo ""
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo "📊 Deployment Details:"
    echo "├─ 🚀 Space: $HF_SPACE"
    echo "├─ 🌐 URL: https://huggingface.co/spaces/$HF_SPACE"
    echo "├─ 📅 Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
        echo "└─ 🔄 Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
    fi
    echo ""
    echo "🔗 View your deployment: https://huggingface.co/spaces/$HF_SPACE"
    echo ""
    print_status "Next steps:"
    echo "1. Visit the URL above to see your deployed space"
    echo "2. Check the build logs in the Hugging Face interface"
    echo "3. Set environment variables in Space settings if needed"
    echo "4. Test the application functionality"
    echo ""
}

# Validate token function (can be called separately)
validate_token() {
    if [ -z "$HF_TOKEN" ]; then
        print_error "HF_TOKEN not set"
        return 1
    fi
    
    if ! echo "$HF_TOKEN" | grep -q "^hf_"; then
        print_error "Invalid token format"
        return 1
    fi
    
    if huggingface-cli whoami --token "$HF_TOKEN" >/dev/null 2>&1; then
        print_success "Token is valid"
        huggingface-cli whoami --token "$HF_TOKEN"
        return 0
    else
        print_error "Token validation failed"
        return 1
    fi
}

# Main deployment process
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            prepare_deployment
            deploy_to_hf "$2"
            show_deployment_info
            ;;
        "validate")
            validate_token
            ;;
        "prepare")
            prepare_deployment
            print_success "Deployment files prepared"
            ;;
        "help")
            echo "Usage: $0 [command] [message]"
            echo ""
            echo "Commands:"
            echo "  deploy [message]  - Full deployment (default)"
            echo "  validate          - Validate HF token only"
            echo "  prepare          - Prepare deployment files only"
            echo "  help             - Show this help"
            echo ""
            echo "Environment variables:"
            echo "  HF_TOKEN         - Your Hugging Face token (required)"
            echo ""
            echo "Examples:"
            echo "  export HF_TOKEN=hf_your_token_here"
            echo "  $0 deploy \"Updated UI components\""
            echo "  $0 validate"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"