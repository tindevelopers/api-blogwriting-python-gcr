# Blog Writer Admin Dashboard - LiteLLM Monitoring Guide

**Architecture:** Frontend (Vercel) → Backend (Cloud Run) → LiteLLM → Multiple LLMs  
**Current:** Direct connection (working)  
**Future:** LiteLLM connection (for monitoring and optimization)

---

## 🎯 Two-Phase Architecture

### **Phase 1: Current State (Production Ready)**

```
┌─────────────────┐
│  Frontend       │
│  Dashboard      │
│  (Vercel)       │
└────────┬────────┘
         │
         │ HTTPS
         ▼
┌─────────────────┐
│  Backend API    │──┐
│  (Cloud Run)    │  │
└─────────────────┘  │
                     │ Direct API Calls
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │ OpenAI │  │Anthropic│  │DeepSeek│
    └────────┘  └────────┘  └────────┘

Status: ✅ Working (Tested Dec 21, 2025)
Monitoring: Backend logs only
```

### **Phase 2: Future with LiteLLM (Enhanced)**

```
┌─────────────────┐
│  Frontend       │
│  Dashboard      │
│  (Vercel)       │──┐
└────────┬────────┘  │
         │            │ Monitor Usage
         │            ▼
         │       ┌─────────────────┐
         │       │  LiteLLM Metrics│
         │       │  API             │
         │       └─────────────────┘
         │
         │ HTTPS
         ▼
┌─────────────────┐
│  Backend API    │
│  (Cloud Run)    │
└────────┬────────┘
         │
         │ HTTPS
         ▼
┌─────────────────┐
│  LiteLLM Proxy  │──┐
│  (Cloud Run)    │  │ Routes to multiple LLMs
└─────────────────┘  │ Caching, Load Balancing
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │ OpenAI │  │Anthropic│  │DeepSeek│
    └────────┘  └────────┘  └────────┘

Status: 🔧 To be configured
Monitoring: Frontend dashboard + LiteLLM metrics API
```

---

## 📊 Frontend Monitoring Requirements

### What Frontend Should Monitor from LiteLLM

When LiteLLM is enabled, your dashboard should display:

#### 1. **Connection Status**
```typescript
// Display current routing mode
{litellmEnabled ? (
  <Badge color="blue">
    Using LiteLLM Proxy
  </Badge>
) : (
  <Badge color="zinc">
    Direct Connection
  </Badge>
)}
```

#### 2. **Real-Time Metrics from LiteLLM**

**LiteLLM exposes these metrics endpoints:**

```typescript
// Get usage statistics
GET /litellm/spend/logs

// Get model performance
GET /litellm/model/metrics

// Get cache statistics  
GET /litellm/cache/stats

// Health check
GET /health
```

**Display in dashboard:**
- Requests per model (gpt-4o, claude, etc.)
- Cost per model
- Cache hit rate
- Average latency per model
- Success/error rates
- Token usage breakdown

#### 3. **LiteLLM Control Panel**

Frontend should allow admins to:
```typescript
// Enable/disable LiteLLM
- Toggle switch to activate LiteLLM routing
- Save to Firestore
- Trigger backend config reload

// Configure LiteLLM
- Proxy URL input
- API key (master key) input
- Cache settings (enable, TTL)
- Test connection button

// View LiteLLM status
- Connection health (green/red)
- Current model routing
- Cache statistics
- Recent requests
```

---

## 🔧 Implementation Details

### Frontend Dashboard Components

#### Component 1: Connection Mode Indicator

**File:** `components/monitoring/ConnectionModeIndicator.tsx`

