# Quick Start - Running the Scripts

**Fix for "no such file or directory" error**

---

## ✅ Correct Command

The script name is **`add-dataforseo-secrets.sh`** (not `add-d`).

### Run this command:

```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr
./scripts/add-dataforseo-secrets.sh
```

**Important:** Use the **full script name** including the `.sh` extension.

---

## 🔍 Verify Script Exists

Before running, verify the script exists:

```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr
ls -la scripts/add-dataforseo-secrets.sh
```

You should see:
```
-rwxr-xr-x ... scripts/add-dataforseo-secrets.sh
```

---

## 🚀 Complete Step-by-Step

```bash
# 1. Navigate to project directory
cd /Users/gene/Projects/api-blogwriting-python-gcr

# 2. Verify you're in the right place
pwd
# Should show: /Users/gene/Projects/api-blogwriting-python-gcr

# 3. List available scripts
ls scripts/add-*

# 4. Run the script (use FULL name)
./scripts/add-dataforseo-secrets.sh
```

---

## 💡 Tab Completion Tip

You can use **tab completion** to avoid typing the full name:

```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr
./scripts/add-data<TAB>
```

This will auto-complete to: `./scripts/add-dataforseo-secrets.sh`

---

## ❌ Common Mistakes

### Wrong: Incomplete script name
```bash
./scripts/add-d          # ❌ Missing rest of name
./scripts/add-data       # ❌ Still incomplete
```

### Right: Full script name
```bash
./scripts/add-dataforseo-secrets.sh  # ✅ Correct
```

---

## 🔧 If Script Still Doesn't Run

### Check if script is executable:
```bash
chmod +x scripts/add-dataforseo-secrets.sh
```

### Check if you're in the right directory:
```bash
pwd
# Should be: /Users/gene/Projects/api-blogwriting-python-gcr
```

### List all scripts:
```bash
ls scripts/
```

---

## 📋 All Available Scripts

```bash
# Add DataForSEO secrets
./scripts/add-dataforseo-secrets.sh

# Verify secrets setup
./scripts/verify-secrets-setup.sh dev

# Add Google Search secrets
./scripts/add-google-search-secrets.sh

# Add Stability AI secrets
./scripts/add-stability-ai-secrets.sh

# Setup AI provider secrets
./scripts/setup-ai-provider-secrets.sh
```

---

**Try again with the full script name:**
```bash
./scripts/add-dataforseo-secrets.sh
```

