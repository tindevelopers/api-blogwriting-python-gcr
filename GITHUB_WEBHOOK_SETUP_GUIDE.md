# GitHub Webhook Setup Guide for Cloud Build

## ⚠️ IMPORTANT NOTE

**Cloud Build GitHub App connections automatically manage webhooks.**  
You typically **DO NOT** need to manually create webhooks for Cloud Build triggers.

However, if webhooks are missing or not firing, follow these steps:

## 🔍 Step 1: Verify Webhook Exists

### Using GitHub CLI
```bash
# List all webhooks
gh api repos/tindevelopers/api-blogwriting-python-gcr/hooks

# Check for Cloud Build webhooks
gh api repos/tindevelopers/api-blogwriting-python-gcr/hooks \
  --jq '.[] | select(.config.url | contains("cloudbuild") or contains("googleapis"))'
```

### Using GitHub Web Interface
1. Go to: https://github.com/tindevelopers/api-blogwriting-python-gcr/settings/hooks
2. Look for webhook from Google Cloud Build
3. Check if it's active and has recent deliveries

## 🔧 Step 2: Fix Webhook Issues

### Option A: Reconnect Repository (Recommended)
**This automatically recreates the webhook:**

1. Go to Cloud Console: https://console.cloud.google.com/cloud-build/triggers?project=api-ai-blog-writer
2. **IMPORTANT**: Select region `europe-west9` (top right dropdown)
3. Click on trigger `develop`
4. Click **"Edit"**
5. Under **"Source"** section:
   - Check repository connection status
   - If shows error or "Not Connected":
     - Click **"Reconnect"** or **"Connect Repository"**
     - Select `tindevelopers/api-blogwriting-python-gcr`
     - Authorize GitHub App if needed
6. Click **"Save"**
7. This will automatically recreate the webhook

### Option B: Verify GitHub App Installation
1. Go to GitHub: https://github.com/settings/installations
2. Find "Google Cloud Build" app
3. Verify it has access to `tindevelopers/api-blogwriting-python-gcr`
4. If missing, reconnect repository in Cloud Console

## 🔍 Step 3: Check Webhook Deliveries

### Using GitHub CLI
```bash
# Get webhook ID first
WEBHOOK_ID=$(gh api repos/tindevelopers/api-blogwriting-python-gcr/hooks \
  --jq '.[] | select(.config.url | contains("cloudbuild")) | .id' | head -1)

# Check recent deliveries
gh api repos/tindevelopers/api-blogwriting-python-gcr/hooks/$WEBHOOK_ID/deliveries \
  --jq '.[] | {id: .id, status: .status_code, event: .event, delivered_at: .delivered_at}' \
  | head -20
```

### Using GitHub Web Interface
1. Go to: https://github.com/tindevelopers/api-blogwriting-python-gcr/settings/hooks
2. Click on Cloud Build webhook
3. Scroll to "Recent Deliveries"
4. Check if recent `push` events show:
   - ✅ Green checkmark (200 status) = Success
   - ❌ Red X (4xx/5xx) = Failure
   - ⚠️ Yellow warning = Pending/Timeout

## 🧪 Step 4: Test Webhook

### Test Manual Trigger (Verify Configuration)
```bash
gcloud builds triggers run 5cabcb18-791d-4082-8871-d7b2c027be27 \
  --project=api-ai-blog-writer \
  --region=europe-west9 \
  --branch=develop
```

### Test Automatic Trigger (Verify Webhook)
1. Make a small change:
   change to `develop` branch:
```bash
echo "# Test webhook" >> README.md
git add README.md
git commit -m "test: Verify webhook firing"
git push origin develop
```

2. Monitor Cloud Build:
```bash
# Watch for new builds
watch -n 5 'gcloud builds list --project=api-ai-blog-writer --limit=1 --format="table(id,status,createTime,buildTriggerId)"'
```

3. Verify:
   - Build appears within 1-2 minutes
   - Build has `BUILD_TRIGGER_ID` set (not null)
   - Build passes safeguard check

## 🚨 Troubleshooting

### Issue: Webhook Not Found
**Solution**: Reconnect repository in Cloud Console (Option A above)

### Issue: Webhook Exists But Not Firing
**Possible Causes**:
1. **GitHub App not installed**: Reinstall in Cloud Console
2. **Repository access revoked**: Reconnect repository
3. **Webhook disabled**: Enable in GitHub webhook settings
4. **Branch filter**: Verify branch pattern matches (`^develop$`)

**Solution**: 
- Check webhook deliveries in GitHub
- Look for error messages
- Reconnect repository if needed

### Issue: Webhook Firing But Builds Not Starting
**Possible Causes**:
1. Trigger disabled
2. Branch pattern mismatch
3. Substitution variables missing

**Solution**: Verify trigger configuration:
```bash
gcloud builds triggers describe 5cabcb18-791d-4082-8871-d7b2c027be27 \
  --project=api-ai-blog-writer \
  --region=europe-west9 \
  --format="yaml"
```

## 📋 Verification Checklist

- [ ] Webhook exists in GitHub repository
- [ ] Webhook is active (not disabled)
- [ ] Recent deliveries show successful (200 status)
- [ ] GitHub App has repository access
- [ ] Cloud Build connection shows as "Connected"
- [ ] Manual trigger run succeeds
- [ ] Push to `develop` triggers automatic build
- [ ] Build has `BUILD_TRIGGER_ID` set
- [ ] Deployment succeeds

## 🎯 Expected Webhook Configuration

**Webhook URL**: Managed by Cloud Build (automatically created)  
**Content Type**: `application/json`  
**Events**: `push` (for branch pushes)  
**Secret**: Managed by Cloud Build GitHub App  
**Active**: `true`

## 📚 Additional Resources

- Cloud Build GitHub App: https://github.com/apps/google-cloud-build
- Cloud Build Triggers: https://console.cloud.google.com/cloud-build/triggers
- GitHub Webhooks API: https://docs.github.com/en/rest/webhooks

---

**Note**: Cloud Build manages webhooks automatically through the GitHub App. Manual webhook creation is **NOT recommended** and may cause conflicts. Always use Cloud Console to reconnect repositories if webhooks are missing.
