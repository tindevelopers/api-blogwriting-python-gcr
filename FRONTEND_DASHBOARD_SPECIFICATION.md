# Blog Writer Admin Dashboard - Frontend Specification

**Version:** 1.0  
**Date:** December 21, 2025  
**Backend API:** `https://blog-writer-api-dev-613248238610.europe-west9.run.app`

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Repository Setup](#repository-setup)
5. [Type Safety & API Integration](#type-safety--api-integration)
6. [Feature Specifications](#feature-specifications)
7. [Component Specifications](#component-specifications)
8. [Deployment](#deployment)
9. [Development Workflow](#development-workflow)
10. [API Endpoints Reference](#api-endpoints-reference)

---

## Project Overview

### Purpose
Create a production-ready Next.js admin dashboard to control, monitor, and test the Blog Writer AI backend system.

### Key Objectives
- **Testing Interface:** Allow users to quickly test blog generation with different parameters
- **Analytics Dashboard:** Visualize usage metrics, costs, and performance data
- **Configuration Panel:** Manage AI providers, API keys, and system settings
- **Monitoring:** View real-time logs, system health, and error tracking
- **Type Safety:** 100% TypeScript coverage using OpenAPI schema from backend

### Target Users
- Internal administrators
- Product team members
- DevOps engineers
- QA testers

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Vercel (Frontend)                      │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Testing    │  │  Analytics   │  │Configuration │ │
│  │  Interface   │  │  Dashboard   │  │    Panel     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Type-Safe API Client                     │   │
│  │     (Generated from OpenAPI Schema)              │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                           │
                           │ HTTPS
                           ▼
┌─────────────────────────────────────────────────────────┐
│            Google Cloud Run (Backend API)               │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   FastAPI    │  │  AI Gateway  │  │  DataForSEO  │ │
│  │   Endpoints  │  │   Service    │  │    Client    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │           OpenAPI Schema (JSON)                  │   │
│  │     https://.../openapi.json                     │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  OpenAI API     │
                  │  Anthropic API  │
                  │  DeepSeek API   │
                  └─────────────────┘
```

### Type Safety Flow

```
Backend OpenAPI Schema
        │
        │ (Auto-fetch during build)
        ▼
   openapi-typescript
        │
        │ (Generates)
        ▼
TypeScript Type Definitions
        │
        ▼
Frontend Components
  (100% Type Safe)
```

---

## Technology Stack

### Core Framework
- **Next.js 14+** - App Router, Server Components
- **React 18+** - UI library
- **TypeScript 5+** - Type safety

### UI & Styling
- **Shadcn/ui** - Component library (built on Radix UI)
- **Tailwind CSS** - Utility-first CSS
- **Radix UI** - Headless component primitives
- **Lucide React** - Icon library

### Data Management
- **TanStack Query (React Query)** - Server state management
- **Zustand** - Client state management
- **openapi-fetch** - Type-safe API client

### Type Generation
- **openapi-typescript** - Generate TypeScript from OpenAPI schema
- **Zod** - Runtime type validation

### Charts & Visualization
- **Recharts** - Chart library
- **date-fns** - Date utilities

### Authentication
- **NextAuth.js** - Authentication framework
- **Google OAuth** - Primary auth provider

### Development Tools
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **TypeScript** - Type checking
- **tsx** - TypeScript execution

---

## Repository Setup

### 1. Create New Repository

```bash
# Create new repository on GitHub
# Repository name: blog-writer-dashboard

# Clone locally
git clone https://github.com/YOUR_ORG/blog-writer-dashboard.git
cd blog-writer-dashboard
```

### 2. Initialize Next.js Project

```bash
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir --import-alias "@/*"

# When prompted:
# ✓ Would you like to use TypeScript? Yes
# ✓ Would you like to use ESLint? Yes
# ✓ Would you like to use Tailwind CSS? Yes
# ✓ Would you like to use `src/` directory? No
# ✓ Would you like to use App Router? Yes
# ✓ Would you like to customize the default import alias? Yes (@/*)
```

### 3. Install Dependencies

```bash
# UI Components
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input label select tabs table badge alert

# Type Generation & API
npm install openapi-typescript openapi-fetch
npm install @tanstack/react-query
npm install axios zod

# Charts & Visualization
npm install recharts date-fns

# State Management
npm install zustand

# Authentication
npm install next-auth @auth/core

# Utilities
npm install clsx tailwind-merge class-variance-authority

# Development
npm install -D tsx @types/node
```

### 4. Project Structure

Create the following directory structure:

```
blog-writer-dashboard/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/
│   │   ├── page.tsx                 # Dashboard home
│   │   ├── testing/
│   │   │   └── page.tsx             # Testing interface
│   │   ├── analytics/
│   │   │   └── page.tsx             # Analytics dashboard
│   │   ├── configuration/
│   │   │   └── page.tsx             # Configuration panel
│   │   ├── monitoring/
│   │   │   └── page.tsx             # Monitoring & logs
│   │   └── layout.tsx               # Dashboard layout
│   ├── api/
│   │   └── auth/
│   │       └── [...nextauth]/
│   │           └── route.ts         # NextAuth configuration
│   ├── layout.tsx                   # Root layout
│   └── globals.css
│
├── components/
│   ├── ui/                          # Shadcn components
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Navigation.tsx
│   ├── dashboard/
│   │   ├── MetricCard.tsx
│   │   └── StatCard.tsx
│   ├── testing/
│   │   ├── BlogGenerationForm.tsx
│   │   ├── BlogPreview.tsx
│   │   └── ModelSelector.tsx
│   ├── analytics/
│   │   ├── RequestsChart.tsx
│   │   ├── CostChart.tsx
│   │   └── ModelUsageTable.tsx
│   ├── configuration/
│   │   ├── AIProviderConfig.tsx
│   │   ├── AIGatewayConfig.tsx
│   │   └── GeneralConfig.tsx
│   └── monitoring/
│       ├── LogViewer.tsx
│       ├── HealthIndicator.tsx
│       └── ErrorList.tsx
│
├── lib/
│   ├── api/
│   │   ├── client.ts                # Main API client
│   │   ├── types.ts                 # Generated from OpenAPI
│   │   └── hooks.ts                 # React Query hooks
│   ├── utils/
│   │   ├── cn.ts                    # Class name utility
│   │   ├── format.ts                # Formatting utilities
│   │   └── validation.ts            # Zod schemas
│   └── stores/
│       └── config-store.ts          # Zustand stores
│
├── scripts/
│   └── generate-types.ts            # OpenAPI type generation
│
├── public/
│   └── logo.svg
│
├── .env.local.example
├── .gitignore
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── README.md
```

---

## Type Safety & API Integration

### OpenAPI Type Generation

#### 1. Create Type Generation Script

**File:** `scripts/generate-types.ts`

```typescript
import openapiTS from 'openapi-typescript';
import fs from 'fs';
import path from 'path';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 
  'https://blog-writer-api-dev-613248238610.europe-west9.run.app';

async function generateTypes() {
  console.log('Fetching OpenAPI schema from:', BACKEND_URL);
  
  try {
    const output = await openapiTS(`${BACKEND_URL}/openapi.json`, {
      // Configuration options
      exportType: true,
      pathParamsAsTypes: true,
    });
    
    const outputPath = path.join(process.cwd(), 'lib/api/types.ts');
    fs.writeFileSync(outputPath, output);
    
    console.log('✓ Generated TypeScript types at:', outputPath);
  } catch (error) {
    console.error('Failed to generate types:', error);
    process.exit(1);
  }
}

generateTypes();
```

#### 2. Update package.json Scripts

```json
{
  "scripts": {
    "dev": "npm run generate:types && next dev",
    "build": "npm run generate:types && next build",
    "generate:types": "tsx scripts/generate-types.ts",
    "start": "next start",
    "lint": "next lint"
  }
}
```

### Type-Safe API Client

#### File: `lib/api/client.ts`

```typescript
import createClient from 'openapi-fetch';
import type { paths } from './types';

const baseUrl = process.env.NEXT_PUBLIC_API_URL || 
  'https://blog-writer-api-dev-613248238610.europe-west9.run.app';

export const client = createClient<paths>({
  baseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Type-safe API methods
export const api = {
  // Health & Status
  health: () => client.GET('/health'),
  config: () => client.GET('/api/v1/config'),
  metrics: () => client.GET('/api/v1/metrics'),
  
  // Blog Generation
  generateBlog: (body: BlogGenerateRequest) => 
    client.POST('/api/v1/blog/generate-gateway', { body }),
  
  polishContent: (body: PolishRequest) =>
    client.POST('/api/v1/blog/polish', { body }),
  
  checkQuality: (body: QualityCheckRequest) =>
    client.POST('/api/v1/blog/quality-check', { body }),
  
  generateMetaTags: (body: MetaTagsRequest) =>
    client.POST('/api/v1/blog/meta-tags', { body }),
  
  // Keywords
  analyzeKeywords: (body: KeywordAnalysisRequest) =>
    client.POST('/api/v1/keywords/analyze', { body }),
  
  // Jobs (for async operations)
  getJobStatus: (jobId: string) =>
    client.GET('/api/v1/blog/jobs/{job_id}', {
      params: { path: { job_id: jobId } }
    }),
};

// Type exports for components
export type {
  paths,
  components,
} from './types';

// Extract request/response types
export type BlogGenerateRequest = 
  paths['/api/v1/blog/generate-gateway']['post']['requestBody']['content']['application/json'];

export type BlogGenerateResponse = 
  paths['/api/v1/blog/generate-gateway']['post']['responses']['200']['content']['application/json'];

export type HealthResponse = 
  paths['/health']['get']['responses']['200']['content']['application/json'];

export type MetricsResponse = 
  paths['/api/v1/metrics']['get']['responses']['200']['content']['application/json'];
```

#### File: `lib/api/hooks.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type { BlogGenerateRequest, BlogGenerateResponse } from './client';

// Health check hook
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await api.health();
      return data;
    },
    refetchInterval: 30000, // Refetch every 30s
  });
}

// Metrics hook
export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: async () => {
      const { data } = await api.metrics();
      return data;
    },
    refetchInterval: 60000, // Refetch every minute
  });
}

// Blog generation mutation
export function useGenerateBlog() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: BlogGenerateRequest) => {
      const { data, error } = await api.generateBlog(request);
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      // Invalidate metrics to show updated usage
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
    },
  });
}

