/**
 * Template Management Hooks
 * 
 * React Query hooks for template API operations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { 
  templateAPI, 
  templateQueryKeys, 
  Template, 
  TemplateCreate, 
  TemplateUpdate 
} from '@/lib/api/templates'
import { usePlatform } from '@/lib/platform'

// Get all templates with optional filtering
export function useTemplates(params?: {
  skip?: number
  limit?: number
  platform?: string
}) {
  const [platform] = usePlatform()
  return useQuery({
    queryKey: templateQueryKeys.list({ ...(params || {}), platform }),
    queryFn: () => templateAPI.getTemplates(params),
    staleTime: 5 * 60 * 1000, // 5 minutes for template list
  })
}

// Get specific template by ID
export function useTemplate(id: number) {
  return useQuery({
    queryKey: templateQueryKeys.detail(id),
    queryFn: () => templateAPI.getTemplate(id),
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10 minutes for template details
  })
}

// Create template mutation
export function useCreateTemplate() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (templateData: TemplateCreate) => templateAPI.createTemplate(templateData),
    onSuccess: (newTemplate) => {
      // Invalidate and refetch template lists
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.lists() })
      
      // Add the new template to the cache
      queryClient.setQueryData(
        templateQueryKeys.detail(newTemplate.id),
        newTemplate
      )
      
      toast.success(`Template "${newTemplate.name}" created successfully`)
    },
    onError: (error: any) => {
      toast.error(`Failed to create template: ${error.detail || 'Unknown error'}`)
    },
  })
}

// Update template mutation
export function useUpdateTemplate() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TemplateUpdate }) => 
      templateAPI.updateTemplate(id, data),
    onSuccess: (updatedTemplate) => {
      // Update the template in cache
      queryClient.setQueryData(
        templateQueryKeys.detail(updatedTemplate.id),
        updatedTemplate
      )
      
      // Invalidate template lists to reflect changes
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.lists() })
      
      toast.success(`Template "${updatedTemplate.name}" updated successfully`)
    },
    onError: (error: any) => {
      toast.error(`Failed to update template: ${error.detail || 'Unknown error'}`)
    },
  })
}

// Delete template mutation
export function useDeleteTemplate() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => templateAPI.deleteTemplate(id),
    onSuccess: (_, deletedId) => {
      // Remove template from cache
      queryClient.removeQueries({ queryKey: templateQueryKeys.detail(deletedId) })
      
      // Invalidate template lists
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.lists() })
      
      toast.success('Template deleted successfully')
    },
    onError: (error: any) => {
      toast.error(`Failed to delete template: ${error.detail || 'Unknown error'}`)
    },
  })
}

// Execute template mutation
export function useExecuteTemplate() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ templateId, deviceId }: { templateId: number; deviceId: number }) => 
      templateAPI.executeTemplate(templateId, deviceId),
    onSuccess: (_, { templateId }) => {
      // Invalidate template details to reflect execution status
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.detail(templateId) })
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.lists() })
      
      toast.success('Template execution started')
    },
    onError: (error: any) => {
      toast.error(`Failed to execute template: ${error.detail || 'Unknown error'}`)
    },
  })
}

// Stop template mutation
export function useStopTemplate() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (templateId: number) => templateAPI.stopTemplate(templateId),
    onSuccess: (_, templateId) => {
      // Invalidate template details to reflect stop status
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.detail(templateId) })
      queryClient.invalidateQueries({ queryKey: templateQueryKeys.lists() })
      
      toast.success('Template execution stopped')
    },
    onError: (error: any) => {
      toast.error(`Failed to stop template: ${error.detail || 'Unknown error'}`)
    },
  })
}
