# Cloud Run Autoscaling Strategy for Blog Writer API

## Load Analysis

### Current Requirements
- **Query Duration**: 4 minutes per blog generation
- **Customers**: 1,000
- **Queries per Customer**: 20 per day
- **Total Daily Queries**: 20,000
- **Peak Hour Assumption**: 30% of daily traffic (6,000 queries/hour = 100 queries/minute)

### Resource Calculation
- **Concurrent Requests Needed**: 100 queries/min × 4 min = **400 concurrent requests**
- **With 80% concurrency per instance**: 400 / 0.8 = **500 instances** (worst case)
- **With 50% utilization**: 400 / 0.5 = **800 instances** (peak load)

## Microservices Architecture

### Service Breakdown

#### 1. **API Gateway Service** (Lightweight)
- **Purpose**: Request routing, authentication, rate limiting
- **Memory**: 512Mi
- **CPU**: 1
- **Min Instances**: 2
- **Max Instances**: 50
- **Concurrency**: 1000
- **Timeout**: 60s

#### 2. **Keyword Analysis Service** (Fast)
- **Purpose**: Keyword research and analysis
- **Memory**: 1Gi
- **CPU**: 1
- **Min Instances**: 1
- **Max Instances**: 100
- **Concurrency**: 50
- **Timeout**: 300s

#### 3. **Blog Generation Service** (Heavy - Long Running)
- **Purpose**: Multi-stage blog generation (4 min per request)
- **Memory**: 4Gi
- **CPU**: 2
- **Min Instances**: 5
- **Max Instances**: 500
- **Concurrency**: 1 (one blog per instance)
- **Timeout**: 900s

#### 4. **Image Generation Service** (Medium)
- **Purpose**: Image generation and optimization
- **Memory**: 2Gi
- **CPU**: 2
- **Min Instances**: 0
- **Max Instances**: 50
- **Concurrency**: 10
- **Timeout**: 300s

#### 5. **Queue Worker Service** (Background)
- **Purpose**: Process blog generation jobs from Cloud Tasks
- **Memory**: 4Gi
- **CPU**: 2
- **Min Instances**: 10
- **Max Instances**: 500
- **Concurrency**: 1
- **Timeout**: 900s

## Recommended Architecture: Async Queue Pattern

### Option 1: Cloud Tasks + Cloud Run (Recommended)

**Flow:**
```
Client → API Gateway → Cloud Tasks Queue → Blog Generation Worker
```

**Benefits:**
- Automatic retry on failure
- Built-in rate limiting
- Cost-effective (pay per task)
- Scales independently

### Option 2: Pub/Sub + Cloud Run

**Flow:**
```
Client → API Gateway → Pub/Sub Topic → Blog Generation Worker
```

**Benefits:**
- Real-time processing
- Multiple subscribers
- Better for streaming

## Implementation Plan

### Phase 1: Immediate Optimizations (Current Service)

Update `cloudbuild.yaml` for better autoscaling:

```yaml
--memory=4Gi
--cpu=2
--min-instances=5
--max-instances=500
--concurrency=1
--timeout=900
--cpu-throttling=false
```

**Why concurrency=1?**
- Blog generation is CPU/memory intensive
- 4-minute duration means one request per instance
- Prevents resource contention

### Phase 2: Microservices Split

#### Step 1: Create Keyword Analysis Service

```yaml
# cloudbuild-keyword-service.yaml
--memory=1Gi
--cpu=1
--min-instances=1
--max-instances=100
--concurrency=50
--timeout=300
```

#### Step 2: Create Blog Generation Worker Service

```yaml
# cloudbuild-blog-worker.yaml
--memory=4Gi
--cpu=2
--min-instances=10
--max-instances=500
--concurrency=1
--timeout=900
```

#### Step 3: Create API Gateway Service

```yaml
# cloudbuild-api-gateway.yaml
--memory=512Mi
--cpu=1
--min-instances=2
--max-instances=50
--concurrency=1000
--timeout=60
```

### Phase 3: Cloud Tasks Integration

1. **Create Cloud Tasks Queue**
```bash
gcloud tasks queues create blog-generation-queue \
  --location=europe-west1 \
  --max-dispatches-per-second=100 \
  --max-concurrent-dispatches=500 \
  --max-retry-duration=3600s
```

