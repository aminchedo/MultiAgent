#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Agent Code Generation System - Launch Script
Script to launch backend server and open frontend

Author: AI Multi-Agent Team
Version: 1.0.0
License: MIT
"""

import os
import sys
import time
import json
import signal
import subprocess
import threading
import webbrowser
import requests
from pathlib import Path
from datetime import datetime

class AppLauncher:
    def __init__(self):
        self.backend_process = None
        self.backend_url = "http://localhost:8000"
        self.frontend_file = "front.html"
        self.test_file = "test_enhanced_ui.html"
        self.health_endpoint = f"{self.backend_url}/health"
        self.max_retries = 30
        self.retry_delay = 2
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print("\n🔄 دریافت سیگنال توقف...")
        self.shutdown()
        sys.exit(0)
    
    def print_banner(self):
        """Print application banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🤖 سیستم چند-عامله تولید کد                ║
║                    Multi-Agent Code Generator                ║
║                                                              ║
║  🚀 نسخه: 1.0.0                                              ║
║  📅 تاریخ: {date}                                           ║
║  🔧 حالت: راه‌اندازی خودکار                                   ║
╚══════════════════════════════════════════════════════════════╝
        """.format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print(banner)
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("🔍 بررسی وابستگی‌ها...")
        
        # Check if virtual environment exists
        venv_path = Path("venv")
        if not venv_path.exists():
            print("❌ محیط مجازی یافت نشد!")
            print("💡 لطفاً ابتدا محیط مجازی را ایجاد کنید:")
            print("   python3 -m venv venv")
            print("   source venv/bin/activate")
            print("   pip install -r 'requirements - Copy.txt'")
            return False
        
        # Check if backend file exists
        if not Path("back.py").exists():
            print("❌ فایل back.py یافت نشد!")
            return False
        
        # Check if frontend file exists
        if not Path(self.frontend_file).exists():
            print(f"❌ فایل {self.frontend_file} یافت نشد!")
            return False
        
        print("✅ تمام وابستگی‌ها موجود هستند")
        return True
    
    def start_backend(self):
        """Start the backend server"""
        print("🚀 راه‌اندازی سرور بک‌اند...")
        
        try:
            # Activate virtual environment and start backend
            if os.name == 'nt':  # Windows
                activate_cmd = "venv\\Scripts\\activate"
                python_cmd = "venv\\Scripts\\python"
            else:  # Unix/Linux/Mac
                activate_cmd = "source venv/bin/activate"
                python_cmd = "venv/bin/python"
            
            # Start backend process
            if os.name == 'nt':
                self.backend_process = subprocess.Popen(
                    [python_cmd, "back.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                self.backend_process = subprocess.Popen(
                    [python_cmd, "back.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            print("✅ سرور بک‌اند شروع شد")
            return True
            
        except Exception as e:
            print(f"❌ خطا در راه‌اندازی سرور بک‌اند: {e}")
            return False
    
    def wait_for_backend(self):
        """Wait for backend to be ready"""
        print("⏳ انتظار برای آماده شدن سرور...")
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(self.health_endpoint, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print("✅ سرور بک‌اند آماده است!")
                    print(f"   📊 وضعیت: {data.get('status', 'unknown')}")
                    print(f"   🗄️ دیتابیس: {data.get('database', 'unknown')}")
                    print(f"   🔑 احراز هویت: {'فعال' if data.get('authentication', {}).get('enabled', False) else 'غیرفعال'}")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            print(f"   ⏳ تلاش {attempt + 1}/{self.max_retries}...")
            time.sleep(self.retry_delay)
        
        print("❌ سرور بک‌اند در زمان مشخص شده آماده نشد!")
        return False
    
    def open_frontend(self, file_path=None):
        """Open frontend in browser"""
        if file_path is None:
            file_path = self.frontend_file
        
        if not Path(file_path).exists():
            print(f"❌ فایل {file_path} یافت نشد!")
            return False
        
        try:
            # Convert to absolute path
            abs_path = Path(file_path).resolve()
            file_url = f"file://{abs_path}"
            
            print(f"🌐 باز کردن {file_path} در مرورگر...")
            
            # Try to open in default browser
            webbrowser.open(file_url)
            
            print("✅ مرورگر باز شد")
            print(f"   📁 فایل: {file_path}")
            print(f"   🔗 آدرس: {file_url}")
            return True
            
        except Exception as e:
            print(f"❌ خطا در باز کردن مرورگر: {e}")
            return False
    
    def show_menu(self):
        """Show interactive menu"""
        while self.running:
            print("\n" + "="*60)
            print("🎛️ منوی کنترل")
            print("="*60)
            print("1. 🌐 باز کردن رابط اصلی")
            print("2. 🧪 باز کردن صفحه تست")
            print("3. 📊 بررسی وضعیت سرور")
            print("4. 🔄 راه‌اندازی مجدد سرور")
            print("5. 📁 باز کردن پوشه پروژه")
            print("6. 📚 مستندات API")
            print("0. 🚪 خروج")
            print("="*60)
            
            try:
                choice = input("انتخاب کنید (0-6): ").strip()
                
                if choice == "1":
                    self.open_frontend(self.frontend_file)
                elif choice == "2":
                    self.open_frontend(self.test_file)
                elif choice == "3":
                    self.check_server_status()
                elif choice == "4":
                    self.restart_backend()
                elif choice == "5":
                    self.open_project_folder()
                elif choice == "6":
                    self.open_api_docs()
                elif choice == "0":
                    print("👋 خروج از برنامه...")
                    break
                else:
                    print("❌ انتخاب نامعتبر!")
                    
            except KeyboardInterrupt:
                print("\n👋 خروج از برنامه...")
                break
            except Exception as e:
                print(f"❌ خطا: {e}")
    
    def check_server_status(self):
        """Check current server status"""
        print("📊 بررسی وضعیت سرور...")
        
        try:
            response = requests.get(self.health_endpoint, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ سرور فعال است")
                print(f"   🕒 زمان: {data.get('timestamp', 'unknown')}")
                print(f"   📊 وضعیت: {data.get('status', 'unknown')}")
                print(f"   🗄️ دیتابیس: {data.get('database', 'unknown')}")
                print(f"   🔄 job های فعال: {data.get('active_jobs', 0)}")
                print(f"   🔑 احراز هویت: {'فعال' if data.get('authentication', {}).get('enabled', False) else 'غیرفعال'}")
            else:
                print(f"❌ سرور پاسخ نامعتبر داد: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ سرور در دسترس نیست: {e}")
    
    def restart_backend(self):
        """Restart the backend server"""
        print("🔄 راه‌اندازی مجدد سرور...")
        
        # Stop current backend
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process.wait()
        
        # Start new backend
        if self.start_backend():
            if self.wait_for_backend():
                print("✅ سرور با موفقیت راه‌اندازی مجدد شد")
            else:
                print("❌ راه‌اندازی مجدد ناموفق بود")
        else:
            print("❌ خطا در راه‌اندازی مجدد")
    
    def open_project_folder(self):
        """Open project folder in file manager"""
        try:
            current_dir = Path.cwd()
            if os.name == 'nt':  # Windows
                os.startfile(current_dir)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', current_dir])
            else:  # Linux
                subprocess.run(['xdg-open', current_dir])
            print("📁 پوشه پروژه باز شد")
        except Exception as e:
            print(f"❌ خطا در باز کردن پوشه: {e}")
    
    def open_api_docs(self):
        """Open API documentation"""
        try:
            docs_url = f"{self.backend_url}/docs"
            webbrowser.open(docs_url)
            print("📚 مستندات API باز شد")
        except Exception as e:
            print(f"❌ خطا در باز کردن مستندات: {e}")
    
    def shutdown(self):
        """Graceful shutdown"""
        print("\n🔄 در حال توقف سرور...")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=10)
                print("✅ سرور متوقف شد")
            except subprocess.TimeoutExpired:
                print("⚠️ سرور به موقع متوقف نشد، در حال اجباری...")
                self.backend_process.kill()
            except Exception as e:
                print(f"❌ خطا در توقف سرور: {e}")
    
    def run(self):
        """Main run method"""
        self.print_banner()
        
        # Check dependencies
        if not self.check_dependencies():
            print("❌ بررسی وابستگی‌ها ناموفق بود!")
            return False
        
        # Start backend
        if not self.start_backend():
            print("❌ راه‌اندازی سرور ناموفق بود!")
            return False
        
        # Wait for backend to be ready
        if not self.wait_for_backend():
            print("❌ سرور در زمان مشخص شده آماده نشد!")
            self.shutdown()
            return False
        
        # Open frontend
        print("\n🎉 راه‌اندازی کامل شد!")
        print("="*60)
        print("📋 اطلاعات دسترسی:")
        print(f"   🌐 سرور: {self.backend_url}")
        print(f"   📚 مستندات: {self.backend_url}/docs")
        print(f"   🔍 وضعیت: {self.health_endpoint}")
        print("="*60)
        
        # Open main frontend
        self.open_frontend(self.frontend_file)
        
        # Show interactive menu
        self.show_menu()
        
        # Cleanup
        self.shutdown()
        return True

def main():
    """Main entry point"""
    launcher = AppLauncher()
    
    try:
        success = launcher.run()
        if success:
            print("✅ برنامه با موفقیت اجرا شد")
        else:
            print("❌ خطا در اجرای برنامه")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 برنامه توسط کاربر متوقف شد")
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()