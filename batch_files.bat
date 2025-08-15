@echo off
REM =================================================
REM          تزریق سریع ویندوز (Windows)
REM =================================================
echo 🤖 تزریق سریع سیستم چند-عامله
echo ========================================

REM بررسی Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python یافت نشد! لطفاً Python 3.8+ نصب کنید
    pause
    exit /b 1
)

echo ✅ Python یافت شد

REM نصب وابستگی‌ها
echo.
echo 📦 نصب وابستگی‌ها...
python -m pip install fastapi uvicorn[standard] websockets pydantic python-multipart --quiet
if errorlevel 1 (
    echo ⚠️ خطا در نصب وابستگی‌ها
) else (
    echo ✅ وابستگی‌ها نصب شدند
)

REM ایجاد پوشه static
if not exist "static" mkdir static
echo ✅ پوشه static ایجاد شد

REM کپی فایل HTML
if exist "front.html" (
    copy "front.html" "static\index.html" >nul
    echo ✅ فایل HTML کپی شد
)

REM بررسی فایل بک‌اند
if not exist "back.py" (
    echo ❌ فایل back.py یافت نشد!
    pause
    exit /b 1
)
echo ✅ فایل back.py یافت شد

echo.
echo 🎉 تزریق موفق!
echo 🚀 برای اجرا: python back.py
echo 🌐 آدرس: http://127.0.0.1:8000

REM پیشنهاد اجرا
set /p choice="آیا سرور را الان اجرا کنم؟ (y/n): "
if /i "%choice%"=="y" (
    echo.
    echo 🚀 در حال اجرای سرور...
    python back.py
)

pause

REM =================================================
REM          Shell Script برای Linux/Mac  
REM =================================================

: <<'EOF'
#!/bin/bash
# تزریق سریع لینوکس/مک (Linux/Mac)

echo "🤖 تزریق سریع سیستم چند-عامله"
echo "========================================"

# بررسی Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 یافت نشد! لطفاً Python 3.8+ نصب کنید"
    exit 1
fi

echo "✅ Python یافت شد"

# نصب وابستگی‌ها
echo ""
echo "📦 نصب وابستگی‌ها..."
python3 -m pip install fastapi uvicorn[standard] websockets pydantic python-multipart --quiet

if [ $? -eq 0 ]; then
    echo "✅ وابستگی‌ها نصب شدند"
else
    echo "⚠️ خطا در نصب وابستگی‌ها"
fi

# ایجاد پوشه static
mkdir -p static
echo "✅ پوشه static ایجاد شد"

# کپی فایل HTML
if [ -f "front.html" ]; then
    cp "front.html" "static/index.html"
    echo "✅ فایل HTML کپی شد"
fi

# بررسی فایل بک‌اند
if [ ! -f "back.py" ]; then
    echo "❌ فایل back.py یافت نشد!"
    exit 1
fi
echo "✅ فایل back.py یافت شد"

echo ""
echo "🎉 تزریق موفق!"
echo "🚀 برای اجرا: python3 back.py"
echo "🌐 آدرس: http://127.0.0.1:8000"

# پیشنهاد اجرا
read -p "آیا سرور را الان اجرا کنم؟ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 در حال اجرای سرور..."
    python3 back.py
fi
EOF

REM =================================================
REM      اسکریپت PowerShell برای ویندوز پیشرفته
REM =================================================

: <<'POWERSHELL'
# PowerShell Script
Write-Host "🤖 تزریق سریع سیستم چند-عامله" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Gray

# بررسی Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python یافت شد: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python یافت نشد! لطفاً Python 3.8+ نصب کنید" -ForegroundColor Red
    Read-Host "برای خروج Enter بزنید"
    exit 1
}

# نصب وابستگی‌ها
Write-Host ""
Write-Host "📦 نصب وابستگی‌ها..." -ForegroundColor Yellow

$packages = @("fastapi", "uvicorn[standard]", "websockets", "pydantic", "python-multipart")

foreach ($package in $packages) {
    try {
        python -m pip install $package --quiet
        Write-Host "✅ $package" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ $package (خطا یا نصب شده)" -ForegroundColor Yellow
    }
}

# ایجاد پوشه static
if (!(Test-Path "static")) {
    New-Item -ItemType Directory -Name "static" | Out-Null
}
Write-Host "✅ پوشه static ایجاد شد" -ForegroundColor Green

# کپی فایل HTML
if (Test-Path "front.html") {
    Copy-Item "front.html" "static/index.html"
    Write-Host "✅ فایل HTML کپی شد" -ForegroundColor Green
}

# بررسی فایل بک‌اند
if (!(Test-Path "back.py")) {
    Write-Host "❌ فایل back.py یافت نشد!" -ForegroundColor Red
    Read-Host "برای خروج Enter بزنید"
    exit 1
}
Write-Host "✅ فایل back.py یافت شد" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 تزریق موفق!" -ForegroundColor Green
Write-Host "🚀 برای اجرا: python back.py" -ForegroundColor Cyan
Write-Host "🌐 آدرس: http://127.0.0.1:8000" -ForegroundColor Cyan

# پیشنهاد اجرا
$choice = Read-Host "آیا سرور را الان اجرا کنم؟ (y/n)"
if ($choice -match "^[Yy]") {
    Write-Host ""
    Write-Host "🚀 در حال اجرای سرور..." -ForegroundColor Yellow
    python back.py
}

Read-Host "برای خروج Enter بزنید"
POWERSHELL
