# 🐳 Multi-Language SDK Dockerization Guide

## Overview
This guide shows how to dockerize SDKs in different languages and deploy them consistently across platforms like Google Cloud Run, DigitalOcean, AWS, etc.

## 🚀 TypeScript/Node.js SDK Dockerization

### Example: AI Content Publisher SDK (TypeScript)

#### Dockerfile for TypeScript SDK
```dockerfile
# Use Node.js LTS
FROM node:18-alpine

# Set environment variables
ENV NODE_ENV=production \
    PORT=3000

# Set work directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY src/ ./src/
COPY dist/ ./dist/

# If you need to build TypeScript
# RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Change ownership
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Start the application
CMD ["node", "dist/index.js"]
```

#### Alternative: Build TypeScript in Docker
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json tsconfig.json ./
RUN npm ci

COPY src/ ./src/
RUN npm run build

# Production stage
FROM node:18-alpine AS production

ENV NODE_ENV=production PORT=3000
WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

COPY --from=builder /app/dist ./dist

RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001
RUN chown -R nextjs:nodejs /app
USER nextjs

EXPOSE $PORT
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

CMD ["node", "dist/index.js"]
```

## 🐍 Python SDK Dockerization (Current Example)

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

COPY . .

RUN adduser --disabled-password --gecos '' --uid 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE $PORT
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## ☕ Java SDK Dockerization

```dockerfile
FROM openjdk:17-jdk-alpine AS builder

WORKDIR /app
COPY pom.xml ./
COPY src ./src

RUN ./mvnw clean package -DskipTests

# Production stage
FROM openjdk:17-jre-alpine

ENV PORT=8080
WORKDIR /app

