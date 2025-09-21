"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Plus, Trash2, X } from "lucide-react"

interface TimeBlock {
  id: string
  start: string
  end: string
}

interface ActivityMix {
  likes: number
  follows: number
  comments: number
  stories: number
  posts: number
}

interface ScheduleFormProps {
  isOpen: boolean
  onClose: () => void
  onSave: (schedule: any) => void
  initialData?: any
}

export function ScheduleForm({ isOpen, onClose, onSave, initialData }: ScheduleFormProps) {
  const [name, setName] = useState(initialData?.name || "")
  const [timeBlocks, setTimeBlocks] = useState<TimeBlock[]>(
    initialData?.timeBlocks || [{ id: "1", start: "09:00", end: "17:00" }],
  )
  const [activityMix, setActivityMix] = useState<ActivityMix>(
    initialData?.activityMix || {
      likes: 40,
      follows: 20,
      comments: 15,
      stories: 15,
      posts: 10,
    },
  )

  const addTimeBlock = () => {
    const newBlock: TimeBlock = {
      id: Date.now().toString(),
      start: "09:00",
      end: "17:00",
    }
    setTimeBlocks([...timeBlocks, newBlock])
  }

  const removeTimeBlock = (id: string) => {
    setTimeBlocks(timeBlocks.filter((block) => block.id !== id))
  }

  const updateTimeBlock = (id: string, field: "start" | "end", value: string) => {
    setTimeBlocks(timeBlocks.map((block) => (block.id === id ? { ...block, [field]: value } : block)))
  }

  const updateActivityMix = (activity: keyof ActivityMix, value: number) => {
    const newMix = { ...activityMix, [activity]: value }
    const total = Object.values(newMix).reduce((sum, val) => sum + val, 0)

    if (total <= 100) {
      setActivityMix(newMix)
    }
  }

  const handleSave = () => {
    onSave({
      name,
      timeBlocks,
      activityMix,
    })
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card rounded-2xl shadow-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Create Schedule</h2>
          <Button variant="outline" size="icon" onClick={onClose} className="rounded-full bg-transparent">
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="space-y-6">
          <div>
            <Label htmlFor="name">Schedule Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Morning Activity"
              className="rounded-full"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-4">
              <Label>Time Blocks</Label>
              <Button variant="outline" size="sm" onClick={addTimeBlock} className="rounded-full bg-transparent">
                <Plus className="w-4 h-4 mr-2" />
                Add Block
              </Button>
            </div>

            <div className="space-y-3">
              {timeBlocks.map((block) => (
                <div key={block.id} className="flex items-center space-x-3 p-3 bg-muted/30 rounded-xl">
                  <Input
                    type="time"
                    value={block.start}
                    onChange={(e) => updateTimeBlock(block.id, "start", e.target.value)}
                    className="rounded-full"
                  />
                  <span className="text-muted-foreground">to</span>
                  <Input
                    type="time"
                    value={block.end}
                    onChange={(e) => updateTimeBlock(block.id, "end", e.target.value)}
                    className="rounded-full"
                  />
                  {timeBlocks.length > 1 && (
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => removeTimeBlock(block.id)}
                      className="rounded-full text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div>
            <Label className="mb-4 block">Activity Mix (must total 100%)</Label>
            <div className="space-y-4">
              {Object.entries(activityMix).map(([activity, value]) => (
                <div key={activity} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium capitalize">{activity}</span>
                    <span className="text-sm text-muted-foreground">{value}%</span>
                  </div>
                  <Slider
                    value={[value]}
                    onValueChange={([newValue]) => updateActivityMix(activity as keyof ActivityMix, newValue)}
                    max={100}
                    step={5}
                    className="w-full"
                  />
                </div>
              ))}
            </div>
            <div className="mt-2 text-sm text-muted-foreground">
              Total: {Object.values(activityMix).reduce((sum, val) => sum + val, 0)}%
            </div>
          </div>

          <div className="flex space-x-3 pt-4">
            <Button variant="outline" onClick={onClose} className="flex-1 rounded-full bg-transparent">
              Cancel
            </Button>
            <Button onClick={handleSave} className="flex-1 bg-black text-white hover:bg-neutral-900 rounded-full">
              Save Schedule
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
