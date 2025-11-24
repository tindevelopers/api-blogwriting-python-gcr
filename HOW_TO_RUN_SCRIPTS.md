# How to Run the Scripts

**Date:** 2025-11-23  
**Quick Reference Guide**

---

## 📍 Where to Run the Scripts

### Location
Run the scripts from the **project root directory**:

```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr
```

---

## ✅ Prerequisites

Before running the scripts, ensure you have:

1. **Google Cloud SDK (gcloud) installed**
   ```bash
   gcloud --version
   ```
   If not installed: https://cloud.google.com/sdk/docs/install

2. **Authenticated with Google Cloud**
   ```bash
   gcloud auth login
   gcloud config set project api-ai-blog-writer
   ```

3. **jq installed** (for JSON parsing)
   ```bash
   jq --version
   ```
   If not installed:
   ```bash
   # macOS
   brew install jq
   
   # Linux
   sudo apt-get install jq
   ```

4. **Scripts are executable**
   ```bash
   chmod +x scripts/add-dataforseo-secrets.sh
   chmod +x scripts/verify-secrets-setup.sh
   ```

---

## 🚀 Running the Scripts

### Step 1: Navigate to Project Directory

```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr
```

### Step 2: Add DataForSEO Secrets

```bash
./scripts/add-dataforseo-secrets.sh
```

**What happens:**
1:**
- Prompts for DataForSEO API Key
- Prompts for DataForSEO API Secret
- Adds credentials to dev, staging, and production secrets
- Asks for confirmation before adding to production

**Alternative ways to run:**
```bash
# With credentials as environment variables
DATAFORSEO_API_KEY="your-key" DATAFORSEO_API_SECRET="your-secret" ./scripts/add-dataforseo-secrets.sh

# With credentials as command-line arguments
./scripts/add-dataforseo-secrets.sh "your-api-key" "your-api-secret"
```

### Step 3: Verify Secrets Setup

```bash
# Verify dev environment
./scripts/verify-secrets-setup.sh dev

# Verify staging environment
./scripts/verify-secrets-setup.sh staging

# Verify production environment
./scripts/verify-secrets-setup.sh prod
```

---

## 📋 Complete Example

```bash
# 1. Navigate to project directory
cd /Users/gene/Projects/api-blogwriting-python-gcr

# 2. Verify you're authenticated
gcloud auth list
gcloud config get-value project

# 3. Add secrets (will prompt for credentials)
./scripts/add-dataforseo-secrets.sh

# 4. Verify secrets were added
./scripts/verify-secrets-setup.sh dev

# 5. Check Cloud Run logs after deployment
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=blog-writer-api-dev" \
  --limit 20 \
  --format json | jq -r '.[] | select(.textPayload | contains("secrets")) | .textPayload'
```

---

## 🔍 Troubleshooting

### Issue: "Permission denied" when running script

**Solution:**
```bash
chmod +x scripts/add-dataforseo-secrets.sh
chmod +x scripts/verify-secrets-setup.sh
```

### Issue: "gcloud: command not found"

**Solution:**
- Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
- Or use Cloud Shell in Google Cloud Console

### Issue: "jq: command not found"

**Solution:**
```bash
# macOS
brew install jq

# Linux
sudo apt-get install jq
```

### Issue: "Not authenticated"

**Solution:**
```bash
gcloud auth login
gcloud config set project api-ai-blog-writer
```

### Issue: "Secret does not exist"

**Solution:**
The script will tell you how to create it, or run:
```bash
echo '{}' | gcloud secrets create blog-writer-env-dev \
  --data-file=- \
  --project=api-ai-blog-writer
```

---

## 🌐 Alternative: Using Google Cloud Shell

If you don't have gcloud installed locally, you can use Google Cloud Shell:

1. Go to: https://console.cloud.google.com/
2. Click the Cloud Shell icon (top right)
3. Clone the repository:
   ```bash
   git clone https://github.com/tindevelopers/api-blogwriting-python-gcr.git
   cd api-blogwriting-python-gcr
   ```
4. Run the scripts:
   ```bash
   ./scripts/add-dataforseo-secrets.sh
   ```

---

## 📝 Script Locations

All scripts are in the `scripts/` directory:

- `scripts/add-dataforseo-secrets.sh` - Add DataForSEO credentials
- `scripts/verify-secrets-setup.sh` - Verify secrets configuration
- `scripts/add-google-search-secrets.sh` - Add Google Search credentials
- `scripts/add-stability-ai-secrets.sh` - Add Stability AI credentials
- `scripts/setup-ai-provider-secrets.sh` - Setup AI provider credentials

---

## ✅ Quick Check

Before running, verify everything is set up:

```bash
# Check location
pwd
# Should show: /Users/gene/Projects/api-blogwriting-python-gcr

# Check scripts exist
ls -la scripts/add-dataforseo-secrets.sh
ls -la scripts/verify-secrets-setup.sh

# Check gcloud is installed
gcloud --version

# Check authentication
gcloud auth list

# Check project
gcloud config get-value project
# Should show: api-ai-blog-writer
```

---

**Ready to run?** Start with:
```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr
./scripts/add-dataforseo-secrets.sh
```

