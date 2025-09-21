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
import { Plus, Edit, Trash2, Copy, Settings, Instagram, MessageSquare, Calendar, Clock, Heart, UserPlus, MessageCircle, Hash, Thermometer } from "lucide-react"
import { LicenseBlocker } from "@/components/license-blocker"

import { WarmupTemplate, WarmupDay } from "@/lib/types"
import { SuccessPopup } from "@/components/ui/unified-popup"
import { HeroCard } from "@/components/hero-card"
import { usePlatform } from "@/lib/platform"
import { PlatformSwitch } from "@/components/platform-switch"
import { GlobalSearchBar } from "@/components/search/global-search-bar"
import { licenseAwareStorageService, LocalWarmupTemplate } from "@/lib/services/license-aware-storage-service"


export default function WarmupPage() {
  const [warmupTemplates, setWarmupTemplates] = useState<LocalWarmupTemplate[]>([])
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const [successMessage, setSuccessMessage] = useState("")
  const [editingTemplate, setEditingTemplate] = useState<LocalWarmupTemplate | null>(null)
  const [platform] = usePlatform()
  const [formData, setFormData] = useState({
    name: "",
    platform: "threads" as "threads" | "instagram",
    description: "",
    days: [
      { day: 1, scrollTime: 10, likes: 5, follows: 2, comments: 0, stories: 0, posts: 0 }
    ] as WarmupDay[]
  })

  // Load warmup templates from license-aware storage on component mount
  useEffect(() => {
    const loadTemplates = async () => {
      try {
        const savedTemplates = await licenseAwareStorageService.getWarmupTemplates() // Get actual warmup templates
        // Filter templates by current platform (show all if platform is 'all')
        const filteredTemplates = platform === 'all' 
          ? savedTemplates 
          : savedTemplates.filter((t: any) => t.platform === platform)
        setWarmupTemplates(filteredTemplates)
        console.log('🔥 WARMUP - Loaded warmup templates:', {
          total: savedTemplates.length,
          filtered: filteredTemplates.length,
          platform,
          templates: filteredTemplates.map(t => ({ id: t.id, name: t.name, platform: t.platform }))
        })
      } catch (error) {
        console.error('Failed to load warmup templates:', error)
        setWarmupTemplates([])
      }
    }
    
    loadTemplates()
  }, [platform])

  const addDay = () => {
    const newDay: WarmupDay = {
      day: formData.days.length + 1,
      scrollTime: 10,
      likes: 5,
      follows: 2,
      comments: 0,
      stories: 0,
      posts: 0
    }
    setFormData({
      ...formData,
      days: [...formData.days, newDay]
    })
  }

  const removeDay = (dayIndex: number) => {
    if (formData.days.length <= 1) return // Keep at least one day
    
    const updatedDays = formData.days
      .filter((_, index) => index !== dayIndex)
      .map((day, index) => ({ ...day, day: index + 1 }))
    
    setFormData({
      ...formData,
      days: updatedDays
    })
  }

  const updateDay = (dayIndex: number, field: keyof WarmupDay, value: number) => {
    const updatedDays = formData.days.map((day, index) => 
      index === dayIndex ? { ...day, [field]: value } : day
    )
    setFormData({
      ...formData,
      days: updatedDays
    })
  }

  const handleCreateTemplate = async () => {
    const newTemplate: LocalWarmupTemplate = {
      id: Date.now().toString(),
      ...formData,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    
    try {
      await licenseAwareStorageService.addWarmupTemplate(newTemplate)
      const updatedTemplates = [...warmupTemplates, newTemplate]
      setWarmupTemplates(updatedTemplates)
      
      setSuccessMessage("Warmup template created successfully!")
      setShowSuccess(true)
      setIsCreateDialogOpen(false)
      resetForm()
    } catch (error) {
      console.error('Failed to create warmup template:', error)
      setSuccessMessage("Failed to create warmup template. Please try again.")
      setShowSuccess(true)
    }
  }

  const handleEditTemplate = (template: LocalWarmupTemplate) => {
    setEditingTemplate(template)
    setFormData({
      name: template.name,
      platform: template.platform,
      description: template.description || "",
      days: template.days
    })
    setIsEditDialogOpen(true)
  }

  const handleUpdateTemplate = async () => {
    if (!editingTemplate) return
    
    const updatedTemplate: LocalWarmupTemplate = {
      ...editingTemplate,
      ...formData,
      updatedAt: new Date().toISOString()
    }
    
    try {
      await licenseAwareStorageService.updateTemplate(editingTemplate.id, formData)
      const updatedTemplates = warmupTemplates.map(t => 
        t.id === editingTemplate.id ? updatedTemplate : t
      )
      setWarmupTemplates(updatedTemplates)
      
      setSuccessMessage("Warmup template updated successfully!")
      setShowSuccess(true)
      setIsEditDialogOpen(false)
      setEditingTemplate(null)
      resetForm()
    } catch (error) {
      console.error('Failed to update warmup template:', error)
      setSuccessMessage("Failed to update warmup template. Please try again.")
      setShowSuccess(true)
    }
  }

  const handleDeleteTemplate = async (id: string) => {
    try {
      await licenseAwareStorageService.deleteTemplate(id)
      const updatedTemplates = warmupTemplates.filter(t => t.id !== id)
      setWarmupTemplates(updatedTemplates)
      
      setSuccessMessage("Warmup template deleted successfully!")
      setShowSuccess(true)
    } catch (error) {
      console.error('Failed to delete warmup template:', error)
      setSuccessMessage("Failed to delete warmup template. Please try again.")
      setShowSuccess(true)
    }
  }

  const handleDuplicateTemplate = (template: LocalWarmupTemplate) => {
    const duplicatedTemplate: LocalWarmupTemplate = {
      ...template,
      id: Date.now().toString(),
      name: `${template.name} (Copy)`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    const updatedTemplates = [...warmupTemplates, duplicatedTemplate]
    setWarmupTemplates(updatedTemplates)
    localStorage.setItem('warmupTemplates', JSON.stringify(updatedTemplates))
    
    setSuccessMessage("Warmup template duplicated successfully!")
    setShowSuccess(true)
  }

  const resetForm = () => {
    setFormData({
      name: "",
      platform: "threads",
      description: "",
      days: [
        { day: 1, scrollTime: 10, likes: 5, follows: 2, comments: 0, stories: 0, posts: 0 }
      ]
    })
  }

  const calculateTotalActions = (template: LocalWarmupTemplate) => {
    if (!template.days || template.days.length === 0) return 0
    return template.days.reduce((total, day) => {
      return total + day.likes + day.follows + (day.comments || 0) + (day.stories || 0) + (day.posts || 0)
    }, 0)
  }

  const calculateTotalScrollTime = (template: LocalWarmupTemplate) => {
    if (!template.days || template.days.length === 0) return 0
    return template.days.reduce((total, day) => total + day.scrollTime, 0)
  }

  return (
    <LicenseBlocker action="access warmup templates">
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
        {/* Main Header Section - Dark Background */}
        <div className="relative overflow-hidden bg-gradient-to-r from-black via-gray-900 to-black">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGRlZnM+CjxwYXR0ZXJuIGlkPSJncmlkIiB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHBhdHRlcm5Vbml0cz0idXNlclNwYWNlT25Vc2UiPgo8cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiLz4KPC9wYXR0ZXJuPgo8L2RlZnM+CjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz4KPHN2Zz4K')] opacity-10"></div>
          
          <div className="relative px-6 py-12">
            <div className="max-w-7xl mx-auto">
              <div className="flex items-center justify-between">
                <div className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center shadow-2xl">
                      <Thermometer className="w-6 h-6 text-black" />
                    </div>
                    <div>
                      <h1 className="text-4xl font-bold text-white tracking-tight">Warmup Templates</h1>
                      <p className="text-gray-300 text-lg mt-1">Create and manage warmup templates for gradual account growth</p>
                    </div>
                  </div>
                  
                  {/* Live Status Indicator */}
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 border border-white/20">
                      <div className="relative">
                        <div className="w-2 h-2 bg-orange-400 rounded-full animate-pulse"></div>
                        <div className="absolute inset-0 w-2 h-2 bg-orange-400 rounded-full animate-ping opacity-75"></div>
                      </div>
                      <span className="text-white text-sm font-medium">Warmup Active</span>
                    </div>
                    
                    <div className="text-white/60 text-sm">
                      Last updated: {new Date().toLocaleTimeString()}
                    </div>
                  </div>
                </div>
                
                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
                  <div className="flex items-center space-x-4">
                    <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                      <DialogTrigger asChild>
                        <Button 
                          onClick={resetForm}
                          className="bg-white text-black hover:bg-gray-100 font-semibold px-6 py-3 rounded-2xl shadow-2xl hover:shadow-3xl transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] border-0"
                        >
                          <Plus className="w-5 h-5 mr-2" />
                          Create Warmup Template
                        </Button>
                      </DialogTrigger>
                    </Dialog>
                    <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                      <DialogContent className="w-[60vw] max-w-[60vw] max-h-[80vh] flex flex-col sm:max-w-[60vw]">
            <DialogHeader className="flex-shrink-0">
              <DialogTitle>Create New Warmup Template</DialogTitle>
              <DialogDescription>
                Define a multi-day warmup schedule with scroll time, likes, follows, and other actions.
              </DialogDescription>
            </DialogHeader>
            <div className="flex-1 overflow-y-auto px-6">
              <div className="space-y-6 py-4">
                {/* Basic Information */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Template Name</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      placeholder="e.g., Conservative Threads Warmup"
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

                <div className="space-y-2">
                  <Label htmlFor="description">Description (Optional)</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    placeholder="Brief description of this warmup template"
                  />
                </div>

                {/* Days Configuration */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">Warmup Days</h3>
                    <Button type="button" variant="outline" onClick={addDay}>
                      <Plus className="w-4 h-4 mr-2" />
                      Add Day
                    </Button>
                  </div>
                  
                  <div className="space-y-4">
                    {formData.days.map((day, dayIndex) => (
                      <Card key={dayIndex} className="p-4">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="font-medium">Day {day.day}</h4>
                          {formData.days.length > 1 && (
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => removeDay(dayIndex)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                        
                        <div className="grid grid-cols-6 gap-8 min-w-full">
                          <div className="space-y-2 min-w-0">
                            <Label className="text-sm font-medium">Scroll (min)</Label>
                            <div className="border-2 border-gray-300 rounded-md p-1 bg-white">
                              <Input
                                type="number"
                                min="0"
                                value={day.scrollTime}
                                onChange={(e) => updateDay(dayIndex, 'scrollTime', parseInt(e.target.value) || 0)}
                                className="w-full border-0 p-0 focus:ring-0 focus:outline-none h-8"
                              />
                            </div>
                          </div>
                          
                          <div className="space-y-2 min-w-0">
                            <Label className="text-sm font-medium">Likes</Label>
                            <div className="border-2 border-gray-300 rounded-md p-1 bg-white">
                              <Input
                                type="number"
                                min="0"
                                value={day.likes}
                                onChange={(e) => updateDay(dayIndex, 'likes', parseInt(e.target.value) || 0)}
                                className="w-full border-0 p-0 focus:ring-0 focus:outline-none h-8"
                              />
                            </div>
                          </div>
                          
                          <div className="space-y-2 min-w-0">
                            <Label className="text-sm font-medium">Follows</Label>
                            <div className="border-2 border-gray-300 rounded-md p-1 bg-white">
                              <Input
                                type="number"
                                min="0"
                                value={day.follows}
                                onChange={(e) => updateDay(dayIndex, 'follows', parseInt(e.target.value) || 0)}
                                className="w-full border-0 p-0 focus:ring-0 focus:outline-none h-8"
                              />
                            </div>
                          </div>
                          
                          <div className="space-y-2 min-w-0">
                            <Label className="text-sm font-medium">Comments</Label>
                            <div className="border-2 border-gray-300 rounded-md p-1 bg-white">
                              <Input
                                type="number"
                                min="0"
                                value={day.comments || 0}
                                onChange={(e) => updateDay(dayIndex, 'comments', parseInt(e.target.value) || 0)}
                                className="w-full border-0 p-0 focus:ring-0 focus:outline-none h-8"
                              />
                            </div>
                          </div>
                          
                          <div className="space-y-2 min-w-0">
                            <Label className="text-sm font-medium">Stories</Label>
                            <div className="border-2 border-gray-300 rounded-md p-1 bg-white">
                              <Input
                                type="number"
                                min="0"
                                value={day.stories || 0}
                                onChange={(e) => updateDay(dayIndex, 'stories', parseInt(e.target.value) || 0)}
                                className="w-full border-0 p-0 focus:ring-0 focus:outline-none h-8"
                              />
                            </div>
                          </div>
                          
                          <div className="space-y-2 min-w-0">
                            <Label className="text-sm font-medium">Posts</Label>
                            <div className="border-2 border-gray-300 rounded-md p-1 bg-white">
                              <Input
                                type="number"
                                min="0"
                                value={day.posts || 0}
                                onChange={(e) => updateDay(dayIndex, 'posts', parseInt(e.target.value) || 0)}
                                className="w-full border-0 p-0 focus:ring-0 focus:outline-none h-8"
                              />
                            </div>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <DialogFooter className="flex-shrink-0">
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
              
              {/* Search Bar and Platform Switcher - Integrated into header */}
              <div className="mt-8">
                <div className="flex items-center justify-between">
                  {/* Search */}
                  <div className="flex-1 max-w-md">
                    <GlobalSearchBar placeholder="Search warmup templates..." />
                  </div>

                  {/* Right side */}
                  <div className="flex items-center space-x-4">
                    <PlatformSwitch />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {warmupTemplates.length === 0 ? (
            <div className="col-span-full text-center py-16">
              <div className="w-24 h-24 mx-auto mb-6 bg-gray-100 rounded-full flex items-center justify-center">
                <Thermometer className="w-12 h-12 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {platform === 'all' ? 'No Warmup Templates Found' : `No ${platform.charAt(0).toUpperCase() + platform.slice(1)} Warmup Templates`}
              </h3>
              <p className="text-gray-600 mb-6 max-w-md mx-auto">
                {platform === 'all' 
                  ? 'You don\'t have any warmup templates yet. Create your first warmup template to gradually increase your account activity.'
                  : `You don't have any ${platform} warmup templates yet. Create a new ${platform} warmup template to gradually increase your account activity.`
                }
              </p>
              <Button 
                onClick={() => setIsCreateDialogOpen(true)}
                className="bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-700 hover:to-amber-700 text-white px-6 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
              >
                <Plus className="w-5 h-5 mr-2" />
                Create Warmup Template
              </Button>
            </div>
          ) : (
            warmupTemplates.map((template) => (
            <Card key={template.id} className="relative bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 border border-gray-100 group overflow-hidden">
              {/* Status Strip */}
              <div className="h-1 w-full bg-gradient-to-r from-orange-400 to-amber-500"></div>
              
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-xl font-bold text-gray-900 mb-2">{template.name}</CardTitle>
                    <div className="flex items-center space-x-3 mb-3">
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
                    </div>
                    <CardDescription className="text-sm text-gray-600">
                      {template.description || "No description"}
                    </CardDescription>
                  </div>
                  <div className="flex space-x-1">
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
                {/* Days Summary */}
                <div className="space-y-3">
                  <h4 className="text-sm font-bold text-gray-900 uppercase tracking-wide">Warmup Schedule</h4>
                  <div className="space-y-3">
                    {template.days?.slice(0, 3).map((day) => (
                      <div key={day.day} className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-2xl border border-gray-100">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-orange-100 rounded-xl flex items-center justify-center">
                            <div className="text-orange-600 text-sm font-bold">🔥</div>
                          </div>
                          <div>
                            <span className="text-sm font-semibold text-gray-900">Day {day.day}</span>
                          </div>
                        </div>
                        <div className="flex space-x-3 text-xs text-gray-600">
                          <div className="bg-white px-2 py-1 rounded-lg border border-gray-200">
                            {day.scrollTime}min scroll
                          </div>
                          <div className="bg-white px-2 py-1 rounded-lg border border-gray-200">
                            {day.likes} likes
                          </div>
                          <div className="bg-white px-2 py-1 rounded-lg border border-gray-200">
                            {day.follows} follows
                          </div>
                        </div>
                      </div>
                    )) || (
                      <div className="text-sm text-gray-500 py-4 text-center bg-gray-50 rounded-2xl">
                        No warmup schedule defined
                      </div>
                    )}
                    {template.days && template.days.length > 3 && (
                      <div className="text-xs text-gray-500 text-center py-2 bg-gray-50 rounded-lg border border-gray-100">
                        +{template.days.length - 3} more days...
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Summary */}
                <div className="pt-3 border-t border-gray-100">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-2xl border border-gray-100">
                      <span className="text-sm font-semibold text-gray-900">Total Actions:</span>
                      <Badge variant="secondary" className="text-xs bg-gray-900 text-white border-0">
                        {calculateTotalActions(template)}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-2xl border border-gray-100">
                      <span className="text-sm font-semibold text-gray-900">Total Scroll:</span>
                      <Badge variant="outline" className="text-xs bg-white border-gray-200 text-gray-700">
                        {calculateTotalScrollTime(template)}min
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
          </Card>
            ))
          )}
        </div>
      </div>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="w-[60vw] max-w-[60vw] max-h-[80vh] flex flex-col sm:max-w-[60vw]">
          <DialogHeader className="flex-shrink-0">
            <DialogTitle>Edit Warmup Template</DialogTitle>
            <DialogDescription>
              Update the warmup schedule and actions for this template.
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto px-6">
            <div className="space-y-6 py-4">
              {/* Basic Information */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-name">Template Name</Label>
                <Input
                  id="edit-name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g., Conservative Threads Warmup"
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

            <div className="space-y-2">
              <Label htmlFor="edit-description">Description (Optional)</Label>
              <Input
                id="edit-description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Brief description of this warmup template"
              />
            </div>

            {/* Days Configuration */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Warmup Days</h3>
                <Button type="button" variant="outline" onClick={addDay}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Day
                </Button>
              </div>
              
              <div className="space-y-4">
                {formData.days.map((day, dayIndex) => (
                  <Card key={dayIndex} className="p-4">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-medium">Day {day.day}</h4>
                      {formData.days.length > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeDay(dayIndex)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-6 gap-8 min-w-full">
                      <div className="space-y-2 min-w-0">
                        <Label className="text-sm font-medium">Scroll (min)</Label>
                        <div className="border-2 border-gray-300 rounded-md p-1 bg-white">
                          <Input
                            type="number"
                            min="0"
                            value={day.scrollTime}
                            onChange={(e) => updateDay(dayIndex, 'scrollTime', parseInt(e.target.value) || 0)}
                            className="w-full border-0 p-0 focus:ring-0 focus:outline-none h-8"
                          />
                        </div>
                      </div>
                      
                      <div className="space-y-2 min-w-0">
                        <Label className="text-sm font-medium">Likes</Label>
                        <div className="border-2 border-gray-300 rounded-md p-1 bg-white">
                          <Input
                            type="number"
                            min="0"
                            value={day.likes}
                            onChange={(e) => updateDay(dayIndex, 'likes', parseInt(e.target.value) || 0)}
                            className="w-full border-0 p-0 focus:ring-0 focus:outline-none h-8"
                          />
                        </div>
                      </div>
                      
                      <div className="space-y-2 min-w-0">
                        <Label className="text-sm font-medium">Follows</Label>
                        <div className="border-2 border-gray-300 rounded-md p-1 bg-white">
                          <Input
                            type="number"
                            min="0"
                            value={day.follows}
                            onChange={(e) => updateDay(dayIndex, 'follows', parseInt(e.target.value) || 0)}
                            className="w-full border-0 p-0 focus:ring-0 focus:outline-none h-8"
                          />
                        </div>
                      </div>
                      
                      <div className="space-y-2 min-w-0">
                        <Label className="text-sm font-medium">Comments</Label>
                        <div className="border-2 border-gray-300 rounded-md p-1 bg-white">
                          <Input
                            type="number"
                            min="0"
                            value={day.comments || 0}
                            onChange={(e) => updateDay(dayIndex, 'comments', parseInt(e.target.value) || 0)}
                            className="w-full border-0 p-0 focus:ring-0 focus:outline-none h-8"
                          />
                        </div>
                      </div>
                      
                      <div className="space-y-2 min-w-0">
                        <Label className="text-sm font-medium">Stories</Label>
                        <div className="border-2 border-gray-300 rounded-md p-1 bg-white">
                          <Input
                            type="number"
                            min="0"
                            value={day.stories || 0}
                            onChange={(e) => updateDay(dayIndex, 'stories', parseInt(e.target.value) || 0)}
                            className="w-full border-0 p-0 focus:ring-0 focus:outline-none h-8"
                          />
                        </div>
                      </div>
                      
                      <div className="space-y-2 min-w-0">
                        <Label className="text-sm font-medium">Posts</Label>
                        <div className="border-2 border-gray-300 rounded-md p-1 bg-white">
                          <Input
                            type="number"
                            min="0"
                            value={day.posts || 0}
                            onChange={(e) => updateDay(dayIndex, 'posts', parseInt(e.target.value) || 0)}
                            className="w-full border-0 p-0 focus:ring-0 focus:outline-none h-8"
                          />
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
            </div>
          </div>
          <DialogFooter className="flex-shrink-0">
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateTemplate}>
              Update Template
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Success Popup */}
      <SuccessPopup
        isOpen={showSuccess}
        onClose={() => setShowSuccess(false)}
        title={successMessage}
        autoClose={true}
        duration={3000}
      />
      </div>
    </LicenseBlocker>
  )
}
