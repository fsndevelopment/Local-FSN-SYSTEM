"use client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { ArrowLeft, User, Upload, Image as ImageIcon } from "lucide-react"
import { useState, useEffect, useRef } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { SuccessPopup } from "@/components/ui/unified-popup"
import { licenseAwareStorageService } from "@/lib/services/license-aware-storage-service"

// Model interface - using LocalModel format for consistency
interface Model {
  id: string
  name: string
  profilePhoto?: string
  createdAt: string
  updatedAt: string
}

export default function AddModelPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [modelName, setModelName] = useState("")
  const [profilePhoto, setProfilePhoto] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [isEditMode, setIsEditMode] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [showSuccess, setShowSuccess] = useState(false)
  const [successMessage, setSuccessMessage] = useState("")

  // Load form data from URL params for editing
  useEffect(() => {
    const edit = searchParams.get('edit')
    const id = searchParams.get('id')
    const name = searchParams.get('name')
    const photo = searchParams.get('photo')

    if (edit === 'true' && id && name) {
      setIsEditMode(true)
      setEditId(id)
      setModelName(decodeURIComponent(name))
      if (photo) {
        setProfilePhoto(decodeURIComponent(photo))
      }
    }
  }, [searchParams])

  // Handle file upload
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file')
        return
      }

      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('File size must be less than 5MB')
        return
      }

      // Convert to base64 for storage
      const reader = new FileReader()
      reader.onload = (e) => {
        const result = e.target?.result as string
        setProfilePhoto(result)
      }
      reader.readAsDataURL(file)
    }
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!modelName.trim()) {
      alert('Please enter a model name')
      return
    }

    setIsLoading(true)

    try {
      // Load existing models from license-aware storage
      const existingModels = await licenseAwareStorageService.getModels()

      if (isEditMode && editId) {
        // Update existing model
        const updatedModel = {
          id: editId,
          name: modelName.trim(),
          profilePhoto: profilePhoto || undefined,
          createdAt: existingModels.find(m => m.id === editId)?.createdAt || new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }
        await licenseAwareStorageService.updateModel(editId, updatedModel)
        
        setSuccessMessage("Model updated successfully!")
      } else {
        // Create new model
        const newModel: Model = {
          id: Date.now().toString(),
          name: modelName.trim(),
          profilePhoto: profilePhoto || undefined,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }
        
        await licenseAwareStorageService.addModel(newModel)
        
        setSuccessMessage("Model created successfully!")
      }

      setShowSuccess(true)
      
      // Redirect back to models page after a short delay
      setTimeout(() => {
        router.push('/models')
      }, 1500)

    } catch (error) {
      console.error('Failed to save model:', error)
      alert('Failed to save model. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  // Remove profile photo
  const removeProfilePhoto = () => {
    setProfilePhoto("")
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Button
          variant="outline"
          size="icon"
          onClick={() => router.push('/models')}
        >
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {isEditMode ? 'Edit Model' : 'Add New Model'}
          </h1>
          <p className="text-muted-foreground">
            {isEditMode ? 'Update model information' : 'Add a new OnlyFans model to your collection'}
          </p>
        </div>
      </div>

      {/* Form */}
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <User className="w-5 h-5" />
            <span>Model Information</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Model Name */}
            <div className="space-y-2">
              <Label htmlFor="modelName">Model Name *</Label>
              <Input
                id="modelName"
                type="text"
                placeholder="Enter model name"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                required
                className="w-full"
              />
            </div>

            {/* Profile Photo */}
            <div className="space-y-4">
              <Label>Profile Photo</Label>
              
              {/* Photo Preview */}
              <div className="flex items-center space-x-4">
                <div className="w-20 h-20 rounded-full overflow-hidden bg-muted flex items-center justify-center">
                  {profilePhoto ? (
                    <img 
                      src={profilePhoto} 
                      alt="Profile preview"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <ImageIcon className="w-8 h-8 text-muted-foreground" />
                  )}
                </div>
                
                <div className="space-y-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    {profilePhoto ? 'Change Photo' : 'Upload Photo'}
                  </Button>
                  
                  {profilePhoto && (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={removeProfilePhoto}
                      className="w-full text-red-600 hover:text-red-700"
                    >
                      Remove Photo
                    </Button>
                  )}
                </div>
              </div>
              
              <p className="text-sm text-muted-foreground">
                Upload a profile photo for this model. Supported formats: JPG, PNG, GIF. Max size: 5MB.
              </p>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push('/models')}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isLoading || !modelName.trim()}
                className="bg-black text-white hover:bg-neutral-900"
              >
                {isLoading ? 'Saving...' : (isEditMode ? 'Update Model' : 'Create Model')}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Success Popup */}
      <SuccessPopup
        isOpen={showSuccess}
        onClose={() => setShowSuccess(false)}
        title={successMessage}
        autoClose={true}
        duration={3000}
      />
    </div>
  )
}