// Configuration hook
export function useConfig() {
  return useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const { data } = await api.config();
      return data;
    },
  });
}
```

---

## Feature Specifications

### 1. Dashboard Home

**Route:** `/`

**Purpose:** Overview of system status and key metrics

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Header                                                  │
├──────┬──────────────────────────────────────────────────┤
│      │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│ Side │  │ API      │  │ Requests │  │ Cost     │       │
│ bar  │  │ Status   │  │ Today    │  │ Today    │       │
│      │  └──────────┘  └──────────┘  └──────────┘       │
│      │                                                   │
│      │  ┌──────────────────┐  ┌──────────────────┐     │
│      │  │ Recent Requests  │  │ Model Usage      │     │
│      │  │ (Line Chart)     │  │ (Pie Chart)      │     │
│      │  └──────────────────┘  └──────────────────┘     │
└──────┴──────────────────────────────────────────────────┘
```

**Components:**
- 4 Metric Cards (Status, Requests, Cost, Cache Rate)
- Recent requests chart (last 24 hours)
- Model usage breakdown chart
- Quick action buttons (Test Generation, View Logs)

**Data Fetching:**
```typescript
// Example component
export default function DashboardPage() {
  const { data: health } = useHealth();
  const { data: metrics } = useMetrics();
  
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard 
          title="API Status" 
          value={health?.status} 
          icon={<ServerIcon />}
        />
        <MetricCard 
          title="Requests Today" 
          value={metrics?.requests_today}
          trend={+12}
        />
        <MetricCard 
          title="Cost Today" 
          value={`$${metrics?.cost_today?.toFixed(2)}`}
          trend={-5}
        />
        <MetricCard 
          title="Cache Hit Rate" 
          value={`${metrics?.cache_rate}%`}
        />
      </div>
      
      {/* Charts */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Requests (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <RequestsChart data={metrics?.time_series} />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Model Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <ModelUsageChart data={metrics?.model_usage} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

---

### 2. Testing Interface

**Route:** `/testing`

**Purpose:** Interactive interface to test blog generation with different parameters

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Testing Interface                                       │
├──────────────────────────┬───────────────────────────────┤
│                          │                               │
│  Configuration Form      │   Live Preview                │
│                          │                               │
│  ┌──────────────────┐   │   ┌───────────────────────┐   │
│  │ Topic            │   │   │ Loading...            │   │
│  │ [Input Field]    │   │   │                       │   │
│  └──────────────────┘   │   │ Or                    │   │
│                          │   │                       │   │
│  ┌──────────────────┐   │   │ Generated Content:    │   │
│  │ Keywords         │   │   │ # Blog Title          │   │
│  │ [Multi-input]    │   │   │                       │   │
│  └──────────────────┘   │   │ Content here...       │   │
│                          │   └───────────────────────┘   │
│  ┌──────────────────┐   │                               │
│  │ Word Count: 1500 │   │   ┌───────────────────────┐   │
│  │ [Slider]         │   │   │ Quality Score: 95/100 │   │
│  └──────────────────┘   │   │ Word Count: 1523      │   │
│                          │   │ Time: 12.3s          │   │
│  [Generate Button]       │   │ Cost: $0.023         │   │
│                          │   └───────────────────────┘   │
└──────────────────────────┴───────────────────────────────┘
```

