"use client"

import type React from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"

export function QueryProvider({ children }: { children: React.ReactNode }) {
  // Create query client in component to avoid SSR issues
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes
        retry: 1,
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
      },
      mutations: {
        retry: 1,
      },
    },
  }))

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
