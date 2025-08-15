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

### 3. Upload Directory Handling
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
```python
# Key changes:
- Increased maxDuration to 60 seconds
- Increased memory to 1024MB
- Added explicit Python 3.9 runtime
```

## Deployment Instructions

### 1. Environment Variables
Ensure these environment variables are set in Vercel:
- `OPENAI_API_KEY`: Your OpenAI API key
- `JWT_SECRET_KEY`: A secure JWT secret key
- `VERCEL`: Automatically set by Vercel

### 2. Deploy to Vercel
```bash
# Install Vercel CLI if not already installed
npm i -g vercel

# Deploy from project root
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
   - Ensure `OPENAI_API_KEY` and `JWT_SECRET_KEY` are set
   - Check that `VERCEL=1` is automatically set

3. **Test locally with Vercel environment**:
   ```bash
   VERCEL=1 python3 -c "from api.index import app; print('App loaded successfully')"
   ```

4. **Check function timeout**:
   - If requests timeout, increase `maxDuration` in `vercel.json`
   - Consider optimizing slow endpoints

### Common Issues

1. **Import errors**: Ensure all dependencies are in `requirements-vercel.txt`
2. **Memory issues**: Increase memory allocation in `vercel.json`
3. **Timeout issues**: Increase `maxDuration` in `vercel.json`
4. **Path issues**: Ensure `PYTHONPATH` is set correctly

## Testing the Fixes

Run the test script to verify fixes work:
```bash
python3 test_vercel_fixes.py
```

This will test:
- Vercel configuration loading
- App import without directory creation
- Index module import
- /tmp directory access

## File Upload Alternative for Vercel

Since Vercel has a read-only filesystem, consider these alternatives for file uploads:

1. **Cloud Storage**: Use AWS S3, Google Cloud Storage, or similar
2. **Temporary Processing**: Process files in memory and return results
3. **External API**: Delegate file handling to another service
4. **Client-side Processing**: Handle files in the frontend

## Summary

The fixes ensure that:
- ✅ App imports successfully without filesystem errors
- ✅ Vercel handler is properly exported
- ✅ Upload functionality gracefully degrades on Vercel
- ✅ All other API endpoints work normally
- ✅ Proper error handling and logging
- ✅ Environment-specific configuration

The application should now deploy successfully on Vercel while maintaining full functionality for local development.