#!/bin/bash
# Simple HF Deploy Script - Copy & Paste Ready
# Deploys everything except this script to Hugging Face

HF_TOKEN="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"
HF_SPACE="Really-amin/ultichat-hugginigfae"
SCRIPT_NAME="deploy.sh"

echo "🚀 Deploying to Hugging Face..."

# Setup
export HF_TOKEN="$HF_TOKEN"
pip install -U huggingface_hub > /dev/null 2>&1

# Login
echo "$HF_TOKEN" | hf auth login --token "$HF_TOKEN" > /dev/null 2>&1

# Create ignore file (exclude this script)
echo "$SCRIPT_NAME" > .deployignore
echo "*.log" >> .deployignore
echo ".git/" >> .deployignore

# Deploy
hf upload "$HF_SPACE" . \
    --repo-type=space \
    --ignore=".deployignore" \
    --commit-message="🚀 Deploy $(date +%H:%M)" \
    --quiet

# Cleanup
rm -f .deployignore

echo "✅ Success! Live at: https://really-amin-ultichat-hugginigfae.hf.space"
echo "🔧 Settings: https://huggingface.co/spaces/$HF_SPACE"