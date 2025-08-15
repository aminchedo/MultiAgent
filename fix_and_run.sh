#!/bin/bash

# Multi-Agent Code Generation System - Fix and Run Script
# This script fixes all known issues and runs the application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_header() {
    echo -e "${CYAN}$1${NC}"
}

# Function to print banner
print_banner() {
    clear
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🤖 سیستم چند-عامله تولید کد                ║"
    echo "║                    Multi-Agent Code Generator                ║"
    echo "║                                                              ║"
    echo "║  🚀 نسخه: 1.0.0                                              ║"
    echo "║  📅 تاریخ: $(date '+%Y-%m-%d %H:%M:%S')                      ║"
    echo "║  🔧 حالت: رفع مشکل و راه‌اندازی                               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to check and kill existing processes
kill_existing_processes() {
    print_status "بررسی و توقف فرآیندهای موجود..."
    
    # Kill any existing Python processes
    if pkill -f "python3 main.py" 2>/dev/null; then
        print_success "فرآیندهای Python متوقف شدند"
    else
        print_status "هیچ فرآیند Python در حال اجرا نبود"
    fi
    
    sleep 2
}

# Function to setup virtual environment
setup_virtual_environment() {
    print_status "بررسی محیط مجازی..."
    
    if [ ! -d "venv" ]; then
        print_status "ایجاد محیط مجازی..."
        python3 -m venv venv
        print_success "محیط مجازی ایجاد شد"
    else
        print_success "محیط مجازی موجود است"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    print_status "به‌روزرسانی pip..."
    pip install --upgrade pip
    
    # Install dependencies
    print_status "نصب وابستگی‌ها..."
    pip install -r requirements.txt
    
    # Install additional required packages
    print_status "نصب بسته‌های اضافی..."
    pip install langchain-community
    
    print_success "تمام وابستگی‌ها نصب شدند"
}

# Function to fix configuration issues
fix_configuration() {
    print_status "رفع مشکلات پیکربندی..."
    
    # Create necessary directories
    mkdir -p uploads temp logs
    
    # Set proper permissions
    chmod 755 uploads temp logs
    
    print_success "پیکربندی اصلاح شد"
}

# Function to check database connection
check_database() {
    print_status "بررسی اتصال پایگاه داده..."
    
    # For now, we'll skip database checks since we're running locally
    print_warning "بررسی پایگاه داده رد شد (اجرای محلی)"
}

# Function to start the application
start_application() {
    print_status "راه‌اندازی برنامه..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start the application
    print_status "شروع سرور FastAPI..."
    python3 main.py &
    
    # Wait for the application to start
    sleep 5
    
    # Check if the application is running
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "برنامه با موفقیت راه‌اندازی شد!"
        print_status "سرور در آدرس: http://localhost:8000"
        print_status "مستندات API: http://localhost:8000/docs"
        print_status "رابط کاربری: http://localhost:8000/"
    else
        print_error "برنامه راه‌اندازی نشد!"
        print_status "بررسی لاگ‌ها..."
        tail -20 temp/app.log
        return 1
    fi
}

# Function to open frontend
open_frontend() {
    print_status "باز کردن رابط کاربری..."
    
    # Check if we have a frontend file
    if [ -f "frontend/pages/front_optimized.html" ]; then
        print_status "باز کردن فایل front_optimized.html..."
        if command -v xdg-open > /dev/null; then
            xdg-open frontend/pages/front_optimized.html
        elif command -v open > /dev/null; then
            open frontend/pages/front_optimized.html
        else
            print_warning "نمی‌توان فایل HTML را باز کرد. لطفاً به صورت دستی باز کنید:"
            echo "   frontend/pages/front_optimized.html"
        fi
    else
        print_warning "فایل frontend یافت نشد"
    fi
}

# Main execution
main() {
    print_banner
    
    print_header "شروع فرآیند رفع مشکل و راه‌اندازی..."
    
    # Step 1: Kill existing processes
    kill_existing_processes
    
    # Step 2: Setup virtual environment
    setup_virtual_environment
    
    # Step 3: Fix configuration
    fix_configuration
    
    # Step 4: Check database
    check_database
    
    # Step 5: Start application
    if start_application; then
        print_success "✅ برنامه با موفقیت راه‌اندازی شد!"
        
        # Step 6: Open frontend
        open_frontend
        
        print_header "🎉 سیستم آماده استفاده است!"
        echo ""
        echo "📋 اطلاعات مهم:"
        echo "   🌐 سرور: http://localhost:8000"
        echo "   📚 مستندات: http://localhost:8000/docs"
        echo "   🔍 وضعیت: http://localhost:8000/health"
        echo "   📁 فایل‌ها: frontend/pages/front_optimized.html"
        echo ""
        echo "🛑 برای توقف برنامه: Ctrl+C"
        echo ""
        
        # Keep the script running
        wait
    else
        print_error "❌ راه‌اندازی ناموفق بود!"
        exit 1
    fi
}

# Run main function
main "$@"