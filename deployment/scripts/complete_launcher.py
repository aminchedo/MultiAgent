#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
راه‌انداز کامل سیستم چند-عامله تولید کد
Complete Launcher for Multi-Agent Code Generation System

نویسنده: سیستم هوش مصنوعی
تاریخ: 2024
"""

import os
import sys
import json
import time
import shutil
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

class CompleteLauncher:
    def __init__(self):
        self.project_dir = Path.cwd()
        self.config = self.load_config()
        self.logo = """
🤖═══════════════════════════════════════════════════════════🤖
║                                                           ║
║    سیستم چند-عامله هوشمند تولید کد                      ║
║    Multi-Agent AI Code Generation System                  ║
║                                                           ║
║    🚀 نسخه 1.0.0 | ساخته شده با ❤️                     ║
║                                                           ║
🤖═══════════════════════════════════════════════════════════🤖
        """
        
    def load_config(self):
        """بارگذاری تنظیمات"""
        config_file = self.project_dir / "config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.default_config()
    
    def default_config(self):
        """تنظیمات پیش‌فرض"""
        return {
            "server": {"host": "127.0.0.1", "port": 8000},
            "paths": {"static": "./static", "database": "./multiagent.db"}
        }
    
    def print_banner(self):
        """نمایش بنر"""
        print(self.logo)
        print(f"📅 تاریخ: {datetime.now().strftime('%Y/%m/%d - %H:%M:%S')}")
        print(f"📁 مسیر: {self.project_dir}")
        print("-" * 65)
    
    def check_system_requirements(self):
        """بررسی نیازمندی‌های سیستم"""
        print("🔍 بررسی نیازمندی‌های سیستم...")
        
        # بررسی Python
        try:
            python_version = sys.version_info
            if python_version.major < 3 or python_version.minor < 8:
                print(f"❌ Python {python_version.major}.{python_version.minor} - حداقل 3.8 مورد نیاز")
                return False
            print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        except:
            print("❌ خطا در تشخیص نسخه Python")
            return False
        
        # بررسی pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         capture_output=True, check=True)
            print("✅ pip موجود است")
        except:
            print("❌ pip یافت نشد")
            return False
        
        # بررسی فضای دیسک
        try:
            free_space = shutil.disk_usage('.').free / (1024**3)  # GB
            if free_space < 1:
                print(f"⚠️ فضای دیسک کم: {free_space:.1f}GB")
            else:
                print(f"✅ فضای دیسک: {free_space:.1f}GB")
        except:
            print("⚠️ نتوانستم فضای دیسک را بررسی کنم")
        
        return True
    
    def install_dependencies(self):
        """نصب وابستگی‌ها"""
        print("\n📦 نصب وابستگی‌ها...")
        
        packages = [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0", 
            "websockets>=12.0",
            "pydantic>=2.5.0",
            "python-multipart>=0.0.6",
            "jinja2>=3.1.0"
        ]
        
        success_count = 0
        for package in packages:
            try:
                print(f"⬇️ نصب {package}...", end=" ")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", package, "--quiet"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅")
                    success_count += 1
                else:
                    print(f"❌ {result.stderr.strip()}")
            except Exception as e:
                print(f"❌ {e}")
        
        print(f"\n📈 نتیجه: {success_count}/{len(packages)} بسته نصب شد")
        return success_count == len(packages)
    
    def setup_project_structure(self):
        """ایجاد ساختار پروژه"""
        print("\n🏗️ ایجاد ساختار پروژه...")
        
        directories = ["static", "templates", "uploads", "logs", "cache"]
        for directory in directories:
            path = self.project_dir / directory
            path.mkdir(exist_ok=True)
            print(f"📁 {directory}/")
        
        # کپی فایل HTML به static
        front_file = self.project_dir / "front_optimized.html"
        if front_file.exists():
            shutil.copy2(front_file, self.project_dir / "static" / "index.html")
            print("📄 front_optimized.html → static/index.html")
        else:
            # Fallback to original front.html if optimized version doesn't exist
            front_file = self.project_dir / "front.html"
            if front_file.exists():
                shutil.copy2(front_file, self.project_dir / "static" / "index.html")
                print("📄 front.html → static/index.html")
        
        # ایجاد فایل‌های کمکی
        self.create_helper_files()
        
        return True
    
    def create_helper_files(self):
        """ایجاد فایل‌های کمکی"""
        
        # فایل requirements.txt
        requirements = """fastapi>=0.104.0
uvicorn[standard]>=0.24.0
websockets>=12.0
pydantic>=2.5.0
python-multipart>=0.0.6
jinja2>=3.1.0
"""
        with open("requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements)
        print("📄 requirements.txt")
        
        # فایل .env
        env_content = f"""# تنظیمات محیط
HOST={self.config['server']['host']}
PORT={self.config['server']['port']}
DATABASE_URL={self.config['paths']['database']}
LOG_LEVEL=info
DEBUG=true
"""
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        print("📄 .env")
        
        # فایل .gitignore
        gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
*.db
*.log
uploads/
cache/
.env.local

# OS
.DS_Store
Thumbs.db
"""
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore)
        print("📄 .gitignore")
    
    def validate_backend(self):
        """اعتبارسنجی فایل بک‌اند"""
        print("\n🔍 اعتبارسنجی فایل back.py...")
        
        back_file = self.project_dir / "back.py"
        if not back_file.exists():
            print("❌ فایل back.py یافت نشد!")
            return False
        
        # بررسی syntax
        try:
    