```typescript
'use client';

import { Badge } from '@/components/catalyst/badge';
import { Text } from '@/components/catalyst/text';
import { useConfig } from '@/lib/api/hooks';

export function ConnectionModeIndicator() {
  const { data: config } = useConfig();
  const litellmEnabled = config?.litellm?.enabled || false;
  
  return (
    <div className="flex items-center gap-3">
      <Text className="text-sm font-medium">AI Routing:</Text>
      
      {litellmEnabled ? (
        <div className="flex items-center gap-2">
          <Badge color="blue">LiteLLM Proxy</Badge>
          <Text className="text-xs text-zinc-500">
            Backend → LiteLLM → AI Providers
          </Text>
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <Badge color="zinc">Direct</Badge>
          <Text className="text-xs text-zinc-500">
            Backend → AI Providers
          </Text>
        </div>
      )}
    </div>
  );
}
```

#### Component 2: LiteLLM Usage Dashboard

**File:** `components/analytics/LiteLLMUsageDashboard.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { Heading } from '@/components/catalyst/heading';
import { Text } from '@/components/catalyst/text';
import { Table, TableHead, TableBody, TableRow, TableHeader, TableCell } from '@/components/catalyst/table';
import { Badge } from '@/components/catalyst/badge';
import { useLiteLLMConfig } from '@/lib/stores/config-store';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export function LiteLLMUsageDashboard() {
  const { litellmEnabled, proxyUrl } = useLiteLLMConfig();
  const [metrics, setMetrics] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    async function fetchMetrics() {
      if (!litellmEnabled || !proxyUrl) {
        setIsLoading(false);
        return;
      }
      
      try {
        // Fetch from LiteLLM metrics API
        const response = await fetch(`${proxyUrl}/litellm/spend/logs`, {
          headers: {
            'Authorization': `Bearer ${process.env.NEXT_PUBLIC_LITELLM_API_KEY}`,
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          setMetrics(data);
        }
      } catch (error) {
        console.error('Failed to fetch LiteLLM metrics:', error);
      } finally {
        setIsLoading(false);
      }
    }
    
    fetchMetrics();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, [litellmEnabled, proxyUrl]);
  
  if (!litellmEnabled) {
    return (
      <div className="rounded-lg border border-zinc-950/10 p-6 dark:border-white/10">
        <Text className="text-zinc-500">
          LiteLLM is not enabled. Switch to LiteLLM mode in Configuration to see metrics.
        </Text>
      </div>
    );
  }
  
  if (isLoading) {
    return <div>Loading LiteLLM metrics...</div>;
  }
  
  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-zinc-950/10 p-4 dark:border-white/10">
          <Text className="text-sm text-zinc-500">Total Requests</Text>
          <div className="mt-2 text-2xl font-semibold">
            {metrics?.total_requests || 0}
          </div>
        </div>
        
        <div className="rounded-lg border border-zinc-950/10 p-4 dark:border-white/10">
          <Text className="text-sm text-zinc-500">Cache Hit Rate</Text>
          <div className="mt-2 text-2xl font-semibold">
            {metrics?.cache_hit_rate?.toFixed(1) || 0}%
          </div>
        </div>
        
        <div className="rounded-lg border border-zinc-950/10 p-4 dark:border-white/10">
          <Text className="text-sm text-zinc-500">Total Cost</Text>
          <div className="mt-2 text-2xl font-semibold">
            ${metrics?.total_cost?.toFixed(2) || '0.00'}
          </div>
        </div>
        
        <div className="rounded-lg border border-zinc-950/10 p-4 dark:border-white/10">
          <Text className="text-sm text-zinc-500">Avg Latency</Text>
          <div className="mt-2 text-2xl font-semibold">
            {metrics?.avg_latency || 0}ms
          </div>
        </div>
      </div>
      
      {/* Requests by Model */}
      <div className="rounded-lg border border-zinc-950/10 p-6 dark:border-white/10">
        <Heading level={2}>Requests by Model</Heading>
        
        <Table className="mt-4" striped>
          <TableHead>
            <TableRow>
              <TableHeader>Model</TableHeader>
              <TableHeader>Requests</TableHeader>
              <TableHeader>Tokens</TableHeader>
              <TableHeader>Cost</TableHeader>
              <TableHeader>Avg Latency</TableHeader>
              <TableHeader>Cache Rate</TableHeader>
            </TableRow>
          </TableHead>
          <TableBody>
            {metrics?.model_stats?.map((stat: any) => (
              <TableRow key={stat.model}>
                <TableCell>
                  <code className="text-sm">{stat.model}</code>
                </TableCell>
                <TableCell>{stat.requests}</TableCell>
                <TableCell>{stat.total_tokens?.toLocaleString()}</TableCell>
                <TableCell>${stat.cost?.toFixed(4)}</TableCell>
                <TableCell>{stat.avg_latency}ms</TableCell>
                <TableCell>
                  <Badge color={stat.cache_rate > 30 ? 'green' : 'zinc'}>
                    {stat.cache_rate}%
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
```

