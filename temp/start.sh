#!/bin/bash
# اسکریپت راه‌اندازی سریع

echo "🚀 Starting Multi-Agent Code Generation System..."

# بررسی Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# نصب وابستگی‌ها
echo "📦 Installing dependencies..."
python3 -m pip install -r requirements.txt

# راه‌اندازی سرور
echo "🌐 Starting server..."
python3 back.py

echo "✅ Server started at http://127.0.0.1:8000"
echo "📚 API Docs: http://127.0.0.1:8000/docs"
echo "🔌 WebSocket: ws://127.0.0.1:8000/ws"
