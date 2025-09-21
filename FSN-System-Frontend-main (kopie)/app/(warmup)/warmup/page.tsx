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
        // Filter templates by current platform
        const filteredTemplates = savedTemplates.filter((t: any) => t.platform === platform)
        setWarmupTemplates(filteredTemplates)
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
      await licenseAwareStorageService.updateWarmupTemplate(editingTemplate.id, formData)
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
      await licenseAwareStorageService.deleteWarmupTemplate(id)
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
    <LicenseBlocker action="access warmup templates" platform={platform}>
      <div className="space-y-6">
      <HeroCard 
        title="Warmup Templates" 
        subtitle="Create and manage warmup templates for gradual account growth"
        icon={Thermometer}
      >
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={resetForm}>
              <Plus className="w-4 h-4 mr-2" />
              Create Warmup Template
            </Button>
          </DialogTrigger>
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
      </HeroCard>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {warmupTemplates.map((template) => (
          <Card key={template.id} className="relative">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CardTitle className="text-lg">{template.name}</CardTitle>
                  <Badge variant={template.platform === "threads" ? "default" : "secondary"}>
                    {template.platform === "threads" ? (
                      <div className="flex items-center">
                        <Hash className="w-3 h-3 mr-1" />
                        Threads
                      </div>
                    ) : (
                      <div className="flex items-center">
                        <Instagram className="w-3 h-3 mr-1" />
                        Instagram
                      </div>
                    )}
                  </Badge>
                </div>
                <div className="flex space-x-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEditTemplate(template)}
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDuplicateTemplate(template)}
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteTemplate(template.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              <CardDescription>
                {template.description || "No description"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Days Summary */}
              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-muted-foreground">Warmup Schedule</h4>
                <div className="space-y-2 text-sm">
                  {template.days?.slice(0, 3).map((day) => (
                    <div key={day.day} className="flex justify-between">
                      <span className="text-muted-foreground">Day {day.day}:</span>
                      <div className="flex space-x-4">
                        <span>{day.scrollTime}min scroll</span>
                        <span>{day.likes} likes</span>
                        <span>{day.follows} follows</span>
                      </div>
                    </div>
                  )) || (
                    <div className="text-sm text-muted-foreground">No warmup schedule defined</div>
                  )}
                  {template.days && template.days.length > 3 && (
                    <div className="text-xs text-muted-foreground">
                      +{template.days.length - 3} more days...
                    </div>
                  )}
                </div>
              </div>
              
              {/* Summary */}
              <div className="pt-2 border-t">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Total Actions:</span>
                    <Badge variant="secondary">
                      {calculateTotalActions(template)}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Total Scroll:</span>
                    <Badge variant="outline">
                      {calculateTotalScrollTime(template)}min
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
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
