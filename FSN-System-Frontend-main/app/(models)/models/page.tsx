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
import { PlatformSwitch } from "@/components/platform-switch"
import { GlobalSearchBar } from "@/components/search/global-search-bar"
import { PlatformHeader } from "@/components/platform-header"
import { LicenseBlocker } from "@/components/license-blocker"
import { AddModelDialog } from "@/components/add-model-dialog"

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
  const [isAddModelDialogOpen, setIsAddModelDialogOpen] = useState(false)
  const [editingModel, setEditingModel] = useState<Model | null>(null)
  const deleteModelMutation = useDeleteModel()

  // Load saved models from license-aware storage
  const loadModels = async () => {
    try {
      const savedModels = await licenseAwareStorageService.getModels()
      setModels(savedModels)
    } catch (error) {
      console.error('Failed to load models:', error)
      setModels([])
    }
  }

  useEffect(() => {
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
    setEditingModel(model)
    setIsAddModelDialogOpen(true)
  }

  return (
    <LicenseBlocker action="access model management">
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
      {/* Main Header Section - Platform Colors */}
      <PlatformHeader>
        <div className="absolute inset-0 opacity-10 bg-[length:40px_40px] bg-[image:url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGRlZnM+CjxwYXR0ZXJuIGlkPSJncmlkIiB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHBhdHRlcm5Vbml0cz0idXNlclNwYWNlT25Vc2UiPgo8cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiLz4KPC9wYXR0ZXJuPgo8L2RlZnM+CjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz4KPHN2Zz4K')]"></div>
        
        <div className="relative px-6 py-12">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center shadow-2xl">
                    <User className="w-6 h-6 text-black" />
                  </div>
                  <div>
                    <h1 className="text-4xl font-bold text-white tracking-tight">Models Management</h1>
                    <p className="text-gray-300 text-lg mt-1">Manage OnlyFans models and their profile information</p>
                  </div>
                </div>
                
                {/* Live Status Indicator */}
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 border border-white/20">
                    <div className="relative">
                      <div className="w-2 h-2 bg-pink-400 rounded-full animate-pulse"></div>
                      <div className="absolute inset-0 w-2 h-2 bg-pink-400 rounded-full animate-ping opacity-75"></div>
                    </div>
                    <span className="text-white text-sm font-medium">Models Active</span>
                  </div>
                  
                  <div className="text-white/60 text-sm">
                    Last updated: {new Date().toLocaleTimeString()}
                  </div>
                </div>
              </div>
              
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
                <div className="flex items-center space-x-4">
                  <Button 
                    onClick={() => {
                      setEditingModel(null)
                      setIsAddModelDialogOpen(true)
                    }}
                    className="bg-white text-black hover:bg-gray-100 font-semibold px-6 py-3 rounded-2xl shadow-2xl hover:shadow-3xl transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] border-0"
                  >
                    <Plus className="w-5 h-5 mr-2" />
                    Add Model
                  </Button>
                </div>
              </div>
            </div>
            
            {/* Search Bar and Platform Switcher - Integrated into header */}
            <div className="mt-8">
              <div className="flex items-center justify-between">
                {/* Search */}
                <div className="flex-1 max-w-md">
                  <GlobalSearchBar placeholder="Search models..." />
                </div>

                {/* Right side */}
                <div className="flex items-center space-x-4">
                  <PlatformSwitch />
                </div>
              </div>
            </div>
          </div>
        </div>
      </PlatformHeader>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Models List */}
        <div className="space-y-8">
          {models.length === 0 ? (
            <div className="bg-white rounded-3xl shadow-lg border border-gray-100 p-12">
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <User className="w-8 h-8 text-gray-600" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">No models found</h3>
                <p className="text-gray-600 mb-8 text-lg">
                  Get started by adding your first model to begin managing profiles
                </p>
                <Button 
                  onClick={() => {
                    setEditingModel(null)
                    setIsAddModelDialogOpen(true)
                  }} 
                  className="bg-black text-white hover:bg-gray-800 font-semibold px-8 py-3 rounded-2xl shadow-2xl hover:shadow-3xl transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98]"
                >
                  <Plus className="w-5 h-5 mr-2" />
                  Add Model
                </Button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {models.map((model) => (
                <Card key={model.id} className="relative bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100 group overflow-hidden">
                  <div className="h-1 w-full bg-gradient-to-r from-pink-400 to-rose-500"></div>
                  <CardContent className="p-6">
                    <div className="flex flex-col items-center space-y-4">
                      {/* Profile Photo */}
                      <div className="w-20 h-20 rounded-2xl overflow-hidden bg-gray-100 flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform duration-300">
                        {model.profilePhoto ? (
                          <img 
                            src={model.profilePhoto} 
                            alt={model.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <ImageIcon className="w-8 h-8 text-gray-500" />
                        )}
                      </div>
                      
                      {/* Model Name */}
                      <div className="text-center">
                        <h3 className="text-lg font-bold text-gray-900 mb-1">
                          {model.name}
                        </h3>
                        <p className="text-sm text-gray-500">
                          Added {new Date(model.createdAt).toLocaleDateString()}
                        </p>
                      </div>
                      
                      {/* Action Buttons */}
                      <div className="flex space-x-2 w-full">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEditModel(model)}
                          className="flex-1 bg-gray-50 hover:bg-gray-100 border-gray-200 text-gray-700 rounded-xl"
                        >
                          <Edit className="w-4 h-4 mr-1" />
                          Edit
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteModel(model.id)}
                          className="flex-1 bg-red-50 hover:bg-red-100 border-red-200 text-red-700 rounded-xl"
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

      {/* Add Model Dialog */}
      <AddModelDialog 
        open={isAddModelDialogOpen}
        onOpenChange={(open) => {
          setIsAddModelDialogOpen(open)
          if (!open) {
            setEditingModel(null)
          }
        }}
        onModelAdded={() => {
          loadModels() // Refresh the models list
        }}
        editModel={editingModel}
      />
      </div>
    </LicenseBlocker>
  )
}