**Components:**

#### BlogGenerationForm Component

**File:** `components/testing/BlogGenerationForm.tsx`

```typescript
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';

interface BlogGenerationFormProps {
  onSubmit: (data: BlogGenerateRequest) => void;
  isLoading: boolean;
}

export function BlogGenerationForm({ onSubmit, isLoading }: BlogGenerationFormProps) {
  const [formData, setFormData] = useState({
    topic: '',
    keywords: [],
    word_count: 1500,
    tone: 'professional',
    model: 'gpt-4o-mini',
    include_polishing: true,
    include_quality_check: true,
    include_meta_tags: true,
  });
  
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(formData); }}>
      <div className="space-y-4">
        {/* Topic Input */}
        <div>
          <Label htmlFor="topic">Blog Topic</Label>
          <Input
            id="topic"
            placeholder="e.g., Benefits of Python Programming"
            value={formData.topic}
            onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
            required
          />
        </div>
        
        {/* Keywords Multi-Input */}
        <div>
          <Label htmlFor="keywords">Keywords</Label>
          <KeywordInput
            value={formData.keywords}
            onChange={(keywords) => setFormData({ ...formData, keywords })}
          />
        </div>
        
        {/* Word Count Slider */}
        <div>
          <Label>Word Count: {formData.word_count}</Label>
          <Slider
            value={[formData.word_count]}
            onValueChange={([value]) => setFormData({ ...formData, word_count: value })}
            min={300}
            max={5000}
            step={100}
          />
        </div>
        
        {/* Tone Selector */}
        <div>
          <Label htmlFor="tone">Tone</Label>
          <Select
            value={formData.tone}
            onValueChange={(tone) => setFormData({ ...formData, tone })}
          >
            <option value="professional">Professional</option>
            <option value="casual">Casual</option>
            <option value="formal">Formal</option>
            <option value="friendly">Friendly</option>
          </Select>
        </div>
        
        {/* Model Selector */}
        <div>
          <Label htmlFor="model">AI Model</Label>
          <Select
            value={formData.model}
            onValueChange={(model) => setFormData({ ...formData, model })}
          >
            <option value="gpt-4o">GPT-4o (Highest Quality)</option>
            <option value="gpt-4o-mini">GPT-4o Mini (Balanced)</option>
            <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
            <option value="claude-3-haiku">Claude 3 Haiku (Fast)</option>
          </Select>
        </div>
        
        {/* Feature Toggles */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="polishing">AI Polishing</Label>
            <Switch
              id="polishing"
              checked={formData.include_polishing}
              onCheckedChange={(checked) => 
                setFormData({ ...formData, include_polishing: checked })
              }
            />
          </div>
          
          <div className="flex items-center justify-between">
            <Label htmlFor="quality">Quality Check</Label>
            <Switch
              id="quality"
              checked={formData.include_quality_check}
              onCheckedChange={(checked) => 
                setFormData({ ...formData, include_quality_check: checked })
              }
            />
          </div>
          
          <div className="flex items-center justify-between">
            <Label htmlFor="meta">Generate Meta Tags</Label>
            <Switch
              id="meta"
              checked={formData.include_meta_tags}
              onCheckedChange={(checked) => 
                setFormData({ ...formData, include_meta_tags: checked })
              }
            />
          </div>
        </div>
        
        {/* Submit Button */}
        <Button 
          type="submit" 
          className="w-full"
          disabled={isLoading}
        >
          {isLoading ? 'Generating...' : 'Generate Blog'}
        </Button>
      </div>
    </form>
  );
}
```

