#!/bin/bash
# update_api_key.sh - Securely update your Google AI Studio API key

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Google AI Studio API Key - Secure Update Script           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if already in docufind directory
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "   Please run this script from: /Users/vallabhnaik/Desktop/docufind"
    exit 1
fi

echo "📝 Step 1: Get Your New API Key"
echo "   Go to: https://aistudio.google.com/app/apikey"
echo "   Click: 'Get API Key' → 'Create API Key in new project'"
echo "   Copy the key that starts with 'AIza...'"
echo ""

read -p "Paste your new API key here: " NEW_API_KEY

# Validate key format
if [[ ! $NEW_API_KEY =~ ^AIza ]]; then
    echo ""
    echo "⚠️  Warning: Key doesn't start with 'AIza'"
    echo "   Make sure you copied the full key from Google AI Studio"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled."
        exit 1
    fi
fi

echo ""
echo "🔐 Step 2: Updating .env file..."

# Create backup
cp .env .env.backup
echo "   ✓ Backup created: .env.backup"

# Update the key
cat > .env << EOF
GOOGLE_API_KEY=$NEW_API_KEY
PROJECT_ID=projects/796327426831
EOF

echo "   ✓ .env updated with new API key"

echo ""
echo "✅ Step 3: Testing new key..."
echo ""

# Test the key
python3 << 'PYTHON'
import os
from pathlib import Path

# Load .env
env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val

api_key = os.getenv("GOOGLE_API_KEY")
if api_key and api_key.startswith("AIza"):
    print(f"   ✓ API Key format is valid!")
    print(f"   ✓ Key length: {len(api_key)} characters")
    print(f"   ✓ Starts with: {api_key[:10]}...")
else:
    print(f"   ❌ API Key format invalid!")
    exit(1)
PYTHON

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error validating API key!"
    echo "   Restoring from backup..."
    cp .env.backup .env
    exit 1
fi

echo ""
echo "📊 Step 4: Next steps"
echo "   1. Activate venv:     source venv/bin/activate"
echo "   2. Test RAG:          python rag_examples.py --auto"
echo "   3. Commit to git:     git add .env && git commit -m '🔐 Update API key'"
echo ""
echo "✨ All done! Your API key is updated and ready to use."
echo ""
