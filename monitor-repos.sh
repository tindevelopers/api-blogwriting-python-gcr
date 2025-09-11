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
