"use client"

import { Check, AlertTriangle } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface WarmupItem {
  day: number
  task: string
  completed: boolean
  warning?: string
}

const warmupTasks: WarmupItem[] = [
  { day: 1, task: "Account created and verified", completed: true },
  { day: 2, task: "Profile setup completed", completed: true },
  { day: 3, task: "First post published", completed: true },
  { day: 4, task: "Add highlights", completed: false, warning: "Highlights should be added by Day 4" },
  { day: 5, task: "Follow 10-15 accounts", completed: true },
  { day: 6, task: "Engage with content", completed: true },
  { day: 7, task: "Add bio link", completed: false, warning: "Link should be added before Day 7-10" },
  { day: 8, task: "Story interactions", completed: true },
  { day: 9, task: "DM conversations", completed: false },
  { day: 10, task: "Full activity pattern", completed: false },
]

export function WarmupChecklist() {
  return (
    <div className="bg-card rounded-2xl shadow p-6">
      <h3 className="font-semibold mb-4">Warmup Checklist</h3>
      <div className="space-y-3">
        {warmupTasks.map((item) => (
          <div key={item.day} className="flex items-center justify-between p-3 bg-muted/30 rounded-xl">
            <div className="flex items-center space-x-3">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center ${
                  item.completed ? "bg-green-500 text-white" : "bg-muted border-2 border-border"
                }`}
              >
                {item.completed ? <Check className="w-3 h-3" /> : <span className="text-xs">{item.day}</span>}
              </div>
              <div>
                <div className="text-sm font-medium">Day {item.day}</div>
                <div className="text-xs text-muted-foreground">{item.task}</div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {item.warning && !item.completed && (
                <div className="flex items-center space-x-1">
                  <AlertTriangle className="w-4 h-4 text-yellow-500" />
                  <Badge variant="outline" className="text-xs text-yellow-700 border-yellow-200">
                    Warning
                  </Badge>
                </div>
              )}
              {item.completed && <Badge className="text-xs bg-green-100 text-green-800">Complete</Badge>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
