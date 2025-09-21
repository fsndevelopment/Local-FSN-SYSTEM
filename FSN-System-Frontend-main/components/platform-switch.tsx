"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { usePlatform } from "@/lib/platform"
import { Instagram, Hash } from "lucide-react"

export function PlatformSwitch() {
  const [platform, setPlatform] = usePlatform()

  const platforms = [
    { id: 'all' as const, label: 'All', icon: '🌐' },
    { id: 'instagram' as const, label: 'Instagram', icon: <Instagram className="w-4 h-4" /> },
    { id: 'threads' as const, label: 'Threads', icon: <Hash className="w-4 h-4" /> }
  ]

  return (
    <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm rounded-full px-2 py-1 border border-white/20">
      {platforms.map((p) => (
        <Button
          key={p.id}
          variant={platform === p.id ? "default" : "ghost"}
          size="sm"
          onClick={() => setPlatform(p.id)}
          className={`h-8 px-3 rounded-full text-xs font-medium transition-all duration-200 ${
            platform === p.id
              ? "bg-white text-black shadow-md"
              : "text-white hover:text-white hover:bg-white/10"
          }`}
        >
          <span className="mr-1">{p.icon}</span>
          {p.label}
        </Button>
      ))}
      <div className="flex items-center space-x-1 ml-2 pl-2 border-l border-white/20">
        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
        <span className="text-white text-xs font-medium">Connected</span>
      </div>
    </div>
  )
}
