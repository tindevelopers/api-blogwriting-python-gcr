# Add Credentials to Staging and Production

**Current Status:** Only DEV has DataForSEO credentials configured.

---

## 🎯 Quick Add Credentials

### Option 1: Non-Interactive Script (Recommended)

If you have your credentials ready:

```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr

# Replace with your actual credentials
./scripts/add-dataforseo-secrets-noninteractive.sh "your-email@example.com" "your-api-key-here"
```

Or with environment variables:

```bash
DATAFORSEO_API_KEY="your-email@example.com" \
DATAFORSEO_API_SECRET="your-api-key-here" \
./scripts/add-dataforseo-secrets-noninteractive.sh
```

### Option 2: Interactive Script

```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr
./scripts/add-dataforseo-secrets.sh
```

When prompted:
1. Enter your DataForSEO Username/Email
2. Enter your DataForSEO API Key
3. For "Add to staging? (y/N)": Type `y`
4. For "Add to production? (y/N)": Type `y`

---

## ✅ Verify After Adding

```bash
# Check staging
./scripts/verify-secrets-setup.sh staging

# Check production
./scripts/verify-secrets-setup.sh prod
```

---

## 📋 What You Need

- **DataForSEO Username/Email:** Your account email (e.g., `developer@tin.info`)
- **DataForSEO API Key:** Your API key from DataForSEO dashboard

---

**Ready to add?** Run the non-interactive script with your credentials!

