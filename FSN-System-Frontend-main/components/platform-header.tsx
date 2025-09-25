"use client"

import { usePlatform } from "@/lib/platform"
import { usePlatformColors } from "@/lib/utils/platform-colors"
import { ReactNode, useEffect, useState, useRef } from "react"

interface PlatformHeaderProps {
  children: ReactNode
  className?: string
}

export function PlatformHeader({ children, className = "" }: PlatformHeaderProps) {
  const [currentPlatform] = usePlatform()
  const { colors, cssVars } = usePlatformColors(currentPlatform)

  // Apply CSS custom properties to document root for global access
  useEffect(() => {
    const root = document.documentElement
    Object.entries(cssVars).forEach(([property, value]) => {
      root.style.setProperty(property, value)
    })
  }, [cssVars])

  return (
    <div className={`relative overflow-hidden ${className}`}>
      {/* Threads background (always present) */}
      <div 
        className="absolute inset-0"
        style={{
          background: 'linear-gradient(90deg, rgb(0, 0, 0) 0%, rgb(17, 24, 39) 50%, rgb(0, 0, 0) 100%)',
        }}
      />
      
      {/* Instagram background (fades in/out) */}
      <div 
        className="absolute inset-0"
        style={{
          background: 'linear-gradient(135deg, rgb(88, 28, 135) 0%, rgb(157, 23, 77) 50%, rgb(194, 65, 12) 100%)',
          opacity: currentPlatform === 'instagram' ? 1 : 0,
          transition: 'opacity 1500ms cubic-bezier(0.25, 0.46, 0.45, 0.94)'
        }}
      />
      {/* Background pattern overlay */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGRlZnM+CjxwYXR0ZXJuIGlkPSJncmlkIiB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHBhdHRlcm5Vbml0cz0idXNlclNwYWNlT25Vc2UiPgo8cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiLz4KPC9wYXR0ZXJuPgo8L2RlZnM+CjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz4KPHN2Zz4K')] opacity-10"></div>
      
      {/* Content */}
      <div className="relative">
        {children}
      </div>
    </div>
  )
}
