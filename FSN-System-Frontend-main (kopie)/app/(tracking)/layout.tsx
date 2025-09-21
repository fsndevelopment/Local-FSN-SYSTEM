import type React from "react"
import { Sidebar } from "@/components/sidebar"
import { Topbar } from "@/components/topbar"
import { QueryProvider } from "@/lib/providers/query-provider"

export default function TrackingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="ml-24 p-6">
        <Topbar />
        <QueryProvider>{children}</QueryProvider>
      </main>
    </div>
  )
}
