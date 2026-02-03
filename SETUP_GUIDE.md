# Complete Setup Guide

## ✅ What's Already Installed

- ✅ Python dependencies (all packages from `pyproject.toml`)
- ✅ Blog Writer SDK (installed in editable mode)

## 📦 What Else You Need

### 1. System Dependencies (if not already installed)

The Dockerfile shows these system dependencies, but for local development you may need:

```bash
# On macOS (using Homebrew)
brew install curl git jq

# On Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y curl git jq build-essential
```

### 2. Google Cloud CLI (for deployment/credentials)

```bash
# Install gcloud CLI (if not installed)
# macOS
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

### 3. Docker (optional, for containerized deployment)

```bash
# macOS
brew install docker

# Or download Docker Desktop from: https://www.docker.com/products/docker-desktop
```

---

## 🔑 Credentials Setup

### Required Credentials

You need to set up credentials for the application to work. Here's what's needed:

#### 1. **Supabase** (REQUIRED - for database)
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (full access)
- `SUPABASE_ANON_KEY` - Anonymous key (public access)

**Get these from:** [Supabase Dashboard](https://app.supabase.com/) → Your Project → Settings → API

#### 2. **AI Providers** (REQUIRED - at least one)
- `OPENAI_API_KEY` - OpenAI API key (starts with `sk-`)
- `ANTHROPIC_API_KEY` - Anthropic API key (starts with `sk-ant-`)

**Get these from:**
- OpenAI: https://platform.openai.com/account/api-keys
- Anthropic: https://console.anthropic.com/settings/keys

#### 3. **Google Services** (OPTIONAL but recommended)
- `GOOGLE_CUSTOM_SEARCH_API_KEY` - For enhanced blog generation
- `GOOGLE_CUSTOM_SEARCH_ENGINE_ID` - Custom Search Engine ID
- `GOOGLE_KNOWLEDGE_GRAPH_API_KEY` - For entity recognition
- `GOOGLE_APPLICATION_CREDENTIALS` - Firebase/Firestore service account JSON

**Get these from:**
- Google Cloud Console → APIs & Services → Credentials
- Firebase Console → Project Settings → Service Accounts

#### 4. **DataForSEO** (OPTIONAL - for enhanced keyword analysis)
- `DATAFORSEO_API_KEY` - Your DataForSEO email/username
- `DATAFORSEO_API_SECRET` - Your DataForSEO API key

**Get these from:** [DataForSEO Dashboard](https://dataforseo.com/)

---

## 🚀 Quick Setup Methods

### Method 1: Local Development (.env file)

**Best for:** Local development and testing

1. **Create a `.env` file:**
```bash
cp env.example .env
```

2. **Edit `.env` with your credentials:**
```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# AI Providers (at least one required)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Optional but recommended
GOOGLE_CUSTOM_SEARCH_API_KEY=your-google-search-key
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your-search-engine-id
```

3. **The app will automatically load from `.env`** (using `python-dotenv`)

### Method 2: Google Cloud Secret Manager (for Cloud Run)

**Best for:** Production deployments on Google Cloud Run

#### Quick Setup Scripts:

**AI Providers:**
```bash
# Interactive setup
./scripts/setup-ai-provider-secrets.sh

# Or non-interactive
export OPENAI_API_KEY="sk-your-key"
export ANTHROPIC_API_KEY="sk-ant-your-key"
./scripts/setup-ai-provider-secrets-noninteractive.sh
```

**DataForSEO:**
```bash
# Interactive setup
./scripts/add-dataforseo-secrets.sh

# Or non-interactive
./scripts/add-dataforseo-secrets-noninteractive.sh "your-email@example.com" "your-api-key"
```

**Google Custom Search:**
```bash
./scripts/setup-google-custom-search-secrets.sh
```

**Verify all secrets:**
```bash
./scripts/verify-secrets-setup.sh dev
```

---

## 📋 Complete Credentials Checklist

### Minimum Required (to run locally)
- [ ] Supabase URL
- [ ] Supabase Service Role Key
- [ ] Supabase Anon Key
- [ ] At least one AI provider key (OpenAI or Anthropic)

### Recommended (for full features)
- [ ] Google Custom Search API Key
- [ ] Google Custom Search Engine ID
- [ ] Google Knowledge Graph API Key
- [ ] DataForSEO credentials (for enhanced keyword analysis)
- [ ] Firebase Service Account (for Firestore)

### Optional (for advanced features)
- [ ] Redis (for caching)
- [ ] Cloudinary (for image storage)
- [ ] AWS S3 (for file storage)
- [ ] Platform integrations (Webflow, Shopify, WordPress)

---

## 🧪 Test Your Setup

### 1. Test Local Environment Variables

```bash
# Check if .env is loaded
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Supabase URL:', os.getenv('SUPABASE_URL', 'NOT SET'))"
```

### 2. Test API Connection

```bash
# Start the server
python3 main.py

# In another terminal, test health endpoint
curl http://localhost:8000/health
```

### 3. Test AI Generation

```bash
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Test Blog Post",
    "keywords": ["test"],
    "tone": "professional",
    "length": "short"
  }'
```

---

## 🔧 Environment-Specific Setup

### Development
- Use `.env` file (local)
- Or Google Secret Manager with `dev` suffix

### Staging/Production
- Use Google Secret Manager
- Secrets are automatically loaded by Cloud Run

---

## 📚 Additional Resources

- **Supabase Setup:** See `SUPABASE_SETUP.md`
- **Google Services Setup:** See `GOOGLE_SECRETS_SETUP_V1.3.6.md`
- **DataForSEO Setup:** See `DATAFORSEO_CREDENTIALS_GUIDE.md`
- **AI Providers Setup:** See `SETUP_AI_PROVIDERS_NOW.md`
- **Scripts Documentation:** See `scripts/README.md`

---

## ⚠️ Security Notes

1. **Never commit `.env` files** - They're in `.gitignore`
2. **Use Secret Manager for production** - Never hardcode credentials
3. **Rotate keys regularly** - Especially if exposed
4. **Use service accounts** - For Google Cloud services
5. **Limit permissions** - Only grant necessary access

---

## 🆘 Troubleshooting

### "Module not found" errors
```bash
# Reinstall dependencies
pip install -e .
```

### "Credentials not found" errors
- Check `.env` file exists and has correct values
- Verify environment variables are set: `echo $SUPABASE_URL`
- For Cloud Run: Check Secret Manager permissions

### "API key invalid" errors
- Verify keys are correct (no extra spaces)
- Check API key hasn't expired
- Ensure billing is enabled (for OpenAI/Anthropic)

---

**Ready to start?** Set up your `.env` file with the minimum required credentials and run `python3 main.py`!
