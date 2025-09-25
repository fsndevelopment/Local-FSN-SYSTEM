/**
 * Platform Color System
 * 
 * Dynamic color schemes that change based on selected platform
 */

import { Platform } from "@/lib/platform"

export interface PlatformColors {
  // Header/Hero card gradients
  headerGradient: string
  headerFrom: string
  headerTo: string
  headerVia?: string
  
  // Sidebar colors
  sidebarBg: string
  sidebarAccent: string
  sidebarHover: string
  sidebarActive: string
  
  // Accent colors
  primary: string
  primaryHover: string
  secondary: string
  
  // CSS custom properties for smooth transitions
  cssVars: Record<string, string>
}

export const platformColors: Record<Platform, PlatformColors> = {
  instagram: {
    // Instagram gradient (purple to pink to orange)
    headerGradient: "bg-gradient-to-br from-purple-600 via-pink-600 to-orange-500",
    headerFrom: "from-purple-600",
    headerTo: "to-orange-500", 
    headerVia: "via-pink-600",
    
    // Sidebar Instagram theme
    sidebarBg: "bg-gradient-to-b from-purple-900 via-pink-900 to-orange-900",
    sidebarAccent: "bg-purple-600",
    sidebarHover: "hover:bg-purple-600/20",
    sidebarActive: "bg-purple-600/30",
    
    // Accent colors
    primary: "bg-purple-600",
    primaryHover: "hover:bg-purple-700",
    secondary: "bg-pink-500",
    
    // CSS custom properties
    cssVars: {
      '--platform-primary': '147 51 234', // purple-600 RGB
      '--platform-secondary': '236 72 153', // pink-500 RGB
      '--platform-accent': '249 115 22', // orange-500 RGB
      '--platform-gradient-start': '147 51 234', // purple-600
      '--platform-gradient-middle': '236 72 153', // pink-600
      '--platform-gradient-end': '249 115 22', // orange-500
    }
  },
  
  threads: {
    // Threads - keep current black/gray theme
    headerGradient: "bg-gradient-to-r from-black via-gray-900 to-black",
    headerFrom: "from-black",
    headerTo: "to-black",
    headerVia: "via-gray-900",
    
    // Sidebar current theme
    sidebarBg: "bg-gradient-to-b from-gray-900 to-black",
    sidebarAccent: "bg-gray-800",
    sidebarHover: "hover:bg-gray-800/50",
    sidebarActive: "bg-gray-700/50",
    
    // Accent colors
    primary: "bg-black",
    primaryHover: "hover:bg-gray-800",
    secondary: "bg-gray-700",
    
    // CSS custom properties  
    cssVars: {
      '--platform-primary': '0 0 0', // black RGB
      '--platform-secondary': '55 65 81', // gray-700 RGB
      '--platform-accent': '31 41 55', // gray-800 RGB
      '--platform-gradient-start': '0 0 0', // black
      '--platform-gradient-middle': '17 24 39', // gray-900
      '--platform-gradient-end': '0 0 0', // black
    }
  }
}

export function getPlatformColors(platform: Platform): PlatformColors {
  return platformColors[platform]
}

export function getPlatformCSSVars(platform: Platform): Record<string, string> {
  return platformColors[platform].cssVars
}

// Hook to get current platform colors
export function usePlatformColors(platform: Platform) {
  return {
    colors: getPlatformColors(platform),
    cssVars: getPlatformCSSVars(platform),
    
    // Helper functions for common use cases
    getHeaderClasses: () => platformColors[platform].headerGradient,
    getSidebarClasses: () => platformColors[platform].sidebarBg,
    getPrimaryClasses: () => platformColors[platform].primary,
    getPrimaryHoverClasses: () => platformColors[platform].primaryHover,
  }
}

// Generate CSS custom properties string for inline styles
export function getPlatformCSSVarsString(platform: Platform): string {
  const vars = getPlatformCSSVars(platform)
  return Object.entries(vars)
    .map(([key, value]) => `${key}: ${value}`)
    .join('; ')
}
