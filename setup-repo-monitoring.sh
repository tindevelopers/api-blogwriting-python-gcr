#!/bin/bash

# Repository Monitoring Setup Script
# Configures GitHub CLI access and monitoring for AI Blog Writer SDKs

set -e

echo "🔧 Setting up Repository Monitoring for AI Blog Writer SDKs"
echo "============================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_REPO="tindevelopers/sdk-ai-blog-writer-python"
FRONTEND_REPO="tindevelopers/tin-ai-agents"
CONFIG_FILE="repo-monitor-config.yaml"

# Check GitHub CLI authentication
echo -e "${BLUE}📋 Checking GitHub CLI authentication...${NC}"
if ! gh auth status > /dev/null 2>&1; then
    echo -e "${RED}❌ GitHub CLI not authenticated. Please run 'gh auth login' first.${NC}"
    exit 1
fi

# Get authenticated user
GITHUB_USER=$(gh api user --jq '.login')
echo -e "${GREEN}✅ Authenticated as: ${GITHUB_USER}${NC}"

# Verify repository access
echo -e "${BLUE}🔍 Verifying repository access...${NC}"

# Check Python SDK repository
if gh repo view $PYTHON_REPO > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Access confirmed: $PYTHON_REPO${NC}"
    PYTHON_REPO_INFO=$(gh repo view $PYTHON_REPO --json name,url,defaultBranchRef,visibility,languages)
    PYTHON_DEFAULT_BRANCH=$(echo $PYTHON_REPO_INFO | jq -r '.defaultBranchRef.name')
    echo -e "   Default branch: ${PYTHON_DEFAULT_BRANCH}"
else
    echo -e "${RED}❌ Cannot access: $PYTHON_REPO${NC}"
    exit 1
fi

# Check Frontend repository
if gh repo view $FRONTEND_REPO > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Access confirmed: $FRONTEND_REPO${NC}"
    FRONTEND_REPO_INFO=$(gh repo view $FRONTEND_REPO --json name,url,defaultBranchRef,visibility,languages)
    FRONTEND_DEFAULT_BRANCH=$(echo $FRONTEND_REPO_INFO | jq -r '.defaultBranchRef.name')
    echo -e "   Default branch: ${FRONTEND_DEFAULT_BRANCH}"
else
    echo -e "${RED}❌ Cannot access: $FRONTEND_REPO${NC}"
    exit 1
fi

# Check repository permissions
echo -e "${BLUE}🔐 Checking repository permissions...${NC}"

# Check Python SDK permissions
PYTHON_PERMISSIONS=$(gh api repos/$PYTHON_REPO --jq '.permissions')
if echo $PYTHON_PERMISSIONS | jq -e '.admin or .maintain or .push' > /dev/null; then
    echo -e "${GREEN}✅ Write access confirmed: $PYTHON_REPO${NC}"
else
    echo -e "${YELLOW}⚠️  Limited access: $PYTHON_REPO (read-only)${NC}"
fi

# Check Frontend permissions
FRONTEND_PERMISSIONS=$(gh api repos/$FRONTEND_REPO --jq '.permissions')
if echo $FRONTEND_PERMISSIONS | jq -e '.admin or .maintain or .push' > /dev/null; then
    echo -e "${GREEN}✅ Write access confirmed: $FRONTEND_REPO${NC}"
else
    echo -e "${YELLOW}⚠️  Limited access: $FRONTEND_REPO (read-only)${NC}"
fi

# List current webhooks
echo -e "${BLUE}🔗 Checking existing webhooks...${NC}"

echo "Python SDK Repository Webhooks:"
PYTHON_HOOKS=$(gh api repos/$PYTHON_REPO/hooks)
if [ "$PYTHON_HOOKS" = "[]" ]; then
    echo -e "${YELLOW}   No webhooks configured${NC}"
else
    echo "$PYTHON_HOOKS" | jq -r '.[] | "   - \(.name): \(.config.url)"'
fi

echo "Frontend Repository Webhooks:"
FRONTEND_HOOKS=$(gh api repos/$FRONTEND_REPO/hooks)
if [ "$FRONTEND_HOOKS" = "[]" ]; then
    echo -e "${YELLOW}   No webhooks configured${NC}"
else
    echo "$FRONTEND_HOOKS" | jq -r '.[] | "   - \(.name): \(.config.url)"'
fi

# Get repository languages and dependencies
echo -e "${BLUE}📊 Analyzing repository dependencies...${NC}"

# Python SDK dependencies
echo "Python SDK Dependencies:"
if [ -f "pyproject.toml" ]; then
    echo -e "${GREEN}   ✅ pyproject.toml found${NC}"
    if command -v toml > /dev/null 2>&1; then
        echo "   Key dependencies:"
        grep -A 20 '\[tool.poetry.dependencies\]' pyproject.toml 2>/dev/null | grep -E '^[a-zA-Z]' | head -5 | sed 's/^/     - /'
    fi
else
    echo -e "${YELLOW}   ⚠️  pyproject.toml not found${NC}"
fi

if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}   ✅ requirements.txt found${NC}"
    echo "   Key dependencies:"
    head -5 requirements.txt | sed 's/^/     - /'
fi

