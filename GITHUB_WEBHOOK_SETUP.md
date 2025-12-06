# GitHub Webhook Setup for Google Cloud Build

**Date:** 2025-01-23  
**Purpose:** Configure GitHub webhook to trigger Cloud Build automatically

---

## Overview

Google Cloud Build triggers can work in two ways:
1. **GitHub App Integration** (Recommended) - Automatic webhook setup
2. **Manual Webhook** - Configure webhook URL manually

---

## Method 1: GitHub App Integration (Recommended)

When you connect a repository via Cloud Build Console, Google automatically sets up the webhook. This is the recommended approach.

### Steps:

1. **Go to Cloud Build Console:**
   - Navigate to: https://console.cloud.google.com/cloud-build/triggers?project=api-ai-blog-writer
   - Click **"Connect repository"** or **"Manage repositories"**

2. **Connect GitHub Repository:**
   - Select **GitHub (Cloud Build GitHub App)**
   - Authorize Google Cloud Build to access your GitHub account
   - Select repository: `tindevelopers/api-blogwriting-python-gcr`
   - Grant necessary permissions

3. **Verify Connection:**
   - The webhook will be automatically configured
   - Check GitHub: Repository → Settings → Webhooks
   - You should see a webhook from `cloudbuild.googleapis.com`

---

## Method 2: Manual Webhook Configuration

If you need to configure the webhook manually:

### Webhook URL Format:

```
https://cloudbuild.googleapis.com/v1/webhooks?key=WEBHOOK_KEY
```

### Steps:

1. **Get Webhook Key from Cloud Build Trigger:**
   - Go to Cloud Build Console → Triggers
   - Click on the `develop` trigger
   - Look for "Webhook URL" or "Webhook key"
   - Copy the webhook URL or key

2. **Configure in GitHub:**
   - Go to: https://github.com/tindevelopers/api-blogwriting-python-gcr/settings/hooks
   - Click **"Add webhook"**
   - **Payload URL:** `https://cloudbuild.googleapis.com/v1/webhooks?key=YOUR_WEBHOOK_KEY`
   - **Content type:** `application/json`
   - **Secret:** (Leave empty or use the secret from Cloud Build trigger)
   - **Which events:** Select "Just the push event" or "Let me select individual events"
     - ✅ Push
     - ✅ Pull request (if needed)
   - **Active:** ✅ Checked
   - Click **"Add webhook"**

3. **Verify Webhook:**
   - GitHub will send a test ping
   - Check webhook delivery logs in GitHub
   - Should show successful delivery

---

## Current Trigger Configuration

Based on the UI, your triggers are configured as:

### Develop Trigger:
- **Name:** `develop`
- **Region:** `europe-west9`
- **Repository:** `tindevelopers/api-blogwriting-python-gcr`
- **Event:** Push to branch
- **Branch Pattern:** Should match `develop` or `^develop$`
- **Config:** `cloudbuild.yaml`
- **Substitution Variables:**
  - `_REGION=europe-west9`
  - `_ENV=dev`
  - `_SERVICE_NAME=blog-writer-api-dev`

---

## Troubleshooting

### If Webhook Isn't Firing:

1. **Check GitHub Webhook Delivery:**
   - Go to: https://github.com/tindevelopers/api-blogwriting-python-gcr/settings/hooks
   - Click on the webhook
   - Check "Recent Deliveries" tab
   - Look for errors or failed deliveries

2. **Verify Branch Pattern:**
   - In Cloud Build trigger, ensure branch pattern matches exactly
   - Pattern `^develop$` matches only `develop` branch
   - Pattern `develop` matches any branch containing "develop"

3. **Check Trigger Status:**
   - Ensure trigger is **Enabled** (not disabled)
   - Verify repository connection is active

4. **Test Manually:**
   - Click "Run" button on the trigger in Cloud Build Console
   - This will test if the trigger configuration is correct

5. **Check Permissions:**
   - Ensure Cloud Build service account has necessary permissions
   - Verify GitHub App has access to the repository

---

## Webhook Payload Format

GitHub sends webhook payloads in this format:

```json
{
  "ref": "refs/heads/develop",
  "repository": {
    "full_name": "tindevelopers/api-blogwriting-python-gcr"
  },
  "pusher": {
    "name": "username"
  },
  "commits": [...]
}
```

Cloud Build uses the `ref` field to match against the branch pattern.

---

## Quick Check Commands

### Check if webhook exists in GitHub:
```bash
# Via GitHub API (requires token)
curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/tindevelopers/api-blogwriting-python-gcr/hooks
```

### Check Cloud Build trigger webhook URL:
```bash
gcloud builds triggers describe develop \
  --project=api-ai-blog-writer \
  --format="value(webhookConfig.url)"
```

---

## Next Steps

1. ✅ Verify webhook exists in GitHub repository settings
2. ✅ Check webhook delivery logs for errors
3. ✅ Test trigger manually via "Run" button
4. ✅ Push a small change to verify automatic triggering
5. ✅ Monitor Cloud Build for automatic builds

---

## References

- [Cloud Build GitHub Triggers](https://cloud.google.com/build/docs/triggers)
- [GitHub Webhooks Documentation](https://docs.github.com/en/webhooks)
- [Cloud Build GitHub App](https://cloud.google.com/build/docs/automate-builds-github)

