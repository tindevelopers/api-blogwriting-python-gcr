## Cloud Run Region & Trigger Policy

We now deploy exclusively through Cloud Build triggers that watch our Git branches.  
Manual scripts and ad-hoc `gcloud run deploy` commands are disabled to keep all
traffic in supported regions.

### Allowed deployment paths

| Branch    | Trigger name              | Service name            | Region        |
|-----------|---------------------------|-------------------------|---------------|
| `develop` | `deploy-dev-on-develop`   | `blog-writer-api-dev`   | `europe-west9`|
| `staging` | `deploy-staging-on-staging` | `blog-writer-api-staging` | `europe-west9` |
| `main`    | `deploy-prod-on-main`     | `blog-writer-api-prod`  | `us-east1`    |

> ℹ️ The Cloud Build trigger definitions live in `trigger-*.yaml/json`.

### How to deploy

1. Push to the appropriate branch (develop/staging/main).  
2. Cloud Build builds the container and deploys to the mapped region/service.  
3. Cloud Run revision names follow the default `blog-writer-api-<env>-xxxxx` pattern.

### Manual deployments are blocked

- `deploy.sh`, `scripts/deploy.sh`, and `scripts/deploy-env.sh` now exit immediately
  with a warning.  
- `cloudbuild.yaml` validates the `_REGION` substitution and fails the build if it
  is anything other than `europe-west9` or `us-east1`.

### Triggering a redeploy manually

If you need to retrigger a build without pushing new commits, run one of:

```bash
gcloud builds triggers run deploy-dev-on-develop \
  --branch=develop --project=api-ai-blog-writer

gcloud builds triggers run deploy-staging-on-staging \
  --branch=staging --project=api-ai-blog-writer

gcloud builds triggers run deploy-prod-on-main \
  --branch=main --project=api-ai-blog-writer
```

### Verifying the active service

```bash
gcloud run services describe blog-writer-api-dev \
  --region=europe-west9 --format='value(status.url)'
```

Repeat for `blog-writer-api-staging` (europe-west9) and `blog-writer-api-prod`
(us-east1).

Keeping deployments restricted to these paths ensures we never recreate the
us-central1 service that was unintentionally provisioned before.

