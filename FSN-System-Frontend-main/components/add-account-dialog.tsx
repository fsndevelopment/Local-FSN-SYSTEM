"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { User, Instagram, MessageCircle, RefreshCw, Plus } from "lucide-react"
import { licenseAwareStorageService, LocalAccount, LocalDevice } from "@/lib/services/license-aware-storage-service"
import { SuccessPopup } from "@/components/ui/unified-popup"
import { useDevices } from "@/lib/hooks/use-devices"

// Model interface
interface Model {
  id: string
  name: string
  profilePhoto?: string
  created_at: string
  updated_at: string
}

interface AddAccountDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onAccountAdded?: () => void
}

export function AddAccountDialog({ open, onOpenChange, onAccountAdded }: AddAccountDialogProps) {
  const [formData, setFormData] = useState({
    platform: "",
    username: "",
    authType: "email", // "email" or "2fa"
    email: "",
    twoFactorCode: "",
    password: "",
    model: "",
    device: "",
    notes: "",
    container_number: ""
  })
  const [showNewModelInput, setShowNewModelInput] = useState(false)
  const [newModelName, setNewModelName] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const [successMessage, setSuccessMessage] = useState("")
  const [generalError, setGeneralError] = useState("")
  
  // Data loading states
  const [devices, setDevices] = useState<LocalDevice[]>([])
  const [models, setModels] = useState<Model[]>([])
  
  // API hooks
  const { data: apiDevicesResponse } = useDevices()

  // Reset form
  const resetForm = () => {
    setFormData({
      platform: "",
      username: "",
      authType: "email",
      email: "",
      twoFactorCode: "",
      password: "",
      model: "",
      device: "",
      notes: "",
      container_number: ""
    })
    setShowNewModelInput(false)
    setNewModelName("")
    setGeneralError("")
  }

  // Load data when dialog opens or API data changes
  useEffect(() => {
    if (open) {
      loadData()
      resetForm()
    }
  }, [open, apiDevicesResponse])

  const loadData = async () => {
    try {
      // Load devices from both API and local storage
      const savedDevices = licenseAwareStorageService.getDevices()
      const apiDevices = Array.isArray(apiDevicesResponse) 
        ? apiDevicesResponse 
        : apiDevicesResponse?.devices || []
      
      // Combine API devices and local devices, removing duplicates
      const allDevices = [...apiDevices, ...savedDevices]
      const uniqueDevices = allDevices.filter((device, index, self) => 
        index === self.findIndex(d => d.id === device.id)
      )
      
      setDevices(uniqueDevices)
      
      // Load models from license-aware storage
      const savedModels = await licenseAwareStorageService.getModels()
      setModels(savedModels)
    } catch (error) {
      console.error('Failed to load data:', error)
      setDevices([])
      setModels([])
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    setGeneralError("")
  }

  const handleCreateNewModel = async () => {
    if (!newModelName.trim()) return

    try {
      const newModel = {
        id: Date.now().toString(),
        name: newModelName.trim(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
      
      await licenseAwareStorageService.addModel(newModel)
      const updatedModels = await licenseAwareStorageService.getModels()
      setModels(updatedModels)
      
      // Select the newly created model
      setFormData(prev => ({ ...prev, model: newModel.id }))
      setShowNewModelInput(false)
      setNewModelName("")
    } catch (error) {
      console.error('Failed to create model:', error)
      setGeneralError("Failed to create model. Please try again.")
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setGeneralError("")

    try {
      // Validate required fields
      if (!formData.platform) {
        setGeneralError("Please select a platform")
        return
      }

      if (!formData.username.trim()) {
        setGeneralError("Username is required")
        return
      }

      if (formData.authType === "email" && !formData.email.trim()) {
        setGeneralError("Email is required for email authentication")
        return
      }

      if (formData.authType === "2fa" && !formData.twoFactorCode.trim()) {
        setGeneralError("2FA code is required for 2FA authentication")
        return
      }

      if (!formData.password.trim()) {
        setGeneralError("Password is required")
        return
      }

      // Create account data
      const accountData: LocalAccount = {
        id: Date.now().toString(),
        platform: formData.platform as "instagram" | "threads" | "both",
        instagram_username: formData.platform === "instagram" || formData.platform === "both" ? formData.username : undefined,
        threads_username: formData.platform === "threads" || formData.platform === "both" ? formData.username : undefined,
        status: "active",
        warmup_phase: "phase_1",
        followers_count: null,
        model: formData.model,
        device: formData.device,
        notes: formData.notes,
        authType: formData.authType,
        email: formData.email || undefined,
        twoFactorCode: formData.twoFactorCode || undefined,
        password: formData.password || undefined,
        container_number: formData.container_number || undefined,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }

      // Save account
      await licenseAwareStorageService.addAccount(accountData)
      
      // Assign account to device if selected
      if (formData.device) {
        licenseAwareStorageService.assignDeviceToAccount(accountData.id, formData.device)
      }

      // Show success message
      setSuccessMessage("Account added successfully!")
      setShowSuccess(true)
      
      // Close dialog
      onOpenChange(false)
      
      // Notify parent component
      if (onAccountAdded) {
        onAccountAdded()
      }

    } catch (error: any) {
      console.error("Failed to add account:", error)
      setGeneralError("Failed to add account. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent 
          className="!w-[1000px] !h-[500px] !max-w-none !max-h-none bg-white rounded-2xl border-0 shadow-2xl flex flex-col"
          style={{ width: '1000px', height: '500px', maxWidth: 'none', maxHeight: 'none' }}
        >
          <DialogHeader className="pb-4 flex-shrink-0">
            <DialogTitle className="flex items-center gap-2 text-xl font-bold">
              <div className="w-10 h-10 bg-black rounded-xl flex items-center justify-center shadow-xl">
                <User className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-gray-900">Add New Account</div>
                <div className="text-xs font-normal text-gray-500 mt-0.5">Connect your social media account to the automation system</div>
              </div>
            </DialogTitle>
          </DialogHeader>

          <div className="grid grid-cols-3 gap-4 flex-1 overflow-y-auto">
            {/* Left Column - Account Information */}
            <div className="bg-gradient-to-br from-gray-50 to-gray-100/50 rounded-xl p-4 border border-gray-100">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-6 h-6 bg-gray-100 rounded-md flex items-center justify-center">
                  <User className="w-3 h-3 text-gray-600" />
                </div>
                <h3 className="font-semibold text-gray-900 text-sm">Account Information</h3>
              </div>
              
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label htmlFor="platform" className="text-xs font-semibold text-gray-700">
                    Platform <span className="text-red-500">*</span>
                  </Label>
                  <Select value={formData.platform} onValueChange={(value) => handleInputChange('platform', value)}>
                    <SelectTrigger className="h-9 rounded-md border-gray-200 focus:border-black focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs">
                      <SelectValue placeholder="Select platform" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="instagram">
                        <div className="flex items-center space-x-2">
                          <Instagram className="w-3 h-3" />
                          <span>Instagram</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="threads">
                        <div className="flex items-center space-x-2">
                          <MessageCircle className="w-3 h-3" />
                          <span>Threads</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="both">
                        <div className="flex items-center space-x-2">
                          <div className="flex space-x-1">
                            <Instagram className="w-3 h-3" />
                            <MessageCircle className="w-3 h-3" />
                          </div>
                          <span>Both</span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="username" className="text-xs font-semibold text-gray-700">
                    Username <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="username"
                    type="text"
                    value={formData.username}
                    onChange={(e) => handleInputChange('username', e.target.value)}
                    placeholder="e.g., john_doe"
                    className="h-9 rounded-md border-gray-200 focus:border-black focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="password" className="text-xs font-semibold text-gray-700">
                    Password <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="password"
                    type="password"
                    value={formData.password}
                    onChange={(e) => handleInputChange('password', e.target.value)}
                    placeholder="Enter password"
                    className="h-9 rounded-md border-gray-200 focus:border-black focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Middle Column - Authentication */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50/50 rounded-xl p-4 border border-blue-100">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-6 h-6 bg-blue-100 rounded-md flex items-center justify-center">
                  <RefreshCw className="w-3 h-3 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 text-sm">Authentication</h3>
              </div>
              
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label htmlFor="authType" className="text-xs font-semibold text-gray-700">
                    Authentication Type
                  </Label>
                  <Select value={formData.authType} onValueChange={(value) => handleInputChange('authType', value)}>
                    <SelectTrigger className="h-9 rounded-md border-gray-200 focus:border-blue-500 focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="email">Email Authentication</SelectItem>
                      <SelectItem value="2fa">2FA Authentication</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {formData.authType === "email" && (
                  <div className="space-y-1">
                    <Label htmlFor="email" className="text-xs font-semibold text-gray-700">
                      Email Address <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      placeholder="user@example.com"
                      className="h-9 rounded-md border-gray-200 focus:border-blue-500 focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs"
                    />
                  </div>
                )}

                {formData.authType === "2fa" && (
                  <div className="space-y-1">
                    <Label htmlFor="twoFactorCode" className="text-xs font-semibold text-gray-700">
                      2FA Secret Key <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="twoFactorCode"
                      type="text"
                      value={formData.twoFactorCode}
                      onChange={(e) => handleInputChange('twoFactorCode', e.target.value)}
                      placeholder="Enter 2FA secret key"
                      className="h-9 rounded-md border-gray-200 focus:border-blue-500 focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs font-mono"
                    />
                  </div>
                )}

                <div className="space-y-1">
                  <Label htmlFor="containerNumber" className="text-xs font-semibold text-gray-700">
                    Container Number
                  </Label>
                  <Input
                    id="containerNumber"
                    type="text"
                    value={formData.container_number}
                    onChange={(e) => handleInputChange('container_number', e.target.value)}
                    placeholder="e.g., 1"
                    className="h-9 rounded-md border-gray-200 focus:border-blue-500 focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs"
                  />
                  <p className="text-xs text-gray-500">
                    For Crane containers on jailbroken devices
                  </p>
                </div>
              </div>
            </div>

            {/* Right Column - Assignment */}
            <div className="bg-gradient-to-br from-green-50 to-emerald-50/50 rounded-xl p-4 border border-green-100">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-6 h-6 bg-green-100 rounded-md flex items-center justify-center">
                  <RefreshCw className="w-3 h-3 text-green-600" />
                </div>
                <h3 className="font-semibold text-gray-900 text-sm">Assignment</h3>
              </div>
              
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label htmlFor="model" className="text-xs font-semibold text-gray-700">
                    Assigned Model
                  </Label>
                  {!showNewModelInput ? (
                    <div className="space-y-1">
                      <Select value={formData.model} onValueChange={(value) => {
                        if (value === "create-new") {
                          setShowNewModelInput(true)
                        } else {
                          handleInputChange('model', value)
                        }
                      }}>
                        <SelectTrigger className="h-9 rounded-md border-gray-200 focus:border-green-500 focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs">
                          <SelectValue placeholder="Select model" />
                        </SelectTrigger>
                        <SelectContent>
                          {models.map((model) => (
                            <SelectItem key={model.id} value={model.id}>
                              <div className="flex items-center space-x-2">
                                {model.profilePhoto && (
                                  <img src={model.profilePhoto} alt={model.name} className="w-4 h-4 rounded-full" />
                                )}
                                <User className="w-3 h-3" />
                                <span className="text-xs">{model.name}</span>
                              </div>
                            </SelectItem>
                          ))}
                          <SelectItem value="create-new">
                            <div className="flex items-center space-x-2">
                              <Plus className="w-3 h-3" />
                              <span className="text-xs">Create New Model</span>
                            </div>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  ) : (
                    <div className="space-y-1">
                      <div className="flex space-x-1">
                        <Input
                          value={newModelName}
                          onChange={(e) => setNewModelName(e.target.value)}
                          placeholder="Enter model name"
                          className="h-9 rounded-md border-gray-200 focus:border-green-500 focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs"
                          onKeyPress={(e) => e.key === 'Enter' && handleCreateNewModel()}
                        />
                        <Button 
                          type="button"
                          onClick={handleCreateNewModel}
                          className="h-9 px-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-xs"
                          disabled={!newModelName.trim()}
                        >
                          <Plus className="w-3 h-3" />
                        </Button>
                      </div>
                      <Button 
                        type="button"
                        onClick={() => {
                          setShowNewModelInput(false)
                          setNewModelName("")
                        }}
                        variant="ghost"
                        className="h-6 px-2 text-xs"
                      >
                        Cancel
                      </Button>
                    </div>
                  )}
                </div>

                <div className="space-y-1">
                  <Label htmlFor="device" className="text-xs font-semibold text-gray-700">
                    Assigned Device
                  </Label>
                  <Select value={formData.device} onValueChange={(value) => handleInputChange('device', value)}>
                    <SelectTrigger className="h-9 rounded-md border-gray-200 focus:border-green-500 focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs">
                      <SelectValue placeholder="Select device" />
                    </SelectTrigger>
                    <SelectContent>
                      {devices.map((device) => (
                        <SelectItem key={device.id} value={device.id.toString()}>
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${
                              device.status === 'connected' ? 'bg-green-500' : 'bg-gray-400'
                            }`} />
                            <span className="text-xs">{device.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-1">
                  <Label htmlFor="notes" className="text-xs font-semibold text-gray-700">
                    Notes
                  </Label>
                  <Input
                    id="notes"
                    type="text"
                    value={formData.notes}
                    onChange={(e) => handleInputChange('notes', e.target.value)}
                    placeholder="Optional notes"
                    className="h-9 rounded-md border-gray-200 focus:border-green-500 focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Error Messages */}
          {generalError && (
            <div className="mt-2 flex-shrink-0">
              <div className="bg-red-50 border border-red-200 rounded-md p-2">
                <div className="text-red-800 font-semibold text-xs">{generalError}</div>
              </div>
            </div>
          )}


          <DialogFooter className="pt-3 flex-shrink-0">
            <Button 
              type="button"
              variant="outline" 
              onClick={() => onOpenChange(false)}
              className="h-9 px-4 rounded-md border-2 border-gray-200 hover:border-gray-300 font-semibold text-xs"
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              type="button"
              onClick={handleSubmit}
              disabled={isLoading || !formData.platform || !formData.username.trim() || !formData.password.trim()}
              className="h-9 px-6 bg-black text-white hover:bg-gray-800 rounded-md font-semibold shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 text-xs"
            >
              {isLoading ? (
                <div className="flex items-center space-x-1">
                  <RefreshCw className="w-3 h-3 animate-spin" />
                  <span>Adding...</span>
                </div>
              ) : (
                "Add Account"
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