#### Component 3: LiteLLM Configuration Toggle

**File:** `components/configuration/LiteLLMToggle.tsx`

```typescript
'use client';

import { Switch } from '@/components/catalyst/switch';
import { Field, Label, Description } from '@/components/catalyst/fieldset';
import { Input } from '@/components/catalyst/input';
import { Button } from '@/components/catalyst/button';
import { Badge } from '@/components/catalyst/badge';
import { Alert, AlertTitle, AlertDescription } from '@/components/catalyst/alert';
import { useState } from 'react';
import { toast } from 'react-hot-toast';

export function LiteLLMToggle({ orgId }: { orgId: string }) {
  const [enabled, setEnabled] = useState(false);
  const [proxyUrl, setProxyUrl] = useState('https://litellm-proxy-613248238610.europe-west9.run.app');
  const [apiKey, setApiKey] = useState('');
  const [cacheEnabled, setCacheEnabled] = useState(true);
  const [cacheTTL, setCacheTTL] = useState(3600);
  const [status, setStatus] = useState<'connected' | 'disconnected' | 'testing'>('disconnected');
  
  const testConnection = async () => {
    setStatus('testing');
    
    try {
      const response = await fetch(`${proxyUrl}/health`);
      if (response.ok) {
        setStatus('connected');
        toast.success('LiteLLM connection successful!');
      } else {
        setStatus('disconnected');
        toast.error('LiteLLM connection failed');
      }
    } catch (error) {
      setStatus('disconnected');
      toast.error('Could not reach LiteLLM proxy');
    }
  };
  
  const saveConfig = async () => {
    try {
      // Save to Firestore
      await fetch('/api/config/litellm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          orgId,
          enabled,
          proxyUrl,
          apiKey,
          cacheEnabled,
          cacheTTL,
        }),
      });
      
      toast.success('Configuration saved');
      
      // Trigger backend to reload config
      await fetch('/api/config/reload', { method: 'POST' });
      
    } catch (error) {
      toast.error('Failed to save configuration');
    }
  };
  
  return (
    <div className="space-y-6">
      {/* Main Toggle */}
      <Field>
        <div className="flex items-center justify-between">
          <div>
            <Label>Enable LiteLLM Proxy</Label>
            <Description>
              Route all AI requests through LiteLLM for caching, monitoring, and multi-provider support
            </Description>
          </div>
          <Switch checked={enabled} onChange={setEnabled} />
        </div>
      </Field>
      
      {/* Status Alert */}
      {enabled && (
        <Alert color={status === 'connected' ? 'green' : status === 'testing' ? 'yellow' : 'red'}>
          <AlertTitle>
            {status === 'connected' && 'LiteLLM Connected'}
            {status === 'disconnected' && 'LiteLLM Disconnected'}
            {status === 'testing' && 'Testing Connection...'}
          </AlertTitle>
          <AlertDescription>
            {status === 'connected' && `Successfully connected to ${proxyUrl}`}
            {status === 'disconnected' && 'Cannot connect to LiteLLM proxy. Check URL and API key.'}
            {status === 'testing' && 'Testing LiteLLM connection...'}
          </AlertDescription>
        </Alert>
      )}
      
      {/* Configuration Fields */}
      {enabled && (
        <div className="space-y-4">
          <Field>
            <Label>LiteLLM Proxy URL</Label>
            <Input
              type="url"
              value={proxyUrl}
              onChange={(e) => setProxyUrl(e.target.value)}
              placeholder="https://litellm-proxy-xxx.run.app"
            />
            <Description>Your LiteLLM Cloud Run service URL</Description>
          </Field>
          
          <Field>
            <Label>Master API Key</Label>
            <Input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-••••••••"
            />
            <Description>LiteLLM master key for authentication</Description>
          </Field>
          
          <Field>
            <div className="flex items-center justify-between">
              <div>
                <Label>Enable Response Caching</Label>
                <Description>Cache responses to reduce costs and latency</Description>
              </div>
              <Switch checked={cacheEnabled} onChange={setCacheEnabled} />
            </div>
          </Field>
          
          {cacheEnabled && (
            <Field>
              <Label>Cache TTL: {cacheTTL} seconds</Label>
              <input
                type="range"
                min={60}
                max={86400}
                value={cacheTTL}
                onChange={(e) => setCacheTTL(parseInt(e.target.value))}
                className="w-full"
              />
              <Description>
                How long to cache responses (60s = 1min, 3600s = 1hr, 86400s = 1day)
              </Description>
            </Field>
          )}
          
          <div className="flex gap-3">
            <Button color="blue" onClick={saveConfig}>
              Save Configuration
            </Button>
            <Button outline onClick={testConnection}>
              Test Connection
            </Button>
          </div>
        </div>
      )}
      
      {/* Current Architecture Display */}
      <div className="rounded-lg bg-zinc-50 p-4 dark:bg-zinc-900">
        <Text className="text-sm font-medium">Current Request Flow:</Text>
        <div className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          {!enabled ? (
            <>Backend → OpenAI/Anthropic/DeepSeek (Direct)</>
          ) : (
            <>Backend → LiteLLM Proxy ({proxyUrl}) → AI Providers</>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

## 🔌 LiteLLM Metrics API Integration

### Fetch LiteLLM Metrics from Frontend

**File:** `lib/api/litellm.ts`

```typescript
import { useLiteLLMConfig } from '@/lib/stores/config-store';

