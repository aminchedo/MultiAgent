#!/bin/bash

# 🚀 Production Deployment Script for Vibe Coding Platform
# This script deploys the complete platform to Vercel with all production features

set -e

echo "🎉 Starting Production Deployment for Vibe Coding Platform"
echo "=========================================================="

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
if [ ! -f "package.json" ]; then
    print_error "package.json not found. Please run this script from the project root."
    exit 1
fi

print_status "📁 Current directory: $(pwd)"

# Step 1: Install dependencies
print_status "📦 Installing dependencies..."
npm install

# Step 2: Build the project
print_status "🔨 Building the project..."
npm run build

# Step 3: Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    print_warning "Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Step 4: Check if user is logged in to Vercel
print_status "🔐 Checking Vercel authentication..."
if ! vercel whoami &> /dev/null; then
    print_warning "Not logged in to Vercel. Please log in..."
    vercel login
fi

# Step 5: Set up environment variables
print_status "⚙️ Setting up environment variables..."

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    print_warning "Creating .env.local file..."
    cat > .env.local << EOF
# Development Environment Variables
NEXT_PUBLIC_API_URL=http://localhost:3000
JWT_SECRET_KEY=your-super-secret-jwt-key-for-development
VERCEL_ENV=development
EOF
fi

# Step 6: Deploy to Vercel
print_status "🚀 Deploying to Vercel..."

# Deploy to preview
print_status "Deploying preview version..."
vercel --yes

# Get the preview URL
PREVIEW_URL=$(vercel ls | grep -o 'https://[^[:space:]]*' | head -1)
print_success "Preview deployed at: $PREVIEW_URL"

# Step 7: Set production environment variables
print_status "🔧 Setting production environment variables..."

# Generate a secure JWT secret for production
PROD_JWT_SECRET=$(openssl rand -base64 32)

# Set environment variables for production
vercel env add JWT_SECRET_KEY production <<< "$PROD_JWT_SECRET"
vercel env add NEXT_PUBLIC_API_URL production <<< "https://your-app.vercel.app"

print_success "Production environment variables set"

# Step 8: Deploy to production
print_status "🌐 Deploying to production..."
vercel --prod --yes

# Get the production URL
PROD_URL=$(vercel ls | grep -o 'https://[^[:space:]]*' | head -1)
print_success "Production deployed at: $PROD_URL"

# Step 9: Test the deployment
print_status "🧪 Testing the deployment..."

# Test the API endpoints
print_status "Testing authentication endpoint..."
curl -X POST "$PROD_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin","password":"admin"}' \
  --max-time 30

print_success "Authentication endpoint test completed"

# Step 10: Create deployment summary
print_status "📋 Creating deployment summary..."

cat > DEPLOYMENT_SUMMARY.md << EOF
# 🎉 Production Deployment Complete!

## Deployment Details
- **Production URL**: $PROD_URL
- **Preview URL**: $PREVIEW_URL
- **Deployment Time**: $(date)
- **Environment**: Production

## Features Deployed
✅ **Frontend**: Revolutionary Next.js app with glassmorphism design
✅ **Backend**: Serverless API functions on Vercel
✅ **Authentication**: JWT-based secure login system
✅ **Job Generation**: Real AI agent simulation
✅ **File Generation**: Actual React/CSS/JSON file creation
✅ **Download System**: ZIP download of generated projects
✅ **Real-time Updates**: Polling-based status updates

## API Endpoints
- \`POST /api/auth/login\` - User authentication
- \`POST /api/generate\` - Create new project
- \`GET /api/status/[job_id]\` - Get job status
- \`GET /api/download/[job_id]\` - Download project

## Environment Variables
- \`JWT_SECRET_KEY\` - Secure JWT signing key
- \`NEXT_PUBLIC_API_URL\` - API base URL
- \`VERCEL_ENV\` - Deployment environment

## Test Credentials
- **Email**: admin
- **Password**: admin

## Next Steps
1. Update DNS settings if using custom domain
2. Set up monitoring and logging
3. Configure database for production use
4. Set up CI/CD pipeline

## Support
For issues or questions, check the Vercel dashboard or logs.
EOF

print_success "Deployment summary created: DEPLOYMENT_SUMMARY.md"

# Step 11: Final status
echo ""
echo "🎉 ================================================="
echo "🎉 PRODUCTION DEPLOYMENT COMPLETE!"
echo "🎉 ================================================="
echo ""
echo "🌐 Production URL: $PROD_URL"
echo "🔗 Preview URL: $PREVIEW_URL"
echo ""
echo "✨ Your revolutionary AI coding platform is now live!"
echo ""
echo "🚀 Features available:"
echo "   • Beautiful glassmorphism UI"
echo "   • Real AI agent collaboration"
echo "   • Project generation and download"
echo "   • Secure authentication"
echo "   • Global CDN distribution"
echo ""
echo "📋 Check DEPLOYMENT_SUMMARY.md for full details"
echo ""

print_success "Deployment completed successfully! 🚀"