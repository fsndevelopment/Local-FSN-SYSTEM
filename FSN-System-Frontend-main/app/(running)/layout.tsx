import type React from "react"
import { Sidebar } from "@/components/sidebar"

export default function RunningLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="ml-24">
        {children}
      </main>
    </div>
  )
}

