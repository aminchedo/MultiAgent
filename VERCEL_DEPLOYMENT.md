# Vercel Deployment Guide

This guide will help you deploy the Multi-Agent Code Generation System to Vercel and fix the 404 NOT_FOUND error.

## 🚀 Quick Deployment

### Option 1: Automated Deployment (Recommended)

1. **Run the deployment script:**
   ```bash
   ./deploy-vercel.sh
   ```

2. **Follow the prompts** to complete the deployment.

### Option 2: Manual Deployment

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   vercel --prod
   ```

## 📁 Project Structure for Vercel

```
├── api/
│   ├── index.py          # Vercel serverless function entry point
│   └── vercel_app.py     # Vercel-specific FastAPI app
├── config/
│   └── vercel_config.py  # Vercel-specific configuration
├── frontend/
│   └── pages/            # Static frontend files
├── vercel.json           # Vercel configuration
├── requirements-vercel.txt # Minimal requirements for Vercel
└── deploy-vercel.sh      # Deployment script
```

## ⚙️ Configuration Files

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/api/index.py"
    }
  ],
  "functions": {
    "api/index.py": {
      "runtime": "python3.9"
    }
  },
  "env": {
    "PYTHONPATH": "."
  }
}
```

### requirements-vercel.txt
Minimal dependencies optimized for serverless deployment:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.5.0
pydantic-settings==2.1.0
structlog==23.2.0
slowapi==0.1.9
prometheus-fastapi-instrumentator==6.1.0
```

## 🔧 Environment Variables

Set these in your Vercel dashboard:

```bash
DEBUG=false
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
OPENAI_API_KEY=your-openai-api-key-here
```

## 🌐 Available Endpoints

After deployment, your application will have these endpoints:

- **Frontend**: `/` - Main application interface
- **Health Check**: `/health` - Application health status
- **API Status**: `/api/status` - API operational status
- **System Info**: `/info` - System configuration and features
- **Static Files**: `/static/*` - Frontend assets

## 🔍 Troubleshooting 404 Errors

### Common Issues and Solutions

1. **404 NOT_FOUND Error**
   - **Cause**: Missing or incorrect Vercel configuration
   - **Solution**: Ensure `vercel.json` exists and is properly configured

2. **Import Errors**
   - **Cause**: Missing dependencies or incorrect Python path
   - **Solution**: Check `requirements-vercel.txt` and ensure all imports are available

3. **Static Files Not Loading**
   - **Cause**: Incorrect static file path configuration
   - **Solution**: Verify the static files route in `vercel.json`

4. **Database Connection Errors**
   - **Cause**: Database dependencies in serverless environment
   - **Solution**: Use the Vercel-specific configuration that disables database features

### Debug Steps

1. **Check Vercel Logs:**
   ```bash
   vercel logs
   ```

2. **Test Locally:**
   ```bash
   vercel dev
   ```

3. **Verify Configuration:**
   ```bash
   vercel inspect
   ```

## 🛠️ Development vs Production

### Development (Local)
- Full database and Redis support
- Debug mode enabled
- Hot reload enabled
- All features available

### Production (Vercel)
- Serverless deployment
- Database and Redis disabled
- Optimized for cold starts
- Rate limiting enabled
- Simplified features

## 📊 Performance Optimization

### For Vercel Deployment
1. **Minimal Dependencies**: Only essential packages included
2. **Cold Start Optimization**: Reduced initialization time
3. **Rate Limiting**: Prevents abuse and controls costs
4. **Static File Caching**: Optimized frontend delivery

### Monitoring
- Health check endpoints for monitoring
- Structured logging for debugging
- Performance headers included

## 🔒 Security Considerations

1. **Environment Variables**: Never commit sensitive data
2. **Rate Limiting**: Prevents abuse
3. **CORS Configuration**: Properly configured for production
4. **Input Validation**: All endpoints validate input

## 📈 Scaling

Vercel automatically scales your application based on demand:
- **Serverless Functions**: Scale to zero when not in use
- **Global CDN**: Fast static file delivery worldwide
- **Edge Functions**: Low-latency response times

## 🆘 Support

If you encounter issues:

1. **Check Vercel Documentation**: https://vercel.com/docs
2. **Review Application Logs**: Use `vercel logs`
3. **Test Locally**: Use `vercel dev` for local testing
4. **Verify Configuration**: Ensure all files are properly configured

## ✅ Success Checklist

- [ ] Vercel CLI installed and logged in
- [ ] All configuration files present
- [ ] Environment variables set
- [ ] Deployment successful
- [ ] Health check endpoint responding
- [ ] Frontend accessible
- [ ] No 404 errors

## 🎉 Deployment Complete!

Once deployed, your application will be available at:
```
https://your-project-name.vercel.app
```

The 404 NOT_FOUND error should be resolved, and your application will display correctly in Vercel services.