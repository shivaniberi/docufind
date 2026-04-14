# Google AI Studio API Key Setup Guide

## ⚠️ SECURITY IMPORTANT

The API key in the current `.env` file has been exposed and should be revoked immediately.

## Steps to Get a New API Key from Google AI Studio

### 1. Go to Google AI Studio
Navigate to: **https://aistudio.google.com/app/apikey**

### 2. Create New API Key
- Click the **"Get API Key"** button (blue button on the page)
- Select **"Create API Key in new project"** 
- Google will automatically generate a new API key for you
- The key will appear on screen

### 3. Copy Your New Key
- Look for the API key that starts with `AIza...`
- Click to copy it (you'll see a copy icon)
- Keep it safe - don't share it!

### 4. Update Your `.env` File
Replace the old key with your new one:

```bash
# Option A: Using nano editor
cd /Users/vallabhnaik/Desktop/docufind
nano .env

# Then edit the GOOGLE_API_KEY line:
# GOOGLE_API_KEY=YOUR_NEW_KEY_HERE
# Save with Ctrl+O, then Ctrl+X
```

Or:

```bash
# Option B: Using echo (replace YOUR_NEW_KEY_HERE first!)
cat > /Users/vallabhnaik/Desktop/docufind/.env << 'EOF'
GOOGLE_API_KEY=YOUR_NEW_KEY_HERE
PROJECT_ID=projects/796327426831
EOF
```

### 5. Verify the Key Works
```bash
cd /Users/vallabhnaik/Desktop/docufind
source venv/bin/activate

python << 'PYEOF'
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
if api_key:
    print(f"✅ API Key loaded successfully!")
    print(f"   Key length: {len(api_key)} characters")
    print(f"   First 10 chars: {api_key[:10]}...")
else:
    print("❌ API Key not found!")
PYEOF
```

### 6. Test with RAG System
```bash
python rag_examples.py --auto
```

### 7. Commit to Git
```bash
git add .env
git commit -m "🔐 Update Google AI Studio API key"
```

---

## What Models Are Available?

With your Google AI Studio API key, you can use:

**For Embeddings:**
- `models/text-embedding-004` (free tier)
- Dimensions: 768
- Used by: VectorStore

**For Generation (Phase 3B):**
- `models/gemini-2.0-flash` (free tier, fastest)
- `models/gemini-1.5-pro` (more powerful)
- `models/gemini-1.5-flash` (balanced)

All are available on the free tier!

---

## Security Checklist

- [ ] Old API key revoked in Google Cloud Console
- [ ] New API key created from Google AI Studio
- [ ] `.env` file updated with new key
- [ ] RAG system tested with new key
- [ ] Changes committed to git
- [ ] Old key removed from any version history

---

## Important Notes

✅ **DO:**
- Use Google AI Studio (aistudio.google.com) for free tier
- Keep API key in `.env` (not in code)
- Add `.env` to `.gitignore`
- Use environment variables to load the key

❌ **DON'T:**
- Share your API key publicly
- Commit API keys to git
- Use the key in client-side code
- Hardcode keys in source files

---

## Ready for Phase 3B?

Once you have your new API key:
1. Update `.env` 
2. Test with `python rag_examples.py --auto`
3. Proceed to Phase 3B LLM integration

See: `PHASE3B_LLM_INTEGRATION_GUIDE.md`

---

**Next Step:** Update `.env` with your new Google AI Studio API key, then we can test Phase 3B!
