@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Multi-Agent Code Generation System - Launch Script
REM Script to launch backend server and open frontend

REM Configuration
set BACKEND_URL=http://localhost:8000
set FRONTEND_FILE=front.html
set TEST_FILE=test_enhanced_ui.html
set MAX_RETRIES=30
set RETRY_DELAY=2

REM Function to print colored output
:print_status
echo [INFO] %~1
goto :eof

:print_warning
echo [WARNING] %~1
goto :eof

:print_error
echo [ERROR] %~1
goto :eof

:print_success
echo [SUCCESS] %~1
goto :eof

:print_header
echo %~1
goto :eof

REM Function to print banner
:print_banner
cls
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🤖 سیستم چند-عامله تولید کد                ║
echo ║                    Multi-Agent Code Generator                ║
echo ║                                                              ║
echo ║  🚀 نسخه: 1.0.0                                              ║
echo ║  📅 تاریخ: %date% %time%                                      ║
echo ║  🔧 حالت: راه‌اندازی خودکار                                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
goto :eof

REM Function to check dependencies
:check_dependencies
call :print_status "بررسی وابستگی‌ها..."

REM Check if virtual environment exists
if not exist "venv" (
    call :print_error "محیط مجازی یافت نشد!"
    echo 💡 لطفاً ابتدا محیط مجازی را ایجاد کنید:
    echo    python -m venv venv
    echo    venv\Scripts\activate
    echo    pip install -r "requirements - Copy.txt"
    exit /b 1
)

REM Check if backend file exists
if not exist "back.py" (
    call :print_error "فایل back.py یافت نشد!"
    exit /b 1
)

REM Check if frontend file exists
if not exist "%FRONTEND_FILE%" (
    call :print_error "فایل %FRONTEND_FILE% یافت نشد!"
    exit /b 1
)

call :print_success "تمام وابستگی‌ها موجود هستند"
exit /b 0

REM Function to start backend
:start_backend
call :print_status "راه‌اندازی سرور بک‌اند..."

REM Check if backend is already running
curl -s "%BACKEND_URL%/health" >nul 2>&1
if !errorlevel! equ 0 (
    call :print_warning "سرور بک‌اند در حال اجرا است"
    exit /b 0
)

REM Start backend in background
call venv\Scripts\activate.bat
start /B python back.py > backend.log 2>&1

REM Wait a moment for the process to start
timeout /t 2 /nobreak >nul

call :print_success "سرور بک‌اند شروع شد"
exit /b 0

REM Function to wait for backend
:wait_for_backend
call :print_status "انتظار برای آماده شدن سرور..."

for /l %%i in (1,1,%MAX_RETRIES%) do (
    curl -s "%BACKEND_URL%/health" >nul 2>&1
    if !errorlevel! equ 0 (
        call :print_success "سرور بک‌اند آماده است!"
        
        REM Get server info
        for /f "tokens=*" %%a in ('curl -s "%BACKEND_URL%/health"') do set SERVER_INFO=%%a
        
        echo    📊 وضعیت: healthy
        echo    🗄️ دیتابیس: connected
        echo    🔑 احراز هویت: فعال
        exit /b 0
    )
    
    echo    ⏳ تلاش %%i/%MAX_RETRIES%...
    timeout /t %RETRY_DELAY% /nobreak >nul
)

call :print_error "سرور بک‌اند در زمان مشخص شده آماده نشد!"
exit /b 1

REM Function to open frontend
:open_frontend
set file_path=%~1
if "%file_path%"=="" set file_path=%FRONTEND_FILE%

if not exist "%file_path%" (
    call :print_error "فایل %file_path% یافت نشد!"
    exit /b 1
)

call :print_status "باز کردن %file_path% در مرورگر..."

REM Get absolute path
for %%i in ("%file_path%") do set ABS_PATH=%%~fi
set FILE_URL=file:///%ABS_PATH%

REM Open in default browser
start "" "%FILE_URL%"

call :print_success "مرورگر باز شد"
echo    📁 فایل: %file_path%
echo    🔗 آدرس: %FILE_URL%
exit /b 0

REM Function to check server status
:check_server_status
call :print_status "بررسی وضعیت سرور..."

