# DataForSEO Credentials Guide

**Date:** 2025-11-23  
**Understanding DataForSEO Authentication**

---

## 🔑 DataForSEO Authentication

DataForSEO uses **Basic Authentication** with:
- **Username/Email** - Your DataForSEO account email address
- **API Key** - Your DataForSEO API key (not a separate "secret")

---

## 📋 What You Have

From your DataForSEO account dashboard, you should have:
1. **Username (Email address)** - e.g., `your-email@example.com`
2. **API Key** - A long string that looks like: `725ec88e0afc0c905...`

---

## 🔄 How It Maps to Our System

Our backend uses these environment variables:
- `DATAFORSEO_API_KEY` = Your **Username/Email**
- `DATAFORSEO_API_SECRET` = Your **API Key**

**Why?** DataForSEO uses Basic Auth where:
- Username = Your email
- Password = Your API key

Our code creates Basic Auth like this:
```python
credentials = f"{api_key}:{api_secret}"  # email:api_key
encoded = base64.b64encode(credentials.encode()).decode()
headers = {"Authorization": f"Basic {encoded}"}
```

---

## ✅ How to Add Credentials

### Option 1: Using the Script (Recommended)

```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr
./scripts/add-dataforseo-secrets.sh
```

**When prompted:**
1. **DataForSEO Username/Email:** Enter your email (e.g., `your-email@example.com`)
2. **DataForSEO API Key:** Enter your API key (the long string)

The script will automatically map:
- Username/Email → `DATAFORSEO_API_KEY`
- API Key → `DATAFORSEO_API_SECRET`

### Option 2: Command Line Arguments

```bash
./scripts/add-dataforseo-secrets.sh "your-email@example.com" "your-api-key-here"
```

### Option 3: Environment Variables

```bash
DATAFORSEO_API_KEY="your-email@example.com" \
DATAFORSEO_API_SECRET="your-api-key-here" \
./scripts/add-dataforseo-secrets.sh
```

---

## 🔍 Verify Your Credentials

After adding, verify they're stored correctly:

```bash
# Check dev environment
gcloud secrets versions access latest \
  --secret=blog-writer-env-dev \
  --project=api-ai-blog-writer | jq '.DATAFORSEO_API_KEY, .DATAFORSEO_API_SECRET'
```

**Expected output:**
```json
"your-email@example.com"
"your-api-key-here"
```

---

## 📝 Example

If your DataForSEO credentials are:
- **Email:** `developer@tin.info`
- **API Key:** `725ec88e0afc0c905...`

Run:
```bash
./scripts/add-dataforseo-secrets.sh "developer@tin.info" "725ec88e0afc0c905..."
```

Or interactively:
```bash
./scripts/add-dataforseo-secrets.sh
# When prompted:
# DataForSEO Username/Email: developer@tin.info
# DataForSEO API Key: 725ec88e0afc0c905...
```

---

## ✅ Quick Checklist

- [ ] Have DataForSEO account email/username
- [ ] Have DataForSEO API key
- [ ] Run `./scripts/add-dataforseo-secrets.sh`
- [ ] Enter email when prompted for "Username/Email"
- [ ] Enter API key when prompted for "API Key"
- [ ] Verify secrets with `./scripts/verify-secrets-setup.sh dev`
- [ ] Redeploy service (push to `develop` branch)

---

## 🐛 Troubleshooting

### Issue: "401 Unauthorized" after adding credentials

**Check:**
1. Email is correct (no typos)
2. API key is complete (not truncated)
3. No extra spaces or newlines

**Verify:**
```bash
# Check what's stored
gcloud secrets versions access latest \
  --secret=blog-writer-env-dev \
  --project=api-ai-blog-writer | jq -r '.DATAFORSEO_API_KEY' | wc -c
# Should show length of your email

gcloud secrets versions access latest \
  --secret=blog-writer-env-dev \
  --project=api-ai-blog-writer | jq -r '.DATAFORSEO_API_SECRET' | wc -c
# Should show length of your API key
```

### Issue: "API Key" vs "API Secret" confusion

**Remember:**
- DataForSEO gives you: **Email** + **API Key**
- Our system stores: `DATAFORSEO_API_KEY` (email) + `DATAFORSEO_API_SECRET` (API key)
- The script handles this mapping automatically

---

## 📚 Related Documentation

- `GOOGLE_SECRETS_SETUP_V1.3.6.md` - Complete setup guide
- `HOW_TO_RUN_SCRIPTS.md` - How to run scripts
- `IMPLEMENT_NEXT_STEPS.md` - Step-by-step implementation

---

**Ready to add credentials?** Run:
```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr
./scripts/add-dataforseo-secrets.sh
```

