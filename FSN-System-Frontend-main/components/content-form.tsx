"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Upload, X, ImageIcon } from "lucide-react"

interface ContentFormProps {
  isOpen: boolean
  onClose: () => void
  onSave: (content: any) => void
}

export function ContentForm({ isOpen, onClose, onSave }: ContentFormProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [caption, setCaption] = useState("")
  const [tags, setTags] = useState("")
  const [account, setAccount] = useState("")
  const [scheduleTime, setScheduleTime] = useState("")

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const file = event.dataTransfer.files[0]
    if (file && file.type.startsWith("image/")) {
      setSelectedFile(file)
    }
  }

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
  }

  const handleSave = () => {
    onSave({
      file: selectedFile,
      caption,
      tags: tags.split(",").map((tag) => tag.trim()),
      account,
      scheduleTime,
    })
    // Reset form
    setSelectedFile(null)
    setCaption("")
    setTags("")
    setAccount("")
    setScheduleTime("")
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card rounded-2xl shadow-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Upload Content</h2>
          <Button variant="outline" size="icon" onClick={onClose} className="rounded-full bg-transparent">
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="space-y-6">
          <div>
            <Label>Media File</Label>
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-border rounded-2xl p-8 text-center hover:border-muted-foreground transition-colors cursor-pointer"
            >
              {selectedFile ? (
                <div className="space-y-2">
                  <ImageIcon className="w-12 h-12 mx-auto text-muted-foreground" />
                  <div className="font-medium">{selectedFile.name}</div>
                  <div className="text-sm text-muted-foreground">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</div>
                  <Button variant="outline" size="sm" onClick={() => setSelectedFile(null)} className="rounded-full">
                    Remove
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="w-12 h-12 mx-auto text-muted-foreground" />
                  <div className="font-medium">Drop your image here</div>
                  <div className="text-sm text-muted-foreground">or click to browse</div>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileSelect}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                </div>
              )}
            </div>
          </div>

          <div>
            <Label htmlFor="account">Target Account</Label>
            <Select value={account} onValueChange={setAccount}>
              <SelectTrigger className="rounded-full">
                <SelectValue placeholder="Select account..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="lifestyle_blogger">@lifestyle_blogger</SelectItem>
                <SelectItem value="fitness_guru">@fitness_guru</SelectItem>
                <SelectItem value="tech_reviewer">@tech_reviewer</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="caption">Caption Template</Label>
            <Textarea
              id="caption"
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder="Write your caption here... Use {hashtags} for dynamic tags"
              className="rounded-2xl min-h-[100px]"
            />
          </div>

          <div>
            <Label htmlFor="tags">Tags (comma separated)</Label>
            <Input
              id="tags"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="lifestyle, motivation, daily"
              className="rounded-full"
            />
          </div>

          <div>
            <Label htmlFor="scheduleTime">Schedule Time (optional)</Label>
            <Input
              id="scheduleTime"
              type="datetime-local"
              value={scheduleTime}
              onChange={(e) => setScheduleTime(e.target.value)}
              className="rounded-full"
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <Button variant="outline" onClick={onClose} className="flex-1 rounded-full bg-transparent">
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={!selectedFile || !account}
              className="flex-1 bg-black text-white hover:bg-neutral-900 rounded-full disabled:opacity-50"
            >
              Create Post Job
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
