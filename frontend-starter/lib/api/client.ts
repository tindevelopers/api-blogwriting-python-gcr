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
  
  // Blog Generation - AI Gateway Endpoint
  generateBlog: (body: BlogGenerateRequest) => 
    client.POST('/api/v1/blog/generate-gateway', { body }),
  
  // Content Operations
  polishContent: (params: { content: string; instructions: string; org_id: string }) =>
    client.POST('/api/v1/blog/polish', { params: { query: params } }),
  
  checkQuality: (params: { content: string }) =>
    client.POST('/api/v1/blog/quality-check', { params: { query: params } }),
  
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

// Type exports
export type { paths, components } from './types';

// Extract commonly used types
export type BlogGenerateRequest = {
  topic: string;
  keywords: string[];
  org_id: string;
  user_id: string;
  word_count?: number;
  tone?: string;
  model?: string;
  custom_instructions?: string;
  include_polishing?: boolean;
  include_quality_check?: boolean;
  include_meta_tags?: boolean;
};

export type BlogGenerateResponse = {
  content: string;
  title: string;
  word_count: number;
  quality_score: number;
  quality_grade: string;
  processing_time: number;
  model_used: string;
  meta_tags?: {
    title: string;
    description: string;
    og_title: string;
    og_description: string;
  };
};

export type MetaTagsRequest = {
  content: string;
  title: string;
  keywords: string[];
  org_id: string;
  user_id: string;
};

export type KeywordAnalysisRequest = {
  keywords: string[];
  location?: string;
  language?: string;
};

export default client;

