"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Plus, Edit, Trash2, Copy, Settings, Instagram, MessageSquare, FolderOpen, Hash, FileText, Play, Square, Pause, LayoutTemplate } from "lucide-react"

import { Template } from "@/lib/types"
import { licenseAwareStorageService, LocalTemplate } from "@/lib/services/license-aware-storage-service"
import { SuccessPopup } from "@/components/ui/unified-popup"
import { HeroCard } from "@/components/hero-card"
import { usePlatform } from "@/lib/platform"
import { TemplateExecutionDialog } from "@/components/template-execution-dialog"
import { useDevices } from "@/lib/hooks/use-devices"
import { useAccounts } from "@/lib/hooks/use-accounts"


export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const [successMessage, setSuccessMessage] = useState("")
  const [runningTemplates, setRunningTemplates] = useState<Set<string>>(new Set())
  const [platform] = usePlatform()
  
  // Template execution dialog state
  const [isExecutionDialogOpen, setIsExecutionDialogOpen] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  
  // Load devices and accounts for execution
  const { data: devices } = useDevices()
  const { data: accounts } = useAccounts()
  
  // Load templates from license-aware storage service
  useEffect(() => {
    const loadTemplates = async () => {
      try {
        const savedTemplates = await licenseAwareStorageService.getTemplates()
        // Filter templates by current platform
        const filteredTemplates = savedTemplates.filter(t => t.platform === platform)
        setTemplates(filteredTemplates)
      } catch (error) {
        console.error('Failed to load templates:', error)
        setTemplates([])
      }
    }
    
    loadTemplates()
  }, [platform])
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null)
  const [formData, setFormData] = useState({
    name: "",
    platform: "threads" as "threads" | "instagram",
    captionsFile: "",
    photosPostsPerDay: 0,
    photosFolder: "",
    textPostsPerDay: 0,
    textPostsFile: "",
    followsPerDay: 0,
    likesPerDay: 0,
    scrollingTimeMinutes: 0
  })

  // Load templates from license-aware storage on component mount
  useEffect(() => {
    const loadTemplates = async () => {
      try {
        const savedTemplates = await licenseAwareStorageService.getTemplates()
        // Filter templates by current platform
        const filteredTemplates = savedTemplates.filter((t: Template) => t.platform === platform)
        setTemplates(filteredTemplates)
      } catch (error) {
        console.error('Failed to load templates:', error)
        // Fallback to empty array
        setTemplates([])
      }
    }
    
    loadTemplates()
  }, [platform])

  // Folder picker function - opens native file explorer
  const handleFolderSelect = (folderType: string) => {
    // Create a hidden file input element
    const input = document.createElement('input')
    input.type = 'file'
    input.webkitdirectory = true
    input.multiple = false
    input.style.display = 'none'
    
    input.onchange = (e) => {
      const files = (e.target as HTMLInputElement).files
      if (files && files.length > 0) {
        // Get the folder path from the first file
        const folderPath = files[0].webkitRelativePath.split('/')[0]
        setFormData({...formData, [folderType]: folderPath})
      }
    }
    
    // Trigger the file picker
    document.body.appendChild(input)
    input.click()
    document.body.removeChild(input)
  }

  // File picker function for XLSX files
  const handleFileSelect = (fileType: string) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.xlsx,.xls'
    input.style.display = 'none'
    
    input.onchange = (e) => {
      const files = (e.target as HTMLInputElement).files
      if (files && files.length > 0) {
        const file = files[0]
        const fileName = file.name
        
        // Read file and convert to base64
        const reader = new FileReader()
        reader.onload = (event) => {
          const base64Content = event.target?.result as string
          
          // Update form data with both filename and content
          if (fileType === 'textPostsFile') {
            setFormData({
              ...formData, 
              [fileType]: fileName,
              textPostsFileContent: base64Content
            })
          } else if (fileType === 'captionsFile') {
            setFormData({
              ...formData, 
              [fileType]: fileName,
              captionsFileContent: base64Content
            })
          }
        }
        reader.readAsDataURL(file) // This creates base64 data URL
      }
    }
    
    document.body.appendChild(input)
    input.click()
    document.body.removeChild(input)
  }

  const handleCreateTemplate = async () => {
    const newTemplate: LocalTemplate = {
      id: Date.now().toString(),
      ...formData,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    
    try {
      // Save to license-aware storage service
      await licenseAwareStorageService.addTemplate(newTemplate)
      
      // Update local state
      const updatedTemplates = [...templates, newTemplate]
      setTemplates(updatedTemplates)
      
      // Show success message
      setSuccessMessage("Template created successfully!")
      setShowSuccess(true)
      
      setIsCreateDialogOpen(false)
      resetForm()
    } catch (error) {
      console.error('Failed to create template:', error)
      setSuccessMessage("Failed to create template. Please try again.")
      setShowSuccess(true)
    }
  }

  const handleEditTemplate = (template: Template) => {
    setEditingTemplate(template)
    setFormData({
      name: template.name,
      platform: template.platform,
      captionsFile: template.captionsFile || "",
      photosPostsPerDay: template.photosPostsPerDay,
      photosFolder: template.photosFolder || "",
      textPostsPerDay: template.textPostsPerDay,
      textPostsFile: template.textPostsFile || "",
      followsPerDay: template.followsPerDay,
      likesPerDay: template.likesPerDay,
      scrollingTimeMinutes: template.scrollingTimeMinutes
    })
    setIsEditDialogOpen(true)
  }

  const handleUpdateTemplate = async () => {
    if (!editingTemplate) return
    
    const updatedTemplate: LocalTemplate = {
      ...editingTemplate,
      ...formData,
      updatedAt: new Date().toISOString()
    }
    
    try {
      // Save to license-aware storage service
      await licenseAwareStorageService.updateTemplate(editingTemplate.id, updatedTemplate)
      
      // Update local state
      const updatedTemplates = templates.map(t => 
        t.id === editingTemplate.id ? updatedTemplate : t
      )
      setTemplates(updatedTemplates)
      
      // Show success message
      setSuccessMessage("Template updated successfully!")
      setShowSuccess(true)
      
      setIsEditDialogOpen(false)
      setEditingTemplate(null)
      resetForm()
    } catch (error) {
      console.error('Failed to update template:', error)
      setSuccessMessage("Failed to update template. Please try again.")
      setShowSuccess(true)
    }
  }

  const handleDeleteTemplate = async (id: string) => {
    try {
      // Delete from license-aware storage service
      await licenseAwareStorageService.deleteTemplate(id)
      
      // Update local state
      const updatedTemplates = templates.filter(t => t.id !== id)
      setTemplates(updatedTemplates)
      
      // Show success message
      setSuccessMessage("Template deleted successfully!")
      setShowSuccess(true)
    } catch (error) {
      console.error('Failed to delete template:', error)
      setSuccessMessage("Failed to delete template. Please try again.")
      setShowSuccess(true)
    }
  }

  const handleDuplicateTemplate = async (template: Template) => {
    const duplicatedTemplate: Template = {
      ...template,
      id: Date.now().toString(),
      name: `${template.name} (Copy)`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    
    try {
      const updatedTemplates = [...templates, duplicatedTemplate]
      setTemplates(updatedTemplates)
      
      // Save to license-aware storage
      await licenseAwareStorageService.saveTemplates(updatedTemplates)
      
      setSuccessMessage("Template duplicated successfully!")
      setShowSuccess(true)
    } catch (error) {
      console.error('Failed to duplicate template:', error)
      setSuccessMessage("Failed to duplicate template. Please try again.")
      setShowSuccess(true)
    }
  }

  const resetForm = () => {
    setFormData({
      name: "",
      platform: "threads",
      captionsFile: "",
      photosPostsPerDay: 0,
      photosFolder: "",
      textPostsPerDay: 0,
      textPostsFile: "",
      followsPerDay: 0,
      likesPerDay: 0,
      scrollingTimeMinutes: 0
    })
  }

  const calculateTotalActions = (template: Template) => {
    return template.photosPostsPerDay + template.textPostsPerDay + template.likesPerDay + template.followsPerDay
  }

  const handleExecuteTemplate = (template: Template) => {
    setSelectedTemplate(template)
    setIsExecutionDialogOpen(true)
  }

  const handleTemplateExecution = async (request: any) => {
    try {
      // Include the actual template data in the request
      const templateExecutionRequest = {
        ...request,
        template_data: {
          id: selectedTemplate?.id,
          name: selectedTemplate?.name,
          platform: selectedTemplate?.platform,
          settings: {
            textPostsPerDay: selectedTemplate?.textPostsPerDay || 0,
            textPostsFile: selectedTemplate?.textPostsFile || "",
            textPostsFileContent: selectedTemplate?.textPostsFileContent || "", // Include xlsx file content
            photosPostsPerDay: selectedTemplate?.photosPostsPerDay || 0,
            photosFolder: selectedTemplate?.photosFolder || "",
            captionsFile: selectedTemplate?.captionsFile || "",
            captionsFileContent: selectedTemplate?.captionsFileContent || "", // Include xlsx file content
            followsPerDay: selectedTemplate?.followsPerDay || 0,
            likesPerDay: selectedTemplate?.likesPerDay || 0,
            scrollingTimeMinutes: selectedTemplate?.scrollingTimeMinutes || 0
          }
        }
      }
      
      // Call backend API to execute template
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/templates/${selectedTemplate?.id}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(templateExecutionRequest)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `Failed to start template: ${response.statusText}`)
      }
      
      const result = await response.json()
      console.log('Template execution started:', result)
      
      // Show success message
      setSuccessMessage(`${selectedTemplate?.name} started successfully!`)
      setShowSuccess(true)
      
      // Add to running templates
      if (selectedTemplate) {
        setRunningTemplates(prev => new Set([...prev, selectedTemplate.id]))
      }
      
    } catch (error) {
      console.error('Failed to start template:', error)
      setSuccessMessage(`Failed to start ${selectedTemplate?.name}: ${error.message}`)
      setShowSuccess(true)
    }
  }

  const handleStopTemplate = async (template: Template) => {
    try {
      // Call backend API to stop template
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/templates/${template.id}/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // Add license key if needed
      })
      
      if (!response.ok) {
        throw new Error(`Failed to stop template: ${response.statusText}`)
      }
      
      const result = await response.json()
      console.log('Template execution stopped:', result)
      
      // Remove from running templates
      setRunningTemplates(prev => {
        const newSet = new Set(prev)
        newSet.delete(template.id)
        return newSet
      })
      
      // Show success message
      setSuccessMessage(`${template.name} stopped successfully!`)
      setShowSuccess(true)
    } catch (error) {
      console.error('Failed to stop template:', error)
      setSuccessMessage(`Failed to stop ${template.name}: ${error.message}`)
      setShowSuccess(true)
    }
  }

  const isTemplateRunning = (templateId: string) => {
    return runningTemplates.has(templateId)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
      {/* Modern Header Section */}
      <div className="relative overflow-hidden bg-gradient-to-r from-black via-gray-900 to-black">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGRlZnM+CjxwYXR0ZXJuIGlkPSJncmlkIiB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHBhdHRlcm5Vbml0cz0idXNlclNwYWNlT25Vc2UiPgo8cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiLz4KPC9wYXR0ZXJuPgo8L2RlZnM+CjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz4KPHN2Zz4K')] opacity-10"></div>
        
        <div className="relative px-6 py-12">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center shadow-2xl">
                    <LayoutTemplate className="w-6 h-6 text-black" />
                  </div>
                  <div>
                    <h1 className="text-4xl font-bold text-white tracking-tight">Templates</h1>
                    <p className="text-gray-300 text-lg mt-1">Create and manage daily action templates for your devices</p>
                  </div>
                </div>
                
                {/* Live Status Indicator */}
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 border border-white/20">
                    <div className="relative">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                      <div className="absolute inset-0 w-2 h-2 bg-green-400 rounded-full animate-ping opacity-75"></div>
                    </div>
                    <span className="text-white text-sm font-medium">Live Templates</span>
                  </div>
                  
                  <div className="text-white/60 text-sm">
                    {templates.length} templates available
                  </div>
                </div>
              </div>
              
              <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                <DialogTrigger asChild>
                  <Button 
                    onClick={resetForm}
                    className="bg-white text-black hover:bg-gray-100 font-semibold px-6 py-3 rounded-2xl shadow-2xl hover:shadow-3xl transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] border-0"
                  >
                    <Plus className="w-5 h-5 mr-2" />
                    Create Template
                  </Button>
                </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Template</DialogTitle>
              <DialogDescription>
                Define daily limits, content types, and safety buffers for your automation templates.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-6 py-4">
              {/* Basic Information */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Template Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="e.g., Conservative Threads Template"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="platform">Platform</Label>
                  <Select
                    value={formData.platform}
                    onValueChange={(value: "threads" | "instagram") => setFormData({...formData, platform: value})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select platform" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="threads">
                        <div className="flex items-center">
                          <Hash className="w-4 h-4 mr-2" />
                          Threads
                        </div>
                      </SelectItem>
                      <SelectItem value="instagram">
                        <div className="flex items-center">
                          <Instagram className="w-4 h-4 mr-2" />
                          Instagram
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Photos Posts per Day with Folder Selection */}
              <div className="space-y-2">
                <Label>Photos Posts per Day</Label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    placeholder="Photos per Day"
                    type="number"
                    min="0"
                    value={formData.photosPostsPerDay}
                    onChange={(e) => setFormData({...formData, photosPostsPerDay: parseInt(e.target.value) || 0})}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    className="justify-start text-left"
                    onClick={() => handleFolderSelect('photosFolder')}
                  >
                    <FolderOpen className="w-4 h-4 mr-2" />
                    {formData.photosFolder || "Select photos folder"}
                  </Button>
                </div>
              </div>

              {/* Text Posts per Day with XLSX File Selection */}
              <div className="space-y-2">
                <Label>Text Posts per Day</Label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    placeholder="Text Posts per Day"
                    type="number"
                    min="0"
                    value={formData.textPostsPerDay}
                    onChange={(e) => setFormData({...formData, textPostsPerDay: parseInt(e.target.value) || 0})}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    className="justify-start text-left"
                    onClick={() => handleFileSelect('textPostsFile')}
                  >
                    <FolderOpen className="w-4 h-4 mr-2" />
                    {formData.textPostsFile || "Select XLSX file"}
                  </Button>
                </div>
              </div>

              {/* Follows and Likes per Day */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="followsPerDay">Follows per Day</Label>
                  <Input
                    id="followsPerDay"
                    type="number"
                    min="0"
                    value={formData.followsPerDay}
                    onChange={(e) => setFormData({...formData, followsPerDay: parseInt(e.target.value) || 0})}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="likesPerDay">Likes per Day</Label>
                  <Input
                    id="likesPerDay"
                    type="number"
                    min="0"
                    value={formData.likesPerDay}
                    onChange={(e) => setFormData({...formData, likesPerDay: parseInt(e.target.value) || 0})}
                  />
                </div>
              </div>

              {/* Captions and Scrolling Time */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Captions (for photos)</Label>
                  <Button
                    type="button"
                    variant="outline"
                    className="justify-start text-left w-full"
                    onClick={() => handleFileSelect('captionsFile')}
                  >
                    <FolderOpen className="w-4 h-4 mr-2" />
                    {formData.captionsFile || "Select XLSX file"}
                  </Button>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="scrollingTimeMinutes">Scrolling Time (in minutes)</Label>
                  <Input
                    id="scrollingTimeMinutes"
                    type="number"
                    min="0"
                    value={formData.scrollingTimeMinutes}
                    onChange={(e) => setFormData({...formData, scrollingTimeMinutes: parseInt(e.target.value) || 0})}
                    placeholder="e.g., 30"
                  />
                </div>
              </div>

            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateTemplate}>
                Create Template
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {templates.map((template) => (
            <Card key={template.id} className="relative bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100 group overflow-hidden">
              {/* Status Strip */}
              <div className={`h-1 w-full ${isTemplateRunning(template.id) ? 'bg-gradient-to-r from-green-400 to-emerald-500' : 'bg-gradient-to-r from-gray-200 to-gray-300'}`}></div>
              
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-xl font-bold text-gray-900 mb-2">{template.name}</CardTitle>
                    <div className="flex items-center space-x-3">
                      <Badge variant="secondary" className="text-xs bg-gray-100 text-gray-700 border border-gray-200">
                        {template.platform === "threads" ? (
                          <div className="flex items-center">
                            <div className="text-gray-600 text-sm font-bold mr-1">#</div>
                            Threads
                          </div>
                        ) : (
                          <div className="flex items-center">
                            <div className="text-gray-600 text-sm font-bold mr-1">📷</div>
                            Instagram
                          </div>
                        )}
                      </Badge>
                      {isTemplateRunning(template.id) && (
                        <Badge className="text-xs bg-green-500 text-white border-0">
                          <div className="flex items-center">
                            <div className="text-white text-sm font-bold mr-1">▶</div>
                            Running
                          </div>
                        </Badge>
                      )}
                      <span className="text-xs text-gray-500">
                        {new Date(template.createdAt).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <div className="flex space-x-1">
                    {isTemplateRunning(template.id) ? (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleStopTemplate(template)}
                        className="h-8 w-8 p-0 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-xl"
                        title="Stop Template"
                      >
                        <div className="text-red-600 text-sm font-bold">■</div>
                      </Button>
                    ) : (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleExecuteTemplate(template)}
                        className="h-8 w-8 p-0 text-green-500 hover:text-green-700 hover:bg-green-50 rounded-xl"
                        title="Start Template"
                      >
                        <div className="text-green-600 text-sm font-bold">▶</div>
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditTemplate(template)}
                      className="h-8 w-8 p-0 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-xl"
                      title="Edit Template"
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDuplicateTemplate(template)}
                      className="h-8 w-8 p-0 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-xl"
                      title="Duplicate Template"
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteTemplate(template.id)}
                      className="h-8 w-8 p-0 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-xl"
                      title="Delete Template"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-6 space-y-6">
                {/* Content Section */}
                <div className="space-y-3">
                  <h4 className="text-sm font-bold text-gray-900 uppercase tracking-wide">Content</h4>
                  <div className="space-y-3">
                    {template.photosPostsPerDay > 0 && (
                      <div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-2xl border border-gray-100">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-blue-100 rounded-xl flex items-center justify-center">
                            <div className="text-blue-600 text-sm font-bold">📁</div>
                          </div>
                          <div>
                            <span className="text-sm font-semibold text-gray-900">Photos</span>
                            {template.photosFolder && (
                              <div className="text-xs text-gray-500 truncate max-w-32">
                                {template.photosFolder}
                              </div>
                            )}
                          </div>
                        </div>
                        <Badge variant="outline" className="text-xs bg-white border-gray-200 text-gray-700">
                          {template.photosPostsPerDay}/day
                        </Badge>
                      </div>
                    )}
                    
                    {template.textPostsPerDay > 0 && (
                      <div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-2xl border border-gray-100">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-green-100 rounded-xl flex items-center justify-center">
                            <div className="text-green-600 text-sm font-bold">📝</div>
                          </div>
                          <div>
                            <span className="text-sm font-semibold text-gray-900">Text Posts</span>
                            {template.textPostsFile && (
                              <div className="text-xs text-gray-500 truncate max-w-32">
                                {template.textPostsFile}
                              </div>
                            )}
                          </div>
                        </div>
                        <Badge variant="outline" className="text-xs bg-white border-gray-200 text-gray-700">
                          {template.textPostsPerDay}/day
                        </Badge>
                      </div>
                    )}
                    
                    {template.captionsFile && (
                      <div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-2xl border border-gray-100">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-purple-100 rounded-xl flex items-center justify-center">
                            <div className="text-purple-600 text-sm font-bold">💬</div>
                          </div>
                          <div>
                            <span className="text-sm font-semibold text-gray-900">Captions</span>
                            <div className="text-xs text-gray-500 truncate max-w-32">
                              {template.captionsFile}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions Section */}
                <div className="space-y-3">
                  <h4 className="text-sm font-bold text-gray-900 uppercase tracking-wide">Actions</h4>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="py-3 px-3 bg-gray-50 rounded-2xl text-center border border-gray-100">
                      <div className="text-xl font-bold text-gray-900">{template.likesPerDay}</div>
                      <div className="text-xs text-gray-500 font-medium">Likes</div>
                    </div>
                    <div className="py-3 px-3 bg-gray-50 rounded-2xl text-center border border-gray-100">
                      <div className="text-xl font-bold text-gray-900">{template.followsPerDay}</div>
                      <div className="text-xs text-gray-500 font-medium">Follows</div>
                    </div>
                    <div className="py-3 px-3 bg-gray-50 rounded-2xl text-center border border-gray-100">
                      <div className="text-xl font-bold text-gray-900">{template.scrollingTimeMinutes}</div>
                      <div className="text-xs text-gray-500 font-medium">Min</div>
                    </div>
                  </div>
                  <div className="pt-3 border-t border-gray-100">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-gray-900">Total Actions:</span>
                      <Badge variant="secondary" className="text-xs bg-gray-900 text-white border-0">
                        {calculateTotalActions(template)} per day
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
          </Card>
        ))}
        </div>
      </div>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Template</DialogTitle>
            <DialogDescription>
              Update the daily limits, content types, and safety buffers for this template.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6 py-4">
            {/* Basic Information */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-name">Template Name</Label>
                <Input
                  id="edit-name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g., Conservative Threads Template"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-platform">Platform</Label>
                <Select
                  value={formData.platform}
                  onValueChange={(value: "threads" | "instagram") => setFormData({...formData, platform: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select platform" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="threads">
                      <div className="flex items-center">
                        <Hash className="w-4 h-4 mr-2" />
                        Threads
                      </div>
                    </SelectItem>
                    <SelectItem value="instagram">
                      <div className="flex items-center">
                        <Instagram className="w-4 h-4 mr-2" />
                        Instagram
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Photos Posts per Day with Folder Selection */}
            <div className="space-y-2">
              <Label>Photos Posts per Day</Label>
              <div className="grid grid-cols-2 gap-2">
                <Input
                  placeholder="Photos per Day"
                  type="number"
                  min="0"
                  value={formData.photosPostsPerDay}
                  onChange={(e) => setFormData({...formData, photosPostsPerDay: parseInt(e.target.value) || 0})}
                />
                <div className="flex gap-2">
                  <Input
                    placeholder="Select photos folder"
                    value={formData.photosFolder}
                    onChange={(e) => setFormData({...formData, photosFolder: e.target.value})}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => handleFolderSelect('photosFolder')}
                  >
                    <FolderOpen className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Text Posts per Day with XLSX File Selection */}
            <div className="space-y-2">
              <Label>Text Posts per Day</Label>
              <div className="grid grid-cols-2 gap-2">
                <Input
                  placeholder="Text Posts per Day"
                  type="number"
                  min="0"
                  value={formData.textPostsPerDay}
                  onChange={(e) => setFormData({...formData, textPostsPerDay: parseInt(e.target.value) || 0})}
                />
                <div className="flex gap-2">
                  <Input
                    placeholder="Select XLSX file"
                    value={formData.textPostsFile}
                    onChange={(e) => setFormData({...formData, textPostsFile: e.target.value})}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => handleFileSelect('textPostsFile')}
                  >
                    <FolderOpen className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Follows and Likes per Day */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-followsPerDay">Follows per Day</Label>
                <Input
                  id="edit-followsPerDay"
                  type="number"
                  min="0"
                  value={formData.followsPerDay}
                  onChange={(e) => setFormData({...formData, followsPerDay: parseInt(e.target.value) || 0})}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-likesPerDay">Likes per Day</Label>
                <Input
                  id="edit-likesPerDay"
                  type="number"
                  min="0"
                  value={formData.likesPerDay}
                  onChange={(e) => setFormData({...formData, likesPerDay: parseInt(e.target.value) || 0})}
                />
              </div>
            </div>

            {/* Captions and Scrolling Time */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Captions (for photos)</Label>
                <Button
                  type="button"
                  variant="outline"
                  className="justify-start text-left w-full"
                  onClick={() => handleFileSelect('captionsFile')}
                >
                  <FolderOpen className="w-4 h-4 mr-2" />
                  {formData.captionsFile || "Select XLSX file"}
                </Button>
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-scrollingTimeMinutes">Scrolling Time (in minutes)</Label>
                <Input
                  id="edit-scrollingTimeMinutes"
                  type="number"
                  min="0"
                  value={formData.scrollingTimeMinutes}
                  onChange={(e) => setFormData({...formData, scrollingTimeMinutes: parseInt(e.target.value) || 0})}
                  placeholder="e.g., 30"
                />
              </div>
            </div>

          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateTemplate}>
              Update Template
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Template Execution Dialog */}
      <TemplateExecutionDialog
        template={selectedTemplate}
        devices={devices?.data?.items || []}
        accounts={accounts?.data?.items || []}
        isOpen={isExecutionDialogOpen}
        onClose={() => {
          setIsExecutionDialogOpen(false)
          setSelectedTemplate(null)
        }}
        onExecute={handleTemplateExecution}
      />

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