# Fix: Multiple Triggers Firing on Single Push

## 🔍 Root Cause Identified

**Problem:** All 3 Cloud Build triggers are configured with `branch pattern = null`, which means they match **ALL BRANCHES**.

When you push to `develop`, all 3 triggers fire:
- ✅ `develop` trigger (should fire)
- ❌ `staging` trigger (should NOT fire)
- ❌ `main` trigger (should NOT fire)

## 📊 Current Trigger Configuration

| Trigger Name | Region | Branch Pattern | Status |
|-------------|--------|----------------|--------|
| `develop` | `europe-west9` | `null` (ALL BRANCHES) ❌ | Enabled |
| `staging` | `europe-west9` | `null` (ALL BRANCHES) ❌ | Enabled |
| `main` | `us-east1` | `null` (ALL BRANCHES) ❌ | Enabled |

## ✅ Solution: Fix Branch Patterns

### Option 1: Cloud Console (Recommended)

1. **Go to Cloud Build Triggers:**
   ```
   https://console.cloud.google.com/cloud-build/triggers?project=api-ai-blog-writer
   ```

2. **For each trigger, click Edit and set the branch pattern:**

   **`develop` trigger:**
   - Event: Push to a branch
   - Branch: `^develop$` (regex pattern)
   - Save

   **`staging` trigger:**
   - Event: Push to a branch
   - Branch: `^staging$` (regex pattern)
   - Save

   **`main` trigger:**
   - Event: Push to a branch
   - Branch: `^main$` (regex pattern)
   - Save

### Option 2: Export/Import via YAML

1. **Export current trigger:**
   ```bash
   gcloud builds triggers export develop \
     --region=europe-west9 \
     --project=api-ai-blog-writer \
     --destination=trigger-develop.yaml
   ```

2. **Edit `trigger-develop.yaml`:**
   ```yaml
   github:
     push:
       branch: '^develop$'  # Add this line
   ```

3. **Update trigger:**
   ```bash
   gcloud builds triggers import \
     --source=trigger-develop.yaml \
     --region=europe-west9 \
     --project=api-ai-blog-writer
   ```

## 🎯 Expected Behavior After Fix

| Branch Pushed | Triggers That Fire |
|---------------|-------------------|
| `develop` | ✅ `develop` only |
| `staging` | ✅ `staging` only |
| `main` | ✅ `main` only |

## ✅ Verification

After fixing, verify with:
```bash
gcloud builds triggers list --project=api-ai-blog-writer \
  --format="table(name,location,github.push.branch,disabled)"
```

All triggers should show their specific branch pattern (not `null`).

## 📝 Notes

- Branch patterns use regex syntax
- `^develop$` means "exactly matches 'develop'"
- `^develop.*` would match "develop", "develop-feature", etc.
- `null` or empty means "matches all branches"


