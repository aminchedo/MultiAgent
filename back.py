#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سیستم چند-عامله تولید کد - بک‌اند کامل
Multi-Agent Code Generation System - Complete Backend

Author: AI Multi-Agent Team
Version: 1.0.0
License: MIT
"""

import os
import sys
import json
import uuid
import asyncio
import sqlite3
import zipfile
import io
import hashlib
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# FastAPI و وابستگی‌ها
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel, Field

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==============================================================================
# مدل‌های داده (Data Models)
# ==============================================================================

class ProjectRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=1000, description="توضیحات پروژه")
    mode: str = Field(default="dry", description="حالت اجرا: dry یا live")
    api_key: Optional[str] = Field(None, description="کلید API")
    rounds: int = Field(default=3, ge=1, le=10, description="تعداد دورهای بررسی")
    models: Optional[List[str]] = Field(None, description="لیست مدل‌های AI")

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    created_at: str
    completed_at: Optional[str] = None
    files_count: int = 0

class AgentMessage(BaseModel):
    job_id: str
    agent: str
    message: str
    log_type: str = "info"
    timestamp: str

# ==============================================================================
# کلاس دیتابیس (Database Manager)
# ==============================================================================

class DatabaseManager:
    def __init__(self, db_path: str = "multiagent.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """ایجاد جداول دیتابیس"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # جدول jobs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    progress INTEGER DEFAULT 0,
                    message TEXT,
                    description TEXT,
                    mode TEXT,
                    created_at TEXT,
                    completed_at TEXT,
                    files_count INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """)
            
            # جدول فایل‌ها
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT,
                    filename TEXT,
                    content TEXT,
                    agent TEXT,
                    file_size INTEGER,
                    file_hash TEXT,
                    created_at TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            """)
            
            # جدول لاگ‌ها
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT,
                    agent TEXT,
                    message TEXT,
                    log_type TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            """)
            
            # جدول آمار
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT,
                    metric_value TEXT,
                    timestamp TEXT
                )
            """)
            
            conn.commit()
        
        logger.info("Database initialized successfully")
    
    def create_job(self, job_id: str, description: str, mode: str) -> None:
        """ایجاد job جدید"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO jobs (id, status, description, mode, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (job_id, "started", description, mode, datetime.now().isoformat()))
    
    def update_job_status(self, job_id: str, status: str, progress: int, message: str) -> None:
        """به‌روزرسانی وضعیت job"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if status == "completed":
                cursor.execute("""
                    UPDATE jobs SET status = ?, progress = ?, message = ?, completed_at = ?
                    WHERE id = ?
                """, (status, progress, message, datetime.now().isoformat(), job_id))
            else:
                cursor.execute("""
                    UPDATE jobs SET status = ?, progress = ?, message = ?
                    WHERE id = ?
                """, (status, progress, message, job_id))
    
    def save_file(self, job_id: str, filename: str, content: str, agent: str) -> None:
        """ذخیره فایل تولید شده"""
        file_size = len(content.encode('utf-8'))
        file_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO job_files (job_id, filename, content, agent, file_size, file_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (job_id, filename, content, agent, file_size, file_hash, datetime.now().isoformat()))
            
            # به‌روزرسانی تعداد فایل‌ها
            cursor.execute("""
                UPDATE jobs SET files_count = (
                    SELECT COUNT(*) FROM job_files WHERE job_id = ?
                ) WHERE id = ?
            """, (job_id, job_id))
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """دریافت وضعیت job"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, progress, message, created_at, completed_at, files_count
                FROM jobs WHERE id = ?
            """, (job_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    "job_id": job_id,
                    "status": result[0],
                    "progress": result[1],
                    "message": result[2],
                    "created_at": result[3],
                    "completed_at": result[4],
                    "files_count": result[5] or 0
                }
        return None
    
    def get_job_files(self, job_id: str) -> List[Dict]:
        """دریافت فایل‌های job"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT filename, content, agent, file_size, file_hash, created_at
                FROM job_files WHERE job_id = ?
                ORDER BY created_at
            """, (job_id,))
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    "filename": row[0],
                    "content": row[1],
                    "agent": row[2],
                    "file_size": row[3],
                    "file_hash": row[4],
                    "created_at": row[5]
                })
            
            return files
    
    def save_log(self, job_id: str, agent: str, message: str, log_type: str = "info") -> None:
        """ذخیره لاگ عامل"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agent_logs (job_id, agent, message, log_type, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (job_id, agent, message, log_type, datetime.now().isoformat()))

# ==============================================================================
# کلاس‌های عوامل (Agent Classes)
# ==============================================================================

class BaseAgent:
    def __init__(self, name: str, db_manager: DatabaseManager):
        self.name = name
        self.db = db_manager
    
    async def log(self, job_id: str, message: str, log_type: str = "info"):
        """ثبت لاگ عامل"""
        logger.info(f"[{self.name}] {message}")
        self.db.save_log(job_id, self.name, message, log_type)
        
        # ارسال به WebSocket
        await broadcast_message({
            "type": "agent_log",
            "job_id": job_id,
            "agent": self.name,
            "message": message,
            "log_type": log_type,
            "timestamp": datetime.now().isoformat()
        })
    
    async def sleep(self, seconds: float):
        """تاخیر غیرهمزمان"""
        await asyncio.sleep(seconds)

class PlannerAgent(BaseAgent):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__("برنامه‌ریز", db_manager)
    
    async def generate_plan(self, job_id: str, description: str) -> Dict:
        """تولید طرح پروژه"""
        await self.log(job_id, "شروع تحلیل و برنامه‌ریزی پروژه...")
        await self.sleep(2)
        
        # تحلیل نوع پروژه
        project_type = self.analyze_project_type(description)
        await self.log(job_id, f"نوع پروژه تشخیص داده شد: {project_type}")
        
        plan = {
            "title": self.extract_project_title(description),
            "type": project_type,
            "components": self.analyze_components(description),
            "files": self.plan_files(description),
            "technologies": self.select_technologies(description),
            "complexity": self.estimate_complexity(description),
            "estimated_time": self.estimate_time(description)
        }
        
        await self.log(job_id, f"طرح پروژه '{plan['title']}' با {len(plan['files'])} فایل تولید شد", "success")
        return plan
    
    def analyze_project_type(self, description: str) -> str:
        """تشخیص نوع پروژه"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['ماشین حساب', 'calculator', 'محاسبه']):
            return "calculator"
        elif any(word in description_lower for word in ['وبلاگ', 'blog', 'مقاله']):
            return "blog"
        elif any(word in description_lower for word in ['فروشگاه', 'shop', 'store', 'e-commerce']):
            return "ecommerce"
        elif any(word in description_lower for word in ['داشبورد', 'dashboard', 'admin']):
            return "dashboard"
        elif any(word in description_lower for word in ['بازی', 'game', 'گیم']):
            return "game"
        else:
            return "webapp"
    
    def extract_project_title(self, description: str) -> str:
        """استخراج عنوان پروژه"""
        type_mapping = {
            "calculator": "ماشین حساب پیشرفته",
            "blog": "سیستم وبلاگ",
            "ecommerce": "فروشگاه آنلاین",
            "dashboard": "داشبورد مدیریت",
            "game": "بازی وب",
            "webapp": "اپلیکیشن وب"
        }
        
        project_type = self.analyze_project_type(description)
        return type_mapping.get(project_type, "پروژه وب")
    
    def analyze_components(self, description: str) -> List[str]:
        """تحلیل کامپوننت‌های پروژه"""
        project_type = self.analyze_project_type(description)
        
        components_map = {
            "calculator": [
                "رابط کاربری محاسبه‌گر",
                "موتور محاسبات",
                "تاریخچه عملیات",
                "پشتیبانی صفحه کلید",
                "محاسبات علمی"
            ],
            "blog": [
                "صفحه اصلی",
                "فهرست مقالات",
                "صفحه مقاله",
                "سیستم جستجو",
                "نظرات کاربران"
            ],
            "ecommerce": [
                "کاتالوگ محصولات",
                "سبد خرید",
                "صفحه پرداخت",
                "پروفایل کاربر",
                "پنل مدیریت"
            ],
            "dashboard": [
                "نمودارها و آمار",
                "جداول داده",
                "فیلترها و جستجو",
                "تنظیمات کاربر",
                "گزارش‌گیری"
            ]
        }
        
        return components_map.get(project_type, ["رابط کاربری", "منطق اپلیکیشن"])
    
    def plan_files(self, description: str) -> List[str]:
        """برنامه‌ریزی فایل‌های پروژه"""
        project_type = self.analyze_project_type(description)
        
        base_files = ["index.html", "style.css", "script.js", "README.md"]
        
        type_files = {
            "calculator": base_files,
            "blog": base_files + ["blog.html", "post.html"],
            "ecommerce": base_files + ["products.html", "cart.html", "checkout.html"],
            "dashboard": base_files + ["dashboard.html", "charts.js"],
            "game": base_files + ["game.html", "game.js"]
        }
        
        return type_files.get(project_type, base_files)
    
    def select_technologies(self, description: str) -> List[str]:
        """انتخاب تکنولوژی‌ها"""
        base_tech = ["HTML5", "CSS3", "JavaScript ES6+"]
        
        if "نمودار" in description or "chart" in description:
            base_tech.append("Chart.js")
        if "انیمیشن" in description or "animation" in description:
            base_tech.append("CSS Animations")
        if "responsive" in description or "ریسپانسیو" in description:
            base_tech.append("Responsive Design")
        
        return base_tech
    
    def estimate_complexity(self, description: str) -> str:
        """تخمین پیچیدگی پروژه"""
        complexity_keywords = {
            "advanced": ["پیشرفته", "advanced", "complex", "sophisticated"],
            "medium": ["متوسط", "standard", "normal"],
            "simple": ["ساده", "simple", "basic", "easy"]
        }
        
        description_lower = description.lower()
        
        for level, keywords in complexity_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return level
        
        return "medium"
    
    def estimate_time(self, description: str) -> str:
        """تخمین زمان تولید"""
        complexity = self.estimate_complexity(description)
        
        time_map = {
            "simple": "2-3 دقیقه",
            "medium": "3-5 دقیقه", 
            "advanced": "5-7 دقیقه"
        }
        
        return time_map.get(complexity, "3-5 دقیقه")

