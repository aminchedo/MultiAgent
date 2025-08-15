#!/bin/bash

# Multi-Agent Code Generation System - Launch Script
# Script to launch backend server and open frontend

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_FILE="front.html"
TEST_FILE="test_enhanced_ui.html"
MAX_RETRIES=30
RETRY_DELAY=2

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
    echo "║  🔧 حالت: راه‌اندازی خودکار                                   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to check dependencies
check_dependencies() {
    print_status "بررسی وابستگی‌ها..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "محیط مجازی یافت نشد!"
        echo "💡 لطفاً ابتدا محیط مجازی را ایجاد کنید:"
        echo "   python3 -m venv venv"
        echo "   source venv/bin/activate"
        echo "   pip install -r 'requirements - Copy.txt'"
        return 1
    fi
    
    # Check if backend file exists
    if [ ! -f "back.py" ]; then
        print_error "فایل back.py یافت نشد!"
        return 1
    fi
    
    # Check if frontend file exists
    if [ ! -f "$FRONTEND_FILE" ]; then
        print_error "فایل $FRONTEND_FILE یافت نشد!"
        return 1
    fi
    
    print_success "تمام وابستگی‌ها موجود هستند"
    return 0
}

# Function to start backend
start_backend() {
    print_status "راه‌اندازی سرور بک‌اند..."
    
    # Check if backend is already running
    if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
        print_warning "سرور بک‌اند در حال اجرا است"
        return 0
    fi
    
    # Start backend in background
    source venv/bin/activate
    nohup python back.py > backend.log 2>&1 &
    BACKEND_PID=$!
    
    # Save PID for cleanup
    echo $BACKEND_PID > backend.pid
    
    print_success "سرور بک‌اند شروع شد (PID: $BACKEND_PID)"
    return 0
}

