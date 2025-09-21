/**
 * React Query hooks for Model Management
 * 
 * Custom hooks for managing model data
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/hooks/use-toast';
import { modelAPI } from '@/lib/services/license-api-service';
import { licenseAwareStorageService } from '@/lib/services/license-aware-storage-service';

// Model interface
export interface Model {
  id: string;
  name: string;
  profilePhoto?: string;
  created_at: string;
  updated_at: string;
}

// Query Keys
export const modelKeys = {
  all: ['models'] as const,
  lists: () => [...modelKeys.all, 'list'] as const,
  list: (filters?: any) => [...modelKeys.lists(), filters] as const,
  details: () => [...modelKeys.all, 'detail'] as const,
  detail: (id: string) => [...modelKeys.details(), id] as const,
};

// Hooks for Model Queries
export const useModels = (filters?: any) => {
  return useQuery({
    queryKey: modelKeys.list(filters),
    queryFn: async () => {
      // Always check license-aware storage first since models are stored there
      const savedModels = await licenseAwareStorageService.getModels();
      if (savedModels.length > 0) {
        return { items: savedModels, total: savedModels.length };
      }
      
      // If no license-aware storage data, try API as fallback
      try {
        const response = await modelAPI.getModels(filters);
        return response.data || { items: [], total: 0 };
      } catch (error) {
        console.error('Failed to fetch models:', error);
        return { items: [], total: 0 };
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useModel = (id: string) => {
  return useQuery({
    queryKey: modelKeys.detail(id),
    queryFn: async () => {
      try {
        const response = await modelAPI.getModel(id);
        return response.data;
      } catch (error) {
        console.error('Failed to fetch model:', error);
        // Fallback to license-aware storage if API fails
        const savedModels = await licenseAwareStorageService.getModels();
        return savedModels.find((model: Model) => model.id === id);
      }
    },
    enabled: !!id,
  });
};

// Hooks for Model Mutations
export const useCreateModel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (modelData: Omit<Model, 'id' | 'created_at' | 'updated_at'>) => {
      try {
        const response = await modelAPI.createModel(modelData);
        return response.data;
      } catch (error) {
        console.error('Failed to create model:', error);
        // Fallback to license-aware storage if API fails
        const newModel: Model = {
          ...modelData,
          id: Date.now().toString(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        
        await licenseAwareStorageService.addModel(newModel);
        
        return newModel;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: modelKeys.all });
      toast({
        title: "Model created",
        description: "Model has been created successfully.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.message || "Failed to create model.",
        variant: "destructive",
      });
    },
  });
};

export const useUpdateModel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...modelData }: Partial<Model> & { id: string }) => {
      try {
        const response = await modelAPI.updateModel(id, modelData);
        return response.data;
      } catch (error) {
        console.error('Failed to update model:', error);
        // Fallback to license-aware storage if API fails
        const savedModels = await licenseAwareStorageService.getModels();
        const index = savedModels.findIndex((model: Model) => model.id === id);
        if (index !== -1) {
          const updatedModel = { ...savedModels[index], ...modelData, updated_at: new Date().toISOString() };
          await licenseAwareStorageService.updateModel(id, updatedModel);
          return updatedModel;
        }
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: modelKeys.all });
      toast({
        title: "Model updated",
        description: "Model has been updated successfully.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.message || "Failed to update model.",
        variant: "destructive",
      });
    },
  });
};

export const useDeleteModel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      try {
        await modelAPI.deleteModel(id);
        return id;
      } catch (error) {
        console.error('Failed to delete model:', error);
        // Fallback to license-aware storage if API fails
        await licenseAwareStorageService.deleteModel(id);
        return id;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: modelKeys.all });
      toast({
        title: "Model deleted",
        description: "Model has been deleted successfully.",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Error",
        description: error.message || "Failed to delete model.",
        variant: "destructive",
      });
    },
  });
};