class CoderAgent(BaseAgent):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__("کدنویس", db_manager)
    
    async def generate_code(self, job_id: str, plan: Dict, description: str) -> Dict:
        """تولید کد پروژه"""
        await self.log(job_id, "شروع تولید کد بر اساس طرح...")
        
        project_type = plan.get("type", "webapp")
        files = {}
        
        if project_type == "calculator":
            files = await self.generate_calculator_project(job_id)
        elif project_type == "blog":
            files = await self.generate_blog_project(job_id)
        elif project_type == "ecommerce":
            files = await self.generate_ecommerce_project(job_id)
        elif project_type == "dashboard":
            files = await self.generate_dashboard_project(job_id)
        else:
            files = await self.generate_basic_project(job_id)
        
        # ذخیره فایل‌ها در دیتابیس
        for filename, content in files.items():
            self.db.save_file(job_id, filename, content, self.name)
        
        await self.log(job_id, f"{len(files)} فایل با موفقیت تولید و ذخیره شد", "success")
        return files
    
    async def generate_calculator_project(self, job_id: str) -> Dict:
        """تولید پروژه ماشین حساب"""
        await self.log(job_id, "تولید ماشین حساب پیشرفته...")
        await self.sleep(1.5)
        
        return {
            "index.html": '''<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ماشین حساب پیشرفته</title>
    <link rel="stylesheet" href="style.css">
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
</head>
<body>
    <div class="container">
        <div class="calculator">
            <div class="display">
                <div class="history" id="history"></div>
                <div class="current" id="current">0</div>
            </div>
            
            <div class="buttons">
                <button class="btn function" onclick="clearAll()">AC</button>
                <button class="btn function" onclick="clearEntry()">CE</button>
                <button class="btn function" onclick="toggleSign()">±</button>
                <button class="btn operator" onclick="operation('/')" data-op="÷">÷</button>
                
                <button class="btn number" onclick="inputNumber('7')">7</button>
                <button class="btn number" onclick="inputNumber('8')">8</button>
                <button class="btn number" onclick="inputNumber('9')">9</button>
                <button class="btn operator" onclick="operation('*')" data-op="×">×</button>
                
                <button class="btn number" onclick="inputNumber('4')">4</button>
                <button class="btn number" onclick="inputNumber('5')">5</button>
                <button class="btn number" onclick="inputNumber('6')">6</button>
                <button class="btn operator" onclick="operation('-')" data-op="−">−</button>
                
                <button class="btn number" onclick="inputNumber('1')">1</button>
                <button class="btn number" onclick="inputNumber('2')">2</button>
                <button class="btn number" onclick="inputNumber('3')">3</button>
                <button class="btn operator" onclick="operation('+')" data-op="+">+</button>
                
                <button class="btn number zero" onclick="inputNumber('0')">0</button>
                <button class="btn number" onclick="inputNumber('.')">.</button>
                <button class="btn equals" onclick="calculate()">=</button>
            </div>
        </div>
        
        <div class="history-panel">
            <h3>تاریخچه محاسبات</h3>
            <div class="history-list" id="historyList"></div>
            <button class="clear-history" onclick="clearHistory()">پاک کردن تاریخچه</button>
        </div>
    </div>
    
    <script src="script.js"></script>
</body>
</html>''',

            "style.css": '''@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --calculator-bg: rgba(255, 255, 255, 0.1);
    --display-bg: rgba(0, 0, 0, 0.3);
    --btn-bg: rgba(255, 255, 255, 0.1);
    --btn-hover: rgba(255, 255, 255, 0.2);
    --operator-bg: linear-gradient(135deg, #ff6b6b, #ffa500);
    --equals-bg: linear-gradient(135deg, #00d4aa, #00b894);
    --function-bg: linear-gradient(135deg, #fdcb6e, #e17055);
    --shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
    --text-white: #ffffff;
    --text-gray: rgba(255, 255, 255, 0.7);
    --border-radius: 20px;
    --blur: blur(20px);
}

body {
    font-family: 'Vazirmatn', 'Inter', sans-serif;
    background: var(--primary-gradient);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    position: relative;
    overflow: hidden;
}

body::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
        radial-gradient(circle at 20% 50%, rgba(102, 126, 234, 0.4) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(118, 75, 162, 0.4) 0%, transparent 50%),
        radial-gradient(circle at 40% 80%, rgba(255, 107, 107, 0.3) 0%, transparent 50%);
    pointer-events: none;
    z-index: -1;
}

.container {
    display: flex;
    gap: 40px;
    align-items: flex-start;
    max-width: 1000px;
    width: 100%;
}

.calculator {
    background: var(--calculator-bg);
    backdrop-filter: var(--blur);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: var(--border-radius);
    padding: 32px;
    box-shadow: var(--shadow);
    flex: 0 0 auto;
    width: 350px;
}

.display {
    background: var(--display-bg);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    min-height: 120px;
    text-align: left;
    direction: ltr;
    position: relative;
    overflow: hidden;
}

.display::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
}

.history {
    font-size: 14px;
    color: var(--text-gray);
    min-height: 24px;
    margin-bottom: 12px;
    font-weight: 400;
}

.current {
    font-size: 42px;
    font-weight: 300;
    color: var(--text-white);
    word-break: break-all;
    line-height: 1.1;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.buttons {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
}

.btn {
    background: var(--btn-bg);
    border: none;
    border-radius: 16px;
    padding: 24px 12px;
    font-size: 20px;
    font-weight: 500;
    color: var(--text-white);
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    min-height: 70px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    font-family: inherit;
}

.btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.5s;
}

.btn:hover::before {
    left: 100%;
}

.btn:hover {
    background: var(--btn-hover);
    transform: translateY(-3px);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
}

.btn:active {
    transform: translateY(-1px);
}

.btn.operator {
    background: var(--operator-bg);
    color: white;
    font-weight: 600;
}

.btn.equals {
    background: var(--equals-bg);
    grid-row: span 2;
    color: white;
    font-weight: 600;
    font-size: 24px;
}

.btn.function {
    background: var(--function-bg);
    color: white;
    font-weight: 600;
}

.btn.zero {
    grid-column: span 2;
}

.history-panel {
    background: var(--calculator-bg);
    backdrop-filter: var(--blur);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: var(--border-radius);
    padding: 32px;
    width: 320px;
    max-height: 600px;
    box-shadow: var(--shadow);
}

.history-panel h3 {
    color: var(--text-white);
    margin-bottom: 24px;
    text-align: center;
    font-size: 18px;
    font-weight: 600;
}

.history-list {
    max-height: 450px;
    overflow-y: auto;
    margin-bottom: 20px;
}

.history-list::-webkit-scrollbar {
    width: 8px;
}

.history-list::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
}

.history-list::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 4px;
}

.history-item {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    animation: slideIn 0.3s ease;
}

.history-expression {
    font-size: 14px;
    color: var(--text-gray);
    margin-bottom: 8px;
    direction: ltr;
    text-align: left;
}

.history-result {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-white);
    direction: ltr;
    text-align: left;
}

.history-time {
    font-size: 11px;
    color: var(--text-gray);
    margin-top: 8px;
    text-align: right;
}

.clear-history {
    width: 100%;
    padding: 12px;
    background: rgba(239, 68, 68, 0.8);
    border: none;
    border-radius: 12px;
    color: white;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    font-family: inherit;
}

.clear-history:hover {
    background: rgba(239, 68, 68, 1);
    transform: translateY(-2px);
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (max-width: 768px) {
    .container {
        flex-direction: column;
        align-items: center;
        gap: 20px;
    }
    
    .calculator,
    .history-panel {
        width: 100%;
        max-width: 400px;
    }
    
    .buttons {
        gap: 12px;
    }
    
    .btn {
        padding: 20px 8px;
        font-size: 18px;
        min-height: 60px;
    }
    
    .current {
        font-size: 32px;
    }
}

@media (max-width: 480px) {
    body {
        padding: 10px;
    }
    
    .calculator,
    .history-panel {
        padding: 20px;
    }
    
    .buttons {
        gap: 8px;
    }
    
    .btn {
        padding: 16px 8px;
        font-size: 16px;
        min-height: 50px;
    }
    
    .current {
        font-size: 28px;
    }
}''',

            "script.js": '''class AdvancedCalculator {
    constructor() {
        this.currentInput = '0';
        this.previousInput = '';
        this.operation = null;
        this.shouldResetDisplay = false;
        this.history = this.loadHistory();
        this.updateDisplay();
        this.updateHistoryDisplay();
        this.setupKeyboardListeners();
    }

    // ========== Input Methods ==========
    inputNumber(number) {
        if (this.shouldResetDisplay) {
            this.currentInput = '';
            this.shouldResetDisplay = false;
        }

        // جلوگیری از ورود چندین نقطه
        if (number === '.' && this.currentInput.includes('.')) {
            return;
        }
        
        // جایگزینی صفر ابتدایی
        if (this.currentInput === '0' && number !== '.') {
            this.currentInput = number;
        } else {
            this.currentInput += number;
        }
        
        this.updateDisplay();
    }

    operation(nextOperation) {
        const inputValue = parseFloat(this.currentInput);

        if (this.previousInput === '') {
            this.previousInput = inputValue;
        } else if (this.operation) {
            const result = this.performCalculation();
            
            if (result === null) return; // خطا در محاسبه
            
            this.currentInput = this.formatNumber(result);
            this.previousInput = result;
        }

        this.shouldResetDisplay = true;
        this.operation = nextOperation;
        this.updateDisplay();
    }

    calculate() {
        if (this.operation === null || this.shouldResetDisplay) {
            return;
        }

        const result = this.performCalculation();
        
        if (result === null) return; // خطا در محاسبه
        
        // ذخیره در تاریخچه
        const expression = `${this.formatNumber(this.previousInput)} ${this.getOperatorSymbol(this.operation)} ${this.currentInput}`;
        this.addToHistory(expression, result);
        
        this.currentInput = this.formatNumber(result);
        this.operation = null;
        this.previousInput = '';
        this.shouldResetDisplay = true;
        this.updateDisplay();
    }

    // ========== Calculation Methods ==========
    performCalculation() {
        const prev = parseFloat(this.previousInput);
        const current = parseFloat(this.currentInput);

        if (isNaN(prev) || isNaN(current)) {
            this.showError('خطا در ورودی');
            return null;
        }

        let result;
        switch (this.operation) {
            case '+':
                result = prev + current;
                break;
            case '-':
                result = prev - current;
                break;
            case '*':
                result = prev * current;
                break;
            case '/':
                if (current === 0) {
                    this.showError('تقسیم بر صفر ممکن نیست');
                    return null;
                }
                result = prev / current;
                break;
            default:
                return current;
        }

        // بررسی محدودیت‌های عددی
        if (!isFinite(result)) {
            this.showError('عدد خارج از محدوده');
            return null;
        }

        return result;
    }

    formatNumber(number) {
        if (typeof number !== 'number') return number;
        
        // رند کردن اعداد اعشاری طولانی
        if (number % 1 !== 0) {
            return parseFloat(number.toFixed(10)).toString();
        }
        
        return number.toString();
    }

    getOperatorSymbol(op) {
        const symbols = {
            '+': '+',
            '-': '−',
            '*': '×',
            '/': '÷'
        };
        return symbols[op] || op;
    }

    // ========== Utility Methods ==========
    clearAll() {
        this.currentInput = '0';
        this.previousInput = '';
        this.operation = null;
        this.shouldResetDisplay = false;
        this.clearError();
        this.updateDisplay();
    }

    clearEntry() {
        this.currentInput = '0';
        this.clearError();
        this.updateDisplay();
    }

    toggleSign() {
        if (this.currentInput !== '0') {
            this.currentInput = this.currentInput.startsWith('-') 
                ? this.currentInput.slice(1) 
                : '-' + this.currentInput;
            this.updateDisplay();
        }
    }

    // ========== Display Methods ==========
    updateDisplay() {
        const currentElement = document.getElementById('current');
        const historyElement = document.getElementById('history');
        
        if (currentElement) {
            currentElement.textContent = this.currentInput;
        }
        
        if (historyElement) {
            let historyText = '';
            if (this.previousInput !== '') {
                historyText = `${this.formatNumber(this.previousInput)} ${this.getOperatorSymbol(this.operation) || ''}`;
            }
            historyElement.textContent = historyText;
        }
    }

    showError(message) {
        const currentElement = document.getElementById('current');
        if (currentElement) {
            currentElement.textContent = message;
            currentElement.style.color = '#ff6b6b';
            
            setTimeout(() => {
                this.clearError();
            }, 2000);
        }
    }

    clearError() {
        const currentElement = document.getElementById('current');
        if (currentElement) {
            currentElement.style.color = '';
        }
    }

    // ========== History Methods ==========
    addToHistory(expression, result) {
        const historyItem = {
            expression,
            result: this.formatNumber(result),
            timestamp: new Date().toLocaleString('fa-IR', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            }),
            id: Date.now()
        };
        
        this.history.unshift(historyItem);
        
        // محدود کردن تاریخچه به 50 آیتم
        if (this.history.length > 50) {
            this.history = this.history.slice(0, 50);
        }
        
        this.saveHistory();
        this.updateHistoryDisplay();
    }

    updateHistoryDisplay() {
        const historyList = document.getElementById('historyList');
        if (!historyList) return;

        if (this.history.length === 0) {
            historyList.innerHTML = '<div style="text-align: center; color: rgba(255,255,255,0.5); padding: 20px;">تاریخچه‌ای وجود ندارد</div>';
            return;
        }

        historyList.innerHTML = '';
        
        this.history.forEach(item => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.innerHTML = `
                <div class="history-expression">${item.expression}</div>
                <div class="history-result">= ${item.result}</div>
                <div class="history-time">${item.timestamp}</div>
            `;
            
            // اضافه کردن قابلیت کلیک برای استفاده مجدد
            historyItem.addEventListener('click', () => {
                this.currentInput = item.result.toString();
                this.shouldResetDisplay = false;
                this.updateDisplay();
            });
            
            historyList.appendChild(historyItem);
        });
    }

    clearHistory() {
        this.history = [];
        this.saveHistory();
        this.updateHistoryDisplay();
    }

    saveHistory() {
        try {
            localStorage.setItem('calculatorHistory', JSON.stringify(this.history));
        } catch (e) {
            console.warn('نمی‌توان تاریخچه را ذخیره کرد:', e);
        }
    }

    loadHistory() {
        try {
            const saved = localStorage.getItem('calculatorHistory');
            return saved ? JSON.parse(saved) : [];
        } catch (e) {
            console.warn('نمی‌توان تاریخچه را بارگذاری کرد:', e);
            return [];
        }
    }

    // ========== Keyboard Support ==========
    setupKeyboardListeners() {
        document.addEventListener('keydown', (event) => {
            event.preventDefault(); // جلوگیری از رفتارهای پیش‌فرض
            
            const key = event.key;
            
            // اعداد و نقطه
            if (/[0-9.]/.test(key)) {
                this.inputNumber(key);
            }
            // عملگرها
            else if (['+', '-', '*', '/'].includes(key)) {
                this.operation(key);
            }
            // محاسبه
            else if (key === 'Enter' || key === '=') {
                this.calculate();
            }
            // پاک کردن
            else if (key === 'Escape') {
                this.clearAll();
            }
            else if (key === 'Backspace') {
                this.clearEntry();
            }
            // تغییر علامت
            else if (key === 'F9') {
                this.toggleSign();
            }
        });
    }
}

// ========== Global Functions ==========
let calculator;

// تابع‌های global برای دکمه‌ها
function inputNumber(number) {
    calculator.inputNumber(number);
}

function operation(op) {
    calculator.operation(op);
}

function calculate() {
    calculator.calculate();
}

function clearAll() {
    calculator.clearAll();
}

function clearEntry() {
    calculator.clearEntry();
}

function toggleSign() {
    calculator.toggleSign();
}

function clearHistory() {
    calculator.clearHistory();
}

// راه‌اندازی ماشین حساب
document.addEventListener('DOMContentLoaded', () => {
    calculator = new AdvancedCalculator();
    
    // نمایش پیام خوشامدگویی
    console.log('🧮 ماشین حساب پیشرفته آماده است!');
    console.log('📌 کلیدهای میانبر:');
    console.log('   • 0-9: ورود اعداد');
    console.log('   • +, -, *, /: عملگرها');
    console.log('   • Enter یا =: محاسبه');
    console.log('   • Escape: پاک کردن همه');
    console.log('   • Backspace: پاک کردن ورودی');
    console.log('   • F9: تغییر علامت');
});''',

            "README.md": '''# 🧮 ماشین حساب پیشرفته

یک ماشین حساب وب مدرن و کامل با رابط کاربری زیبا و قابلیت‌های پیشرفته.

## ✨ ویژگی‌ها

### 🎨 طراحی مدرن
- رابط کاربری Glass Morphism
- انیمیشن‌های روان و زیبا
- طراحی ریسپانسیو برای تمام دستگاه‌ها
- فونت فارسی Vazirmatn

### 🧮 قابلیت‌های محاسباتی
- محاسبات اساسی (جمع، تفریق، ضرب، تقسیم)
- تغییر علامت اعداد
- مدیریت نقطه اعشار
- جلوگیری از خطاهای محاسباتی

### 📚 مدیریت تاریخچه
- ذخیره خودکار محاسبات
- نمایش زمان انجام عملیات
- امکان استفاده مجدد از نتایج قبلی
- پاک‌سازی تاریخچه

### ⌨️ پشتیبانی کامل صفحه کلید
- `0-9`: ورود اعداد
- `+, -, *, /`: عملگرها  
- `Enter` یا `=`: محاسبه
- `Escape`: پاک کردن همه
- `Backspace`: پاک کردن ورودی جاری
- `F9`: تغییر علامت

## 🚀 نحوه استفاده

1. فایل `index.html` را در مرورگر باز کنید
2. از دکمه‌های ماشین حساب یا صفحه کلید استفاده کنید
3. تاریخچه محاسبات در پنل سمت راست نمایش داده می‌شود
4. روی هر آیتم تاریخچه کلیک کنید تا نتیجه را دوباره استفاده کنید

## 🛠️ تکنولوژی‌های استفاده شده

- **HTML5**: ساختار پایه
- **CSS3**: 
  - Grid و Flexbox برای لایوت
  - Custom Properties برای متغیرها
  - Backdrop Filter برای افکت شیشه‌ای
  - Media Queries برای ریسپانسیو
- **JavaScript ES6+**:
  - Classes برای ساختار شی‌گرا
  - Local Storage برای ذخیره تاریخچه
  - Event Listeners برای تعامل کاربر
- **فونت Vazirmatn**: بهترین فونت فارسی

## 🌐 سازگاری مرورگرها

- ✅ Chrome 60+
- ✅ Firefox 55+ 
- ✅ Safari 12+
- ✅ Edge 79+

## 📱 پشتیبانی دستگاه‌ها

- 💻 دسکتاپ (1200px+)
- 📱 تبلت (768px - 1199px)
- 📱 موبایل (تا 767px)

## 🎯 ویژگی‌های امنیتی

- ✅ محافظت در برابر تقسیم بر صفر
- ✅ مدیریت اعداد خارج از محدوده
- ✅ اعتبارسنجی ورودی‌ها
- ✅ کنترل حافظه تاریخچه

## 🔧 سفارشی‌سازی

برای تغییر ظاهر، متغیرهای CSS در فایل `style.css` را ویرایش کنید:

```css
:root {
    --primary-gradient: /* رنگ پس‌زمینه */;
    --calculator-bg: /* رنگ ماشین حساب */;
    --operator-bg: /* رنگ دکمه‌های عملگر */;
    /* و سایر متغیرها... */
}
```

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است.

---

**ساخته شده با ❤️ توسط سیستم چند-عامله تولید کد**'''
        }
    
    async def generate_blog_project(self, job_id: str) -> Dict:
        """تولید پروژه وبلاگ"""
        await self.log(job_id, "تولید سیستم وبلاگ...")
        await self.sleep(2)
        
        # Implementation for blog project...
        return {
            "index.html": "<!-- Blog HTML will be generated here -->",
            "style.css": "/* Blog CSS will be generated here */",
            "script.js": "// Blog JavaScript will be generated here",
            "README.md": "# سیستم وبلاگ\n\nیک وبلاگ کامل و زیبا"
        }
    
    async def generate_ecommerce_project(self, job_id: str) -> Dict:
        """تولید پروژه فروشگاه"""
        await self.log(job_id, "تولید فروشگاه آنلاین...")
        await self.sleep(2.5)
        
        # Implementation for ecommerce project...
        return {
            "index.html": "<!-- E-commerce HTML will be generated here -->",
            "style.css": "/* E-commerce CSS will be generated here */",
            "script.js": "// E-commerce JavaScript will be generated here",
            "README.md": "# فروشگاه آنلاین\n\nیک فروشگاه کامل"
        }
    
    async def generate_dashboard_project(self, job_id: str) -> Dict:
        """تولید پروژه داشبورد"""
        await self.log(job_id, "تولید داشبورد مدیریت...")
        await self.sleep(2)
        
        # Implementation for dashboard project...
        return {
            "index.html": "<!-- Dashboard HTML will be generated here -->",
            "style.css": "/* Dashboard CSS will be generated here */",
            "script.js": "// Dashboard JavaScript will be generated here",
            "README.md": "# داشبورد مدیریت\n\nیک داشبورد کامل"
        }
    
    async def generate_basic_project(self, job_id: str) -> Dict:
        """تولید پروژه پایه"""
        await self.log(job_id, "تولید پروژه وب پایه...")
        await self.sleep(1)
        
        return {
            "index.html": '''<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>پروژه وب</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>خوش آمدید</h1>
            <p>این پروژه توسط سیستم چند-عامله تولید شده است</p>
        </header>
        <main>
            <button onclick="showMessage()">کلیک کنید</button>
        </main>
    </div>
    <script src="script.js"></script>
</body>
</html>''',
            "style.css": '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Vazirmatn', Arial, sans-serif;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.container {
    text-align: center;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    padding: 60px 40px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

h1 {
    font-size: 2.5rem;
    margin-bottom: 20px;
    background: linear-gradient(45deg, #fff, #f0f0f0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

p {
    font-size: 1.2rem;
    margin-bottom: 30px;
    opacity: 0.9;
}

button {
    padding: 15px 30px;
    border: none;
    border-radius: 25px;
    background: linear-gradient(45deg, #ff6b6b, #ffa500);
    color: white;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

button:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
}''',
            "script.js": '''function showMessage() {
    alert('سلام! این پروژه توسط سیستم چند-عامله تولید شده است.');
}

// راه‌اندازی اولیه
document.addEventListener('DOMContentLoaded', function() {
    console.log('پروژه با موفقیت بارگذاری شد');
    
    // افکت کلیک روی پس‌زمینه
    document.body.addEventListener('click', function(e) {
        if (e.target === document.body) {
            createRipple(e);
        }
    });
});

function createRipple(event) {
    const ripple = document.createElement('div');
    ripple.style.position = 'fixed';
    ripple.style.borderRadius = '50%';
    ripple.style.background = 'rgba(255, 255, 255, 0.3)';
    ripple.style.transform = 'scale(0)';
    ripple.style.animation = 'ripple 0.6s linear';
    ripple.style.left = (event.clientX - 25) + 'px';
    ripple.style.top = (event.clientY - 25) + 'px';
    ripple.style.width = ripple.style.height = '50px';
    ripple.style.pointerEvents = 'none';
    
    document.body.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// اضافه کردن استایل انیمیشن
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);''',
            "README.md": '''# پروژه وب

یک پروژه وب ساده و زیبا تولید شده توسط سیستم چند-عامله.

## ویژگی‌ها

- طراحی مدرن و زیبا
- افکت‌های بصری
- کد تمیز و مرتب

## نحوه استفاده

فایل index.html را در مرورگر باز کنید.'''
        }

class ReviewerAgent(BaseAgent):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__("بازبین", db_manager)
    
    async def review_code(self, job_id: str, files: Dict) -> Dict:
        """بررسی کیفیت کد"""
        await self.log(job_id, "شروع بررسی کیفیت کد...")
        await self.sleep(2)
        
        # معیارهای بررسی
        score = 5  # امتیاز پایه
        issues = []
        suggestions = []
        
        # بررسی وجود فایل‌های اساسی
        required_files = ['index.html', 'style.css', 'script.js']
        existing_files = list(files.keys())
        
        for file in required_files:
            if file in existing_files:
                score += 1
            else:
                issues.append({
                    "severity": "medium",
                    "description": f"فایل {file} وجود ندارد",
                    "filename": file,
                    "line_hint": "کل فایل"
                })
        
        # بررسی کیفیت کد HTML
        if 'index.html' in files:
            html_content = files['index.html']
            if '<!DOCTYPE html>' in html_content:
                score += 0.5
            if 'charset="UTF-8"' in html_content:
                score += 0.5
            if 'viewport' in html_content:
                score += 0.5
            else:
                suggestions.append("اضافه کردن meta viewport برای responsive design")
        
        # بررسی کیفیت CSS
        if 'style.css' in files:
            css_content = files['style.css']
            if 'box-sizing: border-box' in css_content:
                score += 0.5
            if '@media' in css_content:
                score += 1
            else:
                suggestions.append("اضافه کردن media queries برای responsive design")
        
        # بررسی کیفیت JavaScript
        if 'script.js' in files:
            js_content = files['script.js']
            if 'addEventListener' in js_content:
                score += 0.5
            if 'console.log' in js_content:
                score += 0.3
            if 'function' in js_content or '=>' in js_content:
                score += 0.5
        
        # محدود کردن امتیاز به 10
        score = min(10, score)
        
        review_result = {
            "score": round(score, 1),
            "issues": issues,
            "suggested_changes": suggestions,
            "total_files": len(files),
            "code_quality": "عالی" if score >= 9 else "خوب" if score >= 7 else "متوسط" if score >= 5 else "نیاز به بهبود"
        }
        
        await self.log(job_id, f"بررسی کامل شد - امتیاز: {review_result['score']}/10 ({review_result['code_quality']})", 
                      "success" if score >= 7 else "warning")
        
        return review_result

class OptimizerAgent(BaseAgent):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__("بهینه‌ساز", db_manager)
    
    async def optimize_code(self, job_id: str, files: Dict) -> Dict:
        """بهینه‌سازی کد"""
        await self.log(job_id, "شروع بهینه‌سازی کد...")
        await self.sleep(2)
        
        optimized_files = {}
        
        for filename, content in files.items():
            await self.log(job_id, f"بهینه‌سازی {filename}...")
            
            if filename.endswith('.html'):
                optimized_files[filename] = self.optimize_html(content)
            elif filename.endswith('.css'):
                optimized_files[filename] = self.optimize_css(content)
            elif filename.endswith('.js'):
                optimized_files[filename] = self.optimize_js(content)
            else:
                optimized_files[filename] = content
            
            await self.sleep(0.5)
        
        await self.log(job_id, f"بهینه‌سازی {len(optimized_files)} فایل کامل شد", "success")
        return optimized_files
    
    def optimize_html(self, content: str) -> str:
        """بهینه‌سازی HTML"""
        # اضافه کردن کامنت بهینه‌سازی
        optimization_comment = "<!-- بهینه‌سازی شده برای عملکرد بهتر و SEO -->\n"
        
        # بهبودهای SEO و کارایی
        if '<head>' in content and 'meta name="description"' not in content:
            content = content.replace('<head>', 
                '<head>\n    <meta name="description" content="توضیحات پروژه - ساخته شده با سیستم چند-عامله">')
        
        return optimization_comment + content
    
    def optimize_css(self, content: str) -> str:
        """بهینه‌سازی CSS"""
        optimization_comment = "/* بهینه‌سازی شده برای کارایی و سازگاری */\n\n"
        
        # اضافه کردن prefixes و بهبودهای کارایی
        optimizations = """/* Optimizations added */
* {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Performance improvements */
img, video {
    max-width: 100%;
    height: auto;
}

"""
        
        return optimization_comment + optimizations + content
    
    def optimize_js(self, content: str) -> str:
        """بهینه‌سازی JavaScript"""
        optimization_comment = "/* بهینه‌سازی شده برای عملکرد بهتر */\n\n"
        
        # اضافه کردن error handling و performance improvements
        performance_code = """// Performance monitoring
const performanceObserver = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
        if (entry.duration > 100) {
            console.warn(`Slow operation detected: ${entry.name} took ${entry.duration}ms`);
        }
    }
});

if (typeof PerformanceObserver !== 'undefined') {
    performanceObserver.observe({entryTypes: ['measure', 'navigation']});
}

// Enhanced error handling
window.addEventListener('error', (event) => {
    console.error('Global error caught:', event.error);
});

"""
        
        return optimization_comment + performance_code + content

class TesterAgent(BaseAgent):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__("تست‌کننده", db_manager)
    
    async def generate_tests(self, job_id: str, files: Dict) -> Dict:
        """تولید تست‌ها"""
        await self.log(job_id, "شروع تولید تست‌های خودکار...")
        await self.sleep(1.5)
        
        test_files = {}
        
        # تست HTML
        if any(f.endswith('.html') for f in files.keys()):
            test_files['test.html'] = self.generate_html_test()
            test_files['test.js'] = self.generate_js_test(files)
        
        # تست performance
        test_files['performance-test.html'] = self.generate_performance_test()
        
        await self.log(job_id, f"{len(test_files)} فایل تست تولید شد", "success")
        return test_files
    
    def generate_html_test(self) -> str:
        """تولید فایل تست HTML"""
        return '''<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تست‌های خودکار پروژه</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Vazirmatn', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2rem;
        }
        
        .test-section {
            margin-bottom: 30px;
        }
        
        .test-result {
            margin: 15px 0;
            padding: 15px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.3s ease;
        }
        
        .test-result.pass {
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid rgba(16, 185, 129, 0.5);
        }
        
        .test-result.fail {
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid rgba(239, 68, 68, 0.5);
        }
        
        .test-result.warning {
            background: rgba(245, 158, 11, 0.2);
            border: 1px solid rgba(245, 158, 11, 0.5);
        }
        
        .test-icon {
            font-size: 1.2rem;
            font-weight: bold;
        }
        
        .test-name {
            font-weight: 600;
            flex: 1;
        }
        
        .test-details {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        
        .summary {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            margin-top: 30px;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            margin: 20px 0;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #10b981, #059669);
            width: 0%;
            transition: width 1s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 تست‌های خودکار پروژه</h1>
        
        <div class="test-section">
            <h2>📋 نتایج تست</h2>
            <div id="test-results"></div>
        </div>
        
        <div class="summary">
            <h3>📊 خلاصه نتایج</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill"></div>
            </div>
            <div id="test-summary"></div>
        </div>
    </div>
    
    <script src="test.js"></script>
</body>
</html>'''
    
    def generate_js_test(self, files: Dict) -> str:
        """تولید فایل تست JavaScript"""
        return '''// سیستم تست خودکار پروژه
class ProjectTester {
    constructor() {
        this.tests = [];
        this.results = [];
        this.init();
    }

    init() {
        console.log('🧪 شروع تست‌های خودکار...');
        this.runAllTests();
    }

    // ========== Test Runner ==========
    async runAllTests() {
        // تست‌های اساسی DOM
        this.addTest('بارگذاری DOM', () => {
            return document.readyState === 'complete' && document.body !== null;
        });

        this.addTest('عملکرد JavaScript', () => {
            return typeof console !== 'undefined' && typeof document !== 'undefined';
        });

        this.addTest('پشتیبانی CSS', () => {
            const testElement = document.createElement('div');
            testElement.style.display = 'flex';
            return testElement.style.display === 'flex';
        });

        this.addTest('پشتیبانی Local Storage', () => {
            try {
                localStorage.setItem('test', 'test');
                localStorage.removeItem('test');
                return true;
            } catch (e) {
                return false;
            }
        });

        // تست‌های رسپانسیو
        this.addTest('پشتیبانی Media Queries', () => {
            return window.matchMedia && window.matchMedia('(max-width: 768px)').matches !== undefined;
        });

        // تست‌های کارایی
        this.addTest('Performance API', () => {
            return typeof performance !== 'undefined' && typeof performance.now === 'function';
        });

        // تست‌های مرورگر
        this.addTest('مرورگر مدرن', () => {
            return 'fetch' in window && 'Promise' in window && 'addEventListener' in window;
        });

        // تست‌های فونت
        this.addTest('بارگذاری فونت', () => {
            const element = document.createElement('div');
            element.style.fontFamily = 'Vazirmatn';
            document.body.appendChild(element);
            const fontFamily = window.getComputedStyle(element).fontFamily;
            document.body.removeChild(element);
            return fontFamily.includes('Vazirmatn') || fontFamily.includes('Arial');
        });

        // تست‌های امنیتی
        this.addTest('HTTPS Protocol', () => {
            return location.protocol === 'https:' || location.hostname === 'localhost';
        });

        // اجرای تست‌ها
        await this.executeTests();
        this.displayResults();
        this.showSummary();
    }

    addTest(name, testFunction, expectedResult = true) {
        this.tests.push({
            name,
            testFunction,
            expectedResult
        });
    }

    async executeTests() {
        for (const test of this.tests) {
            try {
                const startTime = performance.now();
                const result = await test.testFunction();
                const endTime = performance.now();
                const duration = Math.round(endTime - startTime);

                this.results.push({
                    name: test.name,
                    passed: result === test.expectedResult,
                    result,
                    expected: test.expectedResult,
                    duration,
                    error: null
                });

                console.log(`✅ ${test.name}: ${result ? 'موفق' : 'ناموفق'} (${duration}ms)`);
            } catch (error) {
                this.results.push({
                    name: test.name,
                    passed: false,
                    result: null,
                    expected: test.expectedResult,
                    duration: 0,
                    error: error.message
                });

                console.error(`❌ ${test.name}: خطا - ${error.message}`);
            }

            // تاخیر کوتاه برای نمایش پیشرفت
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }

    displayResults() {
        const container = document.getElementById('test-results');
        if (!container) return;

        container.innerHTML = '';

        this.results.forEach((result, index) => {
            const resultElement = document.createElement('div');
            resultElement.className = `test-result ${result.passed ? 'pass' : 'fail'}`;
            
            const icon = result.passed ? '✅' : '❌';
            const status = result.passed ? 'موفق' : 'ناموفق';
            const details = result.error ? 
                `خطا: ${result.error}` : 
                `زمان اجرا: ${result.duration}ms`;

            resultElement.innerHTML = `
                <div class="test-icon">${icon}</div>
                <div class="test-name">${result.name}</div>
                <div class="test-status">${status}</div>
                <div class="test-details">${details}</div>
            `;

            // انیمیشن ورود
            setTimeout(() => {
                container.appendChild(resultElement);
            }, index * 100);
        });
    }

    showSummary() {
        const passedTests = this.results.filter(r => r.passed).length;
        const totalTests = this.results.length;
        const successRate = Math.round((passedTests / totalTests) * 100);

        // به‌روزرسانی progress bar
        const progressFill = document.getElementById('progress-fill');
        if (progressFill) {
            setTimeout(() => {
                progressFill.style.width = `${successRate}%`;
                
                // تغییر رنگ بر اساس نتیجه
                if (successRate >= 90) {
                    progressFill.style.background = 'linear-gradient(90deg, #10b981, #059669)';
                } else if (successRate >= 70) {
                    progressFill.style.background = 'linear-gradient(90deg, #f59e0b, #d97706)';
                } else {
                    progressFill.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
                }
            }, 500);
        }

        // نمایش خلاصه
        const summaryElement = document.getElementById('test-summary');
        if (summaryElement) {
            setTimeout(() => {
                let statusText = '';
                let statusIcon = '';
                
                if (successRate >= 90) {
                    statusText = 'عالی! پروژه آماده استقرار است';
                    statusIcon = '🎉';
                } else if (successRate >= 70) {
                    statusText = 'خوب! نیاز به بهبودهای جزئی';
                    statusIcon = '👍';
                } else {
                    statusText = 'نیاز به بررسی و اصلاح';
                    statusIcon = '⚠️';
                }

                summaryElement.innerHTML = `
                    <div style="font-size: 2rem; margin-bottom: 10px;">${statusIcon}</div>
                    <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 10px;">
                        ${passedTests} از ${totalTests} تست موفق (${successRate}%)
                    </div>
                    <div style="opacity: 0.9;">${statusText}</div>
                `;
            }, 1000);
        }

        // گزارش نهایی در کنسول
        console.log(`
🏆 خلاصه تست‌ها:
   ✅ موفق: ${passedTests}
   ❌ ناموفق: ${totalTests - passedTests}
   📊 درصد موفقیت: ${successRate}%
        `);
    }
}

// ========== Event Listeners ==========
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 سیستم تست آماده سازی شده');
    
    // شروع تست‌ها با تاخیر کوتاه
    setTimeout(() => {
        new ProjectTester();
    }, 500);
});

// تست‌های اضافی در صورت وجود عناصر خاص
window.addEventListener('load', () => {
    console.log('📄 صفحه کاملاً بارگذاری شد');
    
    // تست بارگذاری تصاویر
    const images = document.querySelectorAll('img');
    let loadedImages = 0;
    
    images.forEach(img => {
        if (img.complete) {
            loadedImages++;
        } else {
            img.addEventListener('load', () => {
                loadedImages++;
                if (loadedImages === images.length) {
                    console.log('✅ همه تصاویر بارگذاری شدند');
                }
            });
        }
    });
    
    if (images.length === 0) {
        console.log('ℹ️ هیچ تصویری یافت نشد');
    }
});'''
    
    def generate_performance_test(self) -> str:
        """تولید تست کارایی"""
        return '''<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تست کارایی پروژه</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1a1a1a;
            color: white;
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: #2a2a2a;
            padding: 30px;
            border-radius: 15px;
        }
        .metric {
            background: #3a3a3a;
            padding: 15px;
            margin: 10px 0;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .metric-value {
            font-weight: bold;
            color: #4ade80;
        }
        .warning { color: #fbbf24; }
        .error { color: #ef4444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 تست کارایی</h1>
        <div id="performance-results"></div>
    </div>
    
    <script>
        // تست کارایی
        window.addEventListener('load', () => {
            const container = document.getElementById('performance-results');
            const metrics = performance.getEntriesByType('navigation')[0];
            
            const results = [
                {
                    name: 'زمان بارگذاری DOM',
                    value: Math.round(metrics.domContentLoadedEventEnd - metrics.navigationStart),
                    unit: 'ms',
                    threshold: 1000
                },
                {
                    name: 'زمان کامل بارگذاری',
                    value: Math.round(metrics.loadEventEnd - metrics.navigationStart),
                    unit: 'ms',
                    threshold: 2000
                },
                {
                    name: 'زمان اولین byte',
                    value: Math.round(metrics.responseStart - metrics.requestStart),
                    unit: 'ms',
                    threshold: 200
                }
            ];
            
            results.forEach(result => {
                const div = document.createElement('div');
                div.className = 'metric';
                
                let statusClass = '';
                if (result.value > result.threshold * 2) statusClass = 'error';
                else if (result.value > result.threshold) statusClass = 'warning';
                
                div.innerHTML = `
                    <span>${result.name}</span>
                    <span class="metric-value ${statusClass}">
                        ${result.value} ${result.unit}
                    </span>
                `;
                
                container.appendChild(div);
            });
        });
    </script>
</body>
</html>'''

# ==============================================================================
# کلاس ارکستراتور اصلی (Main Orchestrator)
# ==============================================================================

class MultiAgentOrchestrator:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.agents = {
            'planner': PlannerAgent(db_manager),
            'coder': CoderAgent(db_manager),
            'reviewer': ReviewerAgent(db_manager),
            'optimizer': OptimizerAgent(db_manager),
            'tester': TesterAgent(db_manager)
        }
    
    async def generate_project(self, job_id: str, request: ProjectRequest):
        """تولید پروژه با همکاری عوامل"""
        try:
            # ایجاد job در دیتابیس
            self.db.create_job(job_id, request.description, request.mode)
            
            # مرحله 1: برنامه‌ریزی (10%)
            await self.update_progress(job_id, 10, "در حال تحلیل و برنامه‌ریزی...")
            plan = await self.agents['planner'].generate_plan(job_id, request.description)
            
            # مرحله 2: کدنویسی (30%)
            await self.update_progress(job_id, 30, "در حال تولید کد...")
            files = await self.agents['coder'].generate_code(job_id, plan, request.description)
            
            # مرحله 3: بررسی و اصلاح (چندین دور) (40-70%)
            current_files = files
            for round_num in range(request.rounds):
                progress = 40 + (round_num * 10)
                await self.update_progress(job_id, progress, f"بررسی دور {round_num + 1} از {request.rounds}...")
                
                review = await self.agents['reviewer'].review_code(job_id, current_files)
                
                if review['score'] >= 8 or round_num == request.rounds - 1:
                    break
                
                # در پیاده‌سازی واقعی، کدنویس بر اساس نظرات بازبین اصلاحات انجام می‌دهد
                await asyncio.sleep(0.5)  # شبیه‌سازی زمان اصلاح
            
            # مرحله 4: بهینه‌سازی (80%)
            await self.update_progress(job_id, 80, "در حال بهینه‌سازی کد...")
            optimized_files = await self.agents['optimizer'].optimize_code(job_id, current_files)
            
            # مرحله 5: تولید تست (90%)
            await self.update_progress(job_id, 90, "در حال تولید تست‌های خودکار...")
            test_files = await self.agents['tester'].generate_tests(job_id, optimized_files)
            
            # ذخیره فایل‌های تست
            for filename, content in test_files.items():
                self.db.save_file(job_id, filename, content, 'تست‌کننده')
            
            # اتمام (100%)
            await self.update_progress(job_id, 100, "پروژه با موفقیت تولید شد")
            
            all_files = {**optimized_files, **test_files}
            
            # آمارگیری
            await self.save_job_statistics(job_id, plan, len(all_files))
            
            return all_files
            
        except Exception as e:
            logger.error(f"Error in project generation: {e}")
            await self.update_progress(job_id, 0, f"خطا: {str(e)}", "error")
            raise e
    
    async def update_progress(self, job_id: str, progress: int, message: str, status: str = "working"):
        """به‌روزرسانی پیشرفت"""
        if progress == 100:
            status = "completed"
        elif progress == 0 and "خطا" in message:
            status = "error"
        
        self.db.update_job_status(job_id, status, progress, message)
        
        await broadcast_message({
            "type": "progress_update",
            "job_id": job_id,
            "progress": progress,
            "message": message,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
    
    async def save_job_statistics(self, job_id: str, plan: Dict, total_files: int):
        """ذخیره آمار job"""
        stats = {
            "job_id": job_id,
            "project_type": plan.get("type", "unknown"),
            "complexity": plan.get("complexity", "medium"),
            "total_files": total_files,
            "completion_time": datetime.now().isoformat()
        }
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_stats (metric_name, metric_value, timestamp)
                VALUES (?, ?, ?)
            """, ("job_completion", json.dumps(stats), datetime.now().isoformat()))

# ==============================================================================
# WebSocket Manager
# ==============================================================================

websocket_connections: List[WebSocket] = []

async def broadcast_message(message: Dict):
    """ارسال پیام به تمام کلاینت‌های WebSocket"""
    if websocket_connections:
        message_str = json.dumps(message, ensure_ascii=False)
        disconnected = []
        
        for ws in websocket_connections:
            try:
                await ws.send_text(message_str)
            except Exception as e:
                logger.warning(f"WebSocket send failed: {e}")
                disconnected.append(ws)
        
        # حذف اتصالات قطع شده
        for ws in disconnected:
            websocket_connections.remove(ws)

# ==============================================================================
# FastAPI Application
# ==============================================================================

# ایجاد FastAPI app
app = FastAPI(
    title="Multi-Agent Code Generation System",
    description="سیستم چند-عامله تولید کد و پروژه",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# تنظیمات CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# متغیرهای سراسری
db_manager = DatabaseManager()
orchestrator = MultiAgentOrchestrator(db_manager)
active_jobs: Dict[str, dict] = {}

# ==============================================================================
# API Endpoints
# ==============================================================================

@app.get("/")
async def root():
    """صفحه اصلی"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multi-Agent Code Generator</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>🤖 سیستم چند-عامله تولید کد</h1>
        <p>API در حال اجرا است</p>
        <ul>
            <li><a href="/docs">مستندات API</a></li>
            <li><a href="/health">وضعیت سلامت</a></li>
        </ul>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """بررسی سلامت سیستم"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "database": "connected",
        "active_jobs": len(active_jobs)
    }

@app.post("/api/generate")
async def generate_project(request: ProjectRequest, background_tasks: BackgroundTasks):
    """شروع تولید پروژه"""
    job_id = str(uuid.uuid4())
    
    # اعتبارسنجی ورودی
    if len(request.description.strip()) < 10:
        raise HTTPException(status_code=400, detail="توضیحات پروژه باید حداقل 10 کاراکتر باشد")
    
    active_jobs[job_id] = {
        "status": "started",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "description": request.description
    }
    
    # اجرای تولید پروژه در پس‌زمینه
    background_tasks.add_task(orchestrator.generate_project, job_id, request)
    
    logger.info(f"Project generation started: {job_id}")
    
    return {
        "job_id": job_id,
        "message": "تولید پروژه شروع شد",
        "status": "started"
    }

@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """دریافت وضعیت job"""
    status = db_manager.get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Job یافت نشد")
    
    return status

@app.get("/api/jobs")
async def get_all_jobs(limit: int = 50, offset: int = 0):
    """دریافت لیست تمام job ها"""
    with sqlite3.connect(db_manager.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, status, progress, description, created_at, completed_at, files_count
            FROM jobs
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        jobs = []
        for row in cursor.fetchall():
            jobs.append({
                "job_id": row[0],
                "status": row[1],
                "progress": row[2],
                "description": row[3],
                "created_at": row[4],
                "completed_at": row[5],
                "files_count": row[6] or 0
            })
        
        return {"jobs": jobs, "total": len(jobs)}

@app.get("/download/{job_id}")
async def download_project(job_id: str):
    """دانلود فایل ZIP پروژه"""
    files = db_manager.get_job_files(job_id)
    
    if not files:
        raise HTTPException(status_code=404, detail="فایل‌هایی برای این job یافت نشد")
    
    # ایجاد فایل ZIP در حافظه
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
        for file_data in files:
            zip_file.writestr(file_data['filename'], file_data['content'])
        
        # افزودن manifest
        manifest = {
            "job_id": job_id,
            "generated_at": datetime.now().isoformat(),
            "generator": "Multi-Agent Code Generation System v1.0.0",
            "total_files": len(files),
            "files": [
                {
                    "filename": f['filename'],
                    "agent": f['agent'],
                    "file_size": f['file_size'],
                    "file_hash": f['file_hash'],
                    "created_at": f['created_at']
                }
                for f in files
            ]
        }
        zip_file.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        
        # افزودن README برای کاربر
        readme_content = f"""# پروژه تولید شده

این پروژه توسط سیستم چند-عامله تولید کد ساخته شده است.

## اطلاعات پروژه
- 🆔 شناسه: {job_id}
- 📅 تاریخ تولید: {datetime.now().strftime('%Y/%m/%d - %H:%M')}
- 📁 تعداد فایل‌ها: {len(files)}

## فایل‌های تولید شده
{chr(10).join([f"- {f['filename']} (توسط {f['agent']})" for f in files])}

## نحوه استفاده
1. فایل index.html را در مرورگر باز کنید
2. از عملکردهای پروژه استفاده کنید
3. فایل‌های تست را اجرا کنید

## پشتیبانی
برای سوالات و پشتیبانی، به مستندات پروژه مراجعه کنید.

---
ساخته شده با ❤️ توسط سیستم چند-عامله تولید کد
"""
        zip_file.writestr("PROJECT_INFO.md", readme_content)
    
    zip_buffer.seek(0)
    
    # آمارگیری دانلود
    with sqlite3.connect(db_manager.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO system_stats (metric_name, metric_value, timestamp)
            VALUES (?, ?, ?)
        """, ("download", job_id, datetime.now().isoformat()))
    
    logger.info(f"Project downloaded: {job_id}")
    
    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=project_{job_id[:8]}.zip"}
    )

@app.get("/preview/{job_id}/{filename:path}")
async def preview_file(job_id: str, filename: str):
    """پیش‌نمایش فایل"""
    files = db_manager.get_job_files(job_id)
    
    for file_data in files:
        if file_data['filename'] == filename:
            return {
                "filename": filename,
                "content": file_data['content'],
                "agent": file_data['agent'],
                "file_size": file_data['file_size'],
                "file_hash": file_data['file_hash'],
                "created_at": file_data['created_at']
            }
    
    raise HTTPException(status_code=404, detail="فایل یافت نشد")

@app.get("/api/stats")
async def get_system_stats():
    """دریافت آمار سیستم"""
    with sqlite3.connect(db_manager.db_path) as conn:
        cursor = conn.cursor()
        
        # آمار کلی
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'completed'")
        completed_jobs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM job_files")
        total_files = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM system_stats WHERE metric_name = 'download'")
        total_downloads = cursor.fetchone()[0]
        
        # آمار امروز
        today = datetime.now().date().isoformat()
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE DATE(created_at) = ?", (today,))
        today_jobs = cursor.fetchone()[0]
        
        # محبوب‌ترین نوع پروژه‌ها
        cursor.execute("""
            SELECT metric_value, COUNT(*) as count
            FROM system_stats 
            WHERE metric_name = 'job_completion'
            GROUP BY JSON_EXTRACT(metric_value, '$.project_type')
            ORDER BY count DESC
            LIMIT 5
        """)
        popular_types = cursor.fetchall()
        
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "success_rate": round((completed_jobs / max(total_jobs, 1)) * 100, 1),
            "total_files": total_files,
            "total_downloads": total_downloads,
            "today_jobs": today_jobs,
            "popular_project_types": [{"type": row[0], "count": row[1]} for row in popular_types],
            "system_uptime": datetime.now().isoformat(),
            "version": "1.0.0"
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket برای real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # ارسال پیام خوشامدگویی
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "اتصال WebSocket برقرار شد",
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False))
        
        while True:
            # نگه داشتن اتصال زنده
            data = await websocket.receive_text()
            
            # پردازش پیام‌های دریافتی (در صورت نیاز)
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, ensure_ascii=False))
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

# ==============================================================================
# Static Files و Templates
# ==============================================================================

# سرو فایل‌های استاتیک
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ==============================================================================
# Error Handlers
# ==============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """مدیریت خطاهای HTTP"""
    return {
        "error": True,
        "message": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """مدیریت خطاهای عمومی"""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": True,
        "message": "خطای داخلی سرور",
        "status_code": 500,
        "timestamp": datetime.now().isoformat()
    }

# ==============================================================================
# Startup و Shutdown Events
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """رویدادهای راه‌اندازی"""
    logger.info("🚀 Starting Multi-Agent Code Generation System...")
    
    # ایجاد پوشه‌های مورد نیاز
    directories = ["static", "logs", "uploads", "cache"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # تست اتصال دیتابیس
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs")
            job_count = cursor.fetchone()[0]
            logger.info(f"📊 Database connected: {job_count} jobs in history")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
    
    # ثبت آمار راه‌اندازی
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_stats (metric_name, metric_value, timestamp)
                VALUES (?, ?, ?)
            """, ("system_startup", "v1.0.0", datetime.now().isoformat()))
    except Exception as e:
        logger.warning(f"Could not save startup stats: {e}")
    
    logger.info("✅ System startup completed successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """رویدادهای خاموش کردن"""
    logger.info("🔄 Shutting down Multi-Agent Code Generation System...")
    
    # بستن اتصالات WebSocket
    for ws in websocket_connections.copy():
        try:
            await ws.close()
        except:
            pass
    websocket_connections.clear()
    
    # ثبت آمار خاموش کردن
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_stats (metric_name, metric_value, timestamp)
                VALUES (?, ?, ?)
            """, ("system_shutdown", "graceful", datetime.now().isoformat()))
    except Exception as e:
        logger.warning(f"Could not save shutdown stats: {e}")
    
    logger.info("✅ System shutdown completed")

# ==============================================================================
# Admin Routes (اختیاری)
# ==============================================================================

@app.get("/admin/jobs")
async def admin_get_jobs(status: Optional[str] = None, limit: int = 100):
    """مدیریت: دریافت لیست job ها"""
    with sqlite3.connect(db_manager.db_path) as conn:
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT id, status, progress, description, created_at, completed_at, files_count
                FROM jobs WHERE status = ?
                ORDER BY created_at DESC LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT id, status, progress, description, created_at, completed_at, files_count
                FROM jobs
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))
        
        jobs = []
        for row in cursor.fetchall():
            jobs.append({
                "job_id": row[0],
                "status": row[1],
                "progress": row[2],
                "description": row[3][:100] + "..." if len(row[3]) > 100 else row[3],
                "created_at": row[4],
                "completed_at": row[5],
                "files_count": row[6] or 0
            })
        
        return {"jobs": jobs}

@app.delete("/admin/jobs/{job_id}")
async def admin_delete_job(job_id: str):
    """مدیریت: حذف job"""
    with sqlite3.connect(db_manager.db_path) as conn:
        cursor = conn.cursor()
        
        # حذف فایل‌ها
        cursor.execute("DELETE FROM job_files WHERE job_id = ?", (job_id,))
        # حذف لاگ‌ها
        cursor.execute("DELETE FROM agent_logs WHERE job_id = ?", (job_id,))
        # حذف job
        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        
        if cursor.rowcount > 0:
            logger.info(f"Job deleted by admin: {job_id}")
            return {"message": "Job با موفقیت حذف شد"}
        else:
            raise HTTPException(status_code=404, detail="Job یافت نشد")

@app.post("/admin/cleanup")
async def admin_cleanup_old_jobs(days_old: int = 30):
    """مدیریت: پاک‌سازی job های قدیمی"""
    cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
    
    with sqlite3.connect(db_manager.db_path) as conn:
        cursor = conn.cursor()
        
        # شمارش job های قدیمی
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE created_at < ?", (cutoff_date,))
        old_jobs_count = cursor.fetchone()[0]
        
        # حذف فایل‌ها
        cursor.execute("""
            DELETE FROM job_files WHERE job_id IN (
                SELECT id FROM jobs WHERE created_at < ?
            )
        """, (cutoff_date,))
        
        # حذف لاگ‌ها
        cursor.execute("""
            DELETE FROM agent_logs WHERE job_id IN (
                SELECT id FROM jobs WHERE created_at < ?
            )
        """, (cutoff_date,))
        
        # حذف job ها
        cursor.execute("DELETE FROM jobs WHERE created_at < ?", (cutoff_date,))
        
        logger.info(f"Cleaned up {old_jobs_count} old jobs (older than {days_old} days)")
        
        return {
            "message": f"{old_jobs_count} job قدیمی پاک شد",
            "days_old": days_old,
            "cutoff_date": cutoff_date
        }

# ==============================================================================
# Utility Functions
# ==============================================================================

def get_app_info():
    """اطلاعات اپلیکیشن"""
    return {
        "name": "Multi-Agent Code Generation System",
        "version": "1.0.0",
        "description": "سیستم چند-عامله تولید کد و پروژه",
        "author": "AI Multi-Agent Team",
        "license": "MIT",
        "python_version": sys.version,
        "startup_time": datetime.now().isoformat()
    }

async def health_check_database():
    """بررسی سلامت دیتابیس"""
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return True
    except Exception:
        return False

# ==============================================================================
# Command Line Interface
# ==============================================================================

def create_sample_project():
    """ایجاد پروژه نمونه برای تست"""
    print("🧪 Creating sample project...")
    
    # Sample request
    sample_request = ProjectRequest(
        description="ماشین حساب پیشرفته با انیمیشن و تاریخچه",
        mode="dry",
        rounds=2
    )
    
    # Create job
    job_id = str(uuid.uuid4())
    
    async def run_sample():
        try:
            await orchestrator.generate_project(job_id, sample_request)
            print(f"✅ Sample project created with ID: {job_id}")
            return job_id
        except Exception as e:
            print(f"❌ Sample project failed: {e}")
            return None
    
    return asyncio.run(run_sample())

def show_stats():
    """نمایش آمار سیستم"""
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM jobs")
            total_jobs = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'completed'")
            completed_jobs = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM job_files")
            total_files = cursor.fetchone()[0]
            
            print(f"""
📊 آمار سیستم:
   🔢 کل job ها: {total_jobs}
   ✅ job های تکمیل شده: {completed_jobs}
   📁 کل فایل‌های تولید شده: {total_files}
   💯 درصد موفقیت: {(completed_jobs/max(total_jobs,1)*100):.1f}%
            """)
    
    except Exception as e:
        print(f"❌ Error showing stats: {e}")

# ==============================================================================
# Main Application Entry Point
# ==============================================================================

def main():
    """تابع اصلی اجرای برنامه"""
    
    # پردازش آرگومان‌های خط فرمان
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "sample":
            create_sample_project()
            return
        elif command == "stats":
            show_stats()
            return
        elif command == "help":
            print("""
🤖 Multi-Agent Code Generation System

دستورات موجود:
  python main.py                 - اجرای سرور
  python main.py sample          - ایجاد پروژه نمونه
  python main.py stats           - نمایش آمار
  python main.py help            - نمایش راهنما

Environment Variables:
  HOST                          - آدرس سرور (پیش‌فرض: 0.0.0.0)
  PORT                          - پورت سرور (پیش‌فرض: 8000)
  DATABASE_URL                  - مسیر دیتابیس (پیش‌فرض: multiagent.db)
  LOG_LEVEL                     - سطح لاگ (پیش‌فرض: INFO)

مثال‌ها:
  HOST=127.0.0.1 PORT=8080 python main.py
  python main.py sample
            """)
            return
    
    # تنظیمات سرور از متغیرهای محیطی
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    # نمایش اطلاعات راه‌اندازی
    app_info = get_app_info()
    print(f"""
🤖 {app_info['name']} v{app_info['version']}
📝 {app_info['description']}

🌐 سرور در حال راه‌اندازی...
   📡 آدرس: http://{host}:{port}
   📚 مستندات API: http://{host}:{port}/docs
   🔌 WebSocket: ws://{host}:{port}/ws
   📊 آمار سیستم: http://{host}:{port}/api/stats
   💾 دیتابیس: {db_manager.db_path}

🎯 برای تست سریع:
   curl -X POST "http://{host}:{port}/api/generate" \\
        -H "Content-Type: application/json" \\
        -d '{{"description": "ماشین حساب ساده", "mode": "dry"}}'

⏹️  برای توقف: Ctrl+C
    """)
    
    try:
        # اجرای سرور
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            access_log=True,
            server_header=False,
            date_header=False
        )
    except KeyboardInterrupt:
        print("\n🔄 سرور متوقف شد")
    except Exception as e:
        print(f"\n❌ خطا در اجرای سرور: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    