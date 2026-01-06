# Frontend Admin API Integration Guide

**Version:** 1.0  
**Last Updated:** 2026-01-04  
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication Setup](#authentication-setup)
3. [API Client Configuration](#api-client-configuration)
4. [Admin Endpoints](#admin-endpoints)
5. [TypeScript Types](#typescript-types)
6. [Complete Examples](#complete-examples)
7. [Error Handling](#error-handling)
8. [Environment Configuration](#environment-configuration)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install @supabase/supabase-js
# or
yarn add @supabase/supabase-js
```

### 2. Set Up Environment Variables

Create `.env.local`:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# API Base URLs
NEXT_PUBLIC_API_URL_DEV=https://blog-writer-api-dev-613248238610.europe-west9.run.app
NEXT_PUBLIC_API_URL_STAGING=https://blog-writer-api-staging-613248238610.europe-west9.run.app
NEXT_PUBLIC_API_URL_PROD=https://blog-writer-api-prod-613248238610.us-east1.run.app
```

### 3. Basic Usage

```typescript
import { getAdminToken } from '@/lib/auth'
import { adminApi } from '@/lib/api/admin'

// Get AI costs
const costs = await adminApi.getAICosts('default', 30)
console.log('Total cost:', costs.total_cost)
```

---

## 🔐 Authentication Setup

### Step 1: Initialize Supabase Client

Create `lib/auth/supabase.ts`:

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

### Step 2: Authentication Helper Functions

Create `lib/auth/admin.ts`:

```typescript
import { supabase } from './supabase'

/**
 * Sign in and get admin JWT token
 */
export async function signInAdmin(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (error) {
    throw new Error(`Authentication failed: ${error.message}`)
  }

  if (!data.session) {
    throw new Error('No session returned')
  }

  return {
    token: data.session.access_token,
    user: data.user,
    expiresAt: data.session.expires_at,
  }
}

/**
 * Get current admin token (from session)
 */
export async function getAdminToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token || null
}

/**
 * Check if user is admin
 */
export async function isAdmin(): Promise<boolean> {
  const { data } = await supabase.auth.getSession()
  if (!data.session) return false

  // Get user profile to check role
  const { data: profile } = await supabase
    .from('user_profiles')
    .select('role_id, roles(name)')
    .eq('id', data.session.user.id)
    .single()

  if (!profile) return false

  const roleName = (profile.roles as any)?.name?.toLowerCase()
  return roleName === 'admin' || roleName === 'system_admin'
}

/**
 * Sign out
 */
export async function signOut() {
  await supabase.auth.signOut()
}
```

### Step 3: Create Auth Context (Optional but Recommended)

Create `contexts/AuthContext.tsx`:

```typescript
'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '@/lib/auth/supabase'
import { getAdminToken, isAdmin } from '@/lib/auth/admin'

interface AuthContextType {
  token: string | null
  isAuthenticated: boolean
  isAdminUser: boolean
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isAdminUser, setIsAdminUser] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check initial session
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        setToken(data.session.access_token)
        setIsAuthenticated(true)
        checkAdminStatus()
      }
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (session) {
        setToken(session.access_token)
        setIsAuthenticated(true)
        await checkAdminStatus()
      } else {
        setToken(null)
        setIsAuthenticated(false)
        setIsAdminUser(false)
      }
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  const checkAdminStatus = async () => {
    const admin = await isAdmin()
    setIsAdminUser(admin)
  }

  const signIn = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) throw error
    if (data.session) {
      setToken(data.session.access_token)
      setIsAuthenticated(true)
      await checkAdminStatus()
    }
  }

  const signOut = async () => {
    await supabase.auth.signOut()
    setToken(null)
    setIsAuthenticated(false)
    setIsAdminUser(false)
  }

  return (
    <AuthContext.Provider
      value={{
        token,
        isAuthenticated,
        isAdminUser,
        loading,
        signIn,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
```

---

## 🔧 API Client Configuration

### Create Admin API Client

Create `lib/api/admin.ts`:

```typescript
import { getAdminToken } from '@/lib/auth/admin'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL_PROD || 
  process.env.NEXT_PUBLIC_API_URL_STAGING ||
  process.env.NEXT_PUBLIC_API_URL_DEV

/**
 * Make authenticated admin API request
 */
async function adminRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAdminToken()
  
  if (!token) {
    throw new Error('Not authenticated. Please sign in.')
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ 
      message: response.statusText 
    }))
    throw new Error(error.message || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Admin API client
 */
export const adminApi = {
  // ============================================
  // AI Usage & Cost Tracking
  // ============================================

  /**
   * Get AI cost breakdown for an organization
   * 
   * @param orgId - Organization ID (required, e.g., 'default')
   * @param days - Number of days to look back (default: 30, max: 365)
   * @param includeRequests - Include request-level rows (default: false)
   * @param limit - Cap request rows when includeRequests=true (default: 100, max: 1000)
   */
  getAICosts: async (
    orgId: string, 
    days: number = 30,
    includeRequests: boolean = false,
    limit: number = 100
  ) => {
    const params = new URLSearchParams({
      org_id: orgId,
      days: days.toString(),
      include_requests: includeRequests.toString(),
      limit: limit.toString()
    })
    return adminRequest<AICostBreakdown>(
      `/api/v1/admin/ai/costs?${params.toString()}`
    )
  },

  /**
   * Get AI usage statistics
   * 
   * @param orgId - Organization ID (optional)
   * @param days - Number of days to look back (default: 30, max: 365)
   */
  getAIUsage: async (orgId?: string, days: number = 30) => {
    const params = new URLSearchParams({ days: days.toString() })
    if (orgId) params.append('org_id', orgId)
    
    return adminRequest<AIUsageStats>(
      `/api/v1/admin/ai/usage?${params.toString()}`
    )
  },

  /**
   * Get AI cache performance statistics
   * 
   * @param orgId - Organization ID
   * @param days - Number of days to look back (default: 7, max: 90)
   */
  getAICacheStats: async (orgId: string, days: number = 7) => {
    return adminRequest<AICacheStats>(
      `/api/v1/admin/ai/cache-stats?org_id=${orgId}&days=${days}`
    )
  },

  // ============================================
  // Admin Status
  // ============================================

  /**
   * Get admin dashboard status overview
   */
  getStatus: async () => {
    return adminRequest<AdminStatus>('/api/v1/admin/status')
  },

  // ============================================
  // Job Management
  // ============================================

  /**
   * List all blog generation jobs
   */
  listJobs: async (status?: string, limit: number = 50, offset: number = 0) => {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    })
    if (status) params.append('status', status)
    
    return adminRequest<JobListResponse>(
      `/api/v1/admin/jobs?${params.toString()}`
    )
  },

  /**
   * Get job details
   */
  getJob: async (jobId: string) => {
    return adminRequest<JobDetails>(`/api/v1/admin/jobs/${jobId}`)
  },

  /**
   * Cancel a running job
   */
  cancelJob: async (jobId: string, reason?: string) => {
    return adminRequest<JobActionResponse>(
      `/api/v1/admin/jobs/${jobId}/cancel`,
      {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }
    )
  },

  /**
   * Retry a failed job
   */
  retryJob: async (jobId: string) => {
    return adminRequest<JobActionResponse>(
      `/api/v1/admin/jobs/${jobId}/retry`,
      {
        method: 'POST',
      }
    )
  },

  // ============================================
  // Logs Viewer
  // ============================================

  /**
   * Query Cloud Logging for application logs
   */
  getLogs: async (
    filter?: string,
    severity?: string,
    hours: number = 1,
    limit: number = 100
  ) => {
    const params = new URLSearchParams({
      hours: hours.toString(),
      limit: limit.toString(),
    })
    if (filter) params.append('filter', filter)
    if (severity) params.append('severity', severity)
    
    return adminRequest<LogsResponse>(`/api/v1/admin/logs?${params.toString()}`)
  },

  // ============================================
  // Secrets Management (Advanced)
  // ============================================

  /**
   * List all secrets (metadata only)
   */
  listSecrets: async () => {
    return adminRequest<SecretMetadata[]>('/api/v1/admin/secrets')
  },

  /**
   * Get secret value
   */
  getSecret: async (name: string) => {
    return adminRequest<SecretValue>(`/api/v1/admin/secrets/${name}`)
  },
}
```

---

## 📊 TypeScript Types

Create `types/admin.ts`:

```typescript
// AI Cost & Usage Types

export interface AICostBreakdown {
  org_id: string
  period: {
    start_date: string
    end_date: string
    days: number
  }
  summary: {
    total_cost: number
    total_requests: number
    total_tokens: number
    avg_cost_per_request: number
    avg_tokens_per_request: number
  }
  by_provider: Array<{
    provider_type: string
    total_cost: number
    total_requests: number
    total_tokens: number
    avg_cost_per_request: number
    avg_latency_ms: number
  }>
  by_source: Record<string, {
    total_cost: number
    total_requests: number
    total_tokens: number
  }>
  by_client: Record<string, {
    total_cost: number
    total_requests: number
    total_tokens: number
  }>
  by_date: Array<{
    date: string
    total_cost: number
    total_requests: number
    total_tokens: number
  }>
  requests?: Array<{
    request_id: string
    job_id: string | null
    timestamp: string
    provider_type: string
    model: string
    cost: number
    tokens: {
      prompt: number
      completion: number
      total: number
    }
    latency_ms: number
    status: string
    usage_source: string
    usage_client: string
    org_id: string
  }>
}

export interface DailyCost {
  date: string
  cost: number
  requests: number
  tokens: number
}

export interface AIUsageStats {
  org_id?: string
  total_requests: number
  total_tokens: number
  total_cost: number
  by_operation: Record<string, {
    count: number
    tokens: number
    cost: number
  }>
  by_model: Record<string, {
    count: number
    tokens: number
    cost: number
  }>
  daily: Record<string, {
    requests: number
    tokens: number
    cost: number
  }>
}

export interface AICacheStats {
  org_id: string
  days: number
  total_requests: number
  cache_hits: number
  cache_misses: number
  hit_rate: number
  estimated_savings: number
}

// Admin Status Types

export interface AdminStatus {
  admin_user: string
  timestamp: string
  services: {
    secret_manager: string
    cloud_logging: string
    usage_logging: 'enabled' | 'disabled'
  }
  jobs: {
    total: number
    pending: number
    processing: number
    completed: number
    failed: number
  }
}

// Job Management Types

export interface JobListResponse {
  jobs: JobSummary[]
  total: number
  limit: number
  offset: number
}

export interface JobSummary {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  topic?: string
  created_at: string
  completed_at?: string
  error?: string
}

export interface JobDetails extends JobSummary {
  request?: any
  result?: any
  started_at?: string
  progress?: number
}

export interface JobActionResponse {
  job_id: string
  cancelled?: boolean
  retried?: boolean
  cancelled_by?: string
  retried_by?: string
  reason?: string
  new_status?: string
  message?: string
}

// Logs Types

export interface LogsResponse {
  entries: LogEntry[]
  count: number
  filter: string
  hours: number
}

export interface LogEntry {
  timestamp: string
  severity: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  message: string
  labels: Record<string, string>
  trace?: string
}

// Secrets Types

export interface SecretMetadata {
  name: string
  create_time?: string
  labels: Record<string, string>
  version_count: number
}

export interface SecretValue {
  name: string
  value: string
  accessed_at: string
  accessed_by: string
}
```

---

## 💡 Complete Examples

### Example 1: AI Cost Dashboard Component

Create `components/admin/AICostDashboard.tsx`:

```typescript
'use client'

import { useEffect, useState } from 'react'
import { adminApi } from '@/lib/api/admin'
import { useAuth } from '@/contexts/AuthContext'
import type { AICostBreakdown } from '@/types/admin'

export function AICostDashboard({ orgId = 'default' }: { orgId?: string }) {
  const { isAdminUser, loading: authLoading } = useAuth()
  const [costs, setCosts] = useState<AICostBreakdown | null>(null)
  const [days, setDays] = useState(30)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAdminUser) return
    loadCosts()
  }, [orgId, days, isAdminUser])

  const loadCosts = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await adminApi.getAICosts(orgId, days)
      setCosts(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load costs')
    } finally {
      setLoading(false)
    }
  }

  if (authLoading) {
    return <div>Loading...</div>
  }

  if (!isAdminUser) {
    return <div>Admin access required</div>
  }

  if (loading) {
    return <div>Loading cost data...</div>
  }

  if (error) {
    return <div className="text-red-500">Error: {error}</div>
  }

  if (!costs) {
    return <div>No cost data available</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">AI Cost Breakdown</h2>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-4 py-2 border rounded"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value={365}>Last year</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500">Total Cost</div>
          <div className="text-3xl font-bold mt-2">
            ${costs.total_cost.toFixed(4)}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500">Organization</div>
          <div className="text-xl font-semibold mt-2">{costs.org_id}</div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-sm text-gray-500">Period</div>
          <div className="text-xl font-semibold mt-2">Last {costs.days} days</div>
        </div>
      </div>

      {Object.keys(costs.by_source).length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Cost by Source</h3>
          <div className="space-y-2">
            {Object.entries(costs.by_source).map(([source, cost]) => (
              <div key={source} className="flex justify-between">
                <span>{source}</span>
                <span className="font-semibold">${cost.toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {Object.keys(costs.by_client).length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Cost by Client</h3>
          <div className="space-y-2">
            {Object.entries(costs.by_client).map(([client, cost]) => (
              <div key={client} className="flex justify-between">
                <span>{client}</span>
                <span className="font-semibold">${cost.toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
```

### Example 2: Admin Status Component

Create `components/admin/AdminStatus.tsx`:

```typescript
'use client'

import { useEffect, useState } from 'react'
import { adminApi } from '@/lib/api/admin'
import { useAuth } from '@/contexts/AuthContext'
import type { AdminStatus } from '@/types/admin'

export function AdminStatus() {
  const { isAdminUser } = useAuth()
  const [status, setStatus] = useState<AdminStatus | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!isAdminUser) return
    loadStatus()
  }, [isAdminUser])

  const loadStatus = async () => {
    setLoading(true)
    try {
      const data = await adminApi.getStatus()
      setStatus(data)
    } catch (err) {
      console.error('Failed to load status:', err)
    } finally {
      setLoading(false)
    }
  }

  if (!isAdminUser) return null
  if (loading || !status) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">System Status</h2>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white p-4 rounded shadow">
          <div className="text-sm text-gray-500">Usage Logging</div>
          <div className={`text-lg font-semibold mt-1 ${
            status.services.usage_logging === 'enabled' 
              ? 'text-green-600' 
              : 'text-red-600'
          }`}>
            {status.services.usage_logging}
          </div>
        </div>

        <div className="bg-white p-4 rounded shadow">
          <div className="text-sm text-gray-500">Secret Manager</div>
          <div className="text-lg font-semibold mt-1">
            {status.services.secret_manager}
          </div>
        </div>
      </div>

      <div className="bg-white p-4 rounded shadow">
        <h3 className="font-semibold mb-2">Job Statistics</h3>
        <div className="grid grid-cols-5 gap-2 text-sm">
          <div>
            <div className="text-gray-500">Total</div>
            <div className="font-semibold">{status.jobs.total}</div>
          </div>
          <div>
            <div className="text-gray-500">Pending</div>
            <div className="font-semibold">{status.jobs.pending}</div>
          </div>
          <div>
            <div className="text-gray-500">Processing</div>
            <div className="font-semibold">{status.jobs.processing}</div>
          </div>
          <div>
            <div className="text-gray-500">Completed</div>
            <div className="font-semibold text-green-600">{status.jobs.completed}</div>
          </div>
          <div>
            <div className="text-gray-500">Failed</div>
            <div className="font-semibold text-red-600">{status.jobs.failed}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
```

### Example 3: Sign In Page

Create `app/admin/login/page.tsx`:

```typescript
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

export default function AdminLoginPage() {
  const router = useRouter()
  const { signIn, isAuthenticated, isAdminUser } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isAuthenticated && isAdminUser) {
      router.push('/admin/dashboard')
    }
  }, [isAuthenticated, isAdminUser, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      await signIn(email, password)
      router.push('/admin/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <h2 className="text-3xl font-bold text-center">Admin Sign In</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}
```

---

## ⚠️ Error Handling

### Standard Error Handling

```typescript
import { adminApi } from '@/lib/api/admin'

async function loadCosts() {
  try {
    const costs = await adminApi.getAICosts('default', 30)
    // Handle success
  } catch (error) {
    if (error instanceof Error) {
      if (error.message.includes('401') || error.message.includes('Not authenticated')) {
        // Redirect to login
        router.push('/admin/login')
      } else if (error.message.includes('403')) {
        // Show "Admin access required" message
        alert('Admin access required')
      } else {
        // Show generic error
        console.error('Failed to load costs:', error.message)
      }
    }
  }
}
```

### Error Boundary Component

```typescript
'use client'

import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class AdminErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Admin API Error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <h3 className="text-red-800 font-semibold">Error</h3>
          <p className="text-red-600">{this.state.error?.message}</p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded"
          >
            Try Again
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
```

---

## 🌍 Environment Configuration

### Environment-Specific Setup

Create `lib/api/config.ts`:

```typescript
const getApiUrl = () => {
  if (process.env.NODE_ENV === 'production') {
    return process.env.NEXT_PUBLIC_API_URL_PROD
  }
  if (process.env.NEXT_PUBLIC_ENVIRONMENT === 'staging') {
    return process.env.NEXT_PUBLIC_API_URL_STAGING
  }
  return process.env.NEXT_PUBLIC_API_URL_DEV
}

export const API_CONFIG = {
  baseUrl: getApiUrl() || 'https://blog-writer-api-dev-613248238610.europe-west9.run.app',
  timeout: 30000,
}
```

---

## 📝 Summary

### What's Available

✅ **AI Cost Tracking** - Get cost breakdowns by organization, source, and client  
✅ **AI Usage Statistics** - Track usage by operation, model, and time period  
✅ **Cache Statistics** - Monitor cache performance and savings  
✅ **Job Management** - List, view, cancel, and retry blog generation jobs  
✅ **System Status** - Check service health and usage logging status  
✅ **Logs Viewer** - Query application logs (advanced)  
✅ **Secrets Management** - Manage secrets (advanced, admin only)

### Key Points

1. **Authentication Required**: All admin endpoints require Supabase JWT Bearer token
2. **Admin Role Required**: User must have `admin` or `system_admin` role
3. **Usage Logging Enabled**: Firestore usage logging is enabled on all environments
4. **Environment URLs**: Different URLs for dev, staging, and production

### Next Steps

1. Set up Supabase authentication
2. Create admin user with proper role
3. Implement authentication context/provider
4. Use the admin API client to build your dashboard
5. Test with your organization ID

---

## 🔗 Related Documentation

- [Authentication Token Guide](./AUTHENTICATION_TOKEN_GUIDE.md) - Detailed token setup
- [Usage Logging Enable Guide](./USAGE_LOGGING_ENABLE_GUIDE.md) - Backend configuration
- [Frontend Testing Guide](./FRONTEND_TESTING_GUIDE.md) - General API testing

---

**Questions?** Check the backend API documentation or contact the backend team.