#### BlogPreview Component

**File:** `components/testing/BlogPreview.tsx`

```typescript
'use client';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import ReactMarkdown from 'react-markdown';
import { Copy, Download } from 'lucide-react';

interface BlogPreviewProps {
  content: string;
  metadata?: {
    word_count: number;
    quality_score: number;
    quality_grade: string;
    processing_time: number;
    model_used: string;
    meta_tags?: {
      title: string;
      description: string;
    };
  };
}

export function BlogPreview({ content, metadata }: BlogPreviewProps) {
  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    // Show toast notification
  };
  
  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'blog.md';
    a.click();
  };
  
  return (
    <div className="space-y-4">
      {/* Metadata Header */}
      {metadata && (
        <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
          <div className="flex gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Quality</p>
              <div className="flex items-center gap-2">
                <Badge variant={metadata.quality_score >= 90 ? 'success' : 'warning'}>
                  {metadata.quality_score}/100
                </Badge>
                <span className="text-sm">{metadata.quality_grade}</span>
              </div>
            </div>
            
            <div>
              <p className="text-sm text-muted-foreground">Words</p>
              <p className="font-medium">{metadata.word_count}</p>
            </div>
            
            <div>
              <p className="text-sm text-muted-foreground">Time</p>
              <p className="font-medium">{metadata.processing_time}s</p>
            </div>
            
            <div>
              <p className="text-sm text-muted-foreground">Model</p>
              <p className="font-medium text-xs">{metadata.model_used}</p>
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={handleCopy}>
              <Copy className="h-4 w-4 mr-2" />
              Copy
            </Button>
            <Button size="sm" variant="outline" onClick={handleDownload}>
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
          </div>
        </div>
      )}
      
      {/* Content Preview */}
      <div className="prose prose-sm max-w-none p-6 bg-background border rounded-lg">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
      
      {/* Meta Tags Preview */}
      {metadata?.meta_tags && (
        <div className="p-4 bg-muted rounded-lg">
          <h4 className="font-medium mb-2">Generated Meta Tags</h4>
          <dl className="space-y-2 text-sm">
            <div>
              <dt className="text-muted-foreground">Title:</dt>
              <dd className="font-medium">{metadata.meta_tags.title}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Description:</dt>
              <dd className="font-medium">{metadata.meta_tags.description}</dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
}
```

