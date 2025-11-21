# Autoscaling Quick Start Guide

## Current Load Requirements
- **20,000 queries/day** (1,000 customers × 20 queries)
- **4 minutes per query**
- **Peak**: ~100 queries/minute = **400 concurrent requests**

## Immediate Action: Update Cloud Build Config

### Option 1: Use Optimized Config (Recommended)

Replace `cloudbuild.yaml` with `cloudbuild-optimized.yaml`:

```bash
cp cloudbuild-optimized.yaml cloudbuild.yaml
```

**Key Changes:**
- Memory: `2Gi` → `4Gi`
- Max Instances: `100` → `500`
- Min Instances: `0` → `5` (keep warm)
- Concurrency: `80` → `1` (one blog per instance)
- CPU Throttling: `false` (full CPU)

### Option 2: Manual Update

Update `cloudbuild.yaml` line 29-33:

```yaml
--memory=4Gi
--cpu=2
--min-instances=5
--max-instances=500
--concurrency=1
--cpu-throttling=false
```

## Deploy Optimized Configuration

```bash
# Deploy with optimized settings
gcloud builds submit --config=cloudbuild.yaml

# Or use GitHub Actions (will use cloudbuild.yaml)
git add cloudbuild.yaml
git commit -m "feat: optimize autoscaling for 20k queries/day"
git push origin develop
```

## Verify Autoscaling

### Check Current Configuration
```bash
gcloud run services describe blog-writer-api-dev \
  --region=europe-west1 \
  --format="value(spec.template.spec.containers[0].resources)"
```

### Monitor Scaling
```bash
# Watch instance count
watch -n 5 'gcloud run services describe blog-writer-api-dev \
  --region=europe-west1 \
  --format="value(status.conditions[0].message)"'
```

### Load Test
```python
import asyncio
import httpx

async def load_test():
    url = "https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/blog/generate-enhanced"
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        tasks = []
        for i in range(50):  # Start with 50 concurrent
            task = client.post(url, json={
                "topic": f"Test Topic {i}",
                "keywords": ["test"],
                "length": "medium"
            })
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success = sum(1 for r in results if not isinstance(r, Exception) and r.status_code == 200)
        print(f"✅ Success: {success}/{len(tasks)}")

asyncio.run(load_test())
```

## Expected Behavior

### Normal Load (Off-Peak)
- **Instances**: 5-20
- **Response Time**: 4-5 minutes
- **Cost**: ~$50-100/day

### Peak Load (100 queries/min)
- **Instances**: 200-400
- **Response Time**: 4-5 minutes
- **Cost**: ~$200-400/day

### Scaling Triggers
- **Scale Up**: CPU > 70% or request rate > 50/min
- **Scale Down**: CPU < 30% for 5+ minutes
- **Min Instances**: Always keep 5 warm

## Cost Optimization (Next Phase)

### Phase 1: Current (Immediate)
- ✅ Optimized autoscaling config
- ✅ Min instances = 5 (low latency)
- ✅ Max instances = 500 (handle peak)

### Phase 2: Cloud Tasks (Week 1-2)
- Enqueue jobs to Cloud Tasks
- Worker service processes async
- Scale to zero when idle
- **Savings**: 40-50% during off-peak

### Phase 3: Microservices (Week 2-3)
- Split into keyword + blog services
- Independent scaling
- **Savings**: 30% overall

## Troubleshooting

### High Latency
```bash
# Check instance count
gcloud run services describe blog-writer-api-dev \
  --region=europe-west1 \
  --format="value(status.conditions)"

# Check logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 \
  --format=json
```

### Too Many Instances
- Reduce `min-instances` to 1-2
- Increase `concurrency` to 2-4 (if memory allows)
- Check for memory leaks

### Not Scaling Up
- Verify `max-instances` is high enough
- Check CPU/memory limits
- Verify Cloud Run quotas

## Next Steps

1. **Deploy optimized config** (5 minutes)
2. **Monitor for 24 hours** (verify scaling)
3. **Load test** (50-100 concurrent requests)
4. **Implement Cloud Tasks** (if cost is concern)
5. **Split microservices** (if needed)

## Support

See `CLOUD_RUN_AUTOSCALING_STRATEGY.md` for detailed architecture and implementation guide.

