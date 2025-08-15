# 🔐 Security Deployment Guide

## ⚠️ CRITICAL SECURITY NOTICE

**NEVER HARDCODE TOKENS IN YOUR CODE!**

This guide provides secure deployment practices to protect your API keys and tokens.

## 🛡️ Security Best Practices

### 1. Environment Variables Only
Always use environment variables for sensitive data:

```bash
# ✅ CORRECT - Use environment variables
export HF_TOKEN=your_actual_token_here
export OPENAI_API_KEY=your_openai_key_here
export JWT_SECRET_KEY=your_jwt_secret_here
```

```bash
# ❌ WRONG - Never hardcode tokens
HF_TOKEN="hf_actual_token_here"  # This will be blocked by Hugging Face!
```

### 2. .env File Management
Create a `.env` file for local development:

```bash
# Create .env file (this file is gitignored)
cat > .env << EOF
HF_TOKEN=your_actual_token_here
OPENAI_API_KEY=your_openai_key_here
JWT_SECRET_KEY=your_jwt_secret_here
HUGGING_FACE_SPACE=your_space_name
EOF
```

**IMPORTANT**: Never commit `.env` files to git!

### 3. Secure Token Generation
Get your tokens from official sources:

- **Hugging Face Token**: https://huggingface.co/settings/tokens
  - Create token with "Write" permissions
  - Choose appropriate scope (repos, spaces)
- **OpenAI API Key**: https://platform.openai.com/api-keys
- **JWT Secret**: Generate cryptographically secure random string

## 🚀 Secure Deployment Methods

### Method 1: Environment Variables (Recommended)

```bash
# Set your environment variables
export HF_TOKEN=your_actual_token_here
export OPENAI_API_KEY=your_openai_key_here

# Deploy securely
./quick-deploy-test.sh
```

### Method 2: .env File

```bash
# Source from .env file
source .env

# Deploy
./quick-deploy-test.sh
```

### Method 3: Inline Environment Variables

```bash
# One-time deployment with inline vars
HF_TOKEN=your_token OPENAI_API_KEY=your_key ./quick-deploy-test.sh
```

## 🏗️ Platform-Specific Security

### Hugging Face Spaces
1. **Repository Secrets**:
   - Go to your Space settings
   - Add secrets in "Repository secrets" section
   - Never expose tokens in logs or code

2. **Environment Variables**:
   ```python
   import os
   hf_token = os.environ.get('HF_TOKEN')
   if not hf_token:
       raise ValueError("HF_TOKEN environment variable not set")
   ```

### GitHub Actions
Add secrets in repository settings:
- Go to Settings → Secrets and variables → Actions
- Add repository secrets:
  - `HF_TOKEN`: Your Hugging Face token
  - `OPENAI_API_KEY`: Your OpenAI key

### Vercel
Add environment variables in Vercel dashboard:
- Go to Project Settings → Environment Variables
- Add production environment variables

## 🔍 Security Validation

### Pre-deployment Checklist
- [ ] No hardcoded tokens in any file
- [ ] All tokens stored as environment variables
- [ ] .env files are gitignored
- [ ] Security patterns added to .gitignore
- [ ] Tokens have minimal required permissions
- [ ] Regular token rotation schedule established

### Validation Commands
```bash
# Check for hardcoded tokens
grep -r "hf_[a-zA-Z0-9]" . --exclude-dir=.git
grep -r "sk-[a-zA-Z0-9]" . --exclude-dir=.git

# Verify .env is gitignored
git check-ignore .env

# Test environment variable access
echo $HF_TOKEN | head -c 10  # Should show first 10 chars
```

## 🚨 What to Do If Token is Exposed

### Immediate Actions
1. **Revoke the exposed token immediately**:
   - Hugging Face: https://huggingface.co/settings/tokens
   - OpenAI: https://platform.openai.com/api-keys

2. **Generate new tokens**
3. **Update all deployment environments**
4. **Review commit history for exposure**
5. **Rotate all related credentials**

### Clean Git History (if needed)
```bash
# Remove sensitive data from git history (use with caution)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch file_with_token.sh' \
  --prune-empty --tag-name-filter cat -- --all

# Force push (destroys history - use carefully)
git push origin --force --all
```

## 📋 Deployment Command Examples

### Quick Deploy (Secure)
```bash
# Method 1: Environment variables
export HF_TOKEN=your_token_here
./quick-deploy-test.sh

# Method 2: From .env file
source .env && ./quick-deploy-test.sh

# Method 3: Inline (for CI/CD)
HF_TOKEN=$SECURE_TOKEN ./quick-deploy-test.sh
```

### CI/CD Pipeline (GitHub Actions)
```yaml
name: Secure Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to HF
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: ./quick-deploy-test.sh
```

## 🛡️ Advanced Security

### Token Scoping
Use minimal permissions:
- **Hugging Face**: Only "write" to specific spaces
- **OpenAI**: Set usage limits and monitoring
- **JWT**: Use strong, rotating secrets

### Monitoring
- Set up token usage monitoring
- Enable audit logs where available
- Regular security reviews
- Automated vulnerability scanning

### Network Security
- Use HTTPS everywhere
- Implement rate limiting
- Add IP whitelisting if possible
- Enable 2FA on all accounts

## 📞 Security Support

If you suspect a security breach:
1. Immediately revoke all tokens
2. Generate new credentials
3. Review access logs
4. Update all deployments
5. Contact platform support if needed

---

## ✅ Quick Security Checklist

- [ ] Tokens stored as environment variables only
- [ ] No hardcoded credentials in code
- [ ] .env files properly gitignored
- [ ] Minimal token permissions
- [ ] Regular token rotation
- [ ] Monitoring and alerts configured
- [ ] Team trained on security practices

**Remember: Security is not optional - it's essential!** 🔐