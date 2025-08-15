# 🚀 Launch Scripts for Multi-Agent Code Generation System

This document explains how to use the automated launch scripts to start the backend server and open the frontend application.

## 📋 Overview

The launch scripts provide an automated way to:
- ✅ Check dependencies and virtual environment
- 🚀 Start the backend server automatically
- ⏳ Wait for the server to be ready
- 🌐 Open the frontend in your default browser
- 🎛️ Provide an interactive control menu
- 🔄 Restart the server when needed
- 🧹 Clean up processes on exit

## 📁 Available Scripts

| Platform | Script | Description |
|----------|--------|-------------|
| **Cross-Platform** | `launch_app.py` | Python script (recommended) |
| **Linux/macOS** | `launch.sh` | Bash shell script |
| **Windows** | `launch.bat` | Windows batch file |

## 🎯 Quick Start

### Option 1: Python Script (Recommended)
```bash
# Make sure you're in the project directory
cd /path/to/your/project

# Run the Python launch script
python3 launch_app.py
```

### Option 2: Shell Script (Linux/macOS)
```bash
# Make sure you're in the project directory
cd /path/to/your/project

# Run the shell script
./launch.sh
```

### Option 3: Batch File (Windows)
```cmd
REM Make sure you're in the project directory
cd C:\path\to\your\project

REM Run the batch file
launch.bat
```

## 🔧 Prerequisites

Before running the launch scripts, ensure you have:

1. **Python 3.7+** installed
2. **Virtual environment** created and activated
3. **Dependencies** installed
4. **Required files** present

### Setup Commands
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r "requirements - Copy.txt"
```

## 🎛️ Interactive Menu

Once the application is launched, you'll see an interactive menu with the following options:

```
============================================================
🎛️ منوی کنترل
============================================================
1. 🌐 باز کردن رابط اصلی
2. 🧪 باز کردن صفحه تست
3. 📊 بررسی وضعیت سرور
4. 🔄 راه‌اندازی مجدد سرور
5. 📁 باز کردن پوشه پروژه
6. 📚 مستندات API
0. 🚪 خروج
============================================================
```

### Menu Options Explained

| Option | Action | Description |
|--------|--------|-------------|
| **1** | Open Main Interface | Opens `front.html` in browser |
| **2** | Open Test Page | Opens `test_enhanced_ui.html` in browser |
| **3** | Check Server Status | Shows current server health and status |
| **4** | Restart Server | Stops and restarts the backend server |
| **5** | Open Project Folder | Opens the project directory in file manager |
| **6** | Open API Docs | Opens FastAPI documentation in browser |
| **0** | Exit | Gracefully shuts down the application |

## 🔍 What the Scripts Do

### 1. **Dependency Check**
- ✅ Verifies virtual environment exists
- ✅ Checks for required files (`back.py`, `front.html`)
- ✅ Validates Python installation

### 2. **Backend Launch**
- 🚀 Activates virtual environment
- 🚀 Starts the FastAPI server in background
- ⏳ Waits for server to be ready (up to 60 seconds)
- 📊 Displays server status information

### 3. **Frontend Launch**
- 🌐 Opens the main interface in default browser
- 🔗 Provides direct file URLs for manual access
- 📁 Shows file paths and URLs

### 4. **Interactive Control**
- 🎛️ Provides menu-driven control
- 🔄 Allows server restart without full relaunch
- 📊 Real-time status monitoring
- 🧹 Graceful cleanup on exit

## 🛠️ Troubleshooting

### Common Issues

#### 1. **Virtual Environment Not Found**
```
❌ محیط مجازی یافت نشد!
💡 لطفاً ابتدا محیط مجازی را ایجاد کنید:
   python3 -m venv venv
   source venv/bin/activate
   pip install -r "requirements - Copy.txt"
```

**Solution**: Follow the setup commands above.

#### 2. **Backend Server Won't Start**
```
❌ راه‌اندازی سرور ناموفق بود!
```

**Solutions**:
- Check if port 8000 is already in use
- Verify all dependencies are installed
- Check the `backend.log` file for errors

#### 3. **Server Not Responding**
```
❌ سرور بک‌اند در زمان مشخص شده آماده نشد!
```

**Solutions**:
- Wait longer (server might be slow to start)
- Check if firewall is blocking port 8000
- Verify the backend process is running

#### 4. **Browser Won't Open**
```
❌ خطا در باز کردن مرورگر
```

**Solutions**:
- Manually open the provided file URL
- Check if default browser is set correctly
- Try opening the file directly from file manager

### Manual Fallback

If the scripts don't work, you can manually:

1. **Start Backend**:
   ```bash
   source venv/bin/activate
   python back.py
   ```

2. **Open Frontend**:
   - Navigate to the project folder
   - Double-click `front.html` or `test_enhanced_ui.html`

## 🔧 Configuration

### Environment Variables

You can customize the behavior by setting environment variables:

```bash
# Backend URL (default: http://localhost:8000)
export BACKEND_URL=http://localhost:8000

# Frontend file (default: front.html)
export FRONTEND_FILE=front.html

# Test file (default: test_enhanced_ui.html)
export TEST_FILE=test_enhanced_ui.html

# Max retries (default: 30)
export MAX_RETRIES=30

# Retry delay in seconds (default: 2)
export RETRY_DELAY=2
```

### Script Customization

You can modify the scripts to:
- Change default ports
- Add custom startup commands
- Modify timeout values
- Add additional health checks

## 📊 Monitoring and Logs

### Log Files
- `backend.log` - Backend server output
- `app.log` - Application logs
- `backend.pid` - Process ID file (Linux/macOS)

### Health Endpoints
- `http://localhost:8000/health` - Server health check
- `http://localhost:8000/docs` - API documentation
- `http://localhost:8000/` - Root endpoint

## 🚀 Advanced Usage

### Running in Background
```bash
# Linux/macOS
nohup ./launch.sh > launch.log 2>&1 &

# Windows
start /B launch.bat
```

### Custom Port
```bash
# Set custom port
export PORT=8080
python3 launch_app.py
```

### Development Mode
```bash
# Enable debug mode
export DEBUG=true
python3 launch_app.py
```

## 🔒 Security Notes

- The scripts run the backend on `localhost` only
- No external network access by default
- Virtual environment isolation
- Process cleanup on exit

## 📞 Support

If you encounter issues:

1. **Check the logs**: Look at `backend.log` and `app.log`
2. **Verify dependencies**: Ensure all requirements are installed
3. **Check ports**: Make sure port 8000 is available
4. **Manual testing**: Try starting components manually

## 🎉 Success Indicators

When everything works correctly, you should see:

```
🎉 راه‌اندازی کامل شد!
============================================================
📋 اطلاعات دسترسی:
   🌐 سرور: http://localhost:8000
   📚 مستندات: http://localhost:8000/docs
   🔍 وضعیت: http://localhost:8000/health
============================================================
✅ مرورگر باز شد
   📁 فایل: front.html
   🔗 آدرس: file:///path/to/front.html
```

---

**Note**: The launch scripts are designed to provide a seamless experience for both development and production use. They handle common issues automatically and provide clear feedback when manual intervention is needed.