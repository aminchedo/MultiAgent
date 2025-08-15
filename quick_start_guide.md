# 🚀 راهنمای سریع راه‌اندازی

## ⚡ روش فوری (30 ثانیه)

```bash
# 1. دانلود و اجرای تزریق سریع
python quick_inject.py

# 2. اجرای سرور
python back.py
```

**آدرس**: http://127.0.0.1:8000

---

## 🔧 روش کامل (2 دقیقه)

```bash
# 1. اجرای راه‌انداز کامل
python complete_launcher.py

# یا با گزینه‌های مختلف:
python complete_launcher.py setup    # راه‌اندازی کامل
python complete_launcher.py test     # تست سیستم
python complete_launcher.py run      # اجرای مستقیم
python complete_launcher.py fix      # رفع مشکلات
```

---

## 🪟 ویندوز

### روش 1: Batch File
```cmd
# ダブルクلیک روی فایل:
setup.bat
```

### روش 2: PowerShell
```powershell
# اجرا در PowerShell:
.\setup.ps1
```

---

## 🐧 لینوکس/Mac

```bash
# اجازه اجرا
chmod +x setup.sh

# اجرا
./setup.sh
```

---

## 📋 چک‌لیست سریع

- [ ] **Python 3.8+** نصب شده؟
- [ ] **pip** کار می‌کند؟
- [ ] فایل **back.py** موجود است؟
- [ ] فایل **front.html** موجود است؟
- [ ] **1GB فضای خالی** دیسک

---

## 🔗 آدرس‌های مهم

| سرویس | آدرس | توضیح |
|--------|-------|-------|
| 🌐 **API** | http://127.0.0.1:8000 | سرویس اصلی |
| 📚 **Docs** | http://127.0.0.1:8000/docs | مستندات API |
| 🎨 **Frontend** | http://127.0.0.1:8000/static/ | رابط کاربری |
| 🔌 **WebSocket** | ws://127.0.0.1:8000/ws | اتصال Real-time |
| 💊 **Health** | http://127.0.0.1:8000/health | وضعیت سلامت |

---

## 🧪 تست سریع

### 1. تست API:
```bash
curl -X POST "http://127.0.0.1:8000/api/generate" \
     -H "Content-Type: application/json" \
     -d '{"description": "ماشین حساب ساده", "mode": "dry"}'
```

### 2. تست WebSocket:
```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/ws');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

### 3. تست فرانت‌اند:
1. باز کردن http://127.0.0.1:8000/static/
2. پر کردن فرم
3. کلیک روی "شروع تولید"

---

## ❌ رفع مشکلات سریع

### مشکل: خطای Import
```bash
pip install fastapi uvicorn websockets pydantic
```

### مشکل: پورت اشغال
```bash
# تغییر پورت در back.py:
PORT = 8001  # به جای 8000
```

### مشکل: CORS Error
```python
# در back.py اضافه کنید:
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

### مشکل: فایل یافت نشد
```bash
# بررسی فایل‌ها:
ls -la *.py *.html

# یا در ویندوز:
dir *.py *.html
```

---

## 🎯 نکات مهم

- ✅ **بک‌اند** قبل از فرانت‌اند اجرا شود
- ✅ **پورت 8000** آزاد باشد
- ✅ **Python 3.8+** استفاده کنید
- ✅ در صورت مشکل **complete_launcher.py fix** اجرا کنید

---

## 🆘 پشتیبانی سریع

### لاگ‌ها:
```bash
tail -f app.log        # مشاهده لاگ‌ها
python -c "import sys; print(sys.version)"  # نسخه Python
```

### Debug Mode:
```javascript
// در Console مرورگر:
window.debugAI()  # اطلاعات debugging
```

### ری‌استارت سریع:
```bash
Ctrl+C              # توقف سرور
python back.py      # شروع مجدد
```

---

## ✨ ویژگی‌های کلیدی

- 🤖 **5 عامل هوشمند** (برنامه‌ریز، کدنویس، بازبین، بهینه‌ساز، تستر)
- ⚡ **Real-time WebSocket** برای نظارت زنده
- 📦 **دانلود ZIP** پروژه‌های تولید شده
- 🎨 **UI مدرن** با Material Design
- 🌐 **API کامل** با مستندات خودکار
- 📊 **مانیتورینگ سیستم** و آمارگیری

---

## 🎉 آماده برای استفاده!

پس از اجرای موفق، سیستم شما آماده تولید پروژه‌های زیبا و کارآمد است! 

**بردارید و از آن لذت ببرید! 🚀**