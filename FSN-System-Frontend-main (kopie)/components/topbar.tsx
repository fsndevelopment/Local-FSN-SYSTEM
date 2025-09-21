"use client"

// Removed Bell and Avatar imports - no longer needed
import { GlobalSearchBar } from "@/components/search/global-search-bar"
import { RealTimeStatusIndicator } from "@/components/real-time-status"
import { usePlatform } from "@/lib/platform"

export function Topbar() {
  const [current, setCurrent] = usePlatform()
  return (
    <div className="flex items-center justify-between mb-6">
      {/* Search */}
      <div className="flex-1 max-w-md">
        <GlobalSearchBar placeholder="Search devices, accounts, jobs..." />
      </div>

      {/* Right side */}
      <div className="flex items-center space-x-4">
        {/* Real-time status indicator */}
        <RealTimeStatusIndicator />
        
        <div className="flex items-center gap-1 rounded-md border p-1">
          <button
            aria-label="All Platforms"
            className={`px-2 py-1 rounded-sm transition-colors text-xs font-medium ${current === 'all' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            onClick={() => setCurrent('all')}
          >
            All
          </button>
          <button
            aria-label="Instagram"
            className={`px-2 py-1 rounded-sm transition-colors ${current === 'instagram' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            onClick={() => setCurrent('instagram')}
          >
            <img src="/instagram.png" alt="Instagram" className="h-5 w-5" />
          </button>
          <button
            aria-label="Threads"
            className={`px-2 py-1 rounded-sm transition-colors ${current === 'threads' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            onClick={() => setCurrent('threads')}
          >
            <img src="/threads.png" alt="Threads" className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
