"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { User, Upload, Image as ImageIcon, RefreshCw } from "lucide-react"
import { SuccessPopup } from "@/components/ui/unified-popup"
import { licenseAwareStorageService } from "@/lib/services/license-aware-storage-service"

// Model interface
interface Model {
  id: string
  name: string
  profilePhoto?: string
  createdAt: string
  updatedAt: string
}

interface AddModelDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onModelAdded?: () => void
  editModel?: Model | null
}

export function AddModelDialog({ open, onOpenChange, onModelAdded, editModel }: AddModelDialogProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [modelName, setModelName] = useState("")
  const [profilePhoto, setProfilePhoto] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const [successMessage, setSuccessMessage] = useState("")
  const [generalError, setGeneralError] = useState("")

  const isEditMode = !!editModel

  // Reset form when dialog opens/closes or edit model changes
  useEffect(() => {
    if (open && editModel) {
      setModelName(editModel.name)
      setProfilePhoto(editModel.profilePhoto || "")
    } else if (open) {
      resetForm()
    }
  }, [open, editModel])

  const resetForm = () => {
    setModelName("")
    setProfilePhoto("")
    setGeneralError("")
  }

  const handleProfilePhotoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      // Check file size (5MB limit)
      if (file.size > 5 * 1024 * 1024) {
        setGeneralError("File size must be less than 5MB")
        return
      }

      // Check file type
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif']
      if (!allowedTypes.includes(file.type)) {
        setGeneralError("Only JPG, PNG, and GIF files are supported")
        return
      }

      const reader = new FileReader()
      reader.onload = (e) => {
        const result = e.target?.result as string
        setProfilePhoto(result)
        setGeneralError("")
      }
      reader.readAsDataURL(file)
    }
  }

  const removeProfilePhoto = () => {
    setProfilePhoto("")
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setGeneralError("")

    try {
      // Validate required fields
      if (!modelName.trim()) {
        setGeneralError("Model name is required")
        return
      }

      const modelData: Model = {
        id: editModel?.id || Date.now().toString(),
        name: modelName.trim(),
        profilePhoto: profilePhoto || undefined,
        createdAt: editModel?.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }

      if (isEditMode && editModel) {
        // Update existing model
        await licenseAwareStorageService.updateModel(editModel.id, modelData)
        setSuccessMessage("Model updated successfully!")
      } else {
        // Create new model
        await licenseAwareStorageService.addModel(modelData)
        setSuccessMessage("Model added successfully!")
      }

      setShowSuccess(true)
      
      // Close dialog
      onOpenChange(false)
      
      // Notify parent component
      if (onModelAdded) {
        onModelAdded()
      }

    } catch (error: any) {
      console.error("Failed to save model:", error)
      setGeneralError("Failed to save model. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent 
          className="!w-[600px] !h-[500px] !max-w-none !max-h-none bg-white rounded-2xl border-0 shadow-2xl flex flex-col"
          style={{ width: '600px', height: '500px', maxWidth: 'none', maxHeight: 'none' }}
        >
          <DialogHeader className="pb-4 flex-shrink-0">
            <DialogTitle className="flex items-center gap-2 text-xl font-bold">
              <div className="w-10 h-10 bg-black rounded-xl flex items-center justify-center shadow-xl">
                <User className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-gray-900">{isEditMode ? 'Edit Model' : 'Add New Model'}</div>
                <div className="text-xs font-normal text-gray-500 mt-0.5">
                  {isEditMode ? 'Update model information' : 'Add a new OnlyFans model to your collection'}
                </div>
              </div>
            </DialogTitle>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto">
            <div className="bg-gradient-to-br from-gray-50 to-gray-100/50 rounded-xl p-6 border border-gray-100 h-full">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                  <User className="w-4 h-4 text-gray-600" />
                </div>
                <h3 className="font-semibold text-gray-900 text-base">Model Information</h3>
              </div>
              
              <div className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="modelName" className="text-sm font-semibold text-gray-700">
                    Model Name <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="modelName"
                    type="text"
                    value={modelName}
                    onChange={(e) => {
                      setModelName(e.target.value)
                      setGeneralError("")
                    }}
                    placeholder="Enter model name"
                    className="h-12 rounded-lg border-gray-200 focus:border-black focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-sm"
                    required
                  />
                </div>

                <div className="space-y-3">
                  <Label className="text-sm font-semibold text-gray-700">Profile Photo</Label>
                  
                  <div className="flex items-start space-x-4">
                    {/* Photo Preview */}
                    <div className="w-20 h-20 bg-gray-100 rounded-xl border-2 border-dashed border-gray-300 flex items-center justify-center overflow-hidden">
                      {profilePhoto ? (
                        <img 
                          src={profilePhoto} 
                          alt="Profile preview" 
                          className="w-full h-full object-cover rounded-lg"
                        />
                      ) : (
                        <ImageIcon className="w-8 h-8 text-gray-400" />
                      )}
                    </div>
                    
                    {/* Upload Controls */}
                    <div className="flex-1 space-y-2">
                      <div className="flex space-x-2">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => fileInputRef.current?.click()}
                          className="h-10 px-4 rounded-lg border-2 border-gray-200 hover:border-gray-300 text-sm"
                        >
                          <Upload className="w-4 h-4 mr-2" />
                          Upload Photo
                        </Button>
                        
                        {profilePhoto && (
                          <Button
                            type="button"
                            variant="ghost"
                            onClick={removeProfilePhoto}
                            className="h-10 px-3 text-sm text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            Remove
                          </Button>
                        )}
                      </div>
                      
                      <p className="text-xs text-gray-500">
                        Upload a profile photo for this model. Supported formats: JPG, PNG, GIF. Max size: 5MB.
                      </p>
                    </div>
                  </div>
                  
                  {/* Hidden file input */}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/gif"
                    onChange={handleProfilePhotoUpload}
                    className="hidden"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Error Messages */}
          {generalError && (
            <div className="mt-3 flex-shrink-0">
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="text-red-800 font-semibold text-sm">{generalError}</div>
              </div>
            </div>
          )}

          <DialogFooter className="pt-4 flex-shrink-0">
            <Button 
              type="button"
              variant="outline" 
              onClick={() => onOpenChange(false)}
              className="h-10 px-4 rounded-lg border-2 border-gray-200 hover:border-gray-300 font-semibold text-sm"
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              type="button"
              onClick={handleSubmit}
              disabled={isLoading || !modelName.trim()}
              className="h-10 px-6 bg-black text-white hover:bg-gray-800 rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 text-sm"
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>{isEditMode ? 'Updating...' : 'Creating...'}</span>
                </div>
              ) : (
                isEditMode ? "Update Model" : "Create Model"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Success Popup */}
      <SuccessPopup 
        isOpen={showSuccess} 
        onClose={() => setShowSuccess(false)} 
        message={successMessage} 
      />
    </>
  )
}
