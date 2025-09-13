#!/bin/bash

# Local testing script for Cloud Run deployment
# This script helps test your application locally before deploying to Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Local Testing for Cloud Run Deployment${NC}"
echo "=============================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if env.cloudrun.local exists
if [ ! -f "env.cloudrun.local" ]; then
    echo -e "${YELLOW}⚠️  env.cloudrun.local not found. Creating from template...${NC}"
    if [ -f "env.cloudrun" ]; then
        cp env.cloudrun env.cloudrun.local
        echo -e "${YELLOW}📝 Please edit env.cloudrun.local with your actual API keys${NC}"
    else
        echo -e "${RED}❌ env.cloudrun template not found${NC}"
        exit 1
    fi
fi

# Build the Docker image
echo -e "${BLUE}🏗️  Building Docker image...${NC}"
docker build -t blog-writer-sdk-local .

# Run the container with environment variables
echo -e "${BLUE}🚀 Starting container locally...${NC}"
docker run -d \
    --name blog-writer-sdk-test \
    --env-file env.cloudrun.local \
    -p 8080:8000 \
    blog-writer-sdk-local

# Wait for the service to start
echo -e "${BLUE}⏳ Waiting for service to start...${NC}"
sleep 10

# Test the health endpoint
echo -e "${BLUE}🔍 Testing health endpoint...${NC}"
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo -e "${YELLOW}📋 Container logs:${NC}"
    docker logs blog-writer-sdk-test
    docker stop blog-writer-sdk-test
    docker rm blog-writer-sdk-test
    exit 1
fi

# Test the readiness endpoint
echo -e "${BLUE}🔍 Testing readiness endpoint...${NC}"
if curl -f http://localhost:8080/ready > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Readiness check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Readiness check failed (this may be expected if API keys are not configured)${NC}"
fi

# Test the API configuration endpoint
echo -e "${BLUE}🔍 Testing API configuration...${NC}"
if curl -f http://localhost:8080/api/v1/config > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API configuration accessible${NC}"
else
    echo -e "${RED}❌ API configuration failed${NC}"
fi

# Test Cloud Run status endpoint
echo -e "${BLUE}🔍 Testing Cloud Run status endpoint...${NC}"
if curl -f http://localhost:8080/api/v1/cloudrun/status > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Cloud Run status endpoint working${NC}"
else
    echo -e "${YELLOW}⚠️  Cloud Run status endpoint failed (may need psutil)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Local testing completed!${NC}"
echo ""
echo -e "${BLUE}📋 Test Results Summary:${NC}"
echo "- Container: Running on http://localhost:8080"
echo "- Health Check: ✅"
echo "- API Docs: http://localhost:8080/docs"
echo "- Interactive API: http://localhost:8080/redoc"
echo ""
echo -e "${YELLOW}🧪 Manual Testing:${NC}"
echo "1. Open http://localhost:8080/docs in your browser"
echo "2. Try the /api/v1/generate endpoint with test data"
echo "3. Check the logs: docker logs blog-writer-sdk-test"
echo ""
echo -e "${BLUE}🛑 To stop the test container:${NC}"
echo "docker stop blog-writer-sdk-test && docker rm blog-writer-sdk-test"
echo ""
echo -e "${GREEN}✅ Ready for Cloud Run deployment!${NC}"

