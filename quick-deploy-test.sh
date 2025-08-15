#!/bin/bash

# 🚀 Quick Deployment Test Script for Hugging Face
# Usage: ./quick-deploy-test.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
# Check if HF_TOKEN is set
if [ -z "$HF_TOKEN" ]; then
    echo -e "${RED}❌ Error: HF_TOKEN environment variable is not set!${NC}"
    echo -e "${YELLOW}Please set your Hugging Face token:${NC}"
    echo -e "${BLUE}export HF_TOKEN=your_hf_token_here${NC}"
    echo -e "${BLUE}./quick-deploy-test.sh${NC}"
    exit 1
fi

HF_SPACE="Really-amin/ultichat-hugginigfae"
SPACE_URL="https://huggingface.co/spaces/${HF_SPACE}"
LIVE_URL="https://really-amin-ultichat-hugginigfae.hf.space"

echo -e "${PURPLE}🚀 Quick Deployment Test for Hugging Face Spaces${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

# Step 1: Environment Setup
echo -e "${YELLOW}📋 Step 1: Setting up environment...${NC}"
export HF_TOKEN="$HF_TOKEN"
echo -e "${GREEN}✅ HF_TOKEN exported${NC}"

# Step 2: Check Dependencies
echo -e "${YELLOW}📦 Step 2: Checking dependencies...${NC}"

# Check if huggingface_hub is installed
if ! python -c "import huggingface_hub" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installing huggingface_hub...${NC}"
    pip install -U huggingface_hub
fi
echo -e "${GREEN}✅ huggingface_hub ready${NC}"

# Check if git is available
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not found. Please install git.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Git ready${NC}"

# Step 3: Validate Token
echo -e "${YELLOW}🔐 Step 3: Validating HF token...${NC}"
if python -c "
from huggingface_hub import whoami
try:
    user = whoami(token='$HF_TOKEN')
    print(f'✅ Token valid for: {user[\"name\"]}')
except Exception as e:
    print(f'❌ Token validation failed: {e}')
    exit(1)
"; then
    echo -e "${GREEN}✅ Token validation passed${NC}"
else
    echo -e "${RED}❌ Token validation failed${NC}"
    exit 1
fi

# Step 4: Check Required Files
echo -e "${YELLOW}📁 Step 4: Checking required files...${NC}"
required_files=("app.py" "requirements.txt" "README.md")
missing_files=()

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file found${NC}"
    else
        echo -e "${RED}❌ $file missing${NC}"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing required files. Please ensure all files are present.${NC}"
    exit 1
fi

# Step 5: Login to Hugging Face
echo -e "${YELLOW}🔑 Step 5: Logging in to Hugging Face...${NC}"
echo "$HF_TOKEN" | huggingface-cli login --token "$HF_TOKEN" --add-to-git-credential
echo -e "${GREEN}✅ Logged in successfully${NC}"

# Step 6: Deploy to Hugging Face
echo -e "${YELLOW}🚀 Step 6: Deploying to Hugging Face Spaces...${NC}"
echo -e "${BLUE}Target Space: $HF_SPACE${NC}"

# Upload all files
huggingface-cli upload "$HF_SPACE" . \
    --repo-type=space \
    --commit-message="🚀 Quick deployment test - $(date)" \
    --commit-description="Automatic deployment via quick-deploy script"

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"

# Step 7: Deployment Summary
echo ""
echo -e "${PURPLE}🎉 DEPLOYMENT SUMMARY${NC}"
echo -e "${BLUE}===================${NC}"
echo -e "${GREEN}✅ Status: Successfully deployed${NC}"
echo -e "${GREEN}✅ Space: $HF_SPACE${NC}"
echo -e "${GREEN}✅ Space URL: $SPACE_URL${NC}"
echo -e "${GREEN}✅ Live URL: $LIVE_URL${NC}"
echo ""

# Step 8: Next Steps
echo -e "${YELLOW}📋 NEXT STEPS:${NC}"
echo -e "${BLUE}1.${NC} Go to: $SPACE_URL"
echo -e "${BLUE}2.${NC} Click 'Settings' and add these secrets:"
echo -e "   ${YELLOW}OPENAI_API_KEY${NC} = your_openai_api_key"
echo -e "   ${YELLOW}JWT_SECRET_KEY${NC} = your_jwt_secret_key"
echo -e "${BLUE}3.${NC} Wait for build to complete (5-10 minutes)"
echo -e "${BLUE}4.${NC} Test your app at: $LIVE_URL"
echo ""

# Step 9: Real-time Status Check
echo -e "${YELLOW}🔍 Step 9: Checking deployment status...${NC}"
echo -e "${BLUE}Opening Space URL in 3 seconds...${NC}"
sleep 3

# Try to open in browser (works on most systems)
if command -v xdg-open > /dev/null; then
    xdg-open "$SPACE_URL"
elif command -v open > /dev/null; then
    open "$SPACE_URL"
elif command -v start > /dev/null; then
    start "$SPACE_URL"
else
    echo -e "${YELLOW}⚠️  Please manually open: $SPACE_URL${NC}"
fi

# Step 10: Monitor Script
echo ""
echo -e "${PURPLE}🔍 MONITORING COMMANDS:${NC}"
echo -e "${BLUE}Check Space Status:${NC}"
echo "curl -s https://huggingface.co/api/spaces/$HF_SPACE | jq '.runtime.stage'"
echo ""
echo -e "${BLUE}View Live App:${NC}"
echo "curl -s $LIVE_URL"
echo ""
echo -e "${BLUE}Quick Test API:${NC}"
echo "curl -s $LIVE_URL/health"
echo ""

# Step 11: Success Message
echo -e "${GREEN}🎉 DEPLOYMENT TEST COMPLETED!${NC}"
echo -e "${PURPLE}Your Multi-Agent Code Generator is now deploying to Hugging Face Spaces!${NC}"
echo ""
echo -e "${YELLOW}⏰ Build Time: ~5-10 minutes${NC}"
echo -e "${YELLOW}📱 Monitor: $SPACE_URL${NC}"
echo -e "${YELLOW}🌐 Live URL: $LIVE_URL${NC}"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"