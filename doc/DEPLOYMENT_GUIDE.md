# 🚀 DEPLOYMENT GUIDE - PHASE 2 FIXES

## Quick Start

### 1. Environment Setup
```bash
# Set required environment variables
export OPENAI_API_KEY="your-openai-api-key"
export DATABASE_URL="sqlite+aiosqlite:///./dev.db"  # For development
export API_KEY_SECRET="default-dev-key"  # For development
export JWT_SECRET_KEY="your-jwt-secret-key"

# For production, use PostgreSQL:
# export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dbname"
```

### 2. Install Dependencies
```bash
pip install --break-system-packages \
  fastapi uvicorn \
  langchain-openai crewai \
  tenacity sqlalchemy aiosqlite \
  redis python-jose passlib \
  slowapi structlog python-multipart
```

### 3. Start the Backend
```bash
# Option 1: Use the main backend
python3 -m backend.core.app

# Option 2: Use the Vercel-compatible version
python3 api/vercel_app.py

# Option 3: Use uvicorn directly
uvicorn backend.core.app:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Test the API
```bash
# Test authentication
curl -X POST http://localhost:8000/api/validate-key \
  -H "Content-Type: application/json" \
  -d '{"api_key": "default-dev-key"}'

# Test project generation
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "description": "Create a simple Python web API with FastAPI",
    "complexity": "simple"
  }'
```

## Frontend Integration

The frontend expects these endpoints:
- ✅ `/api/validate-key` - API key validation
- ✅ `/api/generate` - Project generation
- ✅ `/api/status/{job_id}` - Job status monitoring
- ✅ `/api/download/{job_id}` - Project download

All endpoints are now properly implemented and tested.

## Production Deployment

### Environment Variables (Production)
```bash
export OPENAI_API_KEY="your-production-openai-key"
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
export API_KEY_SECRET="your-secure-api-key"
export JWT_SECRET_KEY="your-secure-jwt-secret"
export VERCEL_ENV="production"
```

### Vercel Deployment
The system is now Vercel-compatible with the consolidated API structure.

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "backend.core.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Monitoring & Logging

The system includes:
- ✅ Structured logging with `structlog`
- ✅ Prometheus metrics (if enabled)
- ✅ Rate limiting with `slowapi`
- ✅ Error tracking and retry logic

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Database Connection**: Check `DATABASE_URL` format
3. **OpenAI API**: Verify `OPENAI_API_KEY` is valid
4. **Authentication**: Check JWT token format and expiration

### Debug Mode
```bash
export DEBUG=true
export LOG_LEVEL=debug
```

## Success Indicators

✅ All imports successful  
✅ API endpoints responding  
✅ LLM integration working  
✅ Database connections established  
✅ Authentication flow complete  
✅ Project generation functional  

---

**🎉 The system is now ready for deployment with all Phase 2 fixes implemented!**