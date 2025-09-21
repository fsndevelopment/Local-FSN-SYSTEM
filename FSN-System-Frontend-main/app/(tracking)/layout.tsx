import type React from "react"
import { Sidebar } from "@/components/sidebar"
import { QueryProvider } from "@/lib/providers/query-provider"

export default function TrackingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="ml-24">
        <QueryProvider>{children}</QueryProvider>
      </main>
    </div>
  )
}