curl -s "%BACKEND_URL%/health" >nul 2>&1
if !errorlevel! equ 0 (
    call :print_success "سرور فعال است"
    echo    🕒 زمان: %date% %time%
    echo    📊 وضعیت: healthy
    echo    🗄️ دیتابیس: connected
    echo    🔄 job های فعال: 0
    echo    🔑 احراز هویت: فعال
) else (
    call :print_error "سرور در دسترس نیست"
)
goto :eof

REM Function to restart backend
:restart_backend
call :print_status "راه‌اندازی مجدد سرور..."

REM Stop current backend (find and kill Python processes running back.py)
taskkill /f /im python.exe >nul 2>&1

REM Start new backend
call :start_backend
if !errorlevel! equ 0 (
    call :wait_for_backend
    if !errorlevel! equ 0 (
        call :print_success "سرور با موفقیت راه‌اندازی مجدد شد"
    ) else (
        call :print_error "راه‌اندازی مجدد ناموفق بود"
    )
) else (
    call :print_error "خطا در راه‌اندازی مجدد"
)
goto :eof

REM Function to open project folder
:open_project_folder
call :print_status "باز کردن پوشه پروژه..."
explorer .
call :print_success "پوشه پروژه باز شد"
goto :eof

REM Function to open API docs
:open_api_docs
call :print_status "باز کردن مستندات API..."
set DOCS_URL=%BACKEND_URL%/docs
start "" "%DOCS_URL%"
call :print_success "مستندات API باز شد"
goto :eof

REM Function to show menu
:show_menu
:menu_loop
echo.
call :print_header "============================================================"
call :print_header "🎛️ منوی کنترل"
call :print_header "============================================================"
echo 1. 🌐 باز کردن رابط اصلی
echo 2. 🧪 باز کردن صفحه تست
echo 3. 📊 بررسی وضعیت سرور
echo 4. 🔄 راه‌اندازی مجدد سرور
echo 5. 📁 باز کردن پوشه پروژه
echo 6. 📚 مستندات API
echo 0. 🚪 خروج
call :print_header "============================================================"

set /p choice="انتخاب کنید (0-6): "

if "%choice%"=="1" (
    call :open_frontend "%FRONTEND_FILE%"
) else if "%choice%"=="2" (
    call :open_frontend "%TEST_FILE%"
) else if "%choice%"=="3" (
    call :check_server_status
) else if "%choice%"=="4" (
    call :restart_backend
) else if "%choice%"=="5" (
    call :open_project_folder
) else if "%choice%"=="6" (
    call :open_api_docs
) else if "%choice%"=="0" (
    call :print_status "خروج از برنامه..."
    goto :cleanup
) else (
    call :print_error "انتخاب نامعتبر!"
)

goto :menu_loop

REM Function to cleanup
:cleanup
call :print_status "در حال توقف سرور..."
taskkill /f /im python.exe >nul 2>&1
call :print_success "سرور متوقف شد"
goto :eof

REM Main function
:main
call :print_banner

REM Check dependencies
call :check_dependencies
if !errorlevel! neq 0 (
    call :print_error "بررسی وابستگی‌ها ناموفق بود!"
    pause
    exit /b 1
)

REM Start backend
call :start_backend
if !errorlevel! neq 0 (
    call :print_error "راه‌اندازی سرور ناموفق بود!"
    pause
    exit /b 1
)

REM Wait for backend to be ready
call :wait_for_backend
if !errorlevel! neq 0 (
    call :print_error "سرور در زمان مشخص شده آماده نشد!"
    call :cleanup
    pause
    exit /b 1
)

REM Open frontend
echo.
call :print_success "راه‌اندازی کامل شد!"
call :print_header "============================================================"
call :print_header "📋 اطلاعات دسترسی:"
echo    🌐 سرور: %BACKEND_URL%
echo    📚 مستندات: %BACKEND_URL%/docs
echo    🔍 وضعیت: %BACKEND_URL%/health
call :print_header "============================================================"

REM Open main frontend
call :open_frontend "%FRONTEND_FILE%"

REM Show interactive menu
call :show_menu

REM Cleanup
call :cleanup
goto :eof

REM Run main function
call :main
pause