#### Testing Page

**File:** `app/testing/page.tsx`

```typescript
'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BlogGenerationForm } from '@/components/testing/BlogGenerationForm';
import { BlogPreview } from '@/components/testing/BlogPreview';
import { useGenerateBlog } from '@/lib/api/hooks';
import { Loader2 } from 'lucide-react';

export default function TestingPage() {
  const [result, setResult] = useState(null);
  const { mutate: generateBlog, isPending } = useGenerateBlog();
  
  const handleSubmit = (data) => {
    generateBlog(data, {
      onSuccess: (response) => {
        setResult(response);
      },
      onError: (error) => {
        console.error('Generation failed:', error);
        // Show error toast
      },
    });
  };
  
  return (
    <div className="container mx-auto py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Testing Interface</h1>
        <p className="text-muted-foreground">
          Test blog generation with different parameters and see results in real-time
        </p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration Panel */}
        <Card>
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <BlogGenerationForm 
              onSubmit={handleSubmit}
              isLoading={isPending}
            />
          </CardContent>
        </Card>
        
        {/* Preview Panel */}
        <Card>
          <CardHeader>
            <CardTitle>Preview</CardTitle>
          </CardHeader>
          <CardContent>
            {isPending ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <p className="ml-4 text-muted-foreground">
                  Generating blog... This may take 10-60 seconds
                </p>
              </div>
            ) : result ? (
              <BlogPreview 
                content={result.content}
                metadata={{
                  word_count: result.word_count,
                  quality_score: result.quality_score,
                  quality_grade: result.quality_grade,
                  processing_time: result.processing_time,
                  model_used: result.model_used,
                  meta_tags: result.meta_tags,
                }}
              />
            ) : (
              <div className="flex items-center justify-center py-12 text-muted-foreground">
                <p>Configure parameters and click Generate to see results</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

---

### 3. Analytics Dashboard

**Route:** `/analytics`

**Purpose:** Visualize usage metrics, costs, and performance data

**Key Metrics:**
- Total requests (by day/week/month)
- Cost breakdown by model
- Average response time
- Cache hit rate
- Token usage statistics

**Charts:**
1. **Requests Over Time** - Line chart showing request volume
2. **Cost Breakdown** - Pie chart by model
3. **Response Time Trend** - Line chart showing latency
4. **Model Usage** - Bar chart comparing models

**File:** `app/analytics/page.tsx`

```typescript
'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DateRangePicker } from '@/components/ui/date-range-picker';
import { RequestsChart } from '@/components/analytics/RequestsChart';
import { CostChart } from '@/components/analytics/CostChart';
import { ModelUsageTable } from '@/components/analytics/ModelUsageTable';
import { useMetrics } from '@/lib/api/hooks';
import { DollarSign, Activity, Clock, Zap } from 'lucide-react';

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState({
    from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
    to: new Date(),
  });
  
  const { data: metrics, isLoading } = useMetrics();
  
  if (isLoading) {
    return <div>Loading metrics...</div>;
  }
  
  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor usage, costs, and performance metrics
          </p>
        </div>
        
        <DateRangePicker
          value={dateRange}
          onChange={setDateRange}
        />
      </div>
      
      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.total_requests || 0}</div>
            <p className="text-xs text-muted-foreground">
              +12% from last period
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${metrics?.total_cost?.toFixed(2) || '0.00'}</div>
            <p className="text-xs text-muted-foreground">
              -5% from last period
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.avg_latency || 0}ms</div>
            <p className="text-xs text-muted-foreground">
              -8% from last period
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Cache Hit Rate</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.cache_rate || 0}%</div>
            <p className="text-xs text-muted-foreground">
              +3% from last period
            </p>
          </CardContent>
        </Card>
      </div>
      
      {/* Charts Section */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="costs">Costs</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Requests Over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <RequestsChart data={metrics?.time_series} />
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Cost Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <CostChart data={metrics?.cost_by_model} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="models">
          <Card>
            <CardHeader>
              <CardTitle>Model Usage Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <ModelUsageTable data={metrics?.model_stats} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

---

### 4. Configuration Panel

**Route:** `/configuration`

**Purpose:** Manage AI providers, API keys, and system settings

**Sections:**
1. **AI Providers** - Configure OpenAI, Anthropic, DeepSeek
2. **AI Gateway** - Configure LiteLLM/Vercel AI Gateway
3. **General Settings** - Default models, rate limits, etc.

**Security Notes:**
- API keys should be masked (show only last 4 characters)
- Changes should require confirmation
- Sensitive data should be stored in environment variables or secret manager

**File:** `app/configuration/page.tsx`

```typescript
'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AIProviderConfig } from '@/components/configuration/AIProviderConfig';
import { AIGatewayConfig } from '@/components/configuration/AIGatewayConfig';
import { GeneralConfig } from '@/components/configuration/GeneralConfig';
import { useConfig } from '@/lib/api/hooks';

export default function ConfigurationPage() {
  const { data: config, isLoading } = useConfig();
  
  if (isLoading) {
    return <div>Loading configuration...</div>;
  }
  
  return (
    <div className="container mx-auto py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Configuration</h1>
        <p className="text-muted-foreground">
          Manage AI providers, gateway settings, and system configuration
        </p>
      </div>
      
      <Tabs defaultValue="providers" className="space-y-4">
        <TabsList>
          <TabsTrigger value="providers">AI Providers</TabsTrigger>
          <TabsTrigger value="gateway">AI Gateway</TabsTrigger>
          <TabsTrigger value="general">General</TabsTrigger>
        </TabsList>
        
        <TabsContent value="providers">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>OpenAI</CardTitle>
                <CardDescription>
                  Configure OpenAI API access and default models
                </CardDescription>
              </CardHeader>
              <CardContent>
                <AIProviderConfig provider="openai" config={config?.openai} />
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Anthropic (Claude)</CardTitle>
                <CardDescription>
                  Configure Anthropic API access and default models
                </CardDescription>
              </CardHeader>
              <CardContent>
                <AIProviderConfig provider="anthropic" config={config?.anthropic} />
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>DeepSeek</CardTitle>
                <CardDescription>
                  Configure DeepSeek API access and default models
                </CardDescription>
              </CardHeader>
              <CardContent>
                <AIProviderConfig provider="deepseek" config={config?.deepseek} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="gateway">
          <Card>
            <CardHeader>
              <CardTitle>AI Gateway Configuration</CardTitle>
              <CardDescription>
                Configure LiteLLM proxy or Vercel AI Gateway for centralized AI routing
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AIGatewayConfig config={config?.ai_gateway} />
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle>General Settings</CardTitle>
              <CardDescription>
                Configure default models, rate limits, and other system settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <GeneralConfig config={config?.general} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

---

### 5. Monitoring & Logs

**Route:** `/monitoring`

**Purpose:** View real-time logs, system health, and error tracking

**Features:**
- System health indicators
- Real-time log streaming
- Error tracking and alerts
- Performance metrics

**File:** `app/monitoring/page.tsx`

```typescript
'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { HealthIndicator } from '@/components/monitoring/HealthIndicator';
import { LogViewer } from '@/components/monitoring/LogViewer';
import { ErrorList } from '@/components/monitoring/ErrorList';
import { useHealth } from '@/lib/api/hooks';

export default function MonitoringPage() {
  const { data: health } = useHealth();
  
  return (
    <div className="container mx-auto py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Monitoring & Logs</h1>
        <p className="text-muted-foreground">
          Monitor system health, view logs, and track errors
        </p>
      </div>
      
      {/* System Health */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>System Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <HealthIndicator
              service="Backend API"
              status={health?.status}
              url="https://blog-writer-api-dev-613248238610.europe-west9.run.app"
            />
            <HealthIndicator
              service="AI Gateway"
              status={health?.ai_gateway?.status}
              url={health?.ai_gateway?.base_url}
            />
            <HealthIndicator
              service="Database"
              status={health?.database?.status}
            />
          </div>
        </CardContent>
      </Card>
      
      {/* Recent Errors */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Recent Errors</CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorList />
        </CardContent>
      </Card>
      
      {/* Log Viewer */}
      <Card>
        <CardHeader>
          <CardTitle>Live Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <LogViewer />
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## Component Specifications

### Layout Components

#### Sidebar Navigation

**File:** `components/layout/Sidebar.tsx`

```typescript
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils/cn';
import {
  LayoutDashboard,
  Flask,
  BarChart3,
  Settings,
  Activity,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Testing', href: '/testing', icon: Flask },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Configuration', href: '/configuration', icon: Settings },
  { name: 'Monitoring', href: '/monitoring', icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();
  
  return (
    <div className="flex h-full w-64 flex-col border-r bg-background">
      {/* Logo */}
      <div className="flex h-16 items-center border-b px-6">
        <h1 className="text-xl font-bold">Blog Writer</h1>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      
      {/* Footer */}
      <div className="border-t p-4">
        <p className="text-xs text-muted-foreground">
          Version 1.0.0
        </p>
      </div>
    </div>
  );
}
```

#### Header Component

**File:** `components/layout/Header.tsx`

```typescript
'use client';

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useSession, signOut } from 'next-auth/react';
import { User, LogOut, Settings } from 'lucide-react';

export function Header() {
  const { data: session } = useSession();
  
  return (
    <header className="flex h-16 items-center justify-between border-b px-6">
      <div className="flex items-center gap-4">
        {/* Breadcrumbs or page title could go here */}
      </div>
      
      <div className="flex items-center gap-4">
        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-10 w-10 rounded-full">
              <Avatar>
                <AvatarImage src={session?.user?.image} />
                <AvatarFallback>
                  {session?.user?.name?.[0] || 'U'}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>
              <div className="flex flex-col">
                <span className="text-sm font-medium">{session?.user?.name}</span>
                <span className="text-xs text-muted-foreground">
                  {session?.user?.email}
                </span>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="mr-2 h-4 w-4" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => signOut()}>
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
```

---

## Deployment

### Environment Variables

**File:** `.env.local.example`

```bash
# Backend API
NEXT_PUBLIC_API_URL=https://blog-writer-api-dev-613248238610.europe-west9.run.app

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=generate-a-secure-random-string-here
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Optional: For direct Cloud Run log access
GOOGLE_CLOUD_PROJECT=api-ai-blog-writer
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Vercel Deployment

1. **Connect Repository to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import your GitHub repository

2. **Configure Build Settings**
   ```
   Framework Preset: Next.js
   Build Command: npm run build
   Output Directory: .next
   Install Command: npm install
   ```

3. **Add Environment Variables**
   - Go to Project Settings → Environment Variables
   - Add all variables from `.env.local.example`
   - Use different values for Production, Preview, Development

4. **Deploy**
   ```bash
   # Via CLI
   npm install -g vercel
   vercel --prod
   
   # Or push to main branch for automatic deployment
   git push origin main
   ```

### Vercel Configuration

**File:** `vercel.json`

```json
{
  "buildCommand": "npm run generate:types && npm run build",
  "installCommand": "npm install",
  "framework": "nextjs",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/:path*"
    }
  ],
  "headers": [
    {
      "source": "/:path*",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        }
      ]
    }
  ]
}
```

---

## Development Workflow

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/YOUR_ORG/blog-writer-dashboard.git
cd blog-writer-dashboard

# 2. Install dependencies
npm install

# 3. Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with your values

# 4. Generate types from backend
npm run generate:types

# 5. Run development server
npm run dev
```

### Daily Development

```bash
# Start dev server
npm run dev

# In another terminal, watch for type changes
npm run generate:types -- --watch

# Run linter
npm run lint

# Format code
npm run format
```

### Before Committing

```bash
# Generate latest types
npm run generate:types

# Run linter
npm run lint

# Run type check
npm run type-check

# Build to ensure no errors
npm run build
```

### Deploying Updates

```bash
# 1. Commit changes
git add .
git commit -m "Add new feature"

# 2. Push to GitHub
git push origin main

# 3. Vercel will automatically deploy
# Or manually deploy
vercel --prod
```

---

## API Endpoints Reference

### Complete Backend API Endpoints

Your backend exposes the following endpoints (automatically typed via OpenAPI):

#### Health & Status
- `GET /health` - Health check
- `GET /api/v1/config` - Get system configuration
- `GET /api/v1/metrics` - Get usage metrics
- `GET /api/v1/health/detailed` - Detailed health info

#### Blog Generation
- `POST /api/v1/blog/generate-gateway` - Generate blog (AI Gateway)
- `POST /api/v1/blog/generate-enhanced` - Generate blog (enhanced)
- `POST /api/v1/blog/polish` - Polish content
- `POST /api/v1/blog/quality-check` - Check quality
- `POST /api/v1/blog/meta-tags` - Generate meta tags

#### Keywords
- `POST /api/v1/keywords/analyze` - Analyze keywords
- `POST /api/v1/keywords/enhanced` - Enhanced keyword analysis
- `POST /api/v1/keywords/ai-optimization` - AI optimization
- `POST /api/v1/keywords/difficulty` - Keyword difficulty

#### Jobs (Async Operations)
- `GET /api/v1/blog/jobs/{job_id}` - Get job status
- `POST /api/v1/batch/generate` - Batch generation
- `GET /api/v1/batch/{job_id}/status` - Batch status

#### Topics & Suggestions
- `POST /api/v1/topics/recommend` - Recommend topics
- `POST /api/v1/keywords/ai-topic-suggestions` - AI topic suggestions

---

## Best Practices

### 1. Type Safety
- Always regenerate types when backend changes
- Use generated types for all API calls
- Leverage TypeScript's type inference
- Avoid `any` types

### 2. Performance
- Use React Query for data fetching and caching
- Implement proper loading states
- Optimize images with Next.js Image component
- Lazy load heavy components

### 3. Error Handling
- Always handle API errors gracefully
- Show user-friendly error messages
- Log errors for debugging
- Implement retry logic where appropriate

### 4. Security
- Never expose API keys in client code
- Use environment variables for secrets
- Implement proper authentication
- Validate user input

### 5. Code Organization
- Keep components small and focused
- Use custom hooks for reusable logic
- Follow Next.js App Router conventions
- Maintain consistent file naming

---

## Support & Resources

### Documentation
- **Next.js:** https://nextjs.org/docs
- **Shadcn/ui:** https://ui.shadcn.com
- **TanStack Query:** https://tanstack.com/query
- **OpenAPI TypeScript:** https://github.com/drwpow/openapi-typescript

### Backend API
- **API Docs:** https://blog-writer-api-dev-613248238610.europe-west9.run.app/docs
- **OpenAPI Schema:** https://blog-writer-api-dev-613248238610.europe-west9.run.app/openapi.json

### Getting Help
- Check the generated types in `lib/api/types.ts`
- Review backend API documentation
- Test endpoints in the testing interface
- Monitor logs in the monitoring dashboard

---

## Checklist for Frontend Team

### Initial Setup
- [ ] Create GitHub repository
- [ ] Initialize Next.js project
- [ ] Install all dependencies
- [ ] Set up Shadcn/ui
- [ ] Configure environment variables
- [ ] Generate types from OpenAPI schema

### Core Features
- [ ] Implement dashboard layout (sidebar, header)
- [ ] Create testing interface
- [ ] Build analytics dashboard with charts
- [ ] Implement configuration panel
- [ ] Add monitoring and log viewer

### Authentication
- [ ] Set up NextAuth.js
- [ ] Configure Google OAuth
- [ ] Implement protected routes
- [ ] Add user menu and session management

### Polish & Deploy
- [ ] Add loading states
- [ ] Implement error handling
- [ ] Add responsive design
- [ ] Test on different screen sizes
- [ ] Deploy to Vercel
- [ ] Set up CI/CD with GitHub Actions

---

**Questions or Issues?**

Contact the backend team or refer to the OpenAPI schema at:
`https://blog-writer-api-dev-613248238610.europe-west9.run.app/openapi.json`

**Happy coding!** 🚀

