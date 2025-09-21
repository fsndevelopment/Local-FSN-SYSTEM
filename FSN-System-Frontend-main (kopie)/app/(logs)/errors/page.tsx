"use client"

import { useState } from "react"
import { HeroCard } from "@/components/hero-card"
import { StatusBadge } from "@/components/status-badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle, CheckCircle, XCircle, Clock } from "lucide-react"

// Mock error data - TODO: Replace with real API data
const errors = [
  {
    id: "1",
    time: "2024-01-15 14:32:15",
    entity: "@lifestyle_blogger",
    type: "Checkpoint" as const,
    message: "Account requires phone verification",
    status: "unresolved" as const,
  },
  {
    id: "2",
    time: "2024-01-15 13:45:22",
    entity: "iPhone 15 Pro",
    type: "Captcha" as const,
    message: "CAPTCHA challenge detected during login",
    status: "resolved" as const,
  },
  {
    id: "3",
    time: "2024-01-15 12:18:33",
    entity: "@fitness_guru",
    type: "UploadFail" as const,
    message: "Failed to upload story: Network timeout",
    status: "unresolved" as const,
  },
  {
    id: "4",
    time: "2024-01-15 11:55:44",
    entity: "@tech_reviewer",
    type: "Checkpoint" as const,
    message: "Suspicious activity detected, account temporarily limited",
    status: "investigating" as const,
  },
  {
    id: "5",
    time: "2024-01-15 10:22:11",
    entity: "iPhone 14",
    type: "UploadFail" as const,
    message: "Post upload failed: Invalid media format",
    status: "resolved" as const,
  },
  {
    id: "6",
    time: "2024-01-15 09:15:55",
    entity: "@food_lover",
    type: "Captcha" as const,
    message: "Image verification required for follow action",
    status: "unresolved" as const,
  },
]

const getTypeIcon = (type: string) => {
  switch (type) {
    case "Checkpoint":
      return <AlertTriangle className="w-4 h-4 text-yellow-500" />
    case "Captcha":
      return <XCircle className="w-4 h-4 text-red-500" />
    case "UploadFail":
      return <XCircle className="w-4 h-4 text-red-500" />
    default:
      return <AlertTriangle className="w-4 h-4 text-yellow-500" />
  }
}

const getTypeBadge = (type: string) => {
  const colors = {
    Checkpoint: "bg-yellow-100 text-yellow-800",
    Captcha: "bg-red-100 text-red-800",
    UploadFail: "bg-red-100 text-red-800",
  }
  return <Badge className={`text-xs ${colors[type as keyof typeof colors]}`}>{type}</Badge>
}