2. **Update API Gateway to Enqueue Jobs**
```python
from google.cloud import tasks_v2

async def create_blog_job(request: BlogRequest):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(PROJECT_ID, LOCATION, QUEUE_NAME)
    
    task = {
        'http_request': {
            'http_method': tasks_v2.HttpMethod.POST,
            'url': f'https://blog-worker-{ENV}.run.app/api/v1/worker/generate',
            'headers': {'Content-Type': 'application/json'},
            'body': request.json().encode()
        }
    }
    
    response = client.create_task(request={'parent': parent, 'task': task})
    return {'job_id': response.name}
```

3. **Worker Service Endpoint**
```python
@app.post("/api/v1/worker/generate")
async def worker_generate_blog(request: BlogRequest):
    # Process blog generation
    result = await pipeline.generate(...)
    return result
```

## Cost Optimization

### Current Setup (Single Service)
- **Peak Instances**: 500 × 4Gi × 2 CPU = 4,000 Gi-hours/day
- **Cost**: ~$2,000/month (estimated)

### Optimized Microservices
- **API Gateway**: 50 × 512Mi × 1 CPU = 640 Gi-hours/day
- **Keyword Service**: 100 × 1Gi × 1 CPU = 2,400 Gi-hours/day
- **Blog Worker**: 500 × 4Gi × 2 CPU = 4,000 Gi-hours/day
- **Total**: ~$1,500/month (30% savings)

### With Cloud Tasks
- **Queue Processing**: Pay per task (~$0.40 per 1M tasks)
- **Worker Instances**: Scale to zero when idle
- **Estimated Savings**: 40-50% during off-peak hours

## Autoscaling Configuration

### Target Metrics
- **CPU Utilization**: 70% (triggers scale-up)
- **Request Rate**: 100 requests/min (triggers scale-up)
- **Queue Depth**: 50 pending tasks (triggers scale-up)

### Scaling Behavior
```yaml
# Cloud Run Autoscaling
min-instances: 5        # Keep warm for low latency
max-instances: 500     # Handle peak load
concurrency: 1          # One blog per instance
cpu-throttling: false  # Full CPU for generation
```

## Monitoring & Alerts

### Key Metrics
1. **Request Latency**: P50, P95, P99
2. **Instance Count**: Current, min, max
3. **Queue Depth**: Pending tasks
4. **Error Rate**: 4xx, 5xx responses
5. **Cost**: Daily spend

### Alerts
- **High Latency**: P95 > 5 minutes
- **High Error Rate**: > 5% failures
- **Queue Backlog**: > 1000 pending tasks
- **Cost Spike**: > $100/day increase

## Implementation Steps

### Step 1: Update Current Service (Immediate)
1. Update `cloudbuild.yaml` with optimized settings
2. Deploy and monitor scaling behavior
3. Test with load (100 concurrent requests)

### Step 2: Split Services (Week 1)
1. Create keyword analysis service
2. Create blog generation worker service
3. Update API to route to appropriate service
4. Deploy and test

### Step 3: Add Cloud Tasks (Week 2)
1. Create Cloud Tasks queue
2. Update API gateway to enqueue jobs
3. Create worker service endpoint
4. Implement job status tracking
5. Deploy and monitor

### Step 4: Optimize (Week 3)
1. Add caching layer (Redis/Memorystore)
2. Implement request deduplication
3. Add cost monitoring and alerts
4. Fine-tune scaling parameters

## Testing Load

### Load Test Script
```python
import asyncio
import httpx

async def test_load():
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(100):  # 100 concurrent requests
            task = client.post(
                "https://api.run.app/api/v1/blog/generate-enhanced",
                json={"topic": f"Test Topic {i}", "keywords": ["test"]}
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        print(f"Completed: {sum(1 for r in results if r.status_code == 200)}")
```

## Next Steps

1. **Review and approve** this architecture
2. **Update cloudbuild.yaml** with optimized settings
3. **Deploy and monitor** scaling behavior
4. **Implement microservices** split if needed
5. **Add Cloud Tasks** for async processing

