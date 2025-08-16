#!/bin/bash

echo "🚀 Deploying Vibe Coding Platform..."

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

print_status "Starting deployment process..."

# Step 1: Install frontend dependencies
print_status "Installing frontend dependencies..."
npm install

if [ $? -ne 0 ]; then
    print_error "Failed to install frontend dependencies"
    exit 1
fi
print_success "Frontend dependencies installed"

# Step 2: Build frontend
print_status "Building frontend..."
npm run build

if [ $? -ne 0 ]; then
    print_error "Failed to build frontend"
    exit 1
fi
print_success "Frontend built successfully"

# Step 3: Install backend dependencies
print_status "Installing backend dependencies..."
cd backend
pip install -r requirements-minimal.txt --break-system-packages

if [ $? -ne 0 ]; then
    print_error "Failed to install backend dependencies"
    exit 1
fi
print_success "Backend dependencies installed"

# Step 4: Start backend
print_status "Starting backend server..."
cd /workspace/backend
PYTHONPATH=/workspace DATABASE_URL=sqlite+aiosqlite:///./local.db ~/.local/bin/uvicorn simple_app:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Test backend
print_status "Testing backend..."
if curl -s http://localhost:8000/health > /dev/null; then
    print_success "Backend is running and healthy"
else
    print_error "Backend health check failed"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Step 5: Start frontend
print_status "Starting frontend server..."
cd /workspace
npm start &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 10

# Test frontend
print_status "Testing frontend..."
if curl -s http://localhost:3000 > /dev/null; then
    print_success "Frontend is running"
else
    print_warning "Frontend may still be starting up..."
fi

# Step 6: Display final status
echo ""
print_success "🎉 Vibe Coding Platform Deployment Complete!"
echo ""
echo "📊 Service Status:"
echo "  🔧 Backend:  http://localhost:8000 (PID: $BACKEND_PID)"
echo "  🌐 Frontend: http://localhost:3000 (PID: $FRONTEND_PID)"
echo ""
echo "🔗 API Endpoints:"
echo "  Health Check: http://localhost:8000/health"
echo "  Templates:    http://localhost:8000/api/templates"
echo "  WebSocket:    ws://localhost:8000/ws"
echo ""
echo "📁 Project Structure:"
echo "  Frontend:     /workspace"
echo "  Backend:      /workspace/backend"
echo "  Database:     /workspace/backend/local.db"
echo ""
echo "🛠️  To stop services:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
print_success "Ready to generate some amazing code! 🚀"