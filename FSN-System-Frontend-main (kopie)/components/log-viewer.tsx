"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Trash2, Play, Square } from "lucide-react"

interface LogEntry {
  id: string
  timestamp: string
  level: "info" | "warn" | "error" | "debug"
  message: string
}

// Real logs will be fetched from API
const mockLogs: LogEntry[] = []

interface LogViewerProps {
  deviceId?: number
}

export function LogViewer({ deviceId }: LogViewerProps) {
  const [isLive, setIsLive] = useState(false)
  const [selectedLevel, setSelectedLevel] = useState<string>("all")
  const [logs, setLogs] = useState<LogEntry[]>([])

  // TODO: Implement real log fetching from API
  // For now, use empty logs
  const filteredLogs = logs.filter((log) => selectedLevel === "all" || log.level === selectedLevel)

  const getLevelColor = (level: string) => {
    switch (level) {
      case "error":
        return "bg-red-100 text-red-800"
      case "warn":
        return "bg-yellow-100 text-yellow-800"
      case "info":
        return "bg-blue-100 text-blue-800"
      case "debug":
        return "bg-gray-100 text-gray-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <div className="bg-card rounded-2xl shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Device Logs</h3>
        <div className="flex items-center space-x-2">
          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            className="px-3 py-1 text-xs bg-muted rounded-full border-0 focus:ring-2 focus:ring-ring"
          >
            <option value="all">All Levels</option>
            <option value="error">Error</option>
            <option value="warn">Warning</option>
            <option value="info">Info</option>
            <option value="debug">Debug</option>
          </select>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsLive(!isLive)}
            className={`rounded-full ${isLive ? "bg-red-100 text-red-800 border-red-200 hover:bg-red-200" : "bg-green-100 text-green-800 border-green-200 hover:bg-green-200"}`}
          >
            {isLive ? <Square className="w-3 h-3 mr-1" /> : <Play className="w-3 h-3 mr-1" />}
            {isLive ? "Stop" : "Live"}
          </Button>

          <Button variant="outline" size="sm" className="rounded-full bg-transparent">
            <Trash2 className="w-3 h-3 mr-1" />
            Clear
          </Button>
        </div>
      </div>

      <div className="bg-black rounded-xl p-4 h-64 overflow-y-auto font-mono text-sm">
        {filteredLogs.length > 0 ? (
          filteredLogs.map((log) => (
            <div key={log.id} className="flex items-start space-x-3 mb-2 text-white">
              <span className="text-gray-400 text-xs">{log.timestamp}</span>
              <Badge className={`text-xs ${getLevelColor(log.level)} font-mono`}>{log.level.toUpperCase()}</Badge>
              <span className="flex-1">{log.message}</span>
            </div>
          ))
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <div className="text-sm mb-2">No logs available</div>
              <div className="text-xs">Device logs will appear here when available</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
