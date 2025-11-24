# Cloud Build Trigger Setup Instructions

## Current Status

✅ **Cloud Run Service:** HEALTHY and RUNNING
- Service: `blog-writer-api-dev`
- Region: `europe-west9`
- Latest Revision: `blog-writer-api-dev-00130-crz` (Active & Healthy)
- URL: https://blog-writer-api-dev-613248238610.europe-west9.run.app
- IAM: Public access enabled (allUsers can invoke)

❌ **Cloud Build Trigger:** NOT CONFIGURED
- No trigger exists for automatic deployments
- Manual trigger creation via CLI failed (requires GitHub connection setup)

## Issue Analysis

1. **Cloud Run is working correctly** - Latest revision deployed successfully
2. **Trigger creation via CLI failed** - GitHub connection must be set up first via Cloud Console
3. **Previous failed revisions** - Some revisions (00122-00126) failed startup probes, but latest is healthy

## Solution: Create Trigger via Cloud Console

Since CLI creation requires GitHub connection setup, use Cloud Console:

### Step-by-Step Instructions

1. **Open Cloud Build Triggers:**
   ```
   https://console.cloud.google.com/cloud-build/triggers/add?project=api-ai-blog-writer
   ```

2. **Connect GitHub Repository (if not already connected):**
   - Click "Connect Repository"
   - Select "GitHub (Cloud Build GitHub App)"
   - Authenticate with GitHub
   - Select repository: `tindevelopers/api-blogwriting-python-gcr`
   - Click "Connect"

3. **Create Trigger:**
   - **Name:** `deploy-dev-on-develop`
   - **Event:** Push to a branch
   - **Source:** Select the connected repository (`tindevelopers/api-blogwriting-python-gcr`)
   - **Branch:** `^develop$` (regex pattern)
   - **Configuration:** Cloud Build configuration file (yaml or json)
   - **Location:** `cloudbuild.yaml`
   - **Substitution variables:**
     - Click "Add substitution variable"
     - Add three variables:
       - `_REGION` = `europe-west9`
       - `_ENV` = `dev`
       - `_SERVICE_NAME` = `blog-writer-api-dev`
   - **Service account:** Use default Cloud Build service account
   - Click "Create"

4. **Verify Trigger:**
   ```bash
   gcloud builds triggers list --project=api-ai-blog-writer
   ```

5. **Test Trigger:**
   - Push a commit to `develop` branch
   - Check Cloud Build console for new build
   - Verify build has `BUILD_TRIGGER_ID` set
   - Verify deployment succeeds

## Verification Checklist

After creating the trigger:

- [ ] Trigger appears in `gcloud builds triggers list`
- [ ] Trigger is enabled (not disabled)
- [ ] Push to `develop` branch triggers a build
- [ ] Build has `BUILD_TRIGGER_ID` set (not null)
- [ ] Build passes safeguard check
- [ ] Build completes successfully
- [ ] Cloud Run service receives new revision

## Troubleshooting

### If trigger creation fails:
1. Ensure GitHub repository is connected
2. Verify Cloud Build API is enabled
3. Check IAM permissions for Cloud Build service account
4. Verify branch pattern matches (`^develop$`)

### If builds fail:
1. Check build logs: `gcloud builds log <BUILD_ID> --project=api-ai-blog-writer`
2. Verify substitution variables are set correctly
3. Check Cloud Run service logs for deployment issues

## Current Service Status

- **Service URL:** https://blog-writer-api-dev-613248238610.europe-west9.run.app
- **Health Endpoint:** https://blog-writer-api-dev-613248238610.europe-west9.run.app/health
- **Status:** ✅ Healthy and serving traffic
- **Latest Deployment:** 2025-11-22T13:53:27Z

