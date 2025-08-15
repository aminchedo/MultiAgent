# 🤖 سیستم چند-عامله تولید کد

## 🚀 راه‌اندازی سریع

```bash
# نصب وابستگی‌ها
pip install -r requirements.txt

# اجرای سرور
python back.py

# یا استفاده از اسکریپت
./start.sh  # Linux/Mac
```

## 📡 آدرس‌های مهم

- **API Base**: http://127.0.0.1:8000
- **مستندات API**: http://127.0.0.1:8000/docs
- **WebSocket**: ws://127.0.0.1:8000/ws
- **فرانت‌اند**: static/index.html

## 🔧 تست سریع

```bash
# تست API
curl -X POST "http://127.0.0.1:8000/api/generate" \
     -H "Content-Type: application/json" \
     -d '{"description": "ماشین حساب ساده", "mode": "dry"}'

# مشاهده وضعیت
curl "http://127.0.0.1:8000/health"
```

## 📊 مانیتورینگ

- لاگ‌ها: `tail -f app.log`
- آمار: http://127.0.0.1:8000/api/stats
- وضعیت سلامت: http://127.0.0.1:8000/health
