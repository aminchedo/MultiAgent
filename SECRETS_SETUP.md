# 🔐 Vercel Secrets Configuration Guide

This guide will help you configure the required secrets for your Vercel deployment.

## Required Secrets

Your application needs the following secrets configured in Vercel:

### 1. **OPENAI_API_KEY** (`@openai-api-key`)
- **Purpose**: For OpenAI API calls in your multi-agent system
- **Type**: API Key
- **How to get it**: 
  1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
  2. Sign in or create an account
  3. Click "Create new secret key"
  4. Copy the generated key

### 2. **JWT_SECRET_KEY** (`@jwt-secret-key`)
- **Purpose**: For JWT token signing and verification
- **Type**: Secret string
- **How to generate**: 
  ```bash
  # Option 1: Using OpenSSL
  openssl rand -base64 32
  
  # Option 2: Using Python
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  
  # Option 3: Online generator
  # Visit: https://generate-secret.vercel.app/32
  ```

## Configuration Methods

### Method 1: Using Vercel CLI (Recommended)

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Run the automated script**:
   ```bash
   ./configure_secrets.sh
   ```

### Method 2: Manual CLI Configuration

1. **Add OpenAI API Key**:
   ```bash
   echo "your-openai-api-key-here" | vercel env add openai-api-key production
   echo "your-openai-api-key-here" | vercel env add openai-api-key preview
   echo "your-openai-api-key-here" | vercel env add openai-api-key development
   ```

2. **Add JWT Secret Key**:
   ```bash
   echo "your-jwt-secret-key-here" | vercel env add jwt-secret-key production
   echo "your-jwt-secret-key-here" | vercel env add jwt-secret-key preview
   echo "your-jwt-secret-key-here" | vercel env add jwt-secret-key development
   ```

### Method 3: Using Vercel Dashboard

1. **Go to your Vercel project dashboard**
2. **Navigate to Settings → Environment Variables**
3. **Add each secret**:
   - **Name**: `openai-api-key`
   - **Value**: Your OpenAI API key
   - **Environment**: Production, Preview, Development
   
   - **Name**: `jwt-secret-key`
   - **Value**: Your JWT secret key
   - **Environment**: Production, Preview, Development

## Verification

### Check if secrets are configured:
```bash
vercel env ls
```

### Expected output:
```
Environment Variables for your-project:
- openai-api-key (Production, Preview, Development)
- jwt-secret-key (Production, Preview, Development)
```

## Security Best Practices

1. **Never commit secrets to your repository**
2. **Use different secrets for different environments**
3. **Rotate secrets regularly**
4. **Use strong, random values for JWT secrets**
5. **Limit API key permissions to minimum required**

## Troubleshooting

### Error: "Secret does not exist"
- Make sure you've added the secret to all environments (production, preview, development)
- Verify the secret name matches exactly what's in `vercel.json`

### Error: "Invalid API key"
- Check that your OpenAI API key is valid and has sufficient credits
- Ensure the key has the necessary permissions

### Error: "JWT signature verification failed"
- Verify your JWT secret key is consistent across deployments
- Check that the secret is properly configured in all environments

## Next Steps

After configuring secrets:

1. **Deploy your application**:
   ```bash
   vercel --prod
   ```

2. **Test the deployment**:
   ```bash
   curl https://your-app.vercel.app/api/health
   ```

3. **Monitor logs**:
   ```bash
   vercel logs
   ```

## Support

If you encounter issues:
1. Check the [Vercel documentation](https://vercel.com/docs)
2. Review your application logs: `vercel logs`
3. Verify environment variables are loaded correctly in your application