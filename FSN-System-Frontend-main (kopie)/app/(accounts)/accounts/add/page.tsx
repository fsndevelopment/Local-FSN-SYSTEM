"use client"

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { ArrowLeft, Instagram, MessageCircle, User, Plus, Smartphone, LayoutTemplate, Info, CheckCircle, AlertTriangle } from "lucide-react"
import { DeviceWithTemplate, Template } from "@/lib/types"
import { licenseAwareStorageService, LocalAccount, LocalDevice, LocalTemplate } from "@/lib/services/license-aware-storage-service"
import { SuccessPopup } from "@/components/ui/unified-popup"
import { useDevices } from "@/lib/hooks/use-devices"
import { useTemplates } from "@/lib/hooks/use-templates"
import { useModels } from "@/lib/hooks/use-models"

// Model interface
interface Model {
  id: string
  name: string
  profilePhoto?: string
  created_at: string
  updated_at: string
}

export default function AddAccountPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
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
  const [isEditMode, setIsEditMode] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [showSuccess, setShowSuccess] = useState(false)
  const [successMessage, setSuccessMessage] = useState("")
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [isLoadingEditData, setIsLoadingEditData] = useState(false)

  // Load models using the hook
  const { data: modelsData, isLoading: modelsLoading, refetch: refetchModels } = useModels()
  const models = modelsData?.items || []

  // Debug form data changes
  useEffect(() => {
    console.log("Form data changed:", formData)
  }, [formData])

  // Load form data from URL params for editing (now async)
  useEffect(() => {
    const loadEditData = async () => {
      const edit = searchParams.get('edit')
      const id = searchParams.get('id')

      console.log("Edit mode check:", { edit, id, searchParams: searchParams.toString() })

      if (edit === 'true' && id) {
        console.log("Setting edit mode for account ID:", id)
        setIsLoadingEditData(true) // Prevent form reset during edit data loading
        setIsEditMode(true)
        setEditId(id)
        
        // Load account data from license-aware storage (now async)
        const savedAccounts = await licenseAwareStorageService.getAccounts()
        console.log("All saved accounts:", savedAccounts)
        const accountToEdit = savedAccounts.find(account => account.id === id)
        console.log("Account to edit found:", accountToEdit)
        
        if (accountToEdit) {
          const newFormData = {
            platform: accountToEdit.platform || "",
            username: accountToEdit.instagram_username || accountToEdit.threads_username || "",
            authType: accountToEdit.authType || "email",
            email: accountToEdit.email || "",
            twoFactorCode: accountToEdit.twoFactorCode || "",
            password: accountToEdit.password || "",
            model: accountToEdit.model || "",
            device: accountToEdit.device || "",
            notes: accountToEdit.notes || "",
            container_number: accountToEdit.container_number || ""
          }
          console.log("Setting form data for edit:", newFormData)
          console.log("Dropdown values - model:", newFormData.model, "device:", newFormData.device)
          setFormData(newFormData)
          // Set loading to false after a brief delay to ensure form is updated
          setTimeout(() => {
            console.log("Setting isLoadingEditData to false after form data update")
            setIsLoadingEditData(false)
          }, 100)
        } else {
          console.log("Account not found for ID:", id)
          setIsLoadingEditData(false)
        }
      } else {
        console.log("Not in edit mode, edit:", edit, "id:", id)
      }
    }
    
    loadEditData()
  }, [searchParams])

  // Allow form changes after edit data is loaded
  useEffect(() => {
    if (isLoadingEditData && formData.platform && formData.username) {
      console.log("Edit data loaded, allowing form changes")
      console.log("Form data after loading:", formData)
      setIsLoadingEditData(false)
    }
  }, [formData.platform, formData.username, formData.model, formData.device, isLoadingEditData])

  // Additional protection: prevent form reset during edit mode
  useEffect(() => {
    if (isEditMode && formData.platform && formData.username) {
      console.log("Edit mode active with data, preventing form reset")
      // Don't allow form to be reset if we have edit data loaded
    }
  }, [isEditMode, formData.platform, formData.username])

  const handleSubmit = async (e: any) => {
    e.preventDefault()
    setIsLoading(true)

    // Client-side validation
    if (formData.password && formData.password.length < 6) {
      alert("Password must be at least 6 characters long")
      setIsLoading(false)
      return
    }

    try {
      console.log("Form data before save:", formData)
      console.log("Form data fields:", {
        platform: formData.platform,
        username: formData.username,
        authType: formData.authType,
        email: formData.email,
        twoFactorCode: formData.twoFactorCode,
        password: formData.password,
        model: formData.model,
        device: formData.device,
        notes: formData.notes,
        container_number: formData.container_number
      })
      console.log("Form data values check:", {
        "platform exists": !!formData.platform,
        "username exists": !!formData.username,
        "authType exists": !!formData.authType,
        "email exists": !!formData.email,
        "twoFactorCode exists": !!formData.twoFactorCode,
        "password exists": !!formData.password,
        "model exists": !!formData.model,
        "device exists": !!formData.device,
        "notes exists": !!formData.notes,
        "container_number exists": !!formData.container_number
      })
      console.log("Form data raw values:", {
        platform: `"${formData.platform}"`,
        username: `"${formData.username}"`,
        authType: `"${formData.authType}"`,
        email: `"${formData.email}"`,
        twoFactorCode: `"${formData.twoFactorCode}"`,
        password: `"${formData.password}"`,
        model: `"${formData.model}"`,
        device: `"${formData.device}"`,
        notes: `"${formData.notes}"`,
        container_number: `"${formData.container_number}"`
      })
      
      // Log each field individually to avoid truncation
      console.log("=== INDIVIDUAL FIELD VALUES ===")
      console.log("platform:", formData.platform)
      console.log("username:", formData.username)
      console.log("authType:", formData.authType)
      console.log("email:", formData.email)
      console.log("twoFactorCode:", formData.twoFactorCode)
      console.log("password:", formData.password)
      console.log("model:", formData.model)
      console.log("device:", formData.device)
      console.log("notes:", formData.notes)
      console.log("container_number:", formData.container_number)
      console.log("=== END FIELD VALUES ===")
      console.log(isEditMode ? "Updating account:" : "Adding account:", formData)
      
      // Create/update account using local storage service
      const accountData: LocalAccount = {
        id: editId || Date.now().toString(),
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
      
      console.log("Account data to save:", accountData)

      if (isEditMode && editId) {
        // For updates, use the async update method
        await licenseAwareStorageService.updateAccount(editId, accountData)
        // Update device assignment if device changed
        if (formData.device) {
          licenseAwareStorageService.assignDeviceToAccount(accountData.id, formData.device)
        }
        console.log("Account updated successfully")
      } else {
        // For new accounts, use the async add method
        await licenseAwareStorageService.addAccount(accountData)
        // Assign account to device
        if (formData.device) {
          licenseAwareStorageService.assignDeviceToAccount(accountData.id, formData.device)
        }
        console.log("Account added successfully")
      }
      
      // Debug: Check what was actually saved (now async)
      const savedAccounts = await licenseAwareStorageService.getAccounts()
      // Look for the account with the API ID (the last one added)
      const savedAccount = savedAccounts[savedAccounts.length - 1]
      console.log("Account saved to localStorage:", savedAccount)
      console.log("Looking for account ID:", accountData.id)
      console.log("Available account IDs:", savedAccounts.map(acc => acc.id))
      console.log("Using last account (API ID):", savedAccount?.id)
      console.log("All saved account fields:", {
        id: savedAccount?.id,
        platform: savedAccount?.platform,
        instagram_username: savedAccount?.instagram_username,
        threads_username: savedAccount?.threads_username,
        authType: savedAccount?.authType,
        email: savedAccount?.email,
        twoFactorCode: savedAccount?.twoFactorCode,
        password: savedAccount?.password,
        model: savedAccount?.model,
        device: savedAccount?.device,
        notes: savedAccount?.notes,
        container_number: savedAccount?.container_number,
        status: savedAccount?.status,
        warmup_phase: savedAccount?.warmup_phase,
        followers_count: savedAccount?.followers_count,
        created_at: savedAccount?.created_at,
        updated_at: savedAccount?.updated_at
      })
      
      // Log each saved field individually to avoid truncation
      console.log("=== SAVED ACCOUNT FIELD VALUES ===")
      console.log("id:", savedAccount?.id)
      console.log("platform:", savedAccount?.platform)
      console.log("instagram_username:", savedAccount?.instagram_username)
      console.log("threads_username:", savedAccount?.threads_username)
      console.log("authType:", savedAccount?.authType)
      console.log("email:", savedAccount?.email)
      console.log("twoFactorCode:", savedAccount?.twoFactorCode)
      console.log("password:", savedAccount?.password)
      console.log("model:", savedAccount?.model)
      console.log("device:", savedAccount?.device)
      console.log("notes:", savedAccount?.notes)
      console.log("container_number:", savedAccount?.container_number)
      console.log("status:", savedAccount?.status)
      console.log("warmup_phase:", savedAccount?.warmup_phase)
      console.log("followers_count:", savedAccount?.followers_count)
      console.log("created_at:", savedAccount?.created_at)
      console.log("updated_at:", savedAccount?.updated_at)
      console.log("=== END SAVED ACCOUNT FIELDS ===")
      
      await new Promise(resolve => setTimeout(resolve, 500)) // Brief delay for UX
      
      // Show success popup first
      setSuccessMessage(isEditMode ? "Account updated successfully!" : "Account created successfully!")
      setShowSuccess(true)
      setIsSubmitted(true) // Mark form as submitted to prevent further changes
      
      // Don't reset the form after successful submission - let the redirect handle it
      
      if (isEditMode) {
        // For editing, redirect back to accounts with updated data as URL params
        const params = new URLSearchParams({
          platform: formData.platform,
          username: formData.username,
          authType: formData.authType,
          email: formData.email,
          twoFactorCode: formData.twoFactorCode,
          password: formData.password,
          model: formData.model,
          device: formData.device,
          notes: formData.notes,
          editId: editId || '',
        })
        // Redirect after delay to allow popup to show
        setTimeout(() => {
          router.push(`/accounts?${params.toString()}&refresh=${Date.now()}`)
        }, 2000)
      } else {
        // For adding, redirect back to accounts with new data as URL params
        const params = new URLSearchParams({
          platform: formData.platform,
          username: formData.username,
          authType: formData.authType,
          email: formData.email,
          twoFactorCode: formData.twoFactorCode,
          password: formData.password,
          model: formData.model,
          device: formData.device,
          notes: formData.notes,
        })
        // Redirect after delay to allow popup to show
        setTimeout(() => {
          router.push(`/accounts?${params.toString()}&refresh=${Date.now()}`)
        }, 2000)
      }
      
      // Show success message
      console.log(isEditMode ? "Account updated successfully:" : "Account created successfully:", formData)
      
    } catch (error) {
      console.error(isEditMode ? "Failed to update account:" : "Failed to add account:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    console.log(`handleInputChange called: field="${field}", value="${value}", isSubmitted: ${isSubmitted}, isEditMode: ${isEditMode}, isLoadingEditData: ${isLoadingEditData}`)
    
    // Only prevent changes after successful submission
    if (isSubmitted) {
      console.log("Ignoring input change - form already submitted")
      return
    }
    
    // Allow changes during edit mode once data is loaded
    if (isEditMode && !isLoadingEditData) {
      console.log("Edit mode - allowing form changes")
      setFormData((prev: any) => {
        const newData = { ...prev, [field]: value }
        console.log(`Form data updated in edit mode:`, newData)
        return newData
      })
      return
    }
    
    // Allow changes when not in edit mode
    if (!isEditMode) {
      console.log("Normal mode - allowing form changes")
      setFormData((prev: any) => {
        const newData = { ...prev, [field]: value }
        console.log(`Form data updated:`, newData)
        return newData
      })
      return
    }
    
    // Block changes only during edit data loading
    if (isLoadingEditData) {
      console.log("Ignoring input change - still loading edit data")
      return
    }
  }

  // Use real models from localStorage instead of mock data

  // Load devices and templates from real API
  const { data: devicesData, isLoading: devicesLoading, error: devicesError } = useDevices()
  // Temporarily disable templates API to prevent infinite retry loop
  // const { data: templates = [], isLoading: templatesLoading, error: templatesError } = useTemplates()
  const templates: any[] = []
  const templatesLoading = false
  const templatesError = null

  // Extract devices array with proper fallback
  const devices = devicesData?.devices || []

  // Update devices with template information
  const devicesWithTemplates: DeviceWithTemplate[] = devices.map((device: any) => {
    const template = templates.find((t: any) => t.id === device.templateId)
    
    return {
      ...device,
      templateId: device.templateId,
      template,
      capacityStatus: "safe", // Default capacity status
      assignedAccountsCount: device.assignedAccountsCount || 0
    } as DeviceWithTemplate
  })

  const getCapacityIcon = (status: string) => {
    switch (status) {
      case "safe":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case "overloaded":
        return <AlertTriangle className="w-4 h-4 text-red-500" />
      default:
        return <Info className="w-4 h-4 text-gray-500" />
    }
  }

  const getCapacityColor = (status: string) => {
    switch (status) {
      case "safe":
        return "bg-green-100 text-green-800 border-green-200"
      case "warning":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "overloaded":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const handleModelChange = (value: string) => {
    console.log(`handleModelChange called: value="${value}", isSubmitted: ${isSubmitted}, isEditMode: ${isEditMode}, isLoadingEditData: ${isLoadingEditData}`)
    
    // Only prevent changes after successful submission
    if (isSubmitted) {
      console.log("Ignoring model change - form already submitted")
      return
    }
    
    // Block changes only during edit data loading
    if (isLoadingEditData) {
      console.log("Ignoring model change - still loading edit data")
      return
    }
    
    if (value === "new") {
      setShowNewModelInput(true)
      setFormData((prev: any) => {
        const newData = { ...prev, model: "" }
        console.log(`Model set to empty for new model:`, newData)
        return newData
      })
    } else {
      setShowNewModelInput(false)
      // Store the model name directly since we're using model.name as the value
      setFormData((prev: any) => {
        const newData = { ...prev, model: value }
        console.log(`Model set to:`, newData)
        return newData
      })
    }
  }

  const handleNewModelSubmit = () => {
    if (newModelName.trim()) {
      setFormData((prev: any) => ({ ...prev, model: newModelName.trim() }))
      setShowNewModelInput(false)
      setNewModelName("")
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Button
          onClick={() => router.back()}
          variant="outline"
          size="sm"
          className="rounded-full"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{isEditMode ? 'Edit Account' : 'Add New Account'}</h1>
          <p className="text-muted-foreground">{isEditMode ? 'Update account information' : 'Connect a new Instagram or Threads account'}</p>
        </div>
      </div>

      {/* Add Account Form */}
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center">
            <User className="w-5 h-5 mr-2" />
            Account Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="platform">Platform</Label>
              <Select 
                value={formData.platform} 
                onValueChange={(value: string) => handleInputChange('platform', value)}
                disabled={isSubmitted}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select platform" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="instagram">
                    <div className="flex items-center">
                      <Instagram className="w-4 h-4 mr-2" />
                      Instagram
                    </div>
                  </SelectItem>
                  <SelectItem value="threads">
                    <div className="flex items-center">
                      <MessageCircle className="w-4 h-4 mr-2" />
                      Threads
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="@username"
                value={formData.username}
                onChange={(e: any) => handleInputChange('username', e.target.value)}
                disabled={isSubmitted}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="authType">Authentication Method</Label>
              <Select 
                value={formData.authType} 
                onValueChange={(value: string) => handleInputChange('authType', value)}
                disabled={isSubmitted}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select authentication method" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="email">Non-2FA</SelectItem>
                  <SelectItem value="2fa">2FA</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* No email required for Non-2FA - removed as requested */}

            {formData.authType === "2fa" && (
              <div className="space-y-2">
                <Label htmlFor="twoFactorCode">2FA Token</Label>
                <Input
                  id="twoFactorCode"
                  type="text"
                  placeholder="Enter 2FA token"
                  value={formData.twoFactorCode}
                  onChange={(e: any) => handleInputChange('twoFactorCode', e.target.value)}
                  disabled={isSubmitted}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Enter the 2FA token from your authenticator app
                </p>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="password">Account Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e: any) => handleInputChange('password', e.target.value)}
                disabled={isSubmitted}
                required
                minLength={6}
              />
              <p className="text-xs text-muted-foreground">
                Enter the password for your {formData.platform === 'instagram' ? 'Instagram' : formData.platform === 'threads' ? 'Threads' : 'social media'} account
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="model">Model</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => refetchModels()}
                  className="text-xs"
                >
                  Refresh Models
                </Button>
              </div>
              <Select 
                value={formData.model} 
                onValueChange={handleModelChange}
                disabled={isSubmitted}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select or create a model" />
                </SelectTrigger>
                <SelectContent>
                  {models.length === 0 ? (
                    <SelectItem value="no-models" disabled>
                      <div className="flex items-center space-x-2">
                        <User className="w-4 h-4" />
                        <span>No models available</span>
                      </div>
                    </SelectItem>
                  ) : (
                    models.map((model: any) => (
                      <SelectItem key={model.id} value={model.name}>
                        <div className="flex items-center space-x-3">
                          <div className="w-6 h-6 rounded-full overflow-hidden bg-muted flex items-center justify-center">
                            {model.profilePhoto ? (
                              <img 
                                src={model.profilePhoto} 
                                alt={model.name}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <User className="w-3 h-3 text-muted-foreground" />
                            )}
                          </div>
                          <span>{model.name}</span>
                        </div>
                      </SelectItem>
                    ))
                  )}
                  <SelectItem value="new">
                    <div className="flex items-center">
                      <Plus className="w-4 h-4 mr-2" />
                      Create New Model
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
              
              <p className="text-xs text-muted-foreground">
                Choose which model this account will be assigned to.
                {models.length === 0 && (
                  <span className="block mt-1">
                    <Button
                      type="button"
                      variant="link"
                      className="p-0 h-auto text-xs text-blue-600 hover:text-blue-700"
                      onClick={() => router.push('/models/add')}
                    >
                      Create a model first
                    </Button>
                  </span>
                )}
              </p>
              
              {showNewModelInput && (
                <div className="flex space-x-2 mt-2">
                  <Input
                    placeholder="Enter new model name (e.g., Sarah, Jessica)"
                    value={newModelName}
                    onChange={(e: any) => setNewModelName(e.target.value)}
                    onKeyPress={(e: any) => e.key === 'Enter' && handleNewModelSubmit()}
                  />
                  <Button
                    type="button"
                    onClick={handleNewModelSubmit}
                    size="sm"
                    className="bg-black text-white hover:bg-neutral-900"
                  >
                    Add
                  </Button>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="device">Device Assignment</Label>
              <Select 
                value={formData.device} 
                onValueChange={(value: string) => handleInputChange('device', value)}
                disabled={isSubmitted}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select device to connect this account to">
                    {formData.device && (() => {
                      const selectedDevice = devicesWithTemplates.find(d => d.id.toString() === formData.device)
                      return selectedDevice ? (
                        <div className="flex items-center space-x-2">
                          <Smartphone className="w-4 h-4" />
                          <span>{selectedDevice.name}</span>
                        </div>
                      ) : null
                    })()}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {devicesLoading ? (
                    <div className="p-4 text-center text-muted-foreground">
                      <Smartphone className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>Loading devices...</p>
                    </div>
                  ) : devicesError ? (
                    <div className="p-4 text-center text-muted-foreground">
                      <Smartphone className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>Error loading devices</p>
                      <p className="text-xs">Please try refreshing the page</p>
                    </div>
                  ) : devicesWithTemplates.length === 0 ? (
                    <div className="p-4 text-center text-muted-foreground">
                      <Smartphone className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>No devices available</p>
                      <p className="text-xs">Add devices in the Device Management page first</p>
                    </div>
                  ) : (
                    devicesWithTemplates.map((device) => (
                      <SelectItem key={device.id} value={device.id.toString()}>
                        <div className="flex items-center justify-between w-full">
                          <div className="flex items-center space-x-2">
                            <Smartphone className="w-4 h-4" />
                            <span>{device.name}</span>
                          </div>
                          <div className="flex items-center space-x-1 ml-2">
                            {getCapacityIcon(device.capacityStatus)}
                            <span className="text-xs text-muted-foreground">
                              {device.assignedAccountsCount} accounts
                            </span>
                          </div>
                        </div>
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Choose which device this account will be assigned to. The account will inherit the device's template settings.
              </p>
            </div>

            {/* Container Number for Jailbroken Devices */}
            {formData.device && (() => {
              const selectedDevice = devicesWithTemplates.find(d => d.id.toString() === formData.device)
              return selectedDevice && selectedDevice.jailbroken ? (
                <div className="space-y-2">
                  <Label htmlFor="container_number">Container Number (Jailbroken Device)</Label>
                  <Input
                    id="container_number"
                    type="number"
                    placeholder="1"
                    value={formData.container_number}
                    onChange={(e: any) => {
                      const value = e.target.value
                      // Only allow numbers 1-999
                      if (value === '' || (parseInt(value) >= 1 && parseInt(value) <= 999)) {
                        handleInputChange('container_number', value)
                      }
                    }}
                    disabled={isSubmitted}
                    min="1"
                    max="999"
                  />
                  <p className="text-xs text-muted-foreground">
                    Enter the Crane container number for this account (1-999)
                  </p>
                </div>
              ) : null
            })()}

            <div className="space-y-2">
              <Label htmlFor="notes">Notes (Optional)</Label>
              <Input
                id="notes"
                type="text"
                placeholder="Any additional notes..."
                value={formData.notes}
                onChange={(e: any) => handleInputChange('notes', e.target.value)}
                disabled={isSubmitted}
              />
            </div>

            <div className="flex space-x-3 pt-4">
              <Button
                type="submit"
                disabled={isLoading || !formData.platform || !formData.username || !formData.model || !formData.device ||
                  (formData.authType === "2fa" && !formData.twoFactorCode)}
                className="bg-black text-white hover:bg-neutral-900"
              >
                {isLoading ? (isEditMode ? "Updating Account..." : "Adding Account...") : (isEditMode ? "Update Account" : "Add Account")}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
              >
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Security Notice */}
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>🔒 Security Notice</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Your account credentials are encrypted and stored securely. We recommend:
          </p>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• Using app-specific passwords when available</li>
            <li>• Enabling 2FA on your social media accounts</li>
            <li>• Regularly updating your passwords</li>
            <li>• Monitoring account activity for any suspicious behavior</li>
          </ul>
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