export default function ErrorsPage() {
  const [selectedErrors, setSelectedErrors] = useState<string[]>([])
  const [filter, setFilter] = useState("all")

  const filteredErrors = errors.filter((error) => {
    if (filter === "all") return true
    return error.status === filter
  })

  const handleSelectAll = () => {
    if (selectedErrors.length === filteredErrors.length) {
      setSelectedErrors([])
    } else {
      setSelectedErrors(filteredErrors.map((error) => error.id))
    }
  }

  const handleSelectError = (errorId: string) => {
    setSelectedErrors((prev) => (prev.includes(errorId) ? prev.filter((id) => id !== errorId) : [...prev, errorId]))
  }

  const handleBulkResolve = () => {
    console.log("Resolving errors:", selectedErrors)
    
    if (selectedErrors.length === 0) {
      alert("Please select errors to resolve")
      return
    }
    
    alert(`${selectedErrors.length} error(s) have been resolved! (This is a simulation - real API integration needed)`)
    
    // In a real app, this would update the backend
    setSelectedErrors([])
  }

  const handleResolveError = (errorId: string) => {
    console.log("Resolving error:", errorId)
    // In a real app, this would update the backend
  }

  return (
    <div className="space-y-6">
      <HeroCard title="Error Management" subtitle="Monitor and resolve system errors" icon={AlertTriangle}>
        <div className="flex space-x-2">
          {selectedErrors.length > 0 && (
            <Button
              onClick={handleBulkResolve}
              className="bg-green-600 text-white hover:bg-green-700 rounded-full px-6"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Resolve {selectedErrors.length} Error{selectedErrors.length !== 1 ? "s" : ""}
            </Button>
          )}
        </div>
      </HeroCard>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-card rounded-2xl shadow p-6">
          <div className="text-2xl font-bold text-red-600 mb-1">
            {errors.filter((e) => e.status === "unresolved").length}
          </div>
          <div className="text-sm font-medium text-foreground mb-1">Unresolved</div>
          <div className="text-xs text-muted-foreground">Need attention</div>
        </div>

        <div className="bg-card rounded-2xl shadow p-6">
          <div className="text-2xl font-bold text-yellow-600 mb-1">
            {errors.filter((e) => e.status === "investigating").length}
          </div>
          <div className="text-sm font-medium text-foreground mb-1">Investigating</div>
          <div className="text-xs text-muted-foreground">In progress</div>
        </div>

        <div className="bg-card rounded-2xl shadow p-6">
          <div className="text-2xl font-bold text-green-600 mb-1">
            {errors.filter((e) => e.status === "resolved").length}
          </div>
          <div className="text-sm font-medium text-foreground mb-1">Resolved</div>
          <div className="text-xs text-muted-foreground">Fixed today</div>
        </div>

        <div className="bg-card rounded-2xl shadow p-6">
          <div className="text-2xl font-bold text-foreground mb-1">{errors.length}</div>
          <div className="text-sm font-medium text-foreground mb-1">Total Errors</div>
          <div className="text-xs text-muted-foreground">Last 24 hours</div>
        </div>
      </div>

      <div className="bg-card rounded-2xl shadow p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="font-semibold">Error Log</h3>
          <div className="flex space-x-2">
            <button
              onClick={() => setFilter("all")}
              className={`px-3 py-1 text-xs rounded-full ${
                filter === "all" ? "bg-black text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter("unresolved")}
              className={`px-3 py-1 text-xs rounded-full ${
                filter === "unresolved" ? "bg-black text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              Unresolved
            </button>
            <button
              onClick={() => setFilter("investigating")}
              className={`px-3 py-1 text-xs rounded-full ${
                filter === "investigating" ? "bg-black text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              Investigating
            </button>
            <button
              onClick={() => setFilter("resolved")}
              className={`px-3 py-1 text-xs rounded-full ${
                filter === "resolved" ? "bg-black text-white" : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              Resolved
            </button>
          </div>
        </div>

        <div className="space-y-1">
          <div className="flex items-center space-x-4 p-3 bg-muted/20 rounded-xl font-medium text-sm">
            <Checkbox checked={selectedErrors.length === filteredErrors.length} onCheckedChange={handleSelectAll} />
            <div className="flex-1 grid grid-cols-6 gap-4">
              <div>Time</div>
              <div>Entity</div>
              <div>Type</div>
              <div className="col-span-2">Message</div>
              <div>Status</div>
            </div>
            <div className="w-20">Action</div>
          </div>

          {filteredErrors.map((error) => (
            <div
              key={error.id}
              className="flex items-center space-x-4 p-3 bg-muted/10 rounded-xl hover:bg-muted/20 transition-colors"
            >
              <Checkbox
                checked={selectedErrors.includes(error.id)}
                onCheckedChange={() => handleSelectError(error.id)}
              />
              <div className="flex-1 grid grid-cols-6 gap-4 text-sm">
                <div className="font-mono text-xs">{error.time.split(" ")[1]}</div>
                <div className="font-medium">{error.entity}</div>
                <div className="flex items-center space-x-2">
                  {getTypeIcon(error.type)}
                  {getTypeBadge(error.type)}
                </div>
                <div className="col-span-2 text-muted-foreground">{error.message}</div>
                <div>
                  <StatusBadge
                    status={
                      error.status === "resolved" ? "success" : error.status === "investigating" ? "pending" : "error"
                    }
                  >
                    {error.status === "resolved"
                      ? "Resolved"
                      : error.status === "investigating"
                        ? "Investigating"
                        : "Unresolved"}
                  </StatusBadge>
                </div>
              </div>
              <div className="w-20">
                {error.status === "unresolved" && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleResolveError(error.id)}
                    className="rounded-full bg-green-50 text-green-700 border-green-200 hover:bg-green-100"
                  >
                    Resolve
                  </Button>
                )}
                {error.status === "resolved" && (
                  <Button variant="outline" size="sm" className="rounded-full bg-transparent" disabled>
                    <CheckCircle className="w-3 h-3" />
                  </Button>
                )}
                {error.status === "investigating" && (
                  <Button variant="outline" size="sm" className="rounded-full bg-transparent" disabled>
                    <Clock className="w-3 h-3" />
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
