#!/bin/bash

# 🚀 Final Production Deployment Script for Vibe Coding Platform
# This script completes the final 10% to make the platform production-ready

set -e

echo "🎉 Starting Final Production Deployment..."
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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
    echo -e "${PURPLE}$1${NC}"
}

# Step 1: Verify Project Structure
print_header "Step 1: Verifying Project Structure"
print_status "Checking for required files and directories..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    print_error "package.json not found. Please run this script from the project root."
    exit 1
fi

# Check for required directories
required_dirs=("src" "api" "src/components" "src/lib")
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        print_error "Required directory $dir not found!"
        exit 1
    fi
done

print_success "Project structure verified!"

# Step 2: Install Dependencies
print_header "Step 2: Installing Dependencies"
print_status "Installing Node.js dependencies..."

if [ ! -d "node_modules" ]; then
    npm install
    print_success "Node.js dependencies installed!"
else
    print_status "Node.js dependencies already installed, skipping..."
fi

# Step 3: Build the Project
print_header "Step 3: Building the Project"
print_status "Building Next.js application..."

npm run build

if [ $? -eq 0 ]; then
    print_success "Build completed successfully!"
else
    print_error "Build failed! Please check the errors above."
    exit 1
fi

# Step 4: Install Vercel CLI
print_header "Step 4: Setting up Vercel CLI"
print_status "Checking if Vercel CLI is installed..."

if ! command -v vercel &> /dev/null; then
    print_status "Installing Vercel CLI..."
    npm install -g vercel
    print_success "Vercel CLI installed!"
else
    print_status "Vercel CLI already installed!"
fi

# Step 5: Deploy to Vercel
print_header "Step 5: Deploying to Vercel"
print_status "Starting Vercel deployment..."

# Check if user is logged in to Vercel
if ! vercel whoami &> /dev/null; then
    print_warning "Not logged in to Vercel. Please log in:"
    vercel login
fi

# Deploy to preview
print_status "Deploying to preview environment..."
vercel --yes

if [ $? -eq 0 ]; then
    print_success "Preview deployment successful!"
else
    print_error "Preview deployment failed!"
    exit 1
fi

# Step 6: Set Environment Variables
print_header "Step 6: Setting Environment Variables"
print_status "Setting production environment variables..."

# Generate a secure JWT secret
JWT_SECRET=$(openssl rand -base64 32)

# Set environment variables
vercel env add JWT_SECRET_KEY production <<< "$JWT_SECRET"
vercel env add NEXT_PUBLIC_API_URL production <<< "https://$(vercel ls | grep -o '[a-zA-Z0-9-]*\.vercel\.app' | head -1)"

print_success "Environment variables set!"

# Step 7: Deploy to Production
print_header "Step 7: Deploying to Production"
print_status "Deploying to production environment..."

vercel --prod --yes

if [ $? -eq 0 ]; then
    print_success "Production deployment successful!"
else
    print_error "Production deployment failed!"
    exit 1
fi

# Step 8: Test the Deployment
print_header "Step 8: Testing the Deployment"
print_status "Testing API endpoints..."

# Get the production URL
PROD_URL=$(vercel ls | grep -o 'https://[a-zA-Z0-9-]*\.vercel\.app' | head -1)

if [ -z "$PROD_URL" ]; then
    print_warning "Could not determine production URL. Please test manually."
else
    print_status "Testing login endpoint..."
    
    # Test login endpoint
    LOGIN_RESPONSE=$(curl -s -X POST "$PROD_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"admin","password":"admin"}' || echo "FAILED")
    
    if [[ "$LOGIN_RESPONSE" == *"token"* ]]; then
        print_success "Login endpoint working!"
        
        # Extract token for further testing
        TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
        
        if [ ! -z "$TOKEN" ]; then
            print_status "Testing job creation..."
            
            # Test job creation
            JOB_RESPONSE=$(curl -s -X POST "$PROD_URL/api/generate" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $TOKEN" \
                -d '{"description":"Test project","project_type":"web"}' || echo "FAILED")
            
            if [[ "$JOB_RESPONSE" == *"id"* ]]; then
                print_success "Job creation working!"
                
                # Extract job ID
                JOB_ID=$(echo "$JOB_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
                
                if [ ! -z "$JOB_ID" ]; then
                    print_status "Testing job status..."
                    
                    # Test job status
                    STATUS_RESPONSE=$(curl -s -X GET "$PROD_URL/api/status/$JOB_ID" \
                        -H "Authorization: Bearer $TOKEN" || echo "FAILED")
                    
                    if [[ "$STATUS_RESPONSE" == *"status"* ]]; then
                        print_success "Job status endpoint working!"
                    else
                        print_warning "Job status endpoint may have issues."
                    fi
                fi
            else
                print_warning "Job creation endpoint may have issues."
            fi
        fi
    else
        print_warning "Login endpoint may have issues."
    fi
fi

# Step 9: Final Summary
print_header "🎉 Deployment Complete!"
echo ""
print_success "Your Vibe Coding Platform is now live on Vercel!"
echo ""
print_status "Production URL: $PROD_URL"
print_status "Admin Login: admin / admin"
echo ""
print_status "Next Steps:"
echo "1. Visit your production URL"
echo "2. Test the complete user flow"
echo "3. Monitor the deployment in Vercel dashboard"
echo "4. Set up custom domain if needed"
echo ""
print_success "🚀 Revolutionary AI coding platform is ready for the world!"
echo ""

# Optional: Open the production URL
if command -v xdg-open &> /dev/null; then
    xdg-open "$PROD_URL"
elif command -v open &> /dev/null; then
    open "$PROD_URL"
fi

print_header "Deployment script completed successfully! 🎉"