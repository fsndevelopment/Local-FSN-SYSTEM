import type React from "react"
import { Sidebar } from "@/components/sidebar"
import { Topbar } from "@/components/topbar"

// Clean topbar for running tab
function RunningTopbar() {
  return (
    <div className="flex items-center justify-between mb-6">
      {/* Search */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <input
            type="text"
            placeholder="Search running devices..."
            className="w-full px-4 py-2 pl-10 pr-4 text-sm bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
          />
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Clean right side - just empty space for now */}
      <div className="flex items-center">
        {/* Nothing here - clean and simple */}
      </div>
    </div>
  )
}

export default function RunningLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="ml-24 p-6">
        <RunningTopbar />
        {children}
      </main>
    </div>
  )
}

