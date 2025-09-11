# 🚀 GitHub Actions CI/CD Setup

This repository includes automated CI/CD pipelines using GitHub Actions.

## 📋 Workflows

### 1. **CI Pipeline** (`.github/workflows/ci.yml`)
Runs on every pull request and push to `main`:

- **Testing**: Multi-version Python testing (3.11, 3.12)
- **Linting**: Code quality checks with flake8
- **Type Checking**: Static analysis with mypy
- **Security**: Vulnerability scanning with safety and bandit
- **Docker**: Build verification
- **Coverage**: Code coverage reporting

### 2. **Railway Deployment** (`.github/workflows/deploy.yml`)
Automatically deploys to Railway when code is pushed to `main`:

- **Conditional**: Only runs after CI passes
- **Health Checks**: Verifies deployment success
- **Notifications**: Success/failure reporting

## 🔧 Setup Requirements

### Railway Token
To enable automatic deployment, add your Railway token as a GitHub secret:

1. **Get Railway Token**:
   ```bash
   railway login
   railway auth
   ```

2. **Add GitHub Secret**:
   - Go to: `Settings` → `Secrets and variables` → `Actions`
   - Add new secret: `RAILWAY_TOKEN`
   - Paste your Railway token

### Environment Variables
The deployment workflow will use Railway's environment variables. Make sure these are set in your Railway project:

```bash
# Core API Settings
PORT=8000
HOST=0.0.0.0
DEBUG=false
API_TITLE=Blog Writer SDK API
API_VERSION=0.1.0

# Optional: AI Provider Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Optional: DataForSEO Integration
DATAFORSEO_API_KEY=your_key_here
DATAFORSEO_API_SECRET=your_secret_here
```

## 🎯 Workflow Triggers

### Automatic Triggers
- **CI**: Every push and pull request
- **Deploy**: Every push to `main` branch (after CI passes)

### Manual Triggers
- **Deploy**: Can be triggered manually from GitHub Actions tab

## 📊 Status Badges

Add these to your README.md:

```markdown
![CI](https://github.com/tindevelopers/sdk-ai-blog-writer-python/workflows/CI%2FCD%20Pipeline/badge.svg)
![Deploy](https://github.com/tindevelopers/sdk-ai-blog-writer-python/workflows/Deploy%20to%20Railway/badge.svg)
```

## 🔍 Monitoring

- **GitHub Actions**: View workflow runs in the "Actions" tab
- **Railway**: Monitor deployments in Railway dashboard
- **Health Checks**: Automatic endpoint verification post-deployment

## 🛠️ Local Development

Run the same checks locally:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 src/

# Run type checking
mypy src/

# Run security scan
safety check
bandit -r src/
```
