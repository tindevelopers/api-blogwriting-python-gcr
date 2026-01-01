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

// Secrets sync mutation
export function useSyncSecrets() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: import('./client').SecretSyncRequest) => {
      const { data, error } = await api.syncSecrets(request);
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      // Invalidate secrets list
      queryClient.invalidateQueries({ queryKey: ['secrets'] });
    },
  });
}

// List secrets query
export function useSecrets() {
  return useQuery({
    queryKey: ['secrets'],
    queryFn: async () => {
      const { data, error } = await api.listSecrets();
      if (error) throw error;
      return data;
    },
  });
}

// Create/update secret mutation
export function useCreateOrUpdateSecret() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ name, value, labels }: { 
      name: string; 
      value: string; 
      labels?: Record<string, string>;
    }) => {
      const { data, error } = await api.createOrUpdateSecret(name, { value, labels });
      if (error) throw error;
      return data;
    },
    onSuccess: () => {
      // Invalidate secrets list and config
      queryClient.invalidateQueries({ queryKey: ['secrets'] });
      queryClient.invalidateQueries({ queryKey: ['config'] });
    },
  });
}