# Frontend dependencies
echo "Frontend Dependencies:"
FRONTEND_PACKAGE_JSON=$(gh api repos/$FRONTEND_REPO/contents/package.json --jq '.content' | base64 -d 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✅ package.json accessible${NC}"
    echo "   Key dependencies:"
    echo "$FRONTEND_PACKAGE_JSON" | jq -r '.dependencies | to_entries | .[:5] | .[] | "     - \(.key): \(.value)"' 2>/dev/null || echo "     Unable to parse dependencies"
else
    echo -e "${YELLOW}   ⚠️  Cannot access package.json${NC}"
fi

# Create monitoring configuration summary
echo -e "${BLUE}📋 Repository Monitoring Configuration Summary${NC}"
echo "=============================================="
echo "Configuration file: $CONFIG_FILE"
echo ""
echo "Repositories to monitor:"
echo "  1. Python SDK: $PYTHON_REPO"
echo "     - Branch: $PYTHON_DEFAULT_BRANCH"
echo "     - Type: Python/FastAPI backend"
echo "     - Role: AI content generation API"
echo ""
echo "  2. Frontend: $FRONTEND_REPO"
echo "     - Branch: $FRONTEND_DEFAULT_BRANCH"
echo "     - Type: TypeScript/Next.js frontend"
echo "     - Role: AI blog writer interface"
echo ""

# Generate GitHub CLI commands for webhook setup
echo -e "${BLUE}🔧 GitHub CLI Commands for Webhook Setup${NC}"
echo "=========================================="
echo ""
echo "# To create a webhook for the Python SDK repository:"
echo "gh api repos/$PYTHON_REPO/hooks --method POST --field name=web --field active=true --field events[]=push --field events[]=pull_request --field events[]=release --field config[url]=YOUR_WEBHOOK_URL --field config[content_type]=json"
echo ""
echo "# To create a webhook for the Frontend repository:"
echo "gh api repos/$FRONTEND_REPO/hooks --method POST --field name=web --field active=true --field events[]=push --field events[]=pull_request --field events[]=release --field config[url]=YOUR_WEBHOOK_URL --field config[content_type]=json"
echo ""

# Generate repository monitoring commands
echo -e "${BLUE}📊 GitHub CLI Commands for Repository Monitoring${NC}"
echo "==============================================="
echo ""
echo "# Monitor repository activity:"
echo "gh repo view $PYTHON_REPO --web"
echo "gh repo view $FRONTEND_REPO --web"
echo ""
echo "# Check for updates:"
echo "gh api repos/$PYTHON_REPO/commits/$PYTHON_DEFAULT_BRANCH"
echo "gh api repos/$FRONTEND_REPO/commits/$FRONTEND_DEFAULT_BRANCH"
echo ""
echo "# List recent releases:"
echo "gh release list --repo $PYTHON_REPO"
echo "gh release list --repo $FRONTEND_REPO"
echo ""
echo "# Monitor pull requests:"
echo "gh pr list --repo $PYTHON_REPO"
echo "gh pr list --repo $FRONTEND_REPO"
echo ""

# Create a monitoring script
echo -e "${BLUE}📝 Creating monitoring helper script...${NC}"
cat > monitor-repos.sh << 'EOF'
#!/bin/bash

# Repository Monitoring Helper Script
# Quick commands to check repository status

PYTHON_REPO="tindevelopers/sdk-ai-blog-writer-python"
FRONTEND_REPO="tindevelopers/tin-ai-agents"

echo "🔍 AI Blog Writer SDK Repository Status"
echo "======================================"

echo "Python SDK Repository:"
echo "  Latest commit: $(gh api repos/$PYTHON_REPO/commits/main --jq '.commit.message' | head -1)"
echo "  Last updated: $(gh api repos/$PYTHON_REPO --jq '.updated_at')"
echo "  Open PRs: $(gh pr list --repo $PYTHON_REPO --json number | jq length)"

echo ""
echo "Frontend Repository:"
echo "  Latest commit: $(gh api repos/$FRONTEND_REPO/commits/master --jq '.commit.message' | head -1)"
echo "  Last updated: $(gh api repos/$FRONTEND_REPO --jq '.updated_at')"
echo "  Open PRs: $(gh pr list --repo $FRONTEND_REPO --json number | jq length)"

echo ""
echo "🔗 Quick Links:"
echo "  Python SDK: https://github.com/$PYTHON_REPO"
echo "  Frontend: https://github.com/$FRONTEND_REPO"
EOF

chmod +x monitor-repos.sh

echo -e "${GREEN}✅ Repository monitoring setup complete!${NC}"
echo ""
echo -e "${BLUE}📁 Generated files:${NC}"
echo "  - $CONFIG_FILE (monitoring configuration)"
echo "  - monitor-repos.sh (status checking script)"
echo ""
echo -e "${BLUE}🚀 Next steps:${NC}"
echo "  1. Review the configuration in $CONFIG_FILE"
echo "  2. Set up the Repository Update Management SDK"
echo "  3. Configure webhook endpoints for real-time monitoring"
echo "  4. Run ./monitor-repos.sh to check repository status"
echo ""
echo -e "${GREEN}🎉 Repository access successfully configured for both SDKs!${NC}"
