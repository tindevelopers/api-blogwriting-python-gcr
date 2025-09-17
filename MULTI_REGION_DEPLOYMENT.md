# 🌍 Multi-Region Deployment Guide

## Overview

The API AI Blog Writer now supports **multi-region deployment** optimized for European development and global production.

## 🎯 Deployment Strategy

### **Development Environment** 
- **Region**: `europe-west9` (Paris)
- **Service**: `api-ai-blog-writer-dev`
- **URL**: `https://api-ai-blog-writer-dev-xxx-ew9.a.run.app`
- **Purpose**: Fast development for European users (~20ms latency)

### **Staging Environment**
- **Region**: `us-east1` (US-East-1) 
- **Service**: `api-ai-blog-writer-staging`
- **URL**: `https://api-ai-blog-writer-staging-xxx-ue.a.run.app`
- **Purpose**: Test global performance before production

### **Production Environment**
- **Region**: `us-east1` (US-East-1)
- **Service**: `api-ai-blog-writer`
- **URL**: `https://api-ai-blog-writer-xxx-ue.a.run.app`
- **Purpose**: Global production deployment

## 🚀 Quick Deployment

```bash
# Deploy to development (Paris)
./scripts/deploy-simple.sh dev

# Deploy to staging (US-East-1)
./scripts/deploy-simple.sh staging

# Deploy to production (US-East-1)
./scripts/deploy-simple.sh prod
```

## 📊 Performance Benefits

| Environment | Region | Latency (Europe) | Latency (Global) | Development Speed |
|-------------|--------|------------------|------------------|-------------------|
| **Dev**     | Paris  | ~20ms           | ~150ms          | ⚡ Fast          |
| **Staging** | US-East-1 | ~150ms       | ~50ms           | 🧪 Test Global   |
| **Prod**    | US-East-1 | ~150ms       | ~50ms           | 🌍 Global        |

## 🔧 Configuration Files Updated

- ✅ `cloudbuild.yaml` - Updated service name and region
- ✅ `cloudbuild-multi-env.yaml` - Multi-environment support
- ✅ `scripts/deploy-simple.sh` - Environment-specific regions
- ✅ `service.yaml` - Updated service name
- ✅ `region-config.yaml` - New configuration reference

## 🎯 Key Changes Made

1. **Service Naming**: `blog-writer-sdk` → `api-ai-blog-writer`
2. **Region Strategy**: Dev in Paris, Staging/Prod in US-East-1
3. **Environment Suffixes**: 
   - Dev: `-dev`
   - Staging: `-staging` 
   - Prod: No suffix (clean main URL)
4. **Project ID**: Updated to `api-ai-blog-writer`

## 🧪 Testing Your Deployment

```bash
# Test development environment
curl https://api-ai-blog-writer-dev-xxx-ew9.a.run.app/health

# Test staging environment  
curl https://api-ai-blog-writer-staging-xxx-ue.a.run.app/health

# Test production environment
curl https://api-ai-blog-writer-xxx-ue.a.run.app/health
```

## 📋 Next Steps

1. **Configure Environment Variables**: Update `env.dev`, `env.staging`, `env.prod`
2. **Deploy Development**: `./scripts/deploy-simple.sh dev`
3. **Test Staging**: `./scripts/deploy-simple.sh staging`
4. **Deploy Production**: `./scripts/deploy-simple.sh prod`

## 🎉 Benefits Achieved

- ⚡ **Fast European Development**: Paris region for low latency
- 🌍 **Global Production**: US-East-1 for worldwide performance
- 🏷️ **Professional Branding**: Clean `api-ai-blog-writer` naming
- 🧪 **Accurate Testing**: Staging matches production region
- 💰 **Cost Optimization**: Environment-specific resource allocation
