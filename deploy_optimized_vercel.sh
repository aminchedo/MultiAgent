#!/bin/bash

# Optimized Vercel Deployment Script
# Based on Cursor Agent prompt requirements

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Optimized Vercel Deployment Script${NC}"
echo "=================================="

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}❌ Vercel CLI not found. Please install it first:${NC}"
    echo "npm i -g vercel"
    exit 1
fi

# Check if we're in a Vercel project
if [ ! -f "vercel.json" ]; then
    echo -e "${RED}❌ vercel.json not found. Please run this script from your project root.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Vercel project detected${NC}"

# 1. Environment Variables Setup
echo -e "\n${BLUE}🔧 Setting up environment variables...${NC}"

# Check if JWT_SECRET_KEY is already set
if vercel env ls | grep -q "JWT_SECRET_KEY"; then
    echo -e "${GREEN}✅ JWT_SECRET_KEY already configured${NC}"
else
    echo -e "${YELLOW}⚠️  JWT_SECRET_KEY not found. Setting up...${NC}"
    
    # Generate a secure JWT secret
    JWT_SECRET=$(openssl rand -base64 32)
    
    # Add to Vercel environment variables
    echo "$JWT_SECRET" | vercel env add JWT_SECRET_KEY production
    echo "$JWT_SECRET" | vercel env add JWT_SECRET_KEY preview
    echo "$JWT_SECRET" | vercel env add JWT_SECRET_KEY development
    
    echo -e "${GREEN}✅ JWT_SECRET_KEY configured for all environments${NC}"
fi

# Check for OPENAI_API_KEY
if vercel env ls | grep -q "OPENAI_API_KEY"; then
    echo -e "${GREEN}✅ OPENAI_API_KEY already configured${NC}"
else
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not found. Please set it manually:${NC}"
    echo "vercel env add OPENAI_API_KEY"
fi

# 2. Validate Configuration Files
echo -e "\n${BLUE}🔍 Validating configuration files...${NC}"

# Check if security.py exists
if [ -f "config/security.py" ]; then
    echo -e "${GREEN}✅ config/security.py found${NC}"
else
    echo -e "${RED}❌ config/security.py missing${NC}"
    exit 1
fi

# Check if startup.py exists
if [ -f "api/startup.py" ]; then
    echo -e "${GREEN}✅ api/startup.py found${NC}"
else
    echo -e "${RED}❌ api/startup.py missing${NC}"
    exit 1
fi

# Check if __init__.py exists
if [ -f "api/__init__.py" ]; then
    echo -e "${GREEN}✅ api/__init__.py found${NC}"
else
    echo -e "${RED}❌ api/__init__.py missing${NC}"
    exit 1
fi

# 3. Test Local Setup
echo -e "\n${BLUE}🧪 Testing local setup...${NC}"

# Test Python imports
if python3 -c "from config.security import JWT_SECRET_KEY; print('✅ Security module imports successfully')" 2>/dev/null; then
    echo -e "${GREEN}✅ Security module imports successfully${NC}"
else
    echo -e "${RED}❌ Security module import failed${NC}"
    exit 1
fi

if python3 -c "from api.startup import init_app; print('✅ Startup module imports successfully')" 2>/dev/null; then
    echo -e "${GREEN}✅ Startup module imports successfully${NC}"
else
    echo -e "${RED}❌ Startup module import failed${NC}"
    exit 1
fi

# 4. Deploy to Vercel
echo -e "\n${BLUE}🚀 Deploying to Vercel...${NC}"

# Deploy to preview first
echo -e "${YELLOW}Deploying to preview environment...${NC}"
vercel --yes

# Get the preview URL
PREVIEW_URL=$(vercel ls | grep -o 'https://[^[:space:]]*' | head -1)
echo -e "${GREEN}✅ Preview deployed: ${PREVIEW_URL}${NC}"

# 5. Health Check
echo -e "\n${BLUE}🏥 Running health checks...${NC}"

# Wait a moment for deployment to complete
sleep 5

# Test health endpoint
HEALTH_RESPONSE=$(curl -s "${PREVIEW_URL}/health" || echo "FAILED")

if echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    echo "Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "Response: $HEALTH_RESPONSE"
fi

# 6. Production Deployment
echo -e "\n${BLUE}🎯 Deploying to production...${NC}"

read -p "Deploy to production? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    vercel --prod --yes
    
    # Get production URL
    PROD_URL=$(vercel ls | grep -o 'https://[^[:space:]]*' | head -1)
    echo -e "${GREEN}✅ Production deployed: ${PROD_URL}${NC}"
    
    # Final health check
    echo -e "\n${BLUE}🏥 Final production health check...${NC}"
    sleep 5
    
    PROD_HEALTH=$(curl -s "${PROD_URL}/health" || echo "FAILED")
    if echo "$PROD_HEALTH" | grep -q '"status":"ok"'; then
        echo -e "${GREEN}✅ Production health check passed${NC}"
        echo "Response: $PROD_HEALTH"
    else
        echo -e "${RED}❌ Production health check failed${NC}"
        echo "Response: $PROD_HEALTH"
    fi
else
    echo -e "${YELLOW}⏭️  Skipping production deployment${NC}"
fi

# 7. Deployment Summary
echo -e "\n${BLUE}📊 Deployment Summary${NC}"
echo "========================"
echo -e "${GREEN}✅ Environment variables configured${NC}"
echo -e "${GREEN}✅ Configuration files validated${NC}"
echo -e "${GREEN}✅ Local imports tested${NC}"
echo -e "${GREEN}✅ Preview deployment completed${NC}"

if [ ! -z "$PROD_URL" ]; then
    echo -e "${GREEN}✅ Production deployment completed${NC}"
    echo -e "${BLUE}🌐 Production URL: ${PROD_URL}${NC}"
fi

echo -e "\n${BLUE}🔧 Next Steps:${NC}"
echo "1. Monitor the health endpoint: ${PREVIEW_URL}/health"
echo "2. Check Vercel function logs for any issues"
echo "3. Test your application functionality"
echo "4. Set up monitoring and alerts"

echo -e "\n${GREEN}🎉 Optimized deployment completed!${NC}"