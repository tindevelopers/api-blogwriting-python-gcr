import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, type BlogGenerateRequest, type BlogGenerateResponse } from './client';

// Health check hook
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data, error } = await api.health();
      if (error) throw error;
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
      const { data, error } = await api.metrics();
      if (error) throw error;
      return data;
    },
    refetchInterval: 60000, // Refetch every minute
  });
}

// Blog generation mutation
export function useGenerateBlog() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: BlogGenerateRequest): Promise<BlogGenerateResponse> => {
      const { data, error } = await api.generateBlog(request);
      if (error) throw error;
      return data as BlogGenerateResponse;
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
      const { data, error } = await api.config();
      if (error) throw error;
      return data;
    },
  });
}

// Polish content mutation
export function usePolishContent() {
  return useMutation({
    mutationFn: async ({ content, instructions, org_id }: { 
      content: string; 
      instructions: string; 
      org_id: string 
    }) => {
      const { data, error } = await api.polishContent({ content, instructions, org_id });
      if (error) throw error;
      return data;
    },
  });
}

// Quality check mutation
export function useCheckQuality() {
  return useMutation({
    mutationFn: async ({ content }: { content: string }) => {
      const { data, error } = await api.checkQuality({ content });
      if (error) throw error;
      return data;
    },
  });
}

