# Exact Method to Recreate Cloud Build Triggers

## Prerequisites
- Access to Google Cloud Console
- GitHub account with access to `tindevelopers/api-blogwriting-python-gcr` repository
- Cloud Build API enabled in project `api-ai-blog-writer`

## Step-by-Step Instructions

### Step 1: Open Cloud Build Triggers Page
1. Go to: https://console.cloud.google.com/cloud-build/triggers?project=api-ai-blog-writer
2. Click the **"+ CREATE TRIGGER"** button at the top

### Step 2: Connect GitHub Repository (if not already connected)

**If you see "Connect Repository" button:**
1. Click **"Connect Repository"**
2. Select **"GitHub (Cloud Build GitHub App)"**
3. Click **"Continue"**
4. Authenticate with GitHub:
   - You'll be redirected to GitHub
   - Click **"Authorize Google Cloud Build"**
   - Select the organization/account: `tindevelopers`
   - Grant access to the repository: `api-blogwriting-python-gcr`
   - Click **"Install"** or **"Approve"**
5. Return to Cloud Console
6. Select repository: `tindevelopers/api-blogwriting-python-gcr`
7. Click **"Connect"**

**If repository is already connected:**
- Skip to Step 3

### Step 3: Configure Trigger

**Basic Settings:**
- **Name:** `deploy-dev-on-develop`
- **" **Push to a branch**

**Source:**
- **Repository:** Select `tindevelopers/api-blogwriting-python-gcr` (from dropdown)
- **Branch:** Enter `^develop$` (regex pattern - matches exactly "develop"develop"$ branch)

**Configuration:**
- Select: **"Cloud Build configuration file (yaml or json)"**
- **Location:** `cloudbuild.yaml`

**Substitution variables:**
Click **"Add substitution variable"** and add these THREE variables:

1. **Variable name:** `_REGION`
   **Value:** `europe-west9`

2. **Variable name:** `_ENV`
   **Value:** `dev`

3. **Variable name:** `_SERVICE_NAME`
   **Value:** `blog-writer-api-dev`

**Service account:**
- Use default Cloud Build service account (leave as default)

### Step 4: Create Trigger
1. Click **"CREATE"** button at the bottom
2. Wait for confirmation message

### Step 5: Verify Trigger

Run this command to verify:
```bash
gcloud builds triggers list --project=api-ai-blog-writer
```

You should see:
```
NAME                    ID                                    DISABLED  REPO_NAME
deploy-dev-on-develop   <trigger-id>                         False     tindevelopers/api-blogwriting-python-gcr
```

### Step 6: Test Trigger

1. Make a small change to any file (or create a test file):
   ```bash
   echo "# Test trigger $(date)" >> .trigger-test
   git add .trigger-test
   git commit -m "test: Verify trigger works"
   git push origin develop
   ```

2. Check Cloud Build console for new build:
   ```bash
   gcloud builds list --project=api-ai-blog-writer --limit=1
   ```

3. Verify build has `BUILD_TRIGGER_ID` set (not null)

## Troubleshooting

### If "Connect Repository" doesn't appear:
- GitHub connection may already exist
- Check if repository appears in the dropdown
- If not, you may need to reconnect via: https://console.cloud.google.com/cloud-build/triggers?project=api-ai-blog-writer

### If trigger creation fails:
1. Verify Cloud Build API is enabled:
   ```bash
   gcloud services enable cloudbuild.googleapis.com --project=api-ai-blog-writer
   ```

2. Check IAM permissions:
   - Ensure your account has `roles/cloudbuild.builds.editor` role
   - Or `roles/owner` role

3. Verify GitHub App is installed:
   - Go to GitHub Settings → Applications → Authorized OAuth Apps
   - Look for "Google Cloud Build"
   - Ensure it has access to `tindevelopers/api-blogwriting-python-gcr`

### If builds fail after trigger creation:
1. Check build logs:
   ```bash
   gcloud builds log <BUILD_ID> --project=api-ai-blog-writer
   ```

2. Verify substitution variables are correct:
   - `_REGION` = `europe-west9`
   - `_ENV` = `dev`
   - `_SERVICE_NAME` = `blog-writer-api-dev`

3. Verify `cloudbuild.yaml` exists in repository root

## Quick Reference

**Trigger Name:** `deploy-dev-on-develop`
**Repository:** `tindevelopers/api-blogwriting-python-gcr`
**Branch Pattern:** `^develop$`
**Config File:** `cloudbuild.yaml`
**Substitutions:**
- `_REGION` = `europe-west9`
- `_ENV` = `dev`
- `_SERVICE_NAME` = `blog-writer-api-dev`

## Verification Checklist

After creating trigger, verify:
- [ ] Trigger appears in `gcloud builds triggers list`
- [ ] Trigger is enabled (not disabled)
- [ ] Repository is connected correctly
- [ ] Branch pattern is `^develop$`
- [ ] All three substitution variables are set
- [ ] Push to `develop` triggers a build
- [ ] Build has `BUILD_TRIGGER_ID` set
- [ ] Build passes safeguard check
- [ ] Build deploys successfully to Cloud Run