COPY --from=builder /app/target/*.jar app.jar

RUN addgroup -g 1001 -S spring && \
    adduser -S spring -u 1001
RUN chown -R spring:spring /app
USER spring

EXPOSE $PORT
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:$PORT/actuator/health || exit 1

CMD ["java", "-jar", "app.jar"]
```

## 🐹 Go SDK Dockerization

```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Production stage
FROM alpine:latest

ENV PORT=8080
WORKDIR /root/

RUN apk --no-cache add ca-certificates curl
COPY --from=builder /app/main .

RUN adduser -D -s /bin/sh appuser
USER appuser

EXPOSE $PORT
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

CMD ["./main"]
```

## 🔧 Universal Docker Compose for Multiple SDKs

### docker-compose.yml for Multi-SDK Deployment
```yaml
version: '3.8'

services:
  # Python Blog Writer SDK
  blog-writer-sdk:
    build: 
      context: ./blog-writer-python
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - DEBUG=false
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    networks:
      - sdk-network
    restart: unless-stopped

  # TypeScript Content Publisher SDK
  content-publisher-sdk:
    build:
      context: ./content-publisher-typescript
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - PORT=3000
      - NODE_ENV=production
      - STRAPI_API_URL=${STRAPI_API_URL}
    networks:
      - sdk-network
    restart: unless-stopped

  # Java Analytics SDK (example)
  analytics-sdk:
    build:
      context: ./analytics-java
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - PORT=8080
      - SPRING_PROFILES_ACTIVE=production
    networks:
      - sdk-network
    restart: unless-stopped

  # Go Media Processing SDK (example)
  media-sdk:
    build:
      context: ./media-go
      dockerfile: Dockerfile
    ports:
      - "9000:9000"
    environment:
      - PORT=9000
      - GIN_MODE=release
    networks:
      - sdk-network
    restart: unless-stopped

  # Nginx API Gateway (optional)
  api-gateway:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - blog-writer-sdk
      - content-publisher-sdk
      - analytics-sdk
      - media-sdk
    networks:
      - sdk-network
    restart: unless-stopped

networks:
  sdk-network:
    driver: bridge

volumes:
  sdk-data:
```

## 🌐 Nginx Configuration for API Gateway
```nginx
events {
    worker_connections 1024;
}

http {
    upstream blog-writer {
        server blog-writer-sdk:8000;
    }
    
    upstream content-publisher {
        server content-publisher-sdk:3000;
    }
    
    upstream analytics {
        server analytics-sdk:8080;
    }
    
    upstream media {
        server media-sdk:9000;
    }

    server {
        listen 80;
        server_name localhost;

        # Blog Writer SDK
        location /api/blog/ {
            proxy_pass http://blog-writer/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Content Publisher SDK
        location /api/publisher/ {
            proxy_pass http://content-publisher/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Analytics SDK
        location /api/analytics/ {
            proxy_pass http://analytics/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Media SDK
        location /api/media/ {
            proxy_pass http://media/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Health check endpoint
        location /health {
            return 200 'OK';
            add_header Content-Type text/plain;
        }
    }
}
```

## 🚀 Deployment Strategies

### 1. Google Cloud Run Deployment (Individual Services)
Each SDK can be deployed as a separate Google Cloud Run service:

```bash
# Deploy each SDK separately
cd blog-writer-python && gcloud run deploy blog-writer-python --source .
cd ../content-publisher-typescript && gcloud run deploy content-publisher-typescript --source .
cd ../analytics-java && gcloud run deploy analytics-java --source .
```

### 2. DigitalOcean App Platform
```yaml
# .do/app.yaml
name: multi-sdk-platform
services:
- name: blog-writer
  source_dir: /blog-writer-python
  github:
    repo: your-username/your-repo
    branch: main
  run_command: python -m uvicorn main:app --host 0.0.0.0 --port 8080
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  
- name: content-publisher
  source_dir: /content-publisher-typescript
  github:
    repo: your-username/your-repo
    branch: main
  run_command: npm start
  environment_slug: node-js
  instance_count: 1
  instance_size_slug: basic-xxs
```

### 3. AWS ECS/Fargate
```yaml
# docker-compose.aws.yml
version: '3.8'
services:
  blog-writer:
    image: your-registry/blog-writer:latest
    ports:
      - "8000:8000"
    logging:
      driver: awslogs
      options:
        awslogs-group: /ecs/blog-writer
        awslogs-region: us-east-1
        
  content-publisher:
    image: your-registry/content-publisher:latest
    ports:
      - "3000:3000"
    logging:
      driver: awslogs
      options:
        awslogs-group: /ecs/content-publisher
        awslogs-region: us-east-1
```

### 4. Kubernetes Deployment
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blog-writer-sdk
spec:
  replicas: 3
  selector:
    matchLabels:
      app: blog-writer-sdk
  template:
    metadata:
      labels:
        app: blog-writer-sdk
    spec:
      containers:
      - name: blog-writer
        image: your-registry/blog-writer:latest
        ports:
        - containerPort: 8000
        env:
        - name: PORT
          value: "8000"
---
apiVersion: v1
kind: Service
metadata:
  name: blog-writer-service
spec:
  selector:
    app: blog-writer-sdk
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 📦 Container Registry Strategy

### 1. GitHub Container Registry
```bash
# Build and push to GitHub
docker build -t ghcr.io/your-username/blog-writer-sdk:latest .
docker push ghcr.io/your-username/blog-writer-sdk:latest
```

### 2. Docker Hub
```bash
# Build and push to Docker Hub
docker build -t your-username/blog-writer-sdk:latest .
docker push your-username/blog-writer-sdk:latest
```

### 3. AWS ECR
```bash
# Build and push to AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker build -t blog-writer-sdk .
docker tag blog-writer-sdk:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/blog-writer-sdk:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/blog-writer-sdk:latest
```

## 🔧 Development Workflow

### 1. Local Development
```bash
# Start all SDKs locally
docker-compose up -d

# View logs
docker-compose logs -f blog-writer-sdk

# Scale services
docker-compose up -d --scale blog-writer-sdk=3
```

### 2. CI/CD Pipeline (GitHub Actions)
```yaml
# .github/workflows/deploy-sdks.yml
name: Deploy SDKs
on:
  push:
    branches: [main]

jobs:
  deploy-blog-writer:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build and Deploy Blog Writer
      run: |
        cd blog-writer-python
        docker build -t blog-writer:${{ github.sha }} .
        # Deploy to your platform of choice
        
  deploy-content-publisher:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build and Deploy Content Publisher
      run: |
        cd content-publisher-typescript
        docker build -t content-publisher:${{ github.sha }} .
        # Deploy to your platform of choice
```

## 🎯 Best Practices

### 1. Consistent Port Strategy
- Python SDKs: 8000-8099
- Node.js SDKs: 3000-3099
- Java SDKs: 8080-8179
- Go SDKs: 9000-9099

### 2. Health Check Standards
All SDKs should implement:
```
GET /health
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 3. Environment Variables
Standardize environment variables:
- `PORT`: Service port
- `DEBUG`: Debug mode
- `LOG_LEVEL`: Logging level
- `API_KEY_*`: API keys

### 4. Logging Standards
Use structured logging (JSON) for all SDKs:
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "service": "blog-writer-sdk",
  "message": "Request processed",
  "request_id": "abc123"
}
```

## 🚀 Deployment Platforms Comparison

| Platform | Best For | Pros | Cons |
|----------|----------|------|------|
| Google Cloud Run | Quick deployment | Easy setup, auto-scaling | Pay-per-use pricing |
| DigitalOcean | Balanced approach | Good pricing, managed | Less features than AWS |
| AWS ECS/Fargate | Enterprise | Full control, scalable | Complex setup |
| Kubernetes | Large scale | Ultimate flexibility | High complexity |
| Docker Compose | Development/Small scale | Simple, local-friendly | Not production-ready |

## 📋 Checklist for SDK Dockerization

- [ ] Create appropriate Dockerfile for each language
- [ ] Implement health check endpoints
- [ ] Use multi-stage builds for optimization
- [ ] Set up non-root users for security
- [ ] Configure proper logging
- [ ] Standardize environment variables
- [ ] Set up container registry
- [ ] Create deployment pipeline
- [ ] Configure monitoring and alerts
- [ ] Document API endpoints

This approach gives you a consistent, scalable way to deploy all your SDKs regardless of the programming language!