# Function to wait for backend
wait_for_backend() {
    print_status "انتظار برای آماده شدن سرور..."
    
    for attempt in $(seq 1 $MAX_RETRIES); do
        if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
            print_success "سرور بک‌اند آماده است!"
            
            # Get server info
            SERVER_INFO=$(curl -s "$BACKEND_URL/health")
            STATUS=$(echo "$SERVER_INFO" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            DATABASE=$(echo "$SERVER_INFO" | grep -o '"database":"[^"]*"' | cut -d'"' -f4)
            AUTH_ENABLED=$(echo "$SERVER_INFO" | grep -o '"enabled":[^,]*' | cut -d':' -f2)
            
            echo "   📊 وضعیت: $STATUS"
            echo "   🗄️ دیتابیس: $DATABASE"
            echo "   🔑 احراز هویت: $([ "$AUTH_ENABLED" = "true" ] && echo "فعال" || echo "غیرفعال")"
            return 0
        fi
        
        echo "   ⏳ تلاش $attempt/$MAX_RETRIES..."
        sleep $RETRY_DELAY
    done
    
    print_error "سرور بک‌اند در زمان مشخص شده آماده نشد!"
    return 1
}

# Function to open frontend
open_frontend() {
    local file_path=${1:-$FRONTEND_FILE}
    
    if [ ! -f "$file_path" ]; then
        print_error "فایل $file_path یافت نشد!"
        return 1
    fi
    
    print_status "باز کردن $file_path در مرورگر..."
    
    # Get absolute path
    ABS_PATH=$(realpath "$file_path")
    FILE_URL="file://$ABS_PATH"
    
    # Open in default browser
    if command -v xdg-open > /dev/null; then
        xdg-open "$FILE_URL"
    elif command -v open > /dev/null; then
        open "$FILE_URL"
    else
        print_warning "نمی‌توان مرورگر را باز کرد. لطفاً دستی باز کنید:"
        echo "   $FILE_URL"
        return 1
    fi
    
    print_success "مرورگر باز شد"
    echo "   📁 فایل: $file_path"
    echo "   🔗 آدرس: $FILE_URL"
    return 0
}

# Function to check server status
check_server_status() {
    print_status "بررسی وضعیت سرور..."
    
    if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
        SERVER_INFO=$(curl -s "$BACKEND_URL/health")
        TIMESTAMP=$(echo "$SERVER_INFO" | grep -o '"timestamp":"[^"]*"' | cut -d'"' -f4)
        STATUS=$(echo "$SERVER_INFO" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        DATABASE=$(echo "$SERVER_INFO" | grep -o '"database":"[^"]*"' | cut -d'"' -f4)
        ACTIVE_JOBS=$(echo "$SERVER_INFO" | grep -o '"active_jobs":[0-9]*' | cut -d':' -f2)
        AUTH_ENABLED=$(echo "$SERVER_INFO" | grep -o '"enabled":[^,]*' | cut -d':' -f2)
        
        print_success "سرور فعال است"
        echo "   🕒 زمان: $TIMESTAMP"
        echo "   📊 وضعیت: $STATUS"
        echo "   🗄️ دیتابیس: $DATABASE"
        echo "   🔄 job های فعال: $ACTIVE_JOBS"
        echo "   🔑 احراز هویت: $([ "$AUTH_ENABLED" = "true" ] && echo "فعال" || echo "غیرفعال")"
    else
        print_error "سرور در دسترس نیست"
    fi
}

# Function to restart backend
restart_backend() {
    print_status "راه‌اندازی مجدد سرور..."
    
    # Stop current backend
    if [ -f "backend.pid" ]; then
        BACKEND_PID=$(cat backend.pid)
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            kill "$BACKEND_PID"
            rm backend.pid
            print_success "سرور قبلی متوقف شد"
        fi
    fi
    
    # Start new backend
    if start_backend && wait_for_backend; then
        print_success "سرور با موفقیت راه‌اندازی مجدد شد"
    else
        print_error "راه‌اندازی مجدد ناموفق بود"
    fi
}

# Function to open project folder
open_project_folder() {
    print_status "باز کردن پوشه پروژه..."
    
    if command -v xdg-open > /dev/null; then
        xdg-open .
    elif command -v open > /dev/null; then
        open .
    else
        print_warning "نمی‌توان پوشه را باز کرد"
        return 1
    fi
    
    print_success "پوشه پروژه باز شد"
}

# Function to open API docs
open_api_docs() {
    print_status "باز کردن مستندات API..."
    
    DOCS_URL="$BACKEND_URL/docs"
    
    if command -v xdg-open > /dev/null; then
        xdg-open "$DOCS_URL"
    elif command -v open > /dev/null; then
        open "$DOCS_URL"
    else
        print_warning "نمی‌توان مستندات را باز کرد"
        echo "   لطفاً دستی باز کنید: $DOCS_URL"
        return 1
    fi
    
    print_success "مستندات API باز شد"
}

# Function to cleanup
cleanup() {
    print_status "در حال توقف سرور..."
    
    if [ -f "backend.pid" ]; then
        BACKEND_PID=$(cat backend.pid)
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            kill "$BACKEND_PID"
            rm backend.pid
            print_success "سرور متوقف شد"
        fi
    fi
}

# Function to show menu
show_menu() {
    while true; do
        echo
        print_header "============================================================"
        print_header "🎛️ منوی کنترل"
        print_header "============================================================"
        echo "1. 🌐 باز کردن رابط اصلی"
        echo "2. 🧪 باز کردن صفحه تست"
        echo "3. 📊 بررسی وضعیت سرور"
        echo "4. 🔄 راه‌اندازی مجدد سرور"
        echo "5. 📁 باز کردن پوشه پروژه"
        echo "6. 📚 مستندات API"
        echo "0. 🚪 خروج"
        print_header "============================================================"
        
        read -p "انتخاب کنید (0-6): " choice
        
        case $choice in
            1)
                open_frontend "$FRONTEND_FILE"
                ;;
            2)
                open_frontend "$TEST_FILE"
                ;;
            3)
                check_server_status
                ;;
            4)
                restart_backend
                ;;
            5)
                open_project_folder
                ;;
            6)
                open_api_docs
                ;;
            0)
                print_status "خروج از برنامه..."
                break
                ;;
            *)
                print_error "انتخاب نامعتبر!"
                ;;
        esac
    done
}

# Function to handle signals
signal_handler() {
    print_status "دریافت سیگنال توقف..."
    cleanup
    exit 0
}

# Set up signal handlers
trap signal_handler SIGINT SIGTERM

# Main function
main() {
    print_banner
    
    # Check dependencies
    if ! check_dependencies; then
        print_error "بررسی وابستگی‌ها ناموفق بود!"
        exit 1
    fi
    
    # Start backend
    if ! start_backend; then
        print_error "راه‌اندازی سرور ناموفق بود!"
        exit 1
    fi
    
    # Wait for backend to be ready
    if ! wait_for_backend; then
        print_error "سرور در زمان مشخص شده آماده نشد!"
        cleanup
        exit 1
    fi
    
    # Open frontend
    echo
    print_success "راه‌اندازی کامل شد!"
    print_header "============================================================"
    print_header "📋 اطلاعات دسترسی:"
    echo "   🌐 سرور: $BACKEND_URL"
    echo "   📚 مستندات: $BACKEND_URL/docs"
    echo "   🔍 وضعیت: $BACKEND_URL/health"
    print_header "============================================================"
    
    # Open main frontend
    open_frontend "$FRONTEND_FILE"
    
    # Show interactive menu
    show_menu
    
    # Cleanup
    cleanup
}

# Run main function
main "$@"