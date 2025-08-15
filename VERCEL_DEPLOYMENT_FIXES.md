# Vercel Deployment Fixes

This document outlines the fixes applied to resolve Vercel deployment issues with the FastAPI application.

## Issues Fixed

### 1. Directory Creation at Import Time
**Problem**: The original `config/vercel_config.py` attempted to create the `uploads` directory during module import, which failed on Vercel's read-only filesystem.

**Solution**: 
- Moved directory creation to lazy initialization using `ensure_upload_dir()` method
- Only creates directories when actually needed (not at import time)
- Uses `/tmp/uploads` for Vercel environment (the only writable location)

### 2. Handler Export Issue
**Problem**: The `api/index.py` exported `handler = app`, but Vercel's Python runtime expected a proper ASGI application.

**Solution**:
- Removed the `handler` export
- Vercel automatically detects FastAPI apps as ASGI applications
- Added `app.debug = False` for production settings

### 3. Runtime Detection Issue
**Problem**: Vercel was not properly detecting this as a Python project due to conflicting configuration.

**Solution**:
- Simplified `vercel.json` configuration
- Updated `.vercelignore` to include Python files
- Ensured `requirements.txt` is present for Python detection
- Removed conflicting Node.js build scripts

### 4. Upload Directory Handling
**Problem**: Upload functionality was completely broken on Vercel due to filesystem restrictions.

**Solution**:
- Disabled uploads by default on Vercel (`UPLOAD_ENABLED = not settings.is_vercel`)
- Added graceful fallback for upload endpoints
- Provided clear error messages when uploads are disabled

## Files Modified

### 1. `config/vercel_config.py`
```python
# Key changes:
- Removed directory creation from __init__ method
- Added ensure_upload_dir() method for lazy initialization
- Better error handling for filesystem operations
- Uses /tmp for Vercel uploads when needed
```

### 2. `api/index.py`
```python
# Key changes:
- Removed handler export (Vercel auto-detects FastAPI apps)
- Added app.debug = False for production
- Improved error handling and logging
```

### 3. `api/vercel_app.py`
```python
# Key changes:
- Updated upload endpoint to use lazy directory creation
- Better error handling for Vercel environment
- Clear messaging when uploads are disabled
```

### 4. `vercel.json`
```json
# Key changes:
- Simplified configuration to avoid runtime conflicts
- Removed invalid runtime specifications
- Kept only essential function settings
```

### 5. `.vercelignore`
```gitignore
# Key changes:
- Removed exclusion of Python files
- Ensured Python project is properly detected
- Kept only necessary exclusions
```

### 6. `package.json`
```json
# Key changes:
- Removed build script that could interfere with Python detection
- Removed Node.js engine requirement
- Kept only Python engine specification
```

## Deployment Instructions

### 1. Environment Variables
**IMPORTANT**: Set these environment variables in your Vercel dashboard:

1. Go to your Vercel project dashboard
2. Navigate to **Settings → Environment Variables**
3. Add these variables:
   ```
   OPENAI_API_KEY = your_actual_openai_api_key
   JWT_SECRET_KEY = your_secure_jwt_secret
   ```

### 2. Deploy to Vercel
```bash
# Option 1: Via Vercel Dashboard
# - Push your code to GitHub
# - Connect your repository to Vercel
# - Deploy automatically

# Option 2: Via Vercel CLI
npm install -g vercel
vercel --prod
```

### 3. Verify Deployment
After deployment, test these endpoints:
- `https://your-app.vercel.app/api/health` - Health check
- `https://your-app.vercel.app/api` - Root endpoint
- `https://your-app.vercel.app/api/test` - Test endpoint
- `https://your-app.vercel.app/api/upload` - Upload endpoint (should return 503 on Vercel)

## Expected Behavior

### Local Development
- Uploads work normally with local `uploads/` directory
- Full functionality available
- Debug mode enabled

### Vercel Production
- Uploads disabled (returns 503 Service Unavailable)
- Uses in-memory SQLite database
- Debug mode disabled
- All other API endpoints work normally

## Troubleshooting

### If deployment still fails:

1. **Check Vercel logs**:
   ```bash
   vercel logs your-app-name
   ```

2. **Verify environment variables**:
   - Ensure `OPENAI_API_KEY` and `JWT_SECRET_KEY` are set in Vercel dashboard
   - Check that `VERCEL=1` is automatically set

3. **Check Python detection**:
   - Ensure `requirements.txt` exists in project root
   - Verify `runtime.txt` specifies Python version
   - Check that `.vercelignore` doesn't exclude Python files

4. **Test locally with Vercel environment**:
   ```bash
   VERCEL=1 python3 -c "from api.index import app; print('App loaded successfully')"
   ```

### Common Issues

1. **Runtime detection errors**: Ensure `requirements.txt` is present and `.vercelignore` includes Python files
2. **Import errors**: Ensure all dependencies are in `requirements.txt`
3. **Memory issues**: Increase memory allocation in `vercel.json`
4. **Timeout issues**: Increase `maxDuration` in `vercel.json`

## File Upload Alternative for Vercel

Since Vercel has a read-only filesystem, consider these alternatives for file uploads:

1. **Cloud Storage**: Use AWS S3, Google Cloud Storage, or similar
2. **Temporary Processing**: Process files in memory and return results
3. **External API**: Delegate file handling to another service
4. **Client-side Processing**: Handle files in the frontend

## Summary

The fixes ensure that:
- ✅ App imports successfully without filesystem errors
- ✅ Vercel properly detects this as a Python project
- ✅ Vercel handler is properly exported
- ✅ Upload functionality gracefully degrades on Vercel
- ✅ All other API endpoints work normally
- ✅ Proper error handling and logging
- ✅ Environment-specific configuration

The application should now deploy successfully on Vercel while maintaining full functionality for local development.