interface LiteLLMMetrics {
  total_requests: number;
  total_cost: number;
  cache_hit_rate: number;
  avg_latency: number;
  model_stats: Array<{
    model: string;
    requests: number;
    total_tokens: number;
    cost: number;
    avg_latency: number;
    cache_rate: number;
  }>;
  time_series: Array<{
    timestamp: string;
    requests: number;
    cost: number;
  }>;
}

export const litellmAPI = {
  // Check if LiteLLM is reachable
  async checkHealth(proxyUrl: string, apiKey: string): Promise<boolean> {
    try {
      const response = await fetch(`${proxyUrl}/health`, {
        headers: apiKey ? { 'Authorization': `Bearer ${apiKey}` } : {},
      });
      return response.ok;
    } catch {
      return false;
    }
  },
  
  // Get spend logs (usage data)
  async getSpendLogs(proxyUrl: string, apiKey: string): Promise<any[]> {
    try {
      const response = await fetch(`${proxyUrl}/litellm/spend/logs`, {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) throw new Error('Failed to fetch');
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch LiteLLM spend logs:', error);
      return [];
    }
  },
  
  // Get model metrics
  async getModelMetrics(proxyUrl: string, apiKey: string): Promise<any> {
    try {
      const response = await fetch(`${proxyUrl}/litellm/model/metrics`, {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to fetch');
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch model metrics:', error);
      return null;
    }
  },
  
  // Get cache statistics
  async getCacheStats(proxyUrl: string, apiKey: string): Promise<any> {
    try {
      const response = await fetch(`${proxyUrl}/litellm/cache/stats`, {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to fetch');
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch cache stats:', error);
      return null;
    }
  },
  
  // Process metrics into dashboard format
  async getMetrics(proxyUrl: string, apiKey: string): Promise<LiteLLMMetrics> {
    const [spendLogs, modelMetrics, cacheStats] = await Promise.all([
      this.getSpendLogs(proxyUrl, apiKey),
      this.getModelMetrics(proxyUrl, apiKey),
      this.getCacheStats(proxyUrl, apiKey),
    ]);
    
    // Process raw data into dashboard format
    return {
      total_requests: spendLogs.length,
      total_cost: spendLogs.reduce((sum, log) => sum + (log.cost || 0), 0),
      cache_hit_rate: cacheStats?.hit_rate || 0,
      avg_latency: spendLogs.reduce((sum, log) => sum + (log.latency || 0), 0) / spendLogs.length,
      model_stats: processModelStats(spendLogs),
      time_series: processTimeSeries(spendLogs),
    };
  },
};

function processModelStats(logs: any[]): any[] {
  const statsByModel = logs.reduce((acc, log) => {
    const model = log.model || 'unknown';
    if (!acc[model]) {
      acc[model] = {
        model,
        requests: 0,
        total_tokens: 0,
        cost: 0,
        latencies: [],
        cached: 0,
      };
    }
    
    acc[model].requests++;
    acc[model].total_tokens += log.tokens || 0;
    acc[model].cost += log.cost || 0;
    acc[model].latencies.push(log.latency || 0);
    if (log.cached) acc[model].cached++;
    
    return acc;
  }, {});
  
  return Object.values(statsByModel).map((stat: any) => ({
    model: stat.model,
    requests: stat.requests,
    total_tokens: stat.total_tokens,
    cost: stat.cost,
    avg_latency: stat.latencies.reduce((a: number, b: number) => a + b, 0) / stat.latencies.length,
    cache_rate: (stat.cached / stat.requests) * 100,
  }));
}

function processTimeSeries(logs: any[]): any[] {
  // Group by hour
  const byHour = logs.reduce((acc, log) => {
    const hour = new Date(log.timestamp).toISOString().split(':')[0] + ':00';
    if (!acc[hour]) {
      acc[hour] = { timestamp: hour, requests: 0, cost: 0 };
    }
    acc[hour].requests++;
    acc[hour].cost += log.cost || 0;
    return acc;
  }, {});
  
  return Object.values(byHour);
}
```

### React Query Hook for LiteLLM

**File:** `lib/api/hooks.ts` (add this)

```typescript
// Add to existing hooks.ts

export function useLiteLLMMetrics() {
  const { litellmEnabled, proxyUrl, apiKey } = useLiteLLMConfig();
  
  return useQuery({
    queryKey: ['litellm-metrics', proxyUrl],
    queryFn: async () => {
      if (!litellmEnabled || !proxyUrl || !apiKey) {
        return null;
      }
      
      return await litellmAPI.getMetrics(proxyUrl, apiKey);
    },
    enabled: litellmEnabled,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

export function useLiteLLMHealth() {
  const { proxyUrl, apiKey } = useLiteLLMConfig();
  
  return useQuery({
    queryKey: ['litellm-health', proxyUrl],
    queryFn: async () => {
      return await litellmAPI.checkHealth(proxyUrl, apiKey);
    },
    refetchInterval: 10000, // Check every 10 seconds
  });
}
```

---

## 🎨 Dashboard Pages with LiteLLM Monitoring

### Updated Analytics Page

**File:** `app/(dashboard)/analytics/page.tsx`

```typescript
'use client';

import { Heading } from '@/components/catalyst/heading';
import { Text } from '@/components/catalyst/text';
import { Badge } from '@/components/catalyst/badge';
import { Select } from '@/components/catalyst/select';
import { Tabs, TabList, Tab, TabPanels, TabPanel } from '@/components/catalyst/tabs';
import { useLiteLLMMetrics, useMetrics } from '@/lib/api/hooks';
import { useLiteLLMConfig } from '@/lib/stores/config-store';
import { LiteLLMUsageDashboard } from '@/components/analytics/LiteLLMUsageDashboard';
import { ConnectionModeIndicator } from '@/components/monitoring/ConnectionModeIndicator';

export default function AnalyticsPage() {
  const { litellmEnabled } = useLiteLLMConfig();
  const litellmMetrics = useLiteLLMMetrics();
  const backendMetrics = useMetrics();
  
  return (
    <div className="max-w-7xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <Heading>Usage Analytics</Heading>
          <Text>Monitor AI usage, costs, and performance</Text>
        </div>
        
        <ConnectionModeIndicator />
      </div>
      
      <Tabs>
        <TabList>
          <Tab>Overview</Tab>
          {litellmEnabled && <Tab>LiteLLM Metrics</Tab>}
          <Tab>Cost Breakdown</Tab>
          <Tab>Performance</Tab>
        </TabList>
        
        <TabPanels>
          <TabPanel>
            {/* Overview - shows metrics from whichever source is active */}
            {litellmEnabled ? (
              <LiteLLMUsageDashboard />
            ) : (
              <div>
                <Text>Using direct backend metrics</Text>
                {/* Show backend metrics */}
              </div>
            )}
          </TabPanel>
          
          {litellmEnabled && (
            <TabPanel>
              <LiteLLMUsageDashboard />
            </TabPanel>
          )}
          
          <TabPanel>
            {/* Cost breakdown charts */}
          </TabPanel>
          
          <TabPanel>
            {/* Performance metrics */}
          </TabPanel>
        </TabPanels>
      </Tabs>
    </div>
  );
}
```

---

## 🔄 Migration Path: Direct → LiteLLM

### For Frontend Team

**Phase 1: Build Dashboard (Direct Mode)**
- ✅ Build all features
- ✅ Connect to backend
- ✅ Monitor via backend metrics
- ✅ Deploy to production

**Phase 2: Add LiteLLM Monitoring (Parallel)**
- Add LiteLLM toggle in configuration
- Add LiteLLM metrics components
- Keep direct mode as default
- Test LiteLLM mode in staging

**Phase 3: Switch to LiteLLM (When Ready)**
- Backend team deploys LiteLLM
- Admin enables LiteLLM in dashboard
- Dashboard shows LiteLLM metrics
- Monitor for 1-2 weeks

**Phase 4: Make LiteLLM Default**
- Once stable, make LiteLLM default
- Keep direct mode as fallback
- Dashboard shows both options

### Configuration Storage

```typescript
// Firestore document: /organizations/{orgId}/config/litellm
{
  // Current settings
  enabled: false,  // Start with false (direct mode)
  
  // Future settings (when ready)
  proxyUrl: 'https://litellm-proxy-613248238610.europe-west9.run.app',
  apiKey: 'encrypted-master-key',
  cacheEnabled: true,
  cacheTTL: 3600,
  
  // Metadata
  updatedAt: timestamp,
  updatedBy: 'admin@example.com',
}
```

---

## 📱 Dashboard Features Summary

### Must-Have (Phase 1)
- ✅ Testing interface (blog generation)
- ✅ Basic analytics (requests, costs)
- ✅ Configuration panel (AI providers)
- ✅ Connection status indicator

### Should-Have (Phase 2)
- ✅ LiteLLM toggle and config
- ✅ LiteLLM metrics display
- ✅ Usage charts (Recharts)
- ✅ Model comparison table

### Nice-to-Have (Phase 3)
- Advanced cost forecasting
- Email alerts for high usage
- Budget limits per org
- A/B testing different models

---

## 🚀 Deployment Steps

### 1. Set Up Google Firestore

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize Firestore
firebase init firestore

# Select your project
# Use default firestore.rules and firestore.indexes.json

# Deploy
firebase deploy --only firestore
```

### 2. Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy to production
vercel --prod
```

### 3. Configure Environment Variables in Vercel

Add to Vercel Dashboard → Settings → Environment Variables:

**Required:**
```bash
NEXT_PUBLIC_API_URL=https://blog-writer-api-dev-613248238610.europe-west9.run.app
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project
NEXT_PUBLIC_FIREBASE_API_KEY=your-firebase-key
# ... (all Firebase vars)
NEXTAUTH_SECRET=your-nextauth-secret
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-secret
```

**Optional (for LiteLLM management):**
```bash
NEXT_PUBLIC_LITELLM_PROXY_URL=https://litellm-proxy-613248238610.europe-west9.run.app
# Note: Don't expose LITELLM_API_KEY publicly, handle server-side
```

---

## ✅ Complete Checklist for Frontend Team

### Setup
- [ ] Create GitHub repository: `blog-writer-admin`
- [ ] Copy starter files from `frontend-starter/`
- [ ] Copy Catalyst components from Dropbox
- [ ] Install dependencies: `npm install`
- [ ] Configure `.env.local`

### Firebase Setup
- [ ] Create Firebase project
- [ ] Enable Firestore
- [ ] Deploy security rules
- [ ] Get Firebase credentials
- [ ] Add to `.env.local`

### Development
- [ ] Generate API types: `npm run generate:types`
- [ ] Run dev server: `npm run dev`
- [ ] Test backend connectivity
- [ ] Implement dashboard layout (Catalyst SidebarLayout)
- [ ] Build testing interface
- [ ] Add analytics dashboard
- [ ] Create LiteLLM control panel
- [ ] Add configuration pages

### Testing
- [ ] Test blog generation
- [ ] Test configuration save/load (Firestore)
- [ ] Test authentication
- [ ] Test all charts render correctly
- [ ] Test responsive design
- [ ] Test dark mode

### Deployment
- [ ] Deploy to Vercel staging
- [ ] Configure environment variables
- [ ] Test staging deployment
- [ ] Deploy to production
- [ ] Monitor for errors

---

## 🎯 Key Decisions Summary

### ✅ Confirmed Decisions

1. **NO Vercel AI Gateway** - Use LiteLLM directly
2. **Current: Direct connection** - Working perfectly
3. **Future: LiteLLM** - When ready, switch via config
4. **Config Storage: Firestore** - Secure, real-time
5. **UI Components: Catalyst** - Professional, accessible
6. **Monitoring: Yes** - Frontend monitors LiteLLM metrics
7. **Repository: Separate** - Clean separation

### 🔄 Migration Strategy

**Now:** Direct mode (working) → Deploy dashboard  
**Later:** Enable LiteLLM → Monitor metrics → Optimize

---

## 📞 Support

### Documentation
- **Implementation Guide:** `FRONTEND_CATALYST_IMPLEMENTATION_GUIDE.md`
- **LiteLLM Setup:** `VERCEL_AI_GATEWAY_SETUP.md` (ignore Vercel parts, focus on LiteLLM)
- **This Guide:** `FRONTEND_LITELLM_FINAL_GUIDE.md`

### Testing
- **Test Backend:** `./test_ai_gateway.sh`
- **Check Connection:** `./check_vercel_connection.sh`

### Backend
- **API Docs:** https://blog-writer-api-dev-613248238610.europe-west9.run.app/docs
- **OpenAPI:** https://blog-writer-api-dev-613248238610.europe-west9.run.app/openapi.json

---

## 🎉 Summary

**Everything is ready for your frontend team:**

✅ **Backend confirmed working** (direct LLM connection)  
✅ **Starter repository created** (all config files ready)  
✅ **Catalyst UI guide provided** (complete code examples)  
✅ **Firestore schema defined** (secure config storage)  
✅ **LiteLLM monitoring planned** (metrics API integration)  
✅ **Migration path clear** (Direct → LiteLLM when ready)

**Start with direct mode, add LiteLLM monitoring when backend team enables it!** 🚀

---

**Ready to hand off to frontend team!** Give them:
1. `FRONTEND_COMPLETE_PACKAGE.md` (overview)
2. `FRONTEND_CATALYST_IMPLEMENTATION_GUIDE.md` (detailed guide)
3. `frontend-starter/` (starter code)
4. Access to Catalyst components folder

