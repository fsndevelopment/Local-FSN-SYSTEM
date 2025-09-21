"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { HeroCard } from "@/components/hero-card"
import { Plus, Edit, Trash2, User, Image as ImageIcon } from "lucide-react"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ConfirmPopup } from "@/components/ui/unified-popup"
import { licenseAwareStorageService } from "@/lib/services/license-aware-storage-service"
import { useDeleteModel } from "@/lib/hooks/use-models"

// Model interface - using LocalModel format for consistency
interface Model {
  id: string
  name: string
  profilePhoto?: string
  createdAt: string
  updatedAt: string
}

export default function ModelsPage() {
  const router = useRouter()
  const [models, setModels] = useState<Model[]>([])
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [modelToDelete, setModelToDelete] = useState<string | null>(null)
  const deleteModelMutation = useDeleteModel()

  // Load saved models from license-aware storage
  useEffect(() => {
    const loadModels = async () => {
      try {
        const savedModels = await licenseAwareStorageService.getModels()
        setModels(savedModels)
      } catch (error) {
        console.error('Failed to load models:', error)
        setModels([])
      }
    }
    
    loadModels()
  }, [])

  // Save models to license-aware storage
  const saveModels = async (newModels: Model[]) => {
    setModels(newModels)
    try {
      await licenseAwareStorageService.saveModels(newModels)
    } catch (error) {
      console.error('Failed to save models:', error)
    }
  }

  // Handle model deletion
  const handleDeleteModel = (modelId: string) => {
    setModelToDelete(modelId)
    setShowDeleteConfirm(true)
  }

  const confirmDeleteModel = () => {
    if (modelToDelete) {
      deleteModelMutation.mutate(modelToDelete, {
        onSuccess: () => {
          // Reload models after successful deletion
          const loadModels = async () => {
            try {
              const savedModels = await licenseAwareStorageService.getModels()
              setModels(savedModels)
            } catch (error) {
              console.error('Failed to load models:', error)
              setModels([])
            }
          }
          loadModels()
        }
      })
    }
    setShowDeleteConfirm(false)
    setModelToDelete(null)
  }

  // Handle model editing
  const handleEditModel = (model: Model) => {
    router.push(`/models/add?edit=true&id=${model.id}&name=${encodeURIComponent(model.name)}&photo=${model.profilePhoto || ''}`)
  }

  return (
    <div className="space-y-6">
      <HeroCard title="Models Management" subtitle="Manage OnlyFans models and their profile information" icon={User}>
        <Button 
          onClick={() => router.push('/models/add')}
          className="bg-black text-white hover:bg-neutral-900 rounded-full px-6"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Model
        </Button>
      </HeroCard>

      {/* Models List */}
      <div className="space-y-4">
        {models.length === 0 ? (
          <div className="text-center py-12">
            <User className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">No models found</h3>
            <p className="text-muted-foreground mb-4">
              Get started by adding your first model
            </p>
            <Button onClick={() => router.push('/models/add')} className="bg-black text-white hover:bg-neutral-900">
              <Plus className="w-4 h-4 mr-2" />
              Add Model
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {models.map((model) => (
              <Card key={model.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex flex-col items-center space-y-4">
                    {/* Profile Photo */}
                    <div className="w-20 h-20 rounded-full overflow-hidden bg-muted flex items-center justify-center">
                      {model.profilePhoto ? (
                        <img 
                          src={model.profilePhoto} 
                          alt={model.name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <ImageIcon className="w-8 h-8 text-muted-foreground" />
                      )}
                    </div>
                    
                    {/* Model Name */}
                    <div className="text-center">
                      <h3 className="text-lg font-semibold text-foreground mb-1">
                        {model.name}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        Added {new Date(model.createdAt).toLocaleDateString()}
                      </p>
                    </div>
                    
                    {/* Action Buttons */}
                    <div className="flex space-x-2 w-full">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEditModel(model)}
                        className="flex-1"
                      >
                        <Edit className="w-4 h-4 mr-1" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteModel(model.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 flex-1"
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Popup */}
      <ConfirmPopup
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={confirmDeleteModel}
        title="Delete Model"
        message="Are you sure you want to delete this model? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
      />
    </div>
  )